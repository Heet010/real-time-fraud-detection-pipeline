# producer.py
import os
import time
import random
from pathlib import Path

import psycopg2
import avro.schema
from confluent_kafka.avro import AvroProducer

# ──────────────────────────────────────────────────────────
# 0. Locate the Avro schema in a portable way
# ──────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
schema_path = BASE_DIR / "schemas" / "transactions.avsc"

with open(schema_path, "r", encoding="utf-8") as f:
    value_schema = avro.schema.parse(f.read())

# ──────────────────────────────────────────────────────────
# 1. Kafka + Schema Registry config
#    • Defaults assume you run *locally*.
#    • When inside Docker Compose, override via env vars or
#      they will resolve to service names `kafka` / `schema-registry`.
# ──────────────────────────────────────────────────────────
bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
schema_registry   = os.getenv("SCHEMA_REGISTRY_URL",    "http://localhost:8081")

producer = AvroProducer(
    {
        "bootstrap.servers": bootstrap_servers,
        "schema.registry.url": schema_registry
    },
    default_value_schema=value_schema
)

# ──────────────────────────────────────────────────────────
# 2. Postgres connection parameters
#    • Override via env vars if needed.
# ──────────────────────────────────────────────────────────
PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT = int(os.getenv("POSTGRES_PORT", "5432"))

db_conn = psycopg2.connect(
    dbname=os.getenv("POSTGRES_DB", "fraud_db"),
    user=os.getenv("POSTGRES_USER", "postgres"),
    password=os.getenv("POSTGRES_PASSWORD", "password"),
    host=PG_HOST,
    port=PG_PORT,
)
db_conn.autocommit = True
db_cur = db_conn.cursor()

# ──────────────────────────────────────────────────────────
# 3. Fake-transaction generator
# ──────────────────────────────────────────────────────────
def generate_transaction():
    return {
        "transaction_id": random.randint(100000, 999999),
        "user_id":       random.choice([101, 102, 103, 104]),
        "amount":        round(random.uniform(10.0, 5000.0), 2),
        "timestamp":     int(time.time()),
        "country":       random.choice(["US", "NG", "GB", "IN", "DE"]),
    }

# ──────────────────────────────────────────────────────────
# 4. Main loop
# ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🚀 Starting Avro producer...")
    try:
        while True:
            txn = generate_transaction()

            # a) Publish to Kafka (Avro encoded)
            producer.produce(topic="transactions", value=txn)
            producer.flush()

            # b) Store raw in Postgres
            db_cur.execute(
                """
                INSERT INTO transactions_raw
                      (id, user_id, amount, timestamp, country)
                VALUES (%s, %s, %s, to_timestamp(%s), %s)
                """,
                (
                    txn["transaction_id"],
                    txn["user_id"],
                    txn["amount"],
                    txn["timestamp"],
                    txn["country"],
                ),
            )

            print(f"✅ Sent & stored: {txn}")
            time.sleep(1)

    except KeyboardInterrupt:
        print("🛑 Producer stopped by user.")

    finally:
        db_cur.close()
        db_conn.close()
