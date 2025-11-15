#!/usr/bin/env python3
import json, time, traceback
from kafka import KafkaConsumer, KafkaProducer
try:
    from river import drift
except Exception:
    drift = None

BOOTSTRAP = "localhost:9092"
NUMERIC_TOPIC = "revenue_numeric_stream"
ALERT_TOPIC = "revenue_alerts"

def make_detectors():
    """Create drift detectors including CapyMOA-style DDM and EDDM from River's binary drift module."""
    if drift is None:
        return None, None, None, None, None
    try:
        # River's standard drift detectors
        adwin = drift.ADWIN(delta=0.002)  # Lower delta = more sensitive
        kswin = drift.KSWIN(alpha=0.005, window_size=100) if hasattr(drift, 'KSWIN') else None
        page_hinkley = drift.PageHinkley(threshold=10.0, min_instances=30) if hasattr(drift, 'PageHinkley') else None
        
        # CapyMOA-style detectors: DDM and EDDM from River's binary drift module
        # These work on binary classification errors, so we'll convert our score to binary
        ddm = drift.binary.DDM() if hasattr(drift, 'binary') and hasattr(drift.binary, 'DDM') else None
        eddm = drift.binary.EDDM(alpha=0.9, beta=0.8) if hasattr(drift, 'binary') and hasattr(drift.binary, 'EDDM') else None
        
        return adwin, kswin, page_hinkley, ddm, eddm
    except Exception as e:
        print(f'[CapyDrift] Error creating detectors: {e}')
        traceback.print_exc()
        return None, None, None, None, None

def calculate_drift_score(ev):
    """Calculate a meaningful drift score from revenue metrics."""
    try:
        revenue = float(ev.get('revenue', 0.0))
        cashflow = float(ev.get('cashflow', 0.0))
        deferred = float(ev.get('deferred_revenue', 0.0))
        rev_to_cash = float(ev.get('rev_to_cash', 0.0))
        deferred_ratio = float(ev.get('deferred_ratio', 0.0))
        
        # Normalize values for drift detection
        # Use revenue-to-cash ratio as primary signal (anomalies indicate accounting changes)
        # Add deferred revenue ratio as secondary signal
        # Scale to make drift more detectable
        score = rev_to_cash * 10.0 + deferred_ratio * 100.0
        
        # Also track revenue magnitude changes (log scale to handle large numbers)
        if revenue > 0:
            revenue_log = (revenue / 1e9)  # Normalize to billions
        else:
            revenue_log = 0.0
            
        return score, revenue_log, {
            'rev_to_cash': rev_to_cash,
            'deferred_ratio': deferred_ratio,
            'revenue': revenue
        }
    except Exception as e:
        print(f'[CapyDrift] Error calculating score: {e}')
        return 0.0, 0.0, {}

def main():
    try:
        consumer = KafkaConsumer(
            NUMERIC_TOPIC, 
            bootstrap_servers=[BOOTSTRAP], 
            value_deserializer=lambda m: json.loads(m.decode('utf-8')), 
            auto_offset_reset='latest',  # Changed to 'latest' to avoid processing old messages
            enable_auto_commit=True, 
            group_id='capy-drift-group'
        )
        producer = KafkaProducer(
            bootstrap_servers=[BOOTSTRAP], 
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
    except Exception as e:
        print(f'[CapyDrift] kafka connect error: {e}')
        traceback.print_exc()
        return
    
    adwin, kswin, page_hinkley, ddm, eddm = make_detectors()
    print(f'[CapyDrift] detectors -> ADWIN: {bool(adwin)}, KSWIN: {bool(kswin)}, PageHinkley: {bool(page_hinkley)}, DDM: {bool(ddm)}, EDDM: {bool(eddm)}')
    print('[CapyDrift] listening for numeric stream...')
    
    msg_count = 0
    last_alert_time = 0
    
    try:
        while True:
            msg_pack = consumer.poll(timeout_ms=1000, max_records=10)
            if not msg_pack:
                time.sleep(0.5)
                continue
                
            for tp, messages in msg_pack.items():
                for msg in messages:
                    try:
                        ev = msg.value
                        ticker = ev.get('ticker', 'UNK')
                        msg_count += 1
                        
                        # Calculate drift score
                        score, revenue_log, metrics = calculate_drift_score(ev)
                        
                        # Update detectors
                        drift_detected = False
                        detector_flags = {}
                        
                        try:
                            # ADWIN - Adaptive Windowing
                            if adwin:
                                prev_detections = adwin.n_detections
                                adwin.update(score)
                                if adwin.n_detections > prev_detections or adwin.drift_detected:
                                    drift_detected = True
                                    detector_flags['adwin'] = True
                                    print(f'[CapyDrift] ADWIN drift detected! Score: {score:.2f}, Ticker: {ticker}, Detections: {adwin.n_detections}')
                            
                            # KSWIN - Kolmogorov-Smirnov Windowing
                            if kswin:
                                prev_detections = kswin.n_detections if hasattr(kswin, 'n_detections') else 0
                                kswin.update(score)
                                if (hasattr(kswin, 'n_detections') and kswin.n_detections > prev_detections) or (hasattr(kswin, 'drift_detected') and kswin.drift_detected):
                                    drift_detected = True
                                    detector_flags['kswin'] = True
                                    print(f'[CapyDrift] KSWIN drift detected! Score: {score:.2f}, Ticker: {ticker}')
                            
                            # PageHinkley - Mean shift detection
                            if page_hinkley:
                                prev_detections = page_hinkley.n_detections if hasattr(page_hinkley, 'n_detections') else 0
                                page_hinkley.update(score)
                                if (hasattr(page_hinkley, 'n_detections') and page_hinkley.n_detections > prev_detections) or (hasattr(page_hinkley, 'drift_detected') and page_hinkley.drift_detected):
                                    drift_detected = True
                                    detector_flags['page_hinkley'] = True
                                    print(f'[CapyDrift] PageHinkley drift detected! Score: {score:.2f}, Ticker: {ticker}')
                            
                            # DDM (Drift Detection Method) - CapyMOA style
                            # DDM works on binary errors, so we convert score to binary (anomaly = 1 if score > threshold)
                            if ddm:
                                # Use a threshold based on historical data (e.g., score > 50 indicates anomaly)
                                threshold = 50.0
                                is_anomaly = 1 if score > threshold else 0
                                ddm.update(is_anomaly)
                                if ddm.drift_detected or ddm.warning_detected:
                                    drift_detected = True
                                    detector_flags['ddm'] = True
                                    print(f'[CapyDrift] DDM drift/warning detected! Score: {score:.2f}, Ticker: {ticker}, Anomaly: {is_anomaly}')
                            
                            # EDDM (Early Drift Detection Method) - CapyMOA style
                            # EDDM also works on binary errors
                            if eddm:
                                threshold = 50.0
                                is_anomaly = 1 if score > threshold else 0
                                eddm.update(is_anomaly)
                                if eddm.drift_detected or eddm.warning_detected:
                                    drift_detected = True
                                    detector_flags['eddm'] = True
                                    print(f'[CapyDrift] EDDM drift/warning detected! Score: {score:.2f}, Ticker: {ticker}, Anomaly: {is_anomaly}')
                        except Exception as e:
                            print(f'[CapyDrift] detector runtime error: {e}')
                            traceback.print_exc()
                        
                        # Log every 10th message for debugging
                        if msg_count % 10 == 0:
                            print(f'[CapyDrift] Processed {msg_count} messages. Last: {ticker}, Score: {score:.2f}, ADWIN width: {adwin.width if adwin else "N/A"}')
                        
                        # Send alert if drift detected (throttle to max 1 per 5 seconds)
                        if drift_detected and (time.time() - last_alert_time) > 5.0:
                            alert = {
                                'type': 'capy_drift',
                                'ticker': ticker,
                                'score': round(score, 2),
                                'revenue': metrics.get('revenue', 0),
                                'rev_to_cash': round(metrics.get('rev_to_cash', 0), 4),
                                'deferred_ratio': round(metrics.get('deferred_ratio', 0), 4),
                                'adwin': detector_flags.get('adwin', False),
                                'kswin': detector_flags.get('kswin', False),
                                'page_hinkley': detector_flags.get('page_hinkley', False),
                                'ddm': detector_flags.get('ddm', False),
                                'eddm': detector_flags.get('eddm', False),
                                'message': 'Drift detected in revenue metrics',
                                'ts': ev.get('ts', time.strftime('%Y-%m-%dT%H:%M:%S'))
                            }
                            try:
                                producer.send(ALERT_TOPIC, value=alert)
                                producer.flush()
                                last_alert_time = time.time()
                                print(f'[CapyDrift] ✅ ALERT PUBLISHED -> {alert}')
                            except Exception as e:
                                print(f'[CapyDrift] publish error: {e}')
                                traceback.print_exc()
                                
                    except Exception as e:
                        print(f'[CapyDrift] processing error: {e}')
                        traceback.print_exc()
                        
    except KeyboardInterrupt:
        print('[CapyDrift] stopped by user')
    finally:
        try:
            consumer.close()
            producer.close()
        except:
            pass

if __name__ == '__main__':
    main()
