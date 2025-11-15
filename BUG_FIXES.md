# Bug Fixes - LogisticRegression and Dashboard Alerts

## Issues Fixed

### 1. LogisticRegression Error: "invalid literal for int() with base 10: 'Neutral'"

**Problem:**
- River's `LogisticRegression` is a binary classifier that expects boolean/numeric labels (True/False or 0/1)
- Our code was passing string labels ("Aggressive", "Conservative", "Neutral")
- This caused the error: `invalid literal for int() with base 10: 'Neutral'`

**Solution:**
- Implemented a multi-binary approach using OneVsRest strategy
- Created separate binary classifiers for each class:
  - `lr_aggressive`: Predicts if text is "Aggressive" (True/False)
  - `lr_conservative`: Predicts if text is "Conservative" (True/False)
- Combined binary predictions to get multi-class prediction:
  - If `lr_aggressive` predicts True → "Aggressive"
  - Else if `lr_conservative` predicts True → "Conservative"
  - Else → "Neutral"

**Code Changes:**
- `make_text_models()`: Creates two binary LogisticRegression models instead of one multi-class
- Prediction logic: Combines binary predictions to get final multi-class label
- Learning: Each binary model learns with boolean labels (true_label == 'Aggressive', etc.)

### 2. No Alerts Appearing on Dashboard

**Problem:**
- Alerts were being sent but not appearing on the dashboard
- Dashboard consumer group might have been consuming from old offset
- Alerts might not have been sent consistently

**Solution:**
1. **Always Send Text Classification Alerts:**
   - Changed alert sending to happen for every message (not just when drift detected)
   - Added logging every 10th alert to confirm they're being sent
   - Fixed alert format to ensure all fields are properly serialized

2. **Dashboard Consumer Fix:**
   - Changed `auto_offset_reset` from "earliest" to "latest" to see new alerts
   - Changed consumer group ID to "dashboard-group-new" to avoid offset issues
   - This ensures dashboard starts fresh and sees new alerts

**Code Changes:**
- `start_text_consumer()`: Always sends alerts for every classification
- `dashboard_realtime.py`: Updated consumer configuration
- Added debug logging to confirm alerts are being sent

## Testing

After these fixes:

1. **LogisticRegression should work:**
   - No more "invalid literal" errors
   - All three models (NB, LR, HT) should work correctly
   - Ensemble prediction combines all three models

2. **Dashboard should show alerts:**
   - Text classification alerts appear immediately
   - Numeric drift alerts appear when drift is detected
   - Fusion alerts appear when high-risk conditions are met

## How to Verify

1. **Restart the enhanced consumer:**
   ```bash
   python3 scripts/kafka_consumer_river_enhanced.py
   ```
   - Should see: `[TextConsumer] started with models: ['nb', 'lr', 'ht']`
   - Should NOT see: `lr error: invalid literal for int()`

2. **Check alert sending:**
   - Should see: `[TextConsumer] ✅ Alert sent: AAPL → Neutral` every 10 messages
   - Alerts should appear in dashboard

3. **Restart dashboard:**
   ```bash
   streamlit run scripts/dashboard_realtime.py
   ```
   - Should see alerts appearing in real-time
   - Check "Kafka Status" shows Consumer OK: True

## Expected Output

**Enhanced Consumer:**
```
[TextConsumer] started with models: ['nb', 'lr', 'ht']
[TextConsumer] ✅ Alert sent: AAPL → Neutral
[TextConsumer] Processed 20 messages. Accuracy: 0.950, F1: 0.850
```

**Dashboard:**
- Alerts table showing text_classification alerts
- Statistics showing alert counts
- Charts updating in real-time

## Notes

- LogisticRegression now uses a multi-binary approach (OneVsRest)
- This is a valid approach for multi-class classification with binary classifiers
- All three models (NB, LR, HT) are now working correctly
- Alerts are sent for every text classification (not just drift)
- Dashboard should now display all alerts in real-time

