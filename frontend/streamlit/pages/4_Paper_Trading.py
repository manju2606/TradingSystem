import os

import requests
import streamlit as st

API = os.getenv("API_BASE_URL", "http://localhost:8000")

st.title("Paper Trading")

token = st.session_state.get("token", "")
headers = {"Authorization": f"Bearer {token}"}

st.subheader("Place Order")
with st.form("order_form"):
    col1, col2, col3, col4 = st.columns(4)
    symbol = col1.selectbox("Symbol", ["NIFTY", "BANKNIFTY"])
    order_type = col2.selectbox("Type", ["BUY", "SELL"])
    quantity = col3.number_input("Quantity", min_value=1, value=1, step=1)
    price = col4.number_input("Price", min_value=1.0, value=22000.0, step=0.5)
    submitted = st.form_submit_button("Place Order")

if submitted:
    r = requests.post(
        f"{API}/paper/order",
        json={"symbol": symbol, "order_type": order_type, "quantity": int(quantity), "price": str(price)},
        headers=headers,
        timeout=10,
    )
    if r.ok:
        st.success(f"Order placed: {r.json()}")
    else:
        st.error(r.text)

st.divider()
st.subheader("Open Positions")
if st.button("Refresh Positions"):
    r = requests.get(f"{API}/portfolio/positions", headers=headers, timeout=10)
    if r.ok:
        positions = r.json()
        if positions:
            st.dataframe(positions, use_container_width=True)
        else:
            st.info("No open positions.")
    else:
        st.error(r.text)
