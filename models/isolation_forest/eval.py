from joblib import load
import pandas as pd

model = load('fraud_isolation_forest.joblib')
df = pd.read_csv('user_features.csv')
scores = model.decision_function(df[['transaction_count', 'avg_amount']])
df['anomaly_score'] = scores
print(df.sort_values('anomaly_score').head(10))