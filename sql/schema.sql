CREATE TABLE IF NOT EXISTS transactions_raw (
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL,
  amount NUMERIC NOT NULL,
  timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
  country VARCHAR(2) NOT NULL
);

CREATE TABLE IF NOT EXISTS fraud_summary (
  user_id INT PRIMARY KEY,
  transaction_count INT NOT NULL,
  total_amount NUMERIC NOT NULL,
  avg_amount NUMERIC NOT NULL,
  anomaly_score DOUBLE PRECISION NOT NULL,
  is_fraud BOOLEAN NOT NULL,
  last_scored TIMESTAMP NOT NULL DEFAULT NOW()
);
