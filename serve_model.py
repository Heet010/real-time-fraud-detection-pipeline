from prometheus_fastapi_instrumentator import Instrumentator
import os
import requests
from joblib import load
import redis
import psycopg2
from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel
from psycopg2 import OperationalError
from metrics import TOTAL_TX_CNT, FRAUD_TX_CNT


# ─── 1. LOAD YOUR TRAINED MODEL ─────────────────────────────────────────────
MODEL_PATH = os.getenv("MODEL_PATH", "fraud_isolation_forest.joblib")
model = load(MODEL_PATH)

# ─── 2. REDIS HELPER ─────────────────────────────────────────────────────────
def load_redis():
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=0
    )

r = load_redis()

# ─── 3. POSTGRES HELPER ───────────────────────────────────────────────────────
def get_db():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB", "fraud_db"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "password"),
            host=os.getenv("POSTGRES_HOST", "postgres"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            connect_timeout=5,           # <- fail after 5s
        )
    except OperationalError as e:
        # return a 503 so the request doesn’t hang indefinitely
        raise HTTPException(
            status_code=503,
            detail="Database unavailable, please try again shortly."
        )
    try:
        yield conn
    finally:
        conn.close()

# ─── 4. LM STUDIO CONFIG ────────────────────────────────────────────────────
LMSTUDIO_URL   = os.getenv("LMSTUDIO_URL",   "http://127.0.0.1:8080/v1/generate")
LMSTUDIO_MODEL = os.getenv("LMSTUDIO_MODEL", "mistral-7b")

# ─── 5. REQUEST/RESPONSE SCHEMAS ────────────────────────────────────────────
class PredictionResponse(BaseModel):
    user_id: int
    anomaly_score: float
    is_fraud: bool

class ExplainResponse(PredictionResponse):
    explanation: str

app = FastAPI(title="Fraud Detection & Explainability API")
Instrumentator().instrument(app).expose(app)

# ─── 6. PREDICT ENDPOINT ───────────────────────────────────────────────────
@app.get("/predict", response_model=PredictionResponse)
def predict(user_id: int = Query(..., description="ID of the user to score")):
    key = f"user:{user_id}"
    if not r.exists(key):
        raise HTTPException(404, detail=f"No features for user {user_id}")

    data       = r.hgetall(key)
    count      = int(data[b"count"])
    avg_amount = float(data[b"avg_amount"])

    score    = float(model.decision_function([[count, avg_amount]])[0])
    is_fraud = score < 0.0

    # ── Prometheus counters ────────────────────────────────
    TOTAL_TX_CNT.inc()          # increment for every request
    if is_fraud:
        FRAUD_TX_CNT.inc()      # increment only when flagged as fraud
    # ───────────────────────────────────────────────────────

    return PredictionResponse(
        user_id=user_id,
        anomaly_score=score,
        is_fraud=is_fraud
    )


# ─── 7. EXPLAIN ENDPOINT ───────────────────────────────────────────────────
@app.get("/explain", response_model=ExplainResponse)
def explain(user_id: int = Query(..., description="ID of the user to explain")):
    key = f"user:{user_id}"
    if not r.exists(key):
        raise HTTPException(404, detail=f"No features for user {user_id}")

    data       = r.hgetall(key)
    count      = int(data[b"count"])
    avg_amount = float(data[b"avg_amount"])
    score      = float(model.decision_function([[count, avg_amount]])[0])
    is_fraud   = score < 0.0

    prompt = (
        f"User {user_id} was flagged with anomaly score {score:.3f} "
        f"(fraud={is_fraud}). They made {count} transactions "
        f"averaging ${avg_amount:.2f}. Explain why this might indicate fraud."
    )

    try:
        resp = requests.post(
            LMSTUDIO_URL,
            json={
                "model": LMSTUDIO_MODEL,
                "prompt": prompt,
                "max_new_tokens": 100,
                "temperature": 0.7,
                "top_p": 0.9
            },
            timeout=10
        )
        resp.raise_for_status()
        explanation = resp.json()["results"][0]["text"].strip()
    except Exception:
        explanation = (
            f"User {user_id}, score {score:.3f}, made {count} txns averaging "
            f"${avg_amount:.2f}. This deviates significantly from normal behavior."
        )

    return ExplainResponse(
        user_id=user_id,
        anomaly_score=score,
        is_fraud=is_fraud,
        explanation=explanation
    )

# ─── 8. SQL ANALYTICS ENDPOINTS ─────────────────────────────────────────────
@app.get("/fraud-by-country")
def fraud_by_country(db_conn=Depends(get_db)):
    cur = db_conn.cursor()
    cur.execute(
        """
        SELECT country, COUNT(*) AS total_frauds
        FROM transactions_raw JOIN fraud_summary USING (user_id)
        WHERE is_fraud
        GROUP BY country
        ORDER BY total_frauds DESC;
        """
    )
    results = [{"country": c, "total_frauds": n} for c, n in cur.fetchall()]
    cur.close()
    return results

@app.get("/top-risk-users")
def top_risk_users(limit: int = 10, db_conn=Depends(get_db)):
    cur = db_conn.cursor()
    cur.execute(
        """
        SELECT user_id, anomaly_score, transaction_count
        FROM fraud_summary
        ORDER BY anomaly_score ASC
        LIMIT %s;
        """,
        (limit,)
    )
    results = [
        {"user_id": u, "anomaly_score": s, "transaction_count": cnt}
        for u, s, cnt in cur.fetchall()
    ]
    cur.close()
    return results
