#!/usr/bin/env python3
"""
Enhanced Kafka Consumer with River ML models, feature importance tracking, and evaluation metrics.
Implements Module 2 (Text Classification), Module 3 (Regression & Drift), Module 4 (Fusion), Module 5 (Explainability)
"""
import json, threading, time, traceback
from collections import defaultdict, deque
from kafka import KafkaConsumer, KafkaProducer

# River imports
try:
    from river import (
        feature_extraction, naive_bayes, compose, ensemble, 
        linear_model, drift, tree, metrics, stats
    )
except Exception:
    feature_extraction = naive_bayes = compose = ensemble = linear_model = drift = tree = metrics = stats = None

BOOTSTRAP = "localhost:9092"
TEXT_TOPIC = "revenue_text_stream"
NUMERIC_TOPIC = "revenue_numeric_stream"
ALERT_TOPIC = "revenue_alerts"

# Evaluation metrics storage
text_metrics = {
    'accuracy': metrics.Accuracy(),
    'f1': metrics.F1(),
    'confusion_matrix': defaultdict(lambda: defaultdict(int))
}

regression_metrics = {
    'mae': metrics.MAE(),
    'rmse': metrics.RMSE(),
    'r2': metrics.R2()
}

# Feature importance tracking (SHAP-like)
feature_importance = {
    'text_features': defaultdict(float),  # word -> importance score
    'numeric_features': defaultdict(float)  # feature -> importance score
}

# Cross-model fusion tracking
fusion_alerts = deque(maxlen=1000)  # Track alerts for fusion analysis

def label_policy(text):
    """Label revenue recognition policy text."""
    t = (text or "").lower()
    if "aggressive" in t or "variable consideration" in t or "multiple-element" in t or "upfront" in t:
        return "Aggressive"
    if "conservative" in t or "immaterial" in t or "consistent" in t or "prudent" in t:
        return "Conservative"
    return "Neutral"

def make_text_models():
    """Create multiple text classification models (Module 2)."""
    models = {}
    try:
        # Model 1: MultinomialNB (handles multi-class with string labels)
        models['nb'] = compose.Pipeline(
            feature_extraction.BagOfWords(lowercase=True),
            naive_bayes.MultinomialNB()
        )
    except Exception:
        models['nb'] = None
    
    try:
        # Model 2: LogisticRegression - Use OneVsRest for multi-class
        # River's LogisticRegression is binary, so we'll use it for binary classification
        # For multi-class, we'll create separate binary classifiers
        from river import multioutput
        # Create binary classifier for each class
        models['lr_aggressive'] = compose.Pipeline(
            feature_extraction.BagOfWords(lowercase=True),
            linear_model.LogisticRegression()
        )
        models['lr_conservative'] = compose.Pipeline(
            feature_extraction.BagOfWords(lowercase=True),
            linear_model.LogisticRegression()
        )
        models['lr'] = 'multi_binary'  # Flag to indicate multi-binary approach
    except Exception:
        models['lr'] = None
        models['lr_aggressive'] = None
        models['lr_conservative'] = None
    
    try:
        # Model 3: HoeffdingTreeClassifier (handles multi-class with string labels)
        models['ht'] = compose.Pipeline(
            feature_extraction.BagOfWords(lowercase=True),
            tree.HoeffdingTreeClassifier()
        )
    except Exception:
        models['ht'] = None
    
    return models

def update_feature_importance_text(model, text, prediction, true_label):
    """Track feature importance for text (SHAP-like, Module 5)."""
    try:
        if hasattr(model, 'steps') and len(model.steps) > 0:
            bow = model.steps[0]  # BagOfWords
            if hasattr(bow, 'transform_one'):
                features = bow.transform_one(text)
                # Simple importance: weight by prediction confidence
                for word, count in features.items():
                    if word in text.lower():
                        # Increment importance based on feature presence
                        feature_importance['text_features'][word] += abs(count) * 0.1
    except Exception:
        pass

def update_feature_importance_numeric(features, importance_scores):
    """Track feature importance for numeric features (Module 5)."""
    for feat, score in zip(features.keys(), importance_scores):
        feature_importance['numeric_features'][feat] += abs(score)

def start_text_consumer(producer):
    """Module 2: Real-Time Text Classification with multiple models."""
    try:
        consumer = KafkaConsumer(
            TEXT_TOPIC, 
            bootstrap_servers=[BOOTSTRAP],
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset='latest', 
            group_id='text-consumer-group-enhanced'
        )
    except Exception as e:
        print(f'[TextConsumer] kafka connect error: {e}')
        traceback.print_exc()
        return
    
    models = make_text_models()
    model_names = [k for k, v in models.items() if v is not None and k != 'lr_aggressive' and k != 'lr_conservative']
    if models.get('lr') == 'multi_binary':
        model_names.append('lr')  # Add lr if multi-binary setup is active
    print(f'[TextConsumer] started with models: {model_names}')
    
    msg_count = 0
    predictions_history = deque(maxlen=100)  # For ensemble voting
    
    for msg in consumer:
        try:
            event = msg.value
            text = event.get('policy_text', '')
            ticker = event.get('ticker', 'UNK')
            true_label = label_policy(text)
            
            # Get predictions from all models
            predictions = {}
            for name, model in models.items():
                if model is None:
                    continue
                
                # Skip lr_aggressive and lr_conservative - they're handled separately
                if name in ['lr_aggressive', 'lr_conservative']:
                    continue
                    
                try:
                    # Handle multi-binary LogisticRegression
                    if name == 'lr' and model == 'multi_binary':
                        # Use binary classifiers for each class
                        pred_agg = models['lr_aggressive'].predict_one(text) if models['lr_aggressive'] else False
                        pred_cons = models['lr_conservative'].predict_one(text) if models['lr_conservative'] else False
                        
                        # Convert binary predictions to multi-class
                        if pred_agg:
                            lr_pred = 'Aggressive'
                        elif pred_cons:
                            lr_pred = 'Conservative'
                        else:
                            lr_pred = 'Neutral'
                        
                        # Update binary models
                        if models['lr_aggressive']:
                            models['lr_aggressive'].learn_one(text, true_label == 'Aggressive')
                        if models['lr_conservative']:
                            models['lr_conservative'].learn_one(text, true_label == 'Conservative')
                        
                        predictions[name] = {'pred': lr_pred, 'proba': {}}
                        pred = lr_pred
                    else:
                        # Standard multi-class models
                        pred = model.predict_one(text)
                        proba = model.predict_proba_one(text) if hasattr(model, 'predict_proba_one') else {}
                        predictions[name] = {'pred': pred, 'proba': proba}
                        
                        # Update model
                        model.learn_one(text, true_label)
                    
                    # Update metrics
                    text_metrics['accuracy'].update(true_label, pred)
                    text_metrics['f1'].update(true_label, pred)
                    text_metrics['confusion_matrix'][true_label][pred] += 1
                    
                    # Update feature importance
                    if name != 'lr' or model != 'multi_binary':
                        update_feature_importance_text(model, text, pred, true_label)
                        
                except Exception as e:
                    print(f'[TextConsumer] {name} error: {e}')
                    traceback.print_exc()
            
            # Ensemble prediction (majority vote)
            if predictions:
                pred_counts = defaultdict(int)
                for pred_data in predictions.values():
                    pred_counts[pred_data['pred']] += 1
                ensemble_pred = max(pred_counts.items(), key=lambda x: x[1])[0] if pred_counts else true_label
            else:
                ensemble_pred = true_label
            
            # Create alert - ALWAYS send alerts
            alert = {
                'type': 'text_classification',
                'ticker': ticker,
                'label': ensemble_pred,
                'true_label': true_label,
                'models': {k: v['pred'] for k, v in predictions.items()},
                'accuracy': float(text_metrics['accuracy'].get()) if text_metrics['accuracy'].get() is not None else 0.0,
                'f1': float(text_metrics['f1'].get()) if text_metrics['f1'].get() is not None else 0.0,
                'ts': event.get('ts', time.strftime('%Y-%m-%dT%H:%M:%S'))
            }
            
            try:
                producer.send(ALERT_TOPIC, value=alert)
                producer.flush()
                # Log every 10th alert for debugging
                if msg_count % 10 == 0:
                    print(f'[TextConsumer] ✅ Alert sent: {ticker} → {ensemble_pred}')
            except Exception as e:
                print(f'[TextConsumer] publish error: {e}')
                traceback.print_exc()
            
            msg_count += 1
            if msg_count % 20 == 0:
                print(f"[TextConsumer] Processed {msg_count} messages. Accuracy: {text_metrics['accuracy'].get():.3f}, F1: {text_metrics['f1'].get():.3f}")
                print(f"[TextConsumer] Last: {ticker} → {ensemble_pred} (true: {true_label})")
                
        except Exception as e:
            print(f'[TextConsumer] processing error: {e}')
            traceback.print_exc()

def start_numeric_consumer(producer):
    """Module 3: Numeric Stream Regression & Drift Detection."""
    try:
        consumer = KafkaConsumer(
            NUMERIC_TOPIC, 
            bootstrap_servers=[BOOTSTRAP],
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest', 
            group_id='numeric-consumer-group-enhanced'
        )
    except Exception as e:
        print(f'[NumericConsumer] kafka connect error: {e}')
        traceback.print_exc()
        return
    
    # Create regressor (Module 3)
    try:
        if ensemble and hasattr(ensemble, "AdaptiveRandomForestRegressor"):
            reg = ensemble.AdaptiveRandomForestRegressor(n_models=5, seed=42)
        else:
            reg = linear_model.LinearRegression()
    except Exception:
        reg = None
    
    # Drift detector
    adwin = drift.ADWIN(delta=0.002) if drift else None
    
    print(f'[NumericConsumer] started, regressor: {bool(reg)}, ADWIN: {bool(adwin)}')
    
    msg_count = 0
    last_alert_time = 0
    
    for msg in consumer:
        try:
            ev = msg.value
            ticker = ev.get('ticker', 'UNK')
            x = {
                'rev_to_cash': float(ev.get('rev_to_cash', 0.0)), 
                'deferred_ratio': float(ev.get('deferred_ratio', 0.0))
            }
            y = float(ev.get('revenue', 0.0))
            y_pred = None
            residual = None
            
            if reg:
                try:
                    y_pred = reg.predict_one(x)
                    reg.learn_one(x, y)
                    residual = abs(y - y_pred) if y_pred is not None else None
                    
                    # Update regression metrics
                    if y_pred is not None:
                        regression_metrics['mae'].update(y, y_pred)
                        regression_metrics['rmse'].update(y, y_pred)
                        regression_metrics['r2'].update(y, y_pred)
                    
                    # Feature importance (simple: use coefficients for linear models)
                    if hasattr(reg, 'weights'):
                        weights = reg.weights
                        if weights:
                            feat_names = list(x.keys())
                            feat_importances = [abs(weights.get(f'_{name}', 0)) for name in feat_names]
                            update_feature_importance_numeric(x, feat_importances)
                except Exception as e:
                    print(f'[NumericConsumer] reg error: {e}')
            
            # Drift detection
            drift_detected = False
            if residual is not None and adwin:
                try:
                    prev_detections = adwin.n_detections
                    adwin.update(residual)
                    if adwin.n_detections > prev_detections or adwin.drift_detected:
                        drift_detected = True
                except Exception:
                    pass
            
            # Create alert if drift detected
            if drift_detected:
                current_time = time.time()
                if (current_time - last_alert_time) > 5.0:
                    drift_alert = {
                        'type': 'numeric_drift',
                        'ticker': ticker,
                        'residual': round(residual, 2) if residual else None,
                        'revenue': y,
                        'predicted': round(y_pred, 2) if y_pred else None,
                        'rev_to_cash': round(x['rev_to_cash'], 4),
                        'deferred_ratio': round(x['deferred_ratio'], 4),
                        'mae': regression_metrics['mae'].get(),
                        'rmse': regression_metrics['rmse'].get(),
                        'r2': regression_metrics['r2'].get(),
                        'message': 'ADWIN detected drift in revenue prediction residuals',
                        'ts': ev.get('ts')
                    }
                    try:
                        producer.send(ALERT_TOPIC, value=drift_alert)
                        producer.flush()
                        last_alert_time = current_time
                        fusion_alerts.append(drift_alert)  # Track for fusion
                        print(f'[NumericConsumer] ✅ DRIFT ALERT -> {ticker}, MAE: {regression_metrics["mae"].get():.2f}, RMSE: {regression_metrics["rmse"].get():.2f}')
                    except Exception as e:
                        print(f'[NumericConsumer] publish error: {e}')
            
            msg_count += 1
            if msg_count % 20 == 0:
                print(f"[NumericConsumer] Processed {msg_count} messages. MAE: {regression_metrics['mae'].get():.2f}, RMSE: {regression_metrics['rmse'].get():.2f}, R²: {regression_metrics['r2'].get():.3f}")
                
        except Exception as e:
            print(f'[NumericConsumer] processing error: {e}')
            traceback.print_exc()

def start_fusion_consumer(producer):
    """Module 4: Cross-Platform Anomaly Fusion - combines River and CapyMOA outputs."""
    try:
        consumer = KafkaConsumer(
            ALERT_TOPIC,
            bootstrap_servers=[BOOTSTRAP],
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            group_id='fusion-consumer-group'
        )
    except Exception as e:
        print(f'[FusionConsumer] kafka connect error: {e}')
        return
    
    print('[FusionConsumer] started - monitoring for cross-model consensus...')
    
    # Track alerts by ticker and quarter
    ticker_alerts = defaultdict(lambda: {'text': [], 'numeric': [], 'capy': []})
    
    for msg in consumer:
        try:
            alert = msg.value
            alert_type = alert.get('type', '')
            ticker = alert.get('ticker', 'UNK')
            ts = alert.get('ts', '')
            
            # Categorize alerts
            if alert_type == 'text_classification':
                ticker_alerts[ticker]['text'].append(alert)
            elif alert_type == 'numeric_drift':
                ticker_alerts[ticker]['numeric'].append(alert)
            elif alert_type == 'capy_drift':
                ticker_alerts[ticker]['capy'].append(alert)
            
            # Check for high-risk fusion (Module 4 requirement)
            # Flag if both River (numeric) and CapyMOA (capy_drift) detect drift within same ticker
            text_alerts = ticker_alerts[ticker]['text']
            numeric_alerts = ticker_alerts[ticker]['numeric']
            capy_alerts = ticker_alerts[ticker]['capy']
            
            # High-risk: Aggressive text classification + numeric drift + capy drift
            aggressive_text = any(a.get('label') == 'Aggressive' for a in text_alerts[-5:])
            has_numeric_drift = len(numeric_alerts) > 0
            has_capy_drift = len(capy_alerts) > 0
            
            if aggressive_text and (has_numeric_drift or has_capy_drift):
                # Create high-risk fusion alert
                fusion_alert = {
                    'type': 'high_risk_fusion',
                    'ticker': ticker,
                    'risk_level': 'HIGH',
                    'indicators': {
                        'aggressive_text': aggressive_text,
                        'numeric_drift': has_numeric_drift,
                        'capy_drift': has_capy_drift,
                        'consensus_rate': (int(has_numeric_drift) + int(has_capy_drift)) / 2.0
                    },
                    'text_alerts_count': len(text_alerts),
                    'numeric_alerts_count': len(numeric_alerts),
                    'capy_alerts_count': len(capy_alerts),
                    'message': 'High-Risk Revenue Recognition: Multiple indicators detected',
                    'ts': ts
                }
                
                try:
                    producer.send(ALERT_TOPIC, value=fusion_alert)
                    producer.flush()
                    print(f'[FusionConsumer] 🚨 HIGH-RISK FUSION ALERT -> {ticker}')
                except Exception as e:
                    print(f'[FusionConsumer] publish error: {e}')
            
            # Clean old alerts (keep last 10 per ticker)
            for alert_list in ticker_alerts[ticker].values():
                if len(alert_list) > 10:
                    alert_list[:] = alert_list[-10:]
                    
        except Exception as e:
            print(f'[FusionConsumer] processing error: {e}')
            traceback.print_exc()

def main():
    """Main function to start all consumers."""
    try:
        producer = KafkaProducer(
            bootstrap_servers=[BOOTSTRAP], 
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
    except Exception as e:
        print(f'[Main] producer init error: {e}')
        traceback.print_exc()
        return
    
    # Start all consumer threads
    t1 = threading.Thread(target=start_text_consumer, args=(producer,), daemon=True)
    t2 = threading.Thread(target=start_numeric_consumer, args=(producer,), daemon=True)
    t3 = threading.Thread(target=start_fusion_consumer, args=(producer,), daemon=True)
    
    t1.start()
    t2.start()
    t3.start()
    
    print('[Main] Enhanced consumers running (Ctrl+C to stop)')
    print('[Main] Modules active: Text Classification, Regression, Drift Detection, Fusion, Explainability')
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('\n[Main] Stopping...')
        print(f'[Main] Final Text Metrics - Accuracy: {text_metrics["accuracy"].get():.3f}, F1: {text_metrics["f1"].get():.3f}')
        print(f'[Main] Final Regression Metrics - MAE: {regression_metrics["mae"].get():.2f}, RMSE: {regression_metrics["rmse"].get():.2f}, R²: {regression_metrics["r2"].get():.3f}')
        
        # Print top feature importances
        print('\n[Main] Top Text Features:')
        top_text = sorted(feature_importance['text_features'].items(), key=lambda x: x[1], reverse=True)[:10]
        for word, score in top_text:
            print(f'  {word}: {score:.3f}')
        
        print('\n[Main] Top Numeric Features:')
        top_num = sorted(feature_importance['numeric_features'].items(), key=lambda x: x[1], reverse=True)
        for feat, score in top_num:
            print(f'  {feat}: {score:.3f}')

if __name__ == '__main__':
    main()

