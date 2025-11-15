#!/usr/bin/env python3
"""
Real-time Streamlit dashboard for FDA-3-Stream alerts.

Usage:
    source venv/bin/activate
    streamlit run scripts/dashboard_realtime.py
Then open http://localhost:8501
"""

import time
import json
import pandas as pd
import streamlit as st
from collections import deque
from kafka import KafkaConsumer, KafkaProducer

# ---------- Config ----------
BOOTSTRAP = "localhost:9092"
ALERT_TOPIC = "revenue_alerts"
# how many alerts to keep in memory for display
MAX_ALERTS = 500
POLL_INTERVAL_SEC = 1.0  # polling sleep between cycles

st.set_page_config(page_title="FDA-3-Stream — Live Alerts", layout="wide")
st.title("FDA-3-Stream — Real-time Alerts Dashboard (Group 16)")

# ---------- Session-state init ----------
if "running" not in st.session_state:
    st.session_state.running = True

if "alerts" not in st.session_state:
    # deque of dicts (most recent appended to right)
    st.session_state.alerts = deque(maxlen=MAX_ALERTS)

if "consumer" not in st.session_state:
    try:
        # auto_offset_reset='earliest' to pick up past alerts (change if undesired)
        st.session_state.consumer = KafkaConsumer(
            ALERT_TOPIC,
            bootstrap_servers=[BOOTSTRAP],
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="latest",  # Start from latest to see new alerts
            consumer_timeout_ms=1000,
            group_id=f"dashboard-group-{int(time.time())}",  # Unique group each time to avoid offset issues
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

# ---------- Top controls ----------
cols = st.columns([1, 1, 1, 2, 1])
with cols[0]:
    if st.button("🔄 Refresh Now"):
        st.session_state.force_refresh = True
        st.rerun()

with cols[1]:
    if st.button("Clear Alerts"):
        st.session_state.alerts.clear()
        st.rerun()

with cols[2]:
    if st.session_state.producer_ok and st.button("Send Test Alert"):
        test_alert = {
            "type": "manual_test",
            "ticker": "TEST",
            "message": "manual test from dashboard",
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        }
        try:
            st.session_state.producer.send(ALERT_TOPIC, value=test_alert)
            st.session_state.producer.flush()
            st.success("Test alert sent")
        except Exception as e:
            st.error(f"Failed to send test alert: {e}")

with cols[3]:
    st.markdown(
        "### Kafka Status\n"
        f"- Broker: `{BOOTSTRAP}`  \n"
        f"- Consumer OK: `{st.session_state.consumer_ok}`  \n"
        f"- Producer OK: `{st.session_state.producer_ok}`"
    )
    # Auto-refresh toggle
    auto_refresh = st.checkbox("Auto-refresh (5s)", value=st.session_state.get('auto_refresh', False), key='auto_refresh_checkbox')
    st.session_state.auto_refresh = auto_refresh

with cols[4]:
    st.write("")  # spacing
    if hasattr(st.session_state, 'alert_count'):
        st.caption(f"Total alerts received: {st.session_state.alert_count}")
    if hasattr(st.session_state, 'last_update_time'):
        st.caption(f"Last update: {time.strftime('%H:%M:%S', time.localtime(st.session_state.last_update_time))}")

# ---------- Main display placeholders ----------
left_col, right_col = st.columns([2, 1])

with left_col:
    alerts_placeholder = st.empty()
    df_placeholder = st.empty()

with right_col:
    stats_placeholder = st.empty()
    chart_placeholder = st.empty()

# ---------- Helper to update UI from alerts deque ----------
def update_ui():
    # convert deque to DataFrame (latest first)
    alerts_list = list(st.session_state.alerts)[::-1]
    if len(alerts_list) == 0:
        alerts_placeholder.info("No alerts yet. Start producers/consumers.")
        df_placeholder.empty()
        stats_placeholder.empty()
        chart_placeholder.empty()
        return

    df = pd.DataFrame(alerts_list)
    # ensure timestamp column exists
    if "ts" in df.columns:
        try:
            # try parse numeric timestamps too
            df["ts_readable"] = pd.to_datetime(df["ts"], errors="coerce")
        except Exception:
            df["ts_readable"] = df["ts"]
    else:
        df["ts_readable"] = pd.NaT

    # show table (limit to last 200 rows)
    df_display = df.head(200)
    df_placeholder.dataframe(df_display, use_container_width=True)

    # stats: counts by type and by ticker
    stats = {}
    try:
        stats["total_alerts"] = len(df)
        stats["by_type"] = df["type"].value_counts().to_dict() if "type" in df.columns else {}
        stats["by_ticker"] = df["ticker"].value_counts().to_dict() if "ticker" in df.columns else {}
    except Exception:
        stats["error"] = "could not compute stats"

    stats_md = "### Stats\n"
    stats_md += f"- Total alerts (in memory): **{stats.get('total_alerts', 0)}**\n\n"
    if stats.get("by_type"):
        for k, v in stats["by_type"].items():
            stats_md += f"- {k}: **{v}**  \n"
    if stats.get("by_ticker"):
        stats_md += "\n**By ticker**\n"
        for k, v in stats["by_ticker"].items():
            stats_md += f"- {k}: **{v}**  \n"

    stats_placeholder.markdown(stats_md)

    # simple bar chart for type counts
    if "type" in df.columns:
        chart_df = df["type"].value_counts().rename_axis("type").reset_index(name="count")
        chart_placeholder.bar_chart(chart_df.set_index("type"))

# ---------- Poll Kafka for new messages ----------
if not st.session_state.consumer_ok:
    st.error("Kafka consumer not initialized: " + str(st.session_state.consumer_err))
else:
    # Poll for messages (only if auto-refresh is on or manual refresh was triggered)
    should_poll = st.session_state.get('auto_refresh', False) or st.session_state.get('force_refresh', False)
    
    if should_poll:
        try:
            # poll for messages (consumer.poll returns dict of partitions->list)
            msgpack = st.session_state.consumer.poll(timeout_ms=300, max_records=50)
            
            # extract messages
            new_alerts_count = 0
            if msgpack:
                for tp, messages in msgpack.items():
                    for msg in messages:
                        try:
                            # msg.value is already deserialized JSON
                            alert = msg.value
                            # normalize/tidy: ensure dict
                            if isinstance(alert, str):
                                # attempt JSON parse
                                try:
                                    alert = json.loads(alert)
                                except Exception:
                                    alert = {"raw": alert}
                            if isinstance(alert, dict):
                                st.session_state.alerts.append(alert)
                                new_alerts_count += 1
                                # Track total count
                                if not hasattr(st.session_state, 'alert_count'):
                                    st.session_state.alert_count = 0
                                st.session_state.alert_count += 1
                        except Exception as ex:
                            st.error(f"Failed to process message: {ex}")
            
            # Update last update time
            st.session_state.last_update_time = time.time()
            
            # Clear force refresh flag
            if st.session_state.get('force_refresh', False):
                st.session_state.force_refresh = False
                if new_alerts_count > 0:
                    st.success(f"✅ Refreshed! Received {new_alerts_count} new alert(s)")
                else:
                    st.info("No new alerts")
                    
        except Exception as e:
            st.error(f"Error polling Kafka consumer: {e}")

# Update UI with current alerts
update_ui()

# Auto-refresh using st.rerun() only if auto-refresh is enabled
if st.session_state.get('auto_refresh', False):
    time.sleep(5.0)  # 5 second interval for auto-refresh
    st.rerun()
