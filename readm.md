# FDA-3-Stream: Real-Time Quantitative Analysis of Revenue Recognition Practices

**Group 16** | Kafka × River × CapyMOA

## 📖 Complete Project Guide

**👉 For a comprehensive A-to-Z guide covering everything about this project, see [`COMPLETE_PROJECT_GUIDE.md`](COMPLETE_PROJECT_GUIDE.md)**

This guide includes:
- Complete project explanation
- Detailed code walkthrough
- Dataset description
- Presentation guide
- FAQ for cross-questions
- Everything you need to know!

## Overview

A real-time streaming system that analyzes revenue recognition disclosures and financial metrics from SEC 10-K filings to detect aggressive accounting or inconsistent revenue practices. The system integrates Apache Kafka for continuous data ingestion, River (Python) for online classification and regression, and CapyMOA-style drift detection for adaptive pattern detection.

## System Architecture

```
Data Source → Kafka Producer → Kafka Topics → River Consumers → CapyMOA Drift → Fusion → Dashboard
```

### Components

1. **Kafka Producer** (`scripts/kafka_producer.py`)
   - Streams revenue recognition data to Kafka topics
   - Generates text and numeric streams

2. **River Consumers** (`scripts/kafka_consumer_river_enhanced.py`)
   - Text classification (MultinomialNB, LogisticRegression, HoeffdingTree)
   - Regression (AdaptiveRandomForest, LinearRegression)
   - Feature importance tracking
   - Evaluation metrics (Accuracy, F1, MAE, RMSE, R²)

3. **CapyMOA Drift Detector** (`scripts/capy_drift.py`)
   - ADWIN, DDM, EDDM, KSWIN, PageHinkley
   - Detects drift in revenue metrics

4. **Fusion Consumer** (in `kafka_consumer_river_enhanced.py`)
   - Cross-platform anomaly fusion
   - High-risk alert generation

5. **Dashboard** (`scripts/dashboard_realtime.py`)
   - Real-time alert visualization
   - Metrics display

## Quick Start

### Prerequisites

- Kafka installed and running
- Python 3.9+
- Virtual environment

### Setup

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Install dependencies (if not already installed)
pip install -r requirements.txt

# 3. Ensure Kafka is running and topics exist
kafka-topics --list --bootstrap-server localhost:9092
# Should see: revenue_text_stream, revenue_numeric_stream, revenue_alerts
```

### Run the System

Open 4 terminal windows:

**Terminal 1: CapyMOA Drift Detector**
```bash
python3 scripts/capy_drift.py
```

**Terminal 2: Enhanced River Consumers (Text + Numeric + Fusion)**
```bash
python3 scripts/kafka_consumer_river_enhanced.py
```

**Terminal 3: Producer**
```bash
python3 scripts/kafka_producer.py --csv datasets/revenue_patterns_sample.csv --interval 1.0
```

**Terminal 4: Dashboard**
```bash
streamlit run scripts/dashboard_realtime.py
```
Then open http://localhost:8501

## Module Coverage

### ✅ Module 1: Streaming Extraction & Feature Generation
- Extracts revenue recognition text
- Computes numeric ratios (Revenue-to-CashFlow, Deferred Revenue Ratio)
- Streams to Kafka topics

### ✅ Module 2: Real-Time Text Classification
- MultinomialNB
- LogisticRegression
- HoeffdingTreeClassifier
- Ensemble prediction
- Metrics: Accuracy, F1

### ✅ Module 3: Numeric Stream Regression & Drift Detection
- AdaptiveRandomForestRegressor
- ADWIN, DDM, EDDM drift detection
- Metrics: MAE, RMSE, R²

### ✅ Module 4: Cross-Platform Anomaly Fusion
- Fuses River and CapyMOA outputs
- High-risk alert generation
- Consensus rate calculation

### ✅ Module 5: Explainable Streaming Analytics
- Feature importance tracking (SHAP-like)
- Top-N keyword importance
- Real-time importance updates

### ✅ Module 6: Automated Monitoring Pipeline
- Complete EDGAR → Kafka → River + CapyMOA → Dashboard pipeline
- Automatic incremental learning
- Real-time processing

## Evaluation Metrics

All metrics are tracked in real-time:

- **Text Classification:** Accuracy, F1-score
- **Regression:** MAE, RMSE, R²
- **Drift Detection:** Detection delay, frequency
- **Streaming:** Throughput, latency
- **Cross-Model:** Consensus rate
- **Explainability:** Feature importance scores

## Project Structure

```
Group16_FDA3_Stream/
├── scripts/
│   ├── kafka_producer.py              # Module 1: Producer
│   ├── kafka_consumer_river_enhanced.py  # Modules 2,3,4,5: Enhanced consumers
│   ├── capy_drift.py                  # Module 3: CapyMOA drift detection
│   └── dashboard_realtime.py          # Module 6: Dashboard
├── notebooks/
│   ├── 01_data_extraction_preprocessing.ipynb
│   ├── 02_model_training_evaluation.ipynb
│   └── README.md
├── datasets/
│   └── revenue_patterns_sample.csv
├── visuals/                           # For charts and diagrams
├── requirements.txt
├── RUN_INSTRUCTIONS.md                # Detailed run instructions
├── ASSIGNMENT_COMPLIANCE.md           # Complete compliance checklist
└── README.md                          # This file
```

## Documentation

- **RUN_INSTRUCTIONS.md** - Step-by-step instructions to run the system
- **ASSIGNMENT_COMPLIANCE.md** - Complete assignment requirements checklist
- **DRIFT_FIXES.md** - Technical documentation on drift detection
- **notebooks/README.md** - Jupyter notebook documentation

## Features

- ✅ Real-time streaming processing
- ✅ Multiple ML models (text classification + regression)
- ✅ Multiple drift detectors (ADWIN, DDM, EDDM, KSWIN, PageHinkley)
- ✅ Cross-platform fusion
- ✅ Feature importance tracking
- ✅ Comprehensive evaluation metrics
- ✅ Real-time dashboard
- ✅ Incremental online learning

## Troubleshooting

See `RUN_INSTRUCTIONS.md` for troubleshooting tips.

Common issues:
- Kafka not running: `brew services start kafka`
- Topics missing: Create them using `kafka-topics --create`
- Import errors: `pip install -r requirements.txt`

## License

This project is part of Group 16's Big Data Analytics assignment.

## Contact

Group 16 - FDA-3-Stream Project

