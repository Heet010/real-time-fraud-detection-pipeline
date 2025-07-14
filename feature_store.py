import json
from kafka import KafkaConsumer
import redis

# 1️⃣ Connect to Kafka
consumer = KafkaConsumer(
    'transactions',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='feature-store-group'
)

# 2️⃣ Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0)

print("🛠️  Feature store updater running…")

# 3️⃣ Process each transaction and update Redis
for msg in consumer:
    txn = msg.value
    user_key = f"user:{txn['user_id']}"

    # Increment count and sum atomically
    pipe = r.pipeline()
    pipe.hincrby(user_key, 'count', 1)
    pipe.hincrbyfloat(user_key, 'sum', txn['amount'])
    pipe.execute()

    # Compute average = sum / count
    data = r.hgetall(user_key)
    count = int(data[b'count'])
    total = float(data[b'sum'])
    avg = total / count if count else 0.0

    # Store average
    r.hset(user_key, 'avg_amount', avg)

    print(f"Updated {user_key}: count={count}, avg_amount={avg:.2f}")
