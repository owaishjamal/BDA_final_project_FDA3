#!/usr/bin/env python3
import json, time, argparse, pandas as pd
from kafka import KafkaProducer
from datetime import datetime, timezone

parser = argparse.ArgumentParser()
parser.add_argument("--csv", default="/Users/adityadwivedi/Downloads/Group16_FDA3_Stream/datasets/revenue_patterns_sample.csv")
parser.add_argument("--bootstrap", default="localhost:9092")
parser.add_argument("--interval", type=float, default=1.0)
args = parser.parse_args()

def make_producer(bootstrap):
    return KafkaProducer(bootstrap_servers=[bootstrap], value_serializer=lambda v: json.dumps(v).encode("utf-8"))

def iso_now():
    return datetime.now(timezone.utc).isoformat()

def main():
    df = pd.read_csv(args.csv)
    prod = make_producer(args.bootstrap)
    text_topic = "revenue_text_stream"
    numeric_topic = "revenue_numeric_stream"
    print(f"[Producer] streaming {len(df)} rows to {args.bootstrap}")
    try:
        while True:
            for _, row in df.iterrows():
                ts = iso_now()
                text_msg = {
                    "company": row["company"], "ticker": row["ticker"], "period": row["period"],
                    "policy_text": row["policy_text"], "ts": ts
                }
                revenue = float(row["revenue"]); cashflow = float(row["revenue_cashflow"]); deferred = float(row["deferred_revenue"])
                rev_to_cash = revenue / (cashflow + 1e-9); deferred_ratio = deferred / (revenue + 1e-9)
                numeric_msg = {
                    "company": row["company"], "ticker": row["ticker"], "period": row["period"],
                    "revenue": revenue, "cashflow": cashflow, "deferred_revenue": deferred,
                    "rev_to_cash": rev_to_cash, "deferred_ratio": deferred_ratio, "ts": ts
                }
                prod.send(text_topic, value=text_msg)
                prod.send(numeric_topic, value=numeric_msg)
                prod.flush()
                print(f"[Producer] sent {row['ticker']} at {ts}")
                time.sleep(args.interval)
    except KeyboardInterrupt:
        print('[Producer] stopped by user')
    finally:
        try:
            prod.close()
        except:
            pass

if __name__ == '__main__':
    main()
