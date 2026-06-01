import os

import pandas as pd
import requests
import streamlit as st

API = os.getenv("API_BASE_URL", "http://localhost:8000")

st.title("ML Predictions")

col1, col2 = st.columns(2)
symbol = col1.selectbox("Symbol", ["NIFTY", "BANKNIFTY"])
timeframe = col2.selectbox("Timeframe", ["15m", "30m", "1h", "4h", "6h", "8h", "1D", "1W", "1M"])

token = st.session_state.get("token", "")
headers = {"Authorization": f"Bearer {token}"}

if st.button("Get Prediction"):
    with st.spinner("Running ML model..."):
        try:
            r = requests.get(
                f"{API}/prediction",
                params={"symbol": symbol, "timeframe": timeframe},
                headers=headers,
                timeout=30,
            )
            if r.ok:
                p = r.json()
                st.subheader(f"{symbol} · {timeframe} · {p['model'].upper()}")
                cols = st.columns(5)
                cols[0].metric("Direction", p["direction"])
                cols[1].metric("Probability", f"{float(p['probability']):.1%}")
                cols[2].metric("Entry", p["entry_price"])
                cols[3].metric("Stop Loss", p["stop_loss"])
                cols[4].metric("Target", p["target_price"])
            else:
                st.error(r.text)
        except requests.RequestException as e:
            st.error(str(e))
