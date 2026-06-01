import streamlit as st

st.set_page_config(
    page_title="AI Trading Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("AI Multi-Trading Platform — NSE Futures")
st.markdown(
    """
    **Paper trading dashboard** for NIFTY and BANKNIFTY futures.
    Use the sidebar to navigate between sections.
    """
)

col1, col2, col3 = st.columns(3)
col1.metric("Win Rate Target", ">55%")
col2.metric("Sharpe Target", ">1.5")
col3.metric("Max Drawdown", "<10%")
