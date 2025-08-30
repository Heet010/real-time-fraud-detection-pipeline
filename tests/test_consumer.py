# tests/test_consumer.py
import os
import pytest
import psycopg2
from consumer import process_single_transaction

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/fraud_db")

@pytest.fixture(scope="module")
def pg_conn():
    # Connect to the CI Postgres service
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    # Reset tables
    cur.execute("DROP TABLE IF EXISTS fraud_summary")
    cur.execute("DROP TABLE IF EXISTS transactions_raw")
    # Create schema
    cur.execute("""
        CREATE TABLE transactions_raw (
            id SERIAL PRIMARY KEY,
            user_id INT,
            amount NUMERIC,
            timestamp TIMESTAMP,
            country VARCHAR(2)
        );
    """)
    cur.execute("""
        CREATE TABLE fraud_summary (
            user_id INT PRIMARY KEY,
            transaction_count INT,
            total_amount NUMERIC,
            avg_amount NUMERIC,
            anomaly_score FLOAT,
            is_fraud BOOL,
            last_scored TIMESTAMP
        );
    """)
    conn.commit()
    yield conn
    cur.close()
    conn.close()

def test_process_single_transaction(monkeypatch, pg_conn):
    txn = {"user_id": 42, "amount": 100.0, "timestamp": 1_700_000_000, "country": "US"}

    # Stub the /predict call
    class FakeResp:
        status_code = 200
        def raise_for_status(self): pass
        def json(self): return {"anomaly_score": -1.0, "is_fraud": True}
    monkeypatch.setattr("consumer.requests.get", lambda *args, **kwargs: FakeResp())

    # Run the helper
    process_single_transaction(txn, pg_conn)

    # Validate transactions_raw
    cur = pg_conn.cursor()
    cur.execute("SELECT COUNT(*), SUM(amount) FROM transactions_raw WHERE user_id = %s", (42,))
    assert cur.fetchone() == (1, 100.0)

    # Validate fraud_summary
    cur.execute("SELECT user_id, is_fraud FROM fraud_summary WHERE user_id = %s", (42,))
    assert cur.fetchone() == (42, True)
    cur.close()
