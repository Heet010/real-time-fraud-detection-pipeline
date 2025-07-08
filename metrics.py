# metrics.py  (project root, next to serve_model.py)
from prometheus_client import Counter

TOTAL_TX_CNT = Counter(
    "fraud_summary_total_transactions",
    "Total number of transactions scored by /predict"
)

FRAUD_TX_CNT = Counter(
    "fraud_summary_is_fraud_total",
    "Number of transactions the model labelled as fraud"
)
