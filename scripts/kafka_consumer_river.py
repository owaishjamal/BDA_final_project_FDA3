#!/usr/bin/env python3
import json, threading, time, traceback
from kafka import KafkaConsumer, KafkaProducer
# guarded river imports for compatibility
try:
    from river import feature_extraction, naive_bayes, compose, ensemble, linear_model, drift
except Exception:
    feature_extraction = naive_bayes = compose = ensemble = linear_model = drift = None

BOOTSTRAP = "localhost:9092"
TEXT_TOPIC = "revenue_text_stream"
NUMERIC_TOPIC = "revenue_numeric_stream"
ALERT_TOPIC = "revenue_alerts"

def label_policy(text):
    t = (text or "").lower()
    if "aggressive" in t or "variable consideration" in t or "multiple-element" in t:
        return "Aggressive"
    if "conservative" in t or "immaterial" in t or "consistent" in t:
        return "Conservative"
    return "Neutral"

def make_text_model():
    try:
        return compose.Pipeline(feature_extraction.BagOfWords(lowercase=True), naive_bayes.MultinomialNB())
    except Exception:
        return None

def make_regressor():
    try:
        if ensemble is not None and hasattr(ensemble, "AdaptiveRandomForestRegressor"):
            return ensemble.AdaptiveRandomForestRegressor(n_models=3)
    except Exception:
        pass
    try:
        return linear_model.LinearRegression()
    except Exception:
        return None

def start_text_consumer(producer):
    try:
        consumer = KafkaConsumer(TEXT_TOPIC, bootstrap_servers=[BOOTSTRAP],
                                 value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                                 auto_offset_reset='earliest', group_id='text-consumer-group')
    except Exception as e:
        print('[TextConsumer] kafka connect error', e); return
    model = make_text_model()
    print('[TextConsumer] started, model:', bool(model))
    for msg in consumer:
        try:
            event = msg.value
            label = label_policy(event.get('policy_text',''))
            if model:
                try:
                    model.learn_one(event.get('policy_text',''), label)
                except Exception as e:
                    print('[TextConsumer] learn error', e)
            alert = {'type':'text_classification','ticker':event.get('ticker'),'label':label,'ts':event.get('ts')}
            try:
                producer.send(ALERT_TOPIC, value=alert); producer.flush()
            except Exception as e:
                print('[TextConsumer] publish error', e)
            print(f"[TextConsumer] {event.get('ticker')} → {label}")
        except Exception as e:
            print('[TextConsumer] processing error', e); traceback.print_exc()

def start_numeric_consumer(producer):
    try:
        consumer = KafkaConsumer(NUMERIC_TOPIC, bootstrap_servers=[BOOTSTRAP],
                                 value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                                 auto_offset_reset='latest', group_id='numeric-consumer-group')
    except Exception as e:
        print(f'[NumericConsumer] kafka connect error: {e}')
        traceback.print_exc()
        return
    reg = make_regressor()
    adwin = drift.ADWIN(delta=0.002) if (drift is not None and hasattr(drift, 'ADWIN')) else None
    print(f'[NumericConsumer] started, regressor: {bool(reg)}, ADWIN: {bool(adwin)}')
    
    msg_count = 0
    last_alert_time = 0
    
    for msg in consumer:
        try:
            ev = msg.value
            ticker = ev.get('ticker','UNK')
            x = {'rev_to_cash': float(ev.get('rev_to_cash',0.0)), 'deferred_ratio': float(ev.get('deferred_ratio',0.0))}
            y = float(ev.get('revenue',0.0))
            y_pred = None
            residual = None
            
            if reg:
                try:
                    y_pred = reg.predict_one(x)
                    reg.learn_one(x, y)
                    residual = abs(y - y_pred) if y_pred is not None else None
                except Exception as e:
                    print(f'[NumericConsumer] reg error: {e}')
            
            # Use ADWIN to detect drift in prediction residuals
            if residual is not None and adwin:
                try:
                    prev_detections = adwin.n_detections
                    adwin.update(residual)
                    # Check if drift was detected (n_detections increased or drift_detected is True)
                    if adwin.n_detections > prev_detections or adwin.drift_detected:
                        # Throttle alerts to max 1 per 5 seconds
                        current_time = time.time()
                        if (current_time - last_alert_time) > 5.0:
                            drift_alert = {
                                'type': 'numeric_drift',
                                'ticker': ticker,
                                'residual': round(residual, 2),
                                'revenue': y,
                                'predicted': round(y_pred, 2) if y_pred else None,
                                'rev_to_cash': round(x['rev_to_cash'], 4),
                                'deferred_ratio': round(x['deferred_ratio'], 4),
                                'message': 'ADWIN detected drift in revenue prediction residuals',
                                'ts': ev.get('ts')
                            }
                            try:
                                producer.send(ALERT_TOPIC, value=drift_alert)
                                producer.flush()
                                last_alert_time = current_time
                                print(f'[NumericConsumer] ✅ DRIFT ALERT PUBLISHED -> {drift_alert}')
                            except Exception as e:
                                print(f'[NumericConsumer] publish error: {e}')
                                traceback.print_exc()
                except Exception as e:
                    print(f'[NumericConsumer] ADWIN error: {e}')
            
            msg_count += 1
            # Log every 20th message for debugging
            if msg_count % 20 == 0:
                print(f"[NumericConsumer] Processed {msg_count} messages. Last: {ticker}, Revenue: {y:.0f}, Predicted: {y_pred:.0f if y_pred else None}, Residual: {residual:.2f if residual else None}")
        except Exception as e:
            print(f'[NumericConsumer] processing error: {e}')
            traceback.print_exc()

def main():
    try:
        producer = KafkaProducer(bootstrap_servers=[BOOTSTRAP], value_serializer=lambda v: json.dumps(v).encode('utf-8'))
    except Exception as e:
        print('[Main] producer init error', e); return
    t1 = threading.Thread(target=start_text_consumer, args=(producer,), daemon=True)
    t2 = threading.Thread(target=start_numeric_consumer, args=(producer,), daemon=True)
    t1.start(); t2.start()
    print('[Main] consumers running (Ctrl+C to stop)')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('[Main] stopping')

if __name__ == '__main__':
    main()
