# Drift Detection Fixes

## Issues Fixed

### 1. **Incorrect Drift Detector API Usage**
   - **Problem:** Code was using `change_detected` attribute which doesn't exist in River
   - **Fix:** Changed to use `drift_detected` attribute (correct River API)
   - **Problem:** Code tried to use DDM and EDDM which don't exist in River
   - **Fix:** Replaced with available detectors: ADWIN, KSWIN, PageHinkley

### 2. **Poor Drift Calculation Logic**
   - **Problem:** Simple score calculation (`rev_to_cash * 100 + deferred_ratio * 1000`) wasn't meaningful
   - **Fix:** Improved calculation with proper normalization:
     - `score = rev_to_cash * 10.0 + deferred_ratio * 100.0`
     - Better scaling for drift detection sensitivity

### 3. **Missing Debug Output**
   - **Problem:** No visibility into whether messages were being processed
   - **Fix:** Added periodic logging (every 10-20 messages) showing:
     - Message count
     - Current ticker being processed
     - Calculated scores/residuals
     - Detector status

### 4. **Alert Throttling**
   - **Problem:** No throttling could cause alert spam
   - **Fix:** Added 5-second throttling between alerts

### 5. **Offset Reset Strategy**
   - **Problem:** Using `auto_offset_reset='earliest'` could process old messages
   - **Fix:** Changed to `'latest'` to only process new messages

## Changes Made

### `scripts/capy_drift.py`
- ✅ Fixed drift detector initialization (ADWIN, KSWIN, PageHinkley)
- ✅ Fixed drift detection check (`drift_detected` instead of `change_detected`)
- ✅ Improved drift score calculation
- ✅ Added comprehensive logging
- ✅ Added alert throttling
- ✅ Better error handling and debugging

### `scripts/kafka_consumer_river.py`
- ✅ Fixed ADWIN drift detection in numeric consumer
- ✅ Fixed `drift_detected` attribute usage
- ✅ Added alert throttling
- ✅ Improved logging
- ✅ Better error handling

## How Drift Detection Now Works

### CapyDrift (`capy_drift.py`)
1. Consumes messages from `revenue_numeric_stream`
2. Calculates drift score: `rev_to_cash * 10.0 + deferred_ratio * 100.0`
3. Updates three drift detectors:
   - **ADWIN** (Adaptive Windowing) - detects changes in data distribution
   - **KSWIN** (Kolmogorov-Smirnov Windowing) - detects distribution changes
   - **PageHinkley** - detects mean shifts
4. When any detector flags drift, publishes alert to `revenue_alerts` topic

### NumericConsumer (`kafka_consumer_river.py`)
1. Consumes messages from `revenue_numeric_stream`
2. Uses regression model to predict revenue from `rev_to_cash` and `deferred_ratio`
3. Calculates prediction residual (absolute difference)
4. Uses ADWIN to detect drift in residuals
5. When drift detected, publishes alert to `revenue_alerts` topic

## Testing

To verify the fixes work:

1. **Start all components:**
   ```bash
   # Terminal 1: Drift Detector
   python3 scripts/capy_drift.py
   
   # Terminal 2: Consumers
   python3 scripts/kafka_consumer_river.py
   
   # Terminal 3: Producer
   python3 scripts/kafka_producer.py --csv datasets/revenue_patterns_sample.csv --interval 1.0
   
   # Terminal 4: Dashboard
   streamlit run scripts/dashboard_realtime.py
   ```

2. **Expected Output:**
   - CapyDrift should show: `[CapyDrift] Processed X messages...`
   - When drift detected: `[CapyDrift] ✅ ALERT PUBLISHED -> {...}`
   - NumericConsumer should show: `[NumericConsumer] Processed X messages...`
   - When drift detected: `[NumericConsumer] ✅ DRIFT ALERT PUBLISHED -> {...}`
   - Dashboard should display alerts in real-time

3. **Debugging:**
   - Check that messages are being received (look for "Processed X messages" logs)
   - Check ADWIN width is increasing (indicates detector is learning)
   - Alerts should appear after sufficient data points and when drift occurs

## Detector Sensitivity

- **ADWIN delta:** 0.002 (lower = more sensitive)
- **KSWIN alpha:** 0.005 (lower = more sensitive)
- **PageHinkley threshold:** 10.0 (lower = more sensitive)

If you need more/fewer alerts, adjust these parameters in the code.

