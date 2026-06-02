import ta
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
from plotly.subplots import make_subplots

st.set_page_config(page_title="Market Watch", layout="wide")

# ── Symbol catalog ─────────────────────────────────────────────────────────────

NSE_SYMBOLS = {
    "NIFTY 50":         "^NSEI",
    "BANK NIFTY":       "^NSEBANK",
    "NIFTY IT":         "^CNXIT",
    "NIFTY PHARMA":     "^CNXPHARMA",
    "NIFTY AUTO":       "^CNXAUTO",
    "NIFTY MIDCAP 100": "^NSMIDCP",
    "RELIANCE":         "RELIANCE.NS",
    "TCS":              "TCS.NS",
    "INFOSYS":          "INFY.NS",
    "HDFC BANK":        "HDFCBANK.NS",
    "ICICI BANK":       "ICICIBANK.NS",
    "SBI":              "SBIN.NS",
    "WIPRO":            "WIPRO.NS",
    "ITC":              "ITC.NS",
    "TATA MOTORS":      "TATAMOTORS.NS",
    "BAJAJ FINANCE":    "BAJFINANCE.NS",
    "MARUTI SUZUKI":    "MARUTI.NS",
    "TATA STEEL":       "TATASTEEL.NS",
    "HINDALCO":         "HINDALCO.NS",
    "ADANI ENT.":       "ADANIENT.NS",
}

BSE_SYMBOLS = {
    "SENSEX":        "^BSESN",
    "RELIANCE":      "RELIANCE.BO",
    "TCS":           "TCS.BO",
    "INFOSYS":       "INFY.BO",
    "HDFC BANK":     "HDFCBANK.BO",
    "ICICI BANK":    "ICICIBANK.BO",
    "SBI":           "SBIN.BO",
    "WIPRO":         "WIPRO.BO",
    "ITC":           "ITC.BO",
    "TATA MOTORS":   "TATAMOTORS.BO",
    "L&T":           "LT.BO",
    "ASIAN PAINTS":  "ASIANPAINT.BO",
    "NESTLE INDIA":  "NESTLEIND.BO",
    "BAJAJ AUTO":    "BAJAJ-AUTO.BO",
    "ULTRATECH CEM": "ULTRACEMCO.BO",
}

MCX_SYMBOLS = {
    "GOLD":            "GC=F",
    "SILVER":          "SI=F",
    "CRUDE OIL (WTI)": "CL=F",
    "BRENT CRUDE":     "BZ=F",
    "NATURAL GAS":     "NG=F",
    "COPPER":          "HG=F",
    "ALUMINIUM":       "ALI=F",
}

EXCHANGE_MAP = {"NSE": NSE_SYMBOLS, "BSE": BSE_SYMBOLS, "MCX": MCX_SYMBOLS}
CURRENCY     = {"NSE": "₹", "BSE": "₹", "MCX": "$"}

TF_CONFIG = {
    "1D":  {"period": "1d",  "interval": "5m"},
    "5D":  {"period": "5d",  "interval": "30m"},
    "1M":  {"period": "1mo", "interval": "1d"},
    "3M":  {"period": "3mo", "interval": "1d"},
    "6M":  {"period": "6mo", "interval": "1d"},
    "1Y":  {"period": "1y",  "interval": "1d"},
    "3Y":  {"period": "3y",  "interval": "1wk"},
}


# ── Data fetching ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=60, show_spinner=False)
def fetch_watchlist(symbol_dict: dict) -> pd.DataFrame:
    tickers = list(symbol_dict.values())
    if not tickers:
        return pd.DataFrame()

    raw = yf.download(tickers, period="5d", interval="1d", progress=False, auto_adjust=True)

    rows = []
    for name, ticker in symbol_dict.items():
        try:
            close = raw["Close"][ticker] if len(tickers) > 1 else raw["Close"]
            high  = raw["High"][ticker]  if len(tickers) > 1 else raw["High"]
            low   = raw["Low"][ticker]   if len(tickers) > 1 else raw["Low"]

            close = close.dropna()
            if close.empty:
                continue

            curr = float(close.iloc[-1])
            prev = float(close.iloc[-2]) if len(close) >= 2 else curr
            chg  = (curr - prev) / prev * 100 if prev else 0.0

            rows.append({
                "Symbol":    name,
                "Ticker":    ticker,
                "Price":     round(curr, 2),
                "Chg %":     round(chg, 2),
                "Day High":  round(float(high.dropna().iloc[-1]), 2),
                "Day Low":   round(float(low.dropna().iloc[-1]), 2),
            })
        except Exception:
            continue

    return pd.DataFrame(rows)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_ohlcv(ticker: str, period: str, interval: str) -> pd.DataFrame:
    df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()


# ── Chart builder ──────────────────────────────────────────────────────────────

def build_chart(
    df: pd.DataFrame,
    symbol_name: str,
    currency: str,
    chart_type: str,
    show_ema20: bool,
    show_ema50: bool,
    show_bb: bool,
    show_volume: bool,
) -> go.Figure:
    rows    = 2 if show_volume else 1
    heights = [0.75, 0.25] if show_volume else [1.0]

    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        row_heights=heights,
        vertical_spacing=0.03,
    )

    close = df["Close"].squeeze()

    # ── Price trace ────────────────────────────────────────────────────────────
    if chart_type == "Candlestick":
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df["Open"].squeeze(),
            high=df["High"].squeeze(),
            low=df["Low"].squeeze(),
            close=close,
            name="Price",
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
        ), row=1, col=1)
    else:
        fig.add_trace(go.Scatter(
            x=df.index, y=close, name="Price",
            line=dict(color="#2196F3", width=2),
            fill="tozeroy", fillcolor="rgba(33,150,243,0.05)",
        ), row=1, col=1)

    # ── Indicators ─────────────────────────────────────────────────────────────
    if show_ema20 and len(close) >= 20:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=ta.trend.ema_indicator(close, window=20),
            name="EMA 20", line=dict(color="#FF9800", width=1.2),
        ), row=1, col=1)

    if show_ema50 and len(close) >= 50:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=ta.trend.ema_indicator(close, window=50),
            name="EMA 50", line=dict(color="#9C27B0", width=1.2),
        ), row=1, col=1)

    if show_bb and len(close) >= 20:
        bb = ta.volatility.BollingerBands(close)
        fig.add_trace(go.Scatter(
            x=df.index, y=bb.bollinger_hband(),
            name="BB Upper", line=dict(color="#607D8B", width=1, dash="dot"),
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=bb.bollinger_lband(),
            name="BB Lower", line=dict(color="#607D8B", width=1, dash="dot"),
            fill="tonexty", fillcolor="rgba(96,125,139,0.05)",
        ), row=1, col=1)

    # ── Volume ─────────────────────────────────────────────────────────────────
    if show_volume and rows == 2:
        vol   = df["Volume"].squeeze()
        colors = [
            "#26a69a" if c >= o else "#ef5350"
            for c, o in zip(df["Close"].squeeze(), df["Open"].squeeze())
        ]
        fig.add_trace(go.Bar(
            x=df.index, y=vol, name="Volume",
            marker_color=colors, opacity=0.7,
        ), row=2, col=1)

    fig.update_layout(
        title=dict(text=f"{symbol_name}", font=dict(size=16)),
        xaxis_rangeslider_visible=False,
        yaxis_title=f"Price ({currency})",
        height=520,
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(orientation="h", y=1.02, x=0),
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(255,255,255,0.07)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.07)")

    return fig


# ── Page ───────────────────────────────────────────────────────────────────────

st.title("Market Watch")

tab_nse, tab_bse, tab_mcx = st.tabs(["NSE", "BSE", "MCX"])

for tab, exchange in zip([tab_nse, tab_bse, tab_mcx], ["NSE", "BSE", "MCX"]):
    with tab:
        symbols  = EXCHANGE_MAP[exchange]
        currency = CURRENCY[exchange]
        key      = f"sel_{exchange}"

        left, right = st.columns([4, 6], gap="large")

        # ── Watchlist ──────────────────────────────────────────────────────────
        with left:
            hdr, btn = st.columns([3, 1])
            hdr.subheader("Watchlist")
            if btn.button("Refresh", key=f"ref_{exchange}", use_container_width=True):
                st.cache_data.clear()

            with st.spinner("Loading prices..."):
                wl_df = fetch_watchlist(symbols)

            if wl_df.empty:
                st.warning("Could not load prices. Check network.")
            else:
                display = wl_df[["Symbol", "Price", "Chg %", "Day High", "Day Low"]].copy()

                def _style_chg(val):
                    color = "#26a69a" if val >= 0 else "#ef5350"
                    return f"color: {color}; font-weight: bold"

                styled = display.style.applymap(_style_chg, subset=["Chg %"]).format({
                    "Price":    f"{currency}{{:,.2f}}",
                    "Chg %":   "{:+.2f}%",
                    "Day High": f"{currency}{{:,.2f}}",
                    "Day Low":  f"{currency}{{:,.2f}}",
                })

                event = st.dataframe(
                    styled,
                    use_container_width=True,
                    hide_index=True,
                    height=560,
                    on_select="rerun",
                    selection_mode="single-row",
                    key=f"tbl_{exchange}",
                )

                rows_sel = event.selection.rows
                if rows_sel:
                    st.session_state[key] = int(rows_sel[0])

        # ── Chart ──────────────────────────────────────────────────────────────
        with right:
            st.subheader("Chart")

            idx = st.session_state.get(key)
            if idx is None or wl_df.empty:
                st.info("Click a symbol in the watchlist to view its chart.")
            else:
                row         = wl_df.iloc[idx]
                sym_name    = row["Symbol"]
                ticker      = row["Ticker"]
                curr_price  = row["Price"]
                chg_pct     = row["Chg %"]

                # Price header
                c1, c2, c3 = st.columns(3)
                c1.metric("Symbol", sym_name)
                c2.metric("Price", f"{currency}{curr_price:,.2f}", f"{chg_pct:+.2f}%")
                c3.metric("Ticker", ticker)

                st.divider()

                # Controls
                ctl1, ctl2, ctl3 = st.columns([3, 2, 3])

                tf = ctl1.radio(
                    "Timeframe",
                    list(TF_CONFIG.keys()),
                    horizontal=True,
                    index=2,
                    key=f"tf_{exchange}",
                )
                chart_type = ctl2.radio(
                    "Chart",
                    ["Candlestick", "Line"],
                    key=f"ct_{exchange}",
                )
                with ctl3:
                    show_ema20  = st.checkbox("EMA 20",  value=True,  key=f"e20_{exchange}")
                    show_ema50  = st.checkbox("EMA 50",  value=False, key=f"e50_{exchange}")
                    show_bb     = st.checkbox("Bollinger Bands", key=f"bb_{exchange}")
                    show_volume = st.checkbox("Volume",  value=True,  key=f"vol_{exchange}")

                cfg = TF_CONFIG[tf]
                with st.spinner(f"Loading {sym_name} ({tf})..."):
                    ohlcv = fetch_ohlcv(ticker, cfg["period"], cfg["interval"])

                if ohlcv.empty:
                    st.warning("No data available for this symbol / timeframe.")
                else:
                    fig = build_chart(
                        ohlcv, sym_name, currency,
                        chart_type, show_ema20, show_ema50, show_bb, show_volume,
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # History table (last 10 rows)
                    with st.expander("Price History (last 10 bars)"):
                        hist = ohlcv[["Open", "High", "Low", "Close", "Volume"]].tail(10).copy()
                        hist.index = hist.index.strftime("%Y-%m-%d %H:%M") if hasattr(hist.index, "strftime") else hist.index
                        st.dataframe(
                            hist.style.format({
                                "Open":   f"{currency}{{:,.2f}}",
                                "High":   f"{currency}{{:,.2f}}",
                                "Low":    f"{currency}{{:,.2f}}",
                                "Close":  f"{currency}{{:,.2f}}",
                                "Volume": "{:,.0f}",
                            }),
                            use_container_width=True,
                        )
