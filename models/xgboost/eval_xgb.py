import pandas as pd
from joblib import load
from sklearn.metrics import classification_report

# 1. Load feature data
# Adjust path if needed depending on where you run this script
df = pd.read_csv('/workspace/real-time-fraud-detection-pipeline/user_features.csv')

# 2. Simulate fraud labels via Isolation Forest
if_model = load('/workspace/real-time-fraud-detection-pipeline/models/isolation_forest/fraud_isolation_forest.joblib')
X = df[['transaction_count', 'avg_amount']]
if_scores = if_model.decision_function(X)

# Mark the bottom 5% of scores as fraud (label=1), rest as normal (label=0)
threshold = pd.Series(if_scores).quantile(0.05)
df['is_fraud_label'] = (if_scores < threshold).astype(int)

# 3. Load the trained XGBoost model
xgb_model = load('xgb_model.joblib')

# 4. Make predictions
y_true = df['is_fraud_label']
y_pred = xgb_model.predict(X)

# 5. Print evaluation metrics
print("XGBoost Classification Report:\n")
print(classification_report(y_true, y_pred, target_names=['normal','fraud'],zero_division=0))