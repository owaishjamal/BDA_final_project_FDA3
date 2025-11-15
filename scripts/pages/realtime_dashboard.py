"""
Enhanced Real-time Dashboard Page with improved UI, KPIs, and visualizations
"""
import time
import json
import pandas as pd
import streamlit as st
from collections import deque
from kafka import KafkaConsumer, KafkaProducer
from datetime import datetime

# Config
BOOTSTRAP = "localhost:9092"
ALERT_TOPIC = "revenue_alerts"
MAX_ALERTS = 500

# Initialize session state
if "alerts" not in st.session_state:
    st.session_state.alerts = deque(maxlen=MAX_ALERTS)

if "consumer" not in st.session_state:
    try:
        st.session_state.consumer = KafkaConsumer(
            ALERT_TOPIC,
            bootstrap_servers=[BOOTSTRAP],
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="latest",
            consumer_timeout_ms=1000,
            group_id=f"dashboard-group-{int(time.time())}",
            enable_auto_commit=True,
            auto_commit_interval_ms=1000
        )
        st.session_state.consumer_ok = True
    except Exception as e:
        st.session_state.consumer = None
        st.session_state.consumer_ok = False
        st.session_state.consumer_err = str(e)

if "producer" not in st.session_state:
    try:
        st.session_state.producer = KafkaProducer(
            bootstrap_servers=[BOOTSTRAP],
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
        st.session_state.producer_ok = True
    except Exception:
        st.session_state.producer = None
        st.session_state.producer_ok = False

def get_alert_color(alert_type):
    """Get color for alert type"""
    colors = {
        'text_classification': '#3498db',  # Blue
        'numeric_drift': '#e74c3c',  # Red
        'capy_drift': '#f39c12',  # Orange
        'high_risk_fusion': '#c0392b',  # Dark Red
        'manual_test': '#95a5a6'  # Gray
    }
    return colors.get(alert_type, '#34495e')

def get_risk_level_badge(alert_type):
    """Get risk level badge"""
    if alert_type == 'high_risk_fusion':
        return "🔴 HIGH RISK"
    elif alert_type in ['numeric_drift', 'capy_drift']:
        return "🟠 MEDIUM RISK"
    elif alert_type == 'text_classification':
        return "🟡 LOW RISK"
    return "⚪ INFO"

def show():
    st.title("📈 Real-time Revenue Recognition Monitoring Dashboard")
    st.markdown("---")
    
    # Status bar
    status_cols = st.columns([2, 1, 1, 1, 1])
    with status_cols[0]:
        if st.session_state.consumer_ok:
            st.success("🟢 Kafka Connected")
        else:
            st.error("🔴 Kafka Disconnected")
    
    with status_cols[1]:
        total_alerts = len(st.session_state.alerts)
        st.metric("Total Alerts", total_alerts)
    
    with status_cols[2]:
        if hasattr(st.session_state, 'alert_count'):
            st.metric("Received", st.session_state.alert_count)
        else:
            st.metric("Received", 0)
    
    with status_cols[3]:
        if hasattr(st.session_state, 'last_update_time'):
            last_update = time.strftime('%H:%M:%S', time.localtime(st.session_state.last_update_time))
            st.caption(f"Last: {last_update}")
        else:
            st.caption("Last: Never")
    
    with status_cols[4]:
        if 'auto_refresh' not in st.session_state:
            st.session_state.auto_refresh = False
        auto_refresh = st.checkbox("🔄 Auto", value=st.session_state.auto_refresh, key='auto_refresh')
    
    # Control buttons
    control_cols = st.columns([1, 1, 1, 1, 2])
    with control_cols[0]:
        if st.button("🔄 Refresh Now", use_container_width=True):
            st.session_state.force_refresh = True
            st.rerun()
    
    with control_cols[1]:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.alerts.clear()
            st.rerun()
    
    with control_cols[2]:
        if st.button("📊 Export", use_container_width=True):
            if len(st.session_state.alerts) > 0:
                df = pd.DataFrame(list(st.session_state.alerts))
                csv = df.to_csv(index=False)
                st.download_button("Download CSV", csv, "alerts.csv", "text/csv", key='download-csv')
    
    with control_cols[3]:
        if st.session_state.producer_ok and st.button("🧪 Test", use_container_width=True):
            test_alert = {
                "type": "manual_test",
                "ticker": "TEST",
                "message": "Test alert from dashboard",
                "ts": datetime.now().isoformat()
            }
            try:
                st.session_state.producer.send(ALERT_TOPIC, value=test_alert)
                st.session_state.producer.flush()
                st.success("✅ Test sent")
            except Exception as e:
                st.error(f"Failed: {e}")
    
    st.markdown("---")
    
    # Poll for new messages
    if st.session_state.consumer_ok:
        should_poll = st.session_state.get('auto_refresh', False) or st.session_state.get('force_refresh', False)
        
        if should_poll:
            try:
                msgpack = st.session_state.consumer.poll(timeout_ms=300, max_records=50)
                new_alerts_count = 0
                
                if msgpack:
                    for tp, messages in msgpack.items():
                        for msg in messages:
                            try:
                                alert = msg.value
                                if isinstance(alert, str):
                                    try:
                                        alert = json.loads(alert)
                                    except Exception:
                                        alert = {"raw": alert}
                                if isinstance(alert, dict):
                                    st.session_state.alerts.append(alert)
                                    new_alerts_count += 1
                                    if not hasattr(st.session_state, 'alert_count'):
                                        st.session_state.alert_count = 0
                                    st.session_state.alert_count += 1
                            except Exception as ex:
                                pass
                
                st.session_state.last_update_time = time.time()
                
                if st.session_state.get('force_refresh', False):
                    st.session_state.force_refresh = False
                    if new_alerts_count > 0:
                        st.success(f"✅ Received {new_alerts_count} new alert(s)")
            except Exception as e:
                pass
    
    # Main content
    if len(st.session_state.alerts) == 0:
        st.info("📭 No alerts yet. Start the producer and consumers to see real-time data.")
        st.markdown("""
        **To get started:**
        1. Start the producer: `python3 scripts/kafka_producer.py --csv datasets/revenue_patterns_sample.csv --interval 1.0`
        2. Start the consumers: `python3 scripts/kafka_consumer_river_enhanced.py`
        3. Enable auto-refresh or click "Refresh Now"
        """)
    else:
        df = pd.DataFrame(list(st.session_state.alerts))
        
        # Parse timestamps
        if "ts" in df.columns:
            try:
                df["timestamp"] = pd.to_datetime(df["ts"], errors="coerce")
            except Exception:
                df["timestamp"] = pd.NaT
        
        # KPIs Row 1
        st.subheader("📊 Key Performance Indicators")
        kpi_cols = st.columns(5)
        
        # Total Alerts
        with kpi_cols[0]:
            st.metric("Total Alerts", len(df), delta=None)
        
        # Alert Types
        if "type" in df.columns:
            alert_types = df["type"].value_counts()
            with kpi_cols[1]:
                text_count = alert_types.get('text_classification', 0)
                st.metric("Text Classifications", text_count)
            with kpi_cols[2]:
                drift_count = alert_types.get('numeric_drift', 0) + alert_types.get('capy_drift', 0)
                st.metric("Drift Detections", drift_count)
            with kpi_cols[3]:
                high_risk = alert_types.get('high_risk_fusion', 0)
                st.metric("High Risk Alerts", high_risk, delta=None, delta_color="inverse")
            with kpi_cols[4]:
                unique_tickers = df["ticker"].nunique() if "ticker" in df.columns else 0
                st.metric("Unique Tickers", unique_tickers)
        
        st.markdown("---")
        
        # Charts Row
        chart_cols = st.columns(2)
        
        with chart_cols[0]:
            st.subheader("📈 Alert Types Distribution")
            if "type" in df.columns:
                type_counts = df["type"].value_counts()
                chart_df = pd.DataFrame({
                    'Type': type_counts.index,
                    'Count': type_counts.values
                })
                st.bar_chart(chart_df.set_index('Type'), height=300)
            else:
                st.info("No alert type data available")
        
        with chart_cols[1]:
            st.subheader("📊 Top Tickers by Alert Count")
            if "ticker" in df.columns:
                ticker_counts = df["ticker"].value_counts().head(10)
                chart_df = pd.DataFrame({
                    'Ticker': ticker_counts.index,
                    'Count': ticker_counts.values
                })
                st.bar_chart(chart_df.set_index('Ticker'), height=300)
            else:
                st.info("No ticker data available")
        
        # Time Series Chart
        if "timestamp" in df.columns and not df["timestamp"].isna().all():
            st.subheader("⏱️ Alerts Over Time")
            df_time = df.copy()
            df_time['hour_minute'] = df_time['timestamp'].dt.floor('1min')
            time_counts = df_time.groupby('hour_minute').size().reset_index(name='count')
            time_counts = time_counts.set_index('hour_minute')
            st.line_chart(time_counts, height=200)
        
        st.markdown("---")
        
        # Detailed Metrics
        metrics_cols = st.columns(3)
        
        with metrics_cols[0]:
            st.subheader("📋 Classification Metrics")
            if "type" in df.columns and "accuracy" in df.columns:
                text_df = df[df["type"] == "text_classification"]
                if len(text_df) > 0:
                    avg_accuracy = text_df["accuracy"].mean() if "accuracy" in text_df.columns else 0
                    avg_f1 = text_df["f1"].mean() if "f1" in text_df.columns else 0
                    st.metric("Avg Accuracy", f"{avg_accuracy:.3f}" if avg_accuracy > 0 else "N/A")
                    st.metric("Avg F1-Score", f"{avg_f1:.3f}" if avg_f1 > 0 else "N/A")
                else:
                    st.info("No classification data yet")
            else:
                st.info("Waiting for classification alerts...")
        
        with metrics_cols[1]:
            st.subheader("📉 Regression Metrics")
            if "type" in df.columns and "mae" in df.columns:
                numeric_df = df[df["type"] == "numeric_drift"]
                if len(numeric_df) > 0:
                    avg_mae = numeric_df["mae"].mean() if "mae" in numeric_df.columns else 0
                    avg_rmse = numeric_df["rmse"].mean() if "rmse" in numeric_df.columns else 0
                    avg_r2 = numeric_df["r2"].mean() if "r2" in numeric_df.columns else 0
                    st.metric("Avg MAE", f"{avg_mae:,.0f}" if avg_mae > 0 else "N/A")
                    st.metric("Avg RMSE", f"{avg_rmse:,.0f}" if avg_rmse > 0 else "N/A")
                    st.metric("Avg R²", f"{avg_r2:.3f}" if avg_r2 != 0 else "N/A")
                else:
                    st.info("No regression data yet")
            else:
                st.info("Waiting for regression alerts...")
        
        with metrics_cols[2]:
            st.subheader("🎯 Risk Analysis")
            if "type" in df.columns:
                risk_counts = {
                    "High": len(df[df["type"] == "high_risk_fusion"]),
                    "Medium": len(df[df["type"].isin(["numeric_drift", "capy_drift"])]),
                    "Low": len(df[df["type"] == "text_classification"])
                }
                total_risk = sum(risk_counts.values())
                if total_risk > 0:
                    for risk, count in risk_counts.items():
                        percentage = (count / total_risk) * 100
                        st.metric(f"{risk} Risk", f"{count} ({percentage:.1f}%)")
                else:
                    st.info("No risk data yet")
            else:
                st.info("Waiting for alerts...")
        
        st.markdown("---")
        
        # Alerts Table
        st.subheader("🔔 Recent Alerts")
        
        # Filters
        filter_cols = st.columns([2, 2, 2, 1])
        with filter_cols[0]:
            if "type" in df.columns:
                # Convert to strings and filter out NaN/None values
                unique_types = df["type"].dropna().unique()
                alert_types_list = ["All"] + sorted([str(t) for t in unique_types])
                selected_type = st.selectbox("Filter by Type", alert_types_list)
            else:
                selected_type = "All"
        
        with filter_cols[1]:
            if "ticker" in df.columns:
                # Convert to strings and filter out NaN/None values
                unique_tickers = df["ticker"].dropna().unique()
                tickers_list = ["All"] + sorted([str(t) for t in unique_tickers])
                selected_ticker = st.selectbox("Filter by Ticker", tickers_list)
            else:
                selected_ticker = "All"
        
        with filter_cols[2]:
            num_rows = st.selectbox("Show Rows", [10, 25, 50, 100, 200], index=1)
        
        with filter_cols[3]:
            sort_order = st.selectbox("Sort", ["Newest", "Oldest"], index=0)
        
        # Filter and sort dataframe
        df_filtered = df.copy()
        
        if selected_type != "All" and "type" in df_filtered.columns:
            df_filtered = df_filtered[df_filtered["type"] == selected_type]
        
        if selected_ticker != "All" and "ticker" in df_filtered.columns:
            df_filtered = df_filtered[df_filtered["ticker"] == selected_ticker]
        
        # Sort by timestamp
        if "timestamp" in df_filtered.columns:
            df_filtered = df_filtered.sort_values("timestamp", ascending=(sort_order == "Oldest"))
        elif "ts" in df_filtered.columns:
            df_filtered = df_filtered.sort_values("ts", ascending=(sort_order == "Oldest"))
        
        # Display table
        df_display = df_filtered.head(num_rows)
        
        # Format columns for display
        display_cols = []
        if "timestamp" in df_display.columns:
            df_display["Time"] = df_display["timestamp"].dt.strftime("%H:%M:%S")
            display_cols.append("Time")
        elif "ts" in df_display.columns:
            display_cols.append("ts")
        
        if "type" in df_display.columns:
            display_cols.append("type")
        if "ticker" in df_display.columns:
            display_cols.append("ticker")
        if "label" in df_display.columns:
            display_cols.append("label")
        if "message" in df_display.columns:
            display_cols.append("message")
        
        # Add other relevant columns
        for col in ["score", "residual", "accuracy", "f1", "mae", "rmse"]:
            if col in df_display.columns:
                display_cols.append(col)
        
        if display_cols:
            st.dataframe(
                df_display[display_cols],
                use_container_width=True,
                height=400
            )
        else:
            st.dataframe(df_display, use_container_width=True, height=400)
        
        # Alert details expander
        if len(df_display) > 0:
            with st.expander("📋 View Raw Alert Data"):
                st.json(df_display.iloc[0].to_dict() if len(df_display) > 0 else {})
    
    # Auto-refresh
    if st.session_state.get('auto_refresh', False):
        time.sleep(5.0)
        st.rerun()

