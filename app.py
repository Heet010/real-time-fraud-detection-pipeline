import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime, timedelta

@st.cache_data(ttl=300)
def get_data(query: str):
    conn = psycopg2.connect(
        dbname="fraud_db", user="postgres",
        password="password", host="localhost", port=5432
    )
    df = pd.read_sql(query, conn)
    conn.close()
    return df

st.set_page_config(page_title="Fraud Detection Dashboard", layout="wide")
st.title("💡 Real-Time Fraud Detection Dashboard")

# 1) Fraud by Country
st.subheader("📍 Fraud by Country")
df_country = get_data("""
    SELECT country, COUNT(*) AS total_frauds
    FROM transactions_raw JOIN fraud_summary USING (user_id)
    WHERE is_fraud
    GROUP BY country
    ORDER BY total_frauds DESC;
""")
st.bar_chart(df_country.set_index("country"))

# 2) Top-Risk Users
st.subheader("⚠️ Top-Risk Users")
df_top = get_data("""
    SELECT user_id, anomaly_score, transaction_count
    FROM fraud_summary
    ORDER BY anomaly_score ASC
    LIMIT 10;
""")
st.dataframe(df_top)

# 3) Fraud Over Time (last 7 days)
st.subheader("⏱ Fraud Over Time (Last 7 Days)")
since = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
df_time = get_data(f"""
    SELECT date_trunc('day', last_scored) AS day, COUNT(*) AS frauds
    FROM fraud_summary
    WHERE is_fraud
      AND last_scored >= '{since}'
    GROUP BY 1
    ORDER BY 1;
""")
st.line_chart(df_time.set_index("day"))
