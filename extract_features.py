import redis
import pandas as pd

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0)

# Fetch all user keys
keys = r.keys('user:*')

rows = []
for key in keys:
    user_id = key.decode().split(':')[1]
    data = r.hgetall(key)
    # Redis returns bytes, decode and convert
    count = int(data[b'count'])
    total = float(data[b'sum'])
    avg   = float(data[b'avg_amount'])
    rows.append({
        'user_id': int(user_id),
        'transaction_count': count,
        'total_amount': total,
        'avg_amount': avg
    })

# Build DataFrame
df = pd.DataFrame(rows)
# Optional: shuffle
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

# Save to CSV for training
df.to_csv('user_features.csv', index=False)
print(f"Extracted {len(df)} users to user_features.csv")



'''Connects to Redis and lists all keys matching user:*.

Reads each user’s count, sum, and avg_amount.

Puts them into a pandas DataFrame and writes user_features.csv.
'''
