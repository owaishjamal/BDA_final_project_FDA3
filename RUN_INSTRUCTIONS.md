# FDA-3-Stream — Run Instructions (Group 16)

## Prerequisites
- ✅ Kafka installed and running
- Python 3.9+ 
- Virtual environment (venv) already exists in this project

## 🚀 Quick Start (Everything is Ready!)

Since Kafka is running and topics are already created, you can start immediately:

```bash
# 1. Navigate to project and activate venv
cd /Users/adityadwivedi/Downloads/Group16_FDA3_Stream
source venv/bin/activate

# 2. Open 3-4 terminal windows and run these commands:

# Terminal 1: Drift Detector
python3 scripts/capy_drift.py

# Terminal 2: Consumers
python3 scripts/kafka_consumer_river.py

# Terminal 3: Producer (starts streaming data)
python3 scripts/kafka_producer.py --csv datasets/revenue_patterns_sample.csv --interval 1.0

# Terminal 4 (Optional): Dashboard
streamlit run scripts/dashboard_realtime.py
# Then open http://localhost:8501 in your browser
```

## Step-by-Step Instructions

### 1. Verify Kafka is Running ✅

**Status Check:**
```bash
# Check if Kafka is running
brew services list | grep kafka

# Verify Kafka is accessible
kafka-broker-api-versions --bootstrap-server localhost:9092
```

**If Kafka is not running:**
```bash
# Start Kafka (Zookeeper is typically included/embedded)
brew services start kafka
```

**Note:** If you get an error about Zookeeper not being installed, that's okay - Kafka may be using an embedded Zookeeper or running in KRaft mode. As long as Kafka is running and responding, you're good to go!

### 2. Verify Kafka Topics ✅

**Check if topics exist:**
```bash
kafka-topics --list --bootstrap-server localhost:9092
```

You should see:
- `revenue_text_stream`
- `revenue_numeric_stream`
- `revenue_alerts`

**If topics are missing, create them:**
```bash
# Topic 1: Text stream
kafka-topics --create --topic revenue_text_stream --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

# Topic 2: Numeric stream  
kafka-topics --create --topic revenue_numeric_stream --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

# Topic 3: Alerts
kafka-topics --create --topic revenue_alerts --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```

**✅ Your setup:** Topics are already created and ready to use!

### 3. Activate Python Virtual Environment

```bash
cd /Users/adityadwivedi/Downloads/Group16_FDA3_Stream
source venv/bin/activate
```

**Note:** If the virtual environment doesn't have dependencies installed:
```bash
pip install -r requirements.txt
```

### 4. Run the Application Components

You'll need to run multiple components. **Open separate terminal windows/tabs** for each:

#### Terminal 1: Drift Detector
```bash
cd /Users/adityadwivedi/Downloads/Group16_FDA3_Stream
source venv/bin/activate
python3 scripts/capy_drift.py
```

**Expected output:** `[CapyDrift] detectors -> DDM: True, EDDM: True, ADWIN: True`

#### Terminal 2: Enhanced Kafka Consumers (Text + Numeric + Fusion)
```bash
cd /Users/adityadwivedi/Downloads/Group16_FDA3_Stream
source venv/bin/activate
python3 scripts/kafka_consumer_river_enhanced.py
```

**Expected output:** 
- `[TextConsumer] started with models: ['nb', 'lr', 'ht']`
- `[NumericConsumer] started, regressor: True, ADWIN: True`
- `[FusionConsumer] started - monitoring for cross-model consensus...`
- `[Main] Enhanced consumers running (Ctrl+C to stop)`

**Note:** You can also use the basic consumer: `python3 scripts/kafka_consumer_river.py` (simpler, fewer features)

#### Terminal 3: Kafka Producer (Streams Data)
```bash
cd /Users/adityadwivedi/Downloads/Group16_FDA3_Stream
source venv/bin/activate
python3 scripts/kafka_producer.py --csv datasets/revenue_patterns_sample.csv --interval 1.0
```

**Expected output:** `[Producer] streaming X rows to localhost:9092` followed by `[Producer] sent <TICKER> at <timestamp>`

#### Terminal 4 (Optional): Real-time Dashboard
```bash
cd /Users/adityadwivedi/Downloads/Group16_FDA3_Stream
source venv/bin/activate
streamlit run scripts/dashboard_app.py
```

Then open your browser to: **http://localhost:8501**

**Note:** The new dashboard has two pages:
- **📖 Project Overview**: Complete project documentation and deliverables
- **📈 Real-time Dashboard**: Enhanced monitoring with KPIs, charts, and filters

### 5. Run Order Summary

**Recommended order:**
1. ✅ Start Kafka (Step 1)
2. ✅ Create topics (Step 2)
3. Start **Drift Detector** (Terminal 1)
4. Start **Consumers** (Terminal 2)
5. Start **Producer** (Terminal 3) - This will begin streaming data
6. (Optional) Start **Dashboard** (Terminal 4) - To visualize alerts

### 6. What to Expect

- **Producer:** Continuously sends revenue data messages to Kafka topics
- **Consumers:** Process messages, detect patterns, and generate alerts
- **Drift Detector:** Monitors numeric stream for data drift using ADWIN, DDM, EDDM
- **Dashboard:** Shows real-time alerts and statistics

### 7. Stopping the Application

Press `Ctrl+C` in each terminal window to stop the components gracefully.

To stop Kafka (if needed):
```bash
# For Homebrew:
brew services stop kafka
# Note: If Zookeeper is embedded, you don't need to stop it separately
```

## Troubleshooting

### Zookeeper Not Installed Error
**Error:** `Error: Formula 'zookeeper' is not installed`

**Solution:** This is normal! Modern Kafka installations (especially via Homebrew) often include Zookeeper embedded or run in KRaft mode (Kafka without Zookeeper). As long as:
- Kafka is running (`brew services list | grep kafka` shows it's started)
- Kafka responds to commands (`kafka-broker-api-versions --bootstrap-server localhost:9092` works)
- Topics can be listed (`kafka-topics --list --bootstrap-server localhost:9092` works)

Then you're all set! You don't need to install Zookeeper separately.

### Kafka Connection Issues
```bash
# Check if Kafka is listening on port 9092
lsof -i :9092

# Check Kafka logs (location depends on your installation)
# For Homebrew: ~/Library/Logs/homebrew/kafka/
```

### Topic Already Exists Error
If topics already exist, you can either:
- Delete and recreate: `kafka-topics --delete --topic <topic_name> --bootstrap-server localhost:9092`
- Or just continue - existing topics will work fine

### Python Import Errors
```bash
# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

### Port Already in Use
If port 9092 is in use, check what's using it:
```bash
lsof -i :9092
```

## Alternative: Using Docker (If Local Kafka Has Issues)

If you prefer to use Docker instead of your local Kafka installation:

```bash
# 1. Start Kafka and Zookeeper via Docker
docker compose up -d

# 2. Create topics
docker exec -it bda_kafka kafka-topics --create --topic revenue_text_stream --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
docker exec -it bda_kafka kafka-topics --create --topic revenue_numeric_stream --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
docker exec -it bda_kafka kafka-topics --create --topic revenue_alerts --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

# 3. Then proceed with running the Python scripts as normal
```

---

**Project Structure:**
- `scripts/kafka_producer.py` - Produces data to Kafka
- `scripts/kafka_consumer_river.py` - Consumes and processes data
- `scripts/capy_drift.py` - Drift detection
- `scripts/dashboard_realtime.py` - Streamlit dashboard
- `datasets/` - CSV data files
- `docker-compose.yml` - Alternative Docker setup (not needed if using local Kafka)

