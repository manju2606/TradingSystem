import os
from datetime import date

import requests
import streamlit as st

API = os.getenv("API_BASE_URL", "http://localhost:8000")

st.title("Backtest")

token = st.session_state.get("token", "")
headers = {"Authorization": f"Bearer {token}"}

with st.form("backtest_form"):
    col1, col2, col3 = st.columns(3)
    symbol = col1.selectbox("Symbol", ["NIFTY", "BANKNIFTY"])
    strategy = col2.selectbox("Strategy", ["ema_crossover", "rsi_mean_reversion", "ml_signal"])
    col2b, col3b = st.columns(2)
    start = col2b.date_input("Start", value=date(2023, 1, 1))
    end = col3b.date_input("End", value=date(2024, 1, 1))
    submitted = st.form_submit_button("Run Backtest")

if submitted:
    r = requests.post(
        f"{API}/backtest/run",
        params={"symbol": symbol, "strategy": strategy, "start": str(start), "end": str(end)},
        headers=headers,
        timeout=10,
    )
    if r.ok:
        st.info(f"Backtest queued: {r.json()}")
    else:
        st.error(r.text)

st.divider()
st.subheader("Previous Backtests")
if st.button("Load History"):
    r = requests.get(f"{API}/backtest", headers=headers, timeout=10)
    if r.ok and r.json():
        st.dataframe(r.json(), use_container_width=True)
    else:
        st.info("No backtests yet.")
