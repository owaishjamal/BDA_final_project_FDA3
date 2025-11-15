# FDA-3-Stream — macOS Run Guide (Group 16)

## Prerequisites
- macOS with Python 3.9+ and Docker Desktop (recommended)
- Git (optional)

## Setup Steps
1. Clone or unzip this folder.
2. Start Kafka via Docker Compose:
   ```bash
   docker compose up -d
   ```
3. Create Kafka topics:
   ```bash
   docker exec -it $(docker ps -qf "ancestor=confluentinc/cp-kafka:7.4.1") kafka-topics --create --topic revenue_text_stream --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
   docker exec -it $(docker ps -qf "ancestor=confluentinc/cp-kafka:7.4.1") kafka-topics --create --topic revenue_numeric_stream --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
   docker exec -it $(docker ps -qf "ancestor=confluentinc/cp-kafka:7.4.1") kafka-topics --create --topic revenue_alerts --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
   ```
4. Create Python environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Run Order
1. Run drift detector:
   ```bash
   python3 scripts/capy_drift.py
   ```
2. Run consumers (text + numeric):
   ```bash
   python3 scripts/kafka_consumer_river.py
   ```
3. Run producer to stream data:
   ```bash
   python3 scripts/kafka_producer.py --csv datasets/revenue_patterns_sample.csv --interval 1.0
   ```
4. (Optional) Launch dashboard:
   ```bash
   streamlit run scripts/dashboard_app.py
   ```

## Expected Output
- Producer prints `[Producer] sent <TICKER>`
- Consumer prints drift detections and alerts
- Dashboard shows live alerts

## Submission Checklist
- Group16_BigData_Contribution_Summary.docx
- FDA3_Stream_Report_Group16.pdf
- requirements.txt
- README_MAC_RUN.md
- docker-compose.yml
- datasets/revenue_patterns_sample.csv
- All scripts in /scripts
- visuals/dashboard_snapshot.png (optional)
