
import pandas as pd
from sklearn.ensemble import IsolationForest
from joblib import dump

# 1️⃣ Load feature data
df = pd.read_csv('user_features.csv')

# 2️⃣ Select the numeric feature columns
X = df[['transaction_count', 'avg_amount']]

# 3️⃣ Initialize and train the model
model = IsolationForest(
    n_estimators=100,
    max_samples='auto',
    contamination=0.05,  # assume ~5% of users are fraudulent
    random_state=42
)
model.fit(X)

# 4️⃣ Save the trained model
dump(model, 'fraud_isolation_forest.joblib')
print("Model trained and saved to fraud_isolation_forest.joblib")




'''
Isolation Forest is an unsupervised anomaly detector: it “isolates” outliers in the feature space.

We train on transaction_count and avg_amount.

contamination=0.05 tells it to expect ~5% anomalies (you can adjust).

The trained model is serialized so our serving layer can load it instantly.
'''





'''
Isolation Forest is an unsupervised anomaly detector: it “isolates” outliers in the feature space.

We train on transaction_count and avg_amount.

contamination=0.05 tells it to expect ~5% anomalies (you can adjust).

The trained model is serialized so our serving layer can load it instantly.
'''