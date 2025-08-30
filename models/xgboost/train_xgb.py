import pandas as pd
from joblib import load
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# 1️⃣ Load the basic user features
df = pd.read_csv('user_features.csv')

# 2️⃣ Load the trained Isolation Forest model
if_model = load('models/isolation_forest/fraud_isolation_forest.joblib')

# 3️⃣ Compute anomaly scores for each user
X = df[['transaction_count', 'avg_amount']]
df['anomaly_score'] = if_model.decision_function(X)

# 4️⃣ Simulate “fraud” labels as the bottom 5% by score
threshold = df['anomaly_score'].quantile(0.05)
df['is_fraud_label'] = (df['anomaly_score'] < threshold).astype(int)

# 5️⃣ Prepare data for XGBoost
X = df[['transaction_count', 'avg_amount']]
y = df['is_fraud_label']

# 6️⃣ Split into train/test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42
)

# 7️⃣ Train the XGBoost classifier
model = XGBClassifier(
    n_estimators=100,
    objective='binary:logistic',   # ensure we’re doing binary classification
    base_score=0.5,                # valid default prior probability
    eval_metric='logloss',
    random_state=42
)
model.fit(X_train, y_train)

# 8️⃣ Evaluate and report
y_pred = model.predict(X_test)
print("=== XGBoost Classification Report ===")
print(classification_report(y_test, y_pred, target_names=['normal','fraud']))

# 9️⃣  Save the trained XGBoost model
from joblib import dump
dump(model, 'models/xgboost/xgb_model.joblib')
print("Saved XGBoost model to models/xgboost/xgb_model.joblib")