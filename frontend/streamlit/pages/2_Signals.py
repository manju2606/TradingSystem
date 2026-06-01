import os

import pandas as pd
import requests
import streamlit as st

API = os.getenv("API_BASE_URL", "http://localhost:8000")

st.title("Multi-Timeframe Signals")

symbol = st.selectbox("Symbol", ["NIFTY", "BANKNIFTY"])
token = st.session_state.get("token", "")
headers = {"Authorization": f"Bearer {token}"}

TIMEFRAMES = ["15m", "30m", "1h", "4h", "6h", "8h", "1D", "1W", "1M"]

if st.button("Generate All Signals"):
    rows = []
    progress = st.progress(0)
    for i, tf in enumerate(TIMEFRAMES):
        try:
            r = requests.post(
                f"{API}/signal",
                json={"symbol": symbol, "timeframe": tf},
                headers=headers,
                timeout=15,
            )
            if r.ok:
                d = r.json()
                rows.append({"Timeframe": tf, "Signal": d["signal"], "Confidence": d["confidence"]})
        except Exception:
            rows.append({"Timeframe": tf, "Signal": "ERROR", "Confidence": 0})
        progress.progress((i + 1) / len(TIMEFRAMES))

    if rows:
        df = pd.DataFrame(rows)

        def color_signal(val):
            colors = {"BUY": "background-color: #d4edda", "SELL": "background-color: #f8d7da", "HOLD": ""}
            return colors.get(val, "")

        st.dataframe(df.style.applymap(color_signal, subset=["Signal"]), use_container_width=True)
