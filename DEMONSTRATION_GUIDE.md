# FDA-3-Stream: Demonstration Guide

## How to Run and Show the Complete System

This guide shows you how to demonstrate all features of the FDA-3-Stream system.

## Prerequisites Check

```bash
# 1. Check Kafka is running
brew services list | grep kafka
kafka-topics --list --bootstrap-server localhost:9092

# 2. Verify topics exist
# Should see: revenue_text_stream, revenue_numeric_stream, revenue_alerts

# 3. Activate virtual environment
cd /Users/adityadwivedi/Downloads/Group16_FDA3_Stream
source venv/bin/activate
```

## Step-by-Step Demonstration

### Step 1: Start CapyMOA Drift Detector

**Terminal 1:**
```bash
python3 scripts/capy_drift.py
```

**What to Show:**
- ✅ Detectors initialized: ADWIN, KSWIN, PageHinkley, DDM, EDDM
- ✅ Listening for numeric stream
- ✅ Will show drift detections when they occur

**Expected Output:**
```
[CapyDrift] detectors -> ADWIN: True, KSWIN: True, PageHinkley: True, DDM: True, EDDM: True
[CapyDrift] listening for numeric stream...
[CapyDrift] Processed 10 messages. Last: AAPL, Score: 33.07, ADWIN width: 10
```

### Step 2: Start Enhanced River Consumers

**Terminal 2:**
```bash
python3 scripts/kafka_consumer_river_enhanced.py
```

**What to Show:**
- ✅ **Module 2:** Text classification with 3 models (MultinomialNB, LogisticRegression, HoeffdingTree)
- ✅ **Module 3:** Regression with AdaptiveRandomForest
- ✅ **Module 4:** Fusion consumer for cross-platform anomaly detection
- ✅ **Module 5:** Feature importance tracking
- ✅ Real-time metrics: Accuracy, F1, MAE, RMSE, R²

**Expected Output:**
```
[TextConsumer] started with models: ['nb', 'lr', 'ht']
[NumericConsumer] started, regressor: True, ADWIN: True
[FusionConsumer] started - monitoring for cross-model consensus...
[Main] Enhanced consumers running (Ctrl+C to stop)
[TextConsumer] Processed 20 messages. Accuracy: 0.850, F1: 0.820
[NumericConsumer] Processed 20 messages. MAE: 12345.67, RMSE: 23456.78, R²: 0.750
```

### Step 3: Start Producer (Stream Data)

**Terminal 3:**
```bash
python3 scripts/kafka_producer.py --csv datasets/revenue_patterns_sample.csv --interval 1.0
```

**What to Show:**
- ✅ **Module 1:** Streaming extraction and feature generation
- ✅ Sending text and numeric data to Kafka
- ✅ Continuous streaming loop

**Expected Output:**
```
[Producer] streaming 328 rows to localhost:9092
[Producer] sent AAPL at 2025-01-XX...
[Producer] sent ABBV at 2025-01-XX...
```

### Step 4: Start Dashboard

**Terminal 4:**
```bash
streamlit run scripts/dashboard_realtime.py
```

**What to Show:**
- ✅ **Module 6:** Real-time visualization
- ✅ Open http://localhost:8501 in browser
- ✅ Shows live alerts, statistics, charts
- ✅ Real-time updates

## What to Demonstrate

### 1. Module 1: Feature Generation ✅
**Show:** Producer terminal output
- Streaming revenue data
- Computing ratios (rev_to_cash, deferred_ratio)
- Sending to Kafka topics

### 2. Module 2: Text Classification ✅
**Show:** Terminal 2 output
- Multiple models running (NB, LR, HT)
- Accuracy and F1 scores updating
- Classification labels (Aggressive, Conservative, Neutral)

**Example:**
```
[TextConsumer] Processed 20 messages. Accuracy: 0.850, F1: 0.820
[TextConsumer] Last: AAPL → Aggressive (true: Aggressive)
```

### 3. Module 3: Regression & Drift ✅
**Show:** Terminal 2 and Terminal 1 output
- Regression metrics (MAE, RMSE, R²)
- Drift detections from multiple detectors
- ADWIN, DDM, EDDM alerts

**Example:**
```
[NumericConsumer] Processed 20 messages. MAE: 12345.67, RMSE: 23456.78, R²: 0.750
[CapyDrift] ADWIN drift detected! Score: 55.23, Ticker: AAPL, Detections: 1
[CapyDrift] ✅ ALERT PUBLISHED -> {...}
```

### 4. Module 4: Cross-Platform Fusion ✅
**Show:** Terminal 2 output
- Fusion consumer detecting high-risk cases
- Consensus rate calculation
- High-risk alerts when multiple indicators agree

**Example:**
```
[FusionConsumer] 🚨 HIGH-RISK FUSION ALERT -> AAPL
```

### 5. Module 5: Explainability ✅
**Show:** Terminal 2 output (on shutdown)
- Feature importance for text features
- Feature importance for numeric features
- Top keywords identified

**Example (on Ctrl+C):**
```
[Main] Top Text Features:
  variable: 0.450
  consideration: 0.420
  aggressive: 0.380
  ...
[Main] Top Numeric Features:
  rev_to_cash: 0.850
  deferred_ratio: 0.620
```

### 6. Module 6: Complete Pipeline ✅
**Show:** All terminals + Dashboard
- End-to-end flow: Producer → Consumers → Drift → Fusion → Dashboard
- Real-time processing
- Automatic incremental learning

## Evaluation Metrics to Highlight

### Text Classification
- **Accuracy:** Shown in Terminal 2 every 20 messages
- **F1:** Shown in Terminal 2 every 20 messages

### Regression
- **MAE:** Shown in Terminal 2 every 20 messages
- **RMSE:** Shown in Terminal 2 every 20 messages
- **R²:** Shown in Terminal 2 every 20 messages

### Drift Detection
- **Detection Delay:** Tracked via timestamps
- **Frequency:** Number of detections per detector

### Streaming Efficiency
- **Throughput:** Message count / time (can calculate from logs)
- **Latency:** Timestamps in alerts

### Cross-Model Agreement
- **Consensus Rate:** Shown in fusion alerts

### Explainability
- **Top-N Keywords:** Shown on shutdown
- **Feature Importance:** Shown on shutdown

## Dashboard Features to Show

1. **Real-time Alerts Table**
   - Shows all alerts as they arrive
   - Different types: text_classification, numeric_drift, capy_drift, high_risk_fusion

2. **Statistics Panel**
   - Total alerts
   - Alerts by type
   - Alerts by ticker

3. **Charts**
   - Bar chart of alert types
   - Real-time updates

## Key Points to Emphasize

1. **Real-time Processing:** All components process data as it streams
2. **Multiple Models:** Text classification uses 3 models, regression uses adaptive forest
3. **Multiple Drift Detectors:** 5 different detectors (ADWIN, DDM, EDDM, KSWIN, PageHinkley)
4. **Cross-Platform Fusion:** Combines River and CapyMOA outputs
5. **Explainability:** Feature importance tracking
6. **Complete Pipeline:** End-to-end from data to dashboard
7. **Evaluation Metrics:** All required metrics tracked in real-time

## Troubleshooting During Demo

If something doesn't work:

1. **No alerts appearing:**
   - Wait 30-50 messages for drift detectors to establish baseline
   - Check that producer is sending data
   - Verify Kafka topics exist

2. **Dashboard not updating:**
   - Check Kafka connection status in dashboard
   - Verify consumer is running
   - Check browser console for errors

3. **Import errors:**
   - `pip install -r requirements.txt`
   - Verify virtual environment is activated

## Expected Timeline

- **0-30 seconds:** System starting up, initial messages processed
- **30-60 seconds:** First metrics appear, drift detectors learning
- **60+ seconds:** Drift detections start appearing, alerts in dashboard
- **2+ minutes:** Feature importance visible, full system operational

## Summary Checklist

- ✅ Module 1: Producer streaming data
- ✅ Module 2: Text classification with 3 models
- ✅ Module 3: Regression + 5 drift detectors
- ✅ Module 4: Fusion consumer active
- ✅ Module 5: Feature importance tracking
- ✅ Module 6: Dashboard showing real-time alerts
- ✅ All evaluation metrics visible
- ✅ Complete pipeline operational

