import os

import plotly.graph_objects as go
import requests
import streamlit as st

API = os.getenv("API_BASE_URL", "http://localhost:8000")

st.title("Dashboard")

symbol = st.selectbox("Symbol", ["NIFTY", "BANKNIFTY"])
timeframe = st.selectbox("Timeframe", ["15m", "30m", "1h", "4h", "1D"])

if st.button("Refresh"):
    with st.spinner("Fetching data..."):
        try:
            token = st.session_state.get("token", "")
            headers = {"Authorization": f"Bearer {token}"}

            sig_resp = requests.post(
                f"{API}/signal",
                json={"symbol": symbol, "timeframe": timeframe},
                headers=headers,
                timeout=10,
            )
            pred_resp = requests.get(
                f"{API}/prediction",
                params={"symbol": symbol, "timeframe": timeframe},
                headers=headers,
                timeout=10,
            )

            if sig_resp.ok:
                sig = sig_resp.json()
                col1, col2 = st.columns(2)
                color = {"BUY": "green", "SELL": "red", "HOLD": "orange"}[sig["signal"]]
                col1.markdown(f"### Signal: :{color}[{sig['signal']}]")
                col2.metric("Confidence", f"{sig['confidence']}%")

            if pred_resp.ok:
                pred = pred_resp.json()
                st.subheader("ML Prediction")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Direction", pred["direction"])
                c2.metric("Entry", pred["entry_price"])
                c3.metric("Stop Loss", pred["stop_loss"])
                c4.metric("Target", pred["target_price"])

        except requests.RequestException as e:
            st.error(f"API error: {e}")
