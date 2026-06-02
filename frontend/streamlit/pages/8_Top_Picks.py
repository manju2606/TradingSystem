"""
Top Gainers, Losers & Tomorrow's Trade Picks

Data sources (in priority order):
  1. NSE India public API  — live gainers / losers (requires session cookie)
  2. yfinance Nifty 50     — batch fallback when NSE API is blocked
  3. MoneyControl          — reference site (uses same NSE India feed)

Scoring: RSI · MACD · Volume · EMA trend · Momentum rank → top 5 picks.
Disclaimer: educational only, not financial advice.
"""

from __future__ import annotations

import requests
import ta
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Top Picks", layout="wide")

# ── Nifty 50 universe ─────────────────────────────────────────────────────────

NIFTY50: dict[str, str] = {
    "ADANI ENT":    "ADANIENT.NS",   "ADANI PORTS":  "ADANIPORTS.NS",
    "APOLLO HOSP":  "APOLLOHOSP.NS", "ASIAN PAINTS": "ASIANPAINT.NS",
    "AXIS BANK":    "AXISBANK.NS",   "BAJAJ AUTO":   "BAJAJ-AUTO.NS",
    "BAJAJ FINSV":  "BAJAJFINSV.NS", "BAJAJ FIN":    "BAJFINANCE.NS",
    "BPCL":         "BPCL.NS",       "BHARTI ARTL":  "BHARTIARTL.NS",
    "BRITANNIA":    "BRITANNIA.NS",  "CIPLA":        "CIPLA.NS",
    "COAL INDIA":   "COALINDIA.NS",  "DIVIS LAB":    "DIVISLAB.NS",
    "DR REDDY":     "DRREDDY.NS",    "EICHER MOT":   "EICHERMOT.NS",
    "GRASIM":       "GRASIM.NS",     "HCL TECH":     "HCLTECH.NS",
    "HDFC BANK":    "HDFCBANK.NS",   "HDFC LIFE":    "HDFCLIFE.NS",
    "HERO MOTO":    "HEROMOTOCO.NS", "HINDALCO":     "HINDALCO.NS",
    "HUL":          "HINDUNILVR.NS", "ICICI BANK":   "ICICIBANK.NS",
    "INDUSIND BK":  "INDUSINDBK.NS", "INFOSYS":      "INFY.NS",
    "ITC":          "ITC.NS",        "JSW STEEL":    "JSWSTEEL.NS",
    "KOTAK BANK":   "KOTAKBANK.NS",  "L&T":          "LT.NS",
    "M&M":          "M&M.NS",        "MARUTI":       "MARUTI.NS",
    "NESTLE":       "NESTLEIND.NS",  "NTPC":         "NTPC.NS",
    "ONGC":         "ONGC.NS",       "POWER GRID":   "POWERGRID.NS",
    "RELIANCE":     "RELIANCE.NS",   "SBI LIFE":     "SBILIFE.NS",
    "SBI":          "SBIN.NS",       "SHRIRAM FIN":  "SHRIRAMFIN.NS",
    "SUN PHARMA":   "SUNPHARMA.NS",  "TATA CONS":    "TATACONSUM.NS",
    "TATA MOTORS":  "TATAMOTORS.NS", "TATA STEEL":   "TATASTEEL.NS",
    "TCS":          "TCS.NS",        "TECH M":       "TECHM.NS",
    "TITAN":        "TITAN.NS",      "ULTRATECH":    "ULTRACEMCO.NS",
    "WIPRO":        "WIPRO.NS",      "ZOMATO":       "ZOMATO.NS",
}

_NSE_HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept":          "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer":         "https://www.nseindia.com/",
}


# ── Data layer ────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def fetch_gainers_losers() -> tuple[list[dict], list[dict], str]:
    """Try NSE India API; fall back to yfinance Nifty 50 batch."""
    # ── attempt 1: NSE India ──
    try:
        session = requests.Session()
        session.get("https://www.nseindia.com/", headers=_NSE_HEADERS, timeout=8)
        gr = session.get(
            "https://www.nseindia.com/api/live-analysis-gainers-loosers?index=gainers",
            headers=_NSE_HEADERS, timeout=8,
        )
        lr = session.get(
            "https://www.nseindia.com/api/live-analysis-gainers-loosers?index=loosers",
            headers=_NSE_HEADERS, timeout=8,
        )
        if gr.status_code == 200 and lr.status_code == 200:
            gainers = gr.json().get("data", [])[:10]
            losers  = lr.json().get("data", [])[:10]
            if gainers and losers:
                return gainers, losers, "NSE India (live)"
    except Exception:
        pass

    # ── attempt 2: yfinance Nifty 50 batch ──
    tickers = list(NIFTY50.values())
    name_map = {v: k for k, v in NIFTY50.items()}
    raw = yf.download(tickers, period="5d", interval="1d", progress=False, auto_adjust=True)

    rows = []
    for ticker in tickers:
        try:
            close = raw["Close"][ticker].dropna()
            vol   = raw["Volume"][ticker].dropna()
            if len(close) < 2:
                continue
            curr = float(close.iloc[-1])
            prev = float(close.iloc[-2])
            chg  = (curr - prev) / prev * 100
            rows.append({
                "symbol":        ticker.replace(".NS", ""),
                "displayName":   name_map.get(ticker, ticker),
                "ltp":           round(curr, 2),
                "previousPrice": round(prev, 2),
                "netPrice":      round(chg, 2),
                "tradedQuantity": float(vol.iloc[-1]) if not vol.empty else 0,
            })
        except Exception:
            continue

    df = pd.DataFrame(rows).sort_values("netPrice", ascending=False)
    gainers = df[df["netPrice"] > 0].head(10).to_dict("records")
    losers  = df[df["netPrice"] < 0].tail(10).iloc[::-1].to_dict("records")
    return gainers, losers, "NSE India via yfinance (Nifty 50)"


@st.cache_data(ttl=600, show_spinner=False)
def technical_score(ticker_ns: str) -> dict | None:
    """Download 3 months daily OHLCV and compute a 0–14 technical score."""
    try:
        df = yf.download(ticker_ns, period="3mo", interval="1d",
                         progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna()
        if len(df) < 30:
            return None

        close = df["Close"].squeeze()
        vol   = df["Volume"].squeeze()
        curr  = float(close.iloc[-1])

        rsi      = float(ta.momentum.rsi(close, window=14).iloc[-1])
        macd_obj = ta.trend.MACD(close)
        macd_v   = float(macd_obj.macd().iloc[-1])
        macd_s   = float(macd_obj.macd_signal().iloc[-1])
        macd_d   = float(macd_obj.macd_diff().iloc[-1])
        macd_dp  = float(macd_obj.macd_diff().iloc[-2])
        ema20    = float(ta.trend.ema_indicator(close, window=20).iloc[-1])
        ema50    = float(ta.trend.ema_indicator(close, window=50).iloc[-1]) if len(close) >= 50 else ema20
        avg_vol  = float(vol.tail(20).mean())
        curr_vol = float(vol.iloc[-1])
        vol_r    = curr_vol / avg_vol if avg_vol > 0 else 1.0

        # Score components (max 14)
        score = 0.0

        # RSI  (0–4): sweet spot 45–65
        if   45 <= rsi <= 65:  score += 4
        elif 35 <= rsi < 45 or 65 < rsi <= 75: score += 3
        elif 25 <= rsi < 35 or 75 < rsi <= 85: score += 1

        # MACD (0–3): bullish crossover with increasing diff
        if   macd_v > macd_s and macd_d > macd_dp: score += 3
        elif macd_v > macd_s:                       score += 2
        elif macd_d > 0:                             score += 1

        # Volume (0–2): above 20-day average
        if   vol_r >= 2.0:  score += 2
        elif vol_r >= 1.5:  score += 1.5
        elif vol_r >= 1.0:  score += 1

        # Trend (0–3): EMA stacking
        if   curr > ema20 and ema20 > ema50: score += 3
        elif curr > ema20:                   score += 2
        elif curr > ema50:                   score += 1

        bullish = macd_v > macd_s and curr > ema20
        tag = (
            "STRONG BUY"   if score >= 10 else
            "BUY"          if score >= 7  else
            "WATCH"        if score >= 5  else
            "REVERSAL"     if rsi < 35    else
            "AVOID"
        )

        return {
            "score":       round(score, 1),
            "rsi":         round(rsi, 1),
            "macd_bull":   bullish,
            "macd_diff":   round(macd_d, 3),
            "ema20":       round(ema20, 2),
            "ema50":       round(ema50, 2),
            "price":       round(curr, 2),
            "vol_ratio":   round(vol_r, 2),
            "tag":         tag,
        }
    except Exception:
        return None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _chg_color(v: float) -> str:
    return "#26a69a" if v >= 0 else "#ef5350"

def _tag_color(tag: str) -> str:
    return {
        "STRONG BUY": "#1b5e20", "BUY": "#2e7d32",
        "WATCH": "#e65100",      "REVERSAL": "#1565c0",
        "AVOID": "#b71c1c",
    }.get(tag, "#555")

def _mini_gauge(rsi: float) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=rsi,
        number={"suffix": "", "font": {"size": 16}},
        gauge={
            "axis": {"range": [0, 100], "tickvals": [30, 50, 70]},
            "bar":  {"color": "#2196F3", "thickness": 0.3},
            "steps": [
                {"range": [0, 30],   "color": "#ef9a9a"},
                {"range": [30, 70],  "color": "#e8f5e9"},
                {"range": [70, 100], "color": "#ffcdd2"},
            ],
            "threshold": {"line": {"color": "white", "width": 2}, "value": rsi},
        },
        title={"text": "RSI", "font": {"size": 12}},
    ))
    fig.update_layout(height=140, margin=dict(l=10, r=10, t=30, b=0),
                      paper_bgcolor="rgba(0,0,0,0)", font_color="white")
    return fig


# ── Page ──────────────────────────────────────────────────────────────────────

st.title("Top Gainers, Losers & Trade Picks")
st.caption("Data: NSE India (same feed used by MoneyControl, Zerodha, etc.). "
           "Technical scoring: RSI · MACD · Volume · EMA trend. "
           "Not financial advice.")

hcol1, hcol2, _ = st.columns([1, 2, 5])
if hcol1.button("Refresh Data", use_container_width=True):
    st.cache_data.clear()

with st.spinner("Fetching market data..."):
    gainers, losers, source = fetch_gainers_losers()

hcol2.caption(f"Source: **{source}**")

if not gainers:
    st.error("Could not load market data. Check internet connectivity.")
    st.stop()

# ── Gainers & Losers tables ───────────────────────────────────────────────────

st.divider()
gc, lc = st.columns(2, gap="large")

def _render_table(title: str, data: list[dict], is_gainer: bool):
    color = "#26a69a" if is_gainer else "#ef5350"
    st.markdown(f"### :{('green' if is_gainer else 'red')}[{'▲' if is_gainer else '▼'} {title}]")
    rows = []
    for d in data:
        sym  = d.get("symbol", d.get("displayName", ""))
        ltp  = float(d.get("ltp", 0))
        chg  = float(d.get("netPrice", d.get("perChange", 0)))
        prev = float(d.get("previousPrice", 0))
        qty  = float(d.get("tradedQuantity", 0))
        rows.append({
            "Symbol":   sym,
            "Price ₹":  ltp,
            "Chg %":    chg,
            "Prev ₹":   prev,
            "Volume":   qty,
        })
    df = pd.DataFrame(rows)
    st.dataframe(
        df.style
          .applymap(lambda v: f"color: {_chg_color(v)}; font-weight:bold", subset=["Chg %"])
          .format({"Price ₹": "₹{:,.2f}", "Chg %": "{:+.2f}%",
                   "Prev ₹": "₹{:,.2f}",  "Volume": "{:,.0f}"}),
        use_container_width=True,
        hide_index=True,
    )

with gc:
    _render_table("Top 10 Gainers — NSE", gainers, is_gainer=True)
with lc:
    _render_table("Top 10 Losers — NSE", losers, is_gainer=False)

# ── Top 5 Trade Picks ─────────────────────────────────────────────────────────

st.divider()
st.subheader("Tomorrow's Top 5 Trade Picks")
st.caption("Scored across gainers + oversold losers using RSI, MACD, Volume, and EMA trend (max 14 pts).")

# Collect candidate pool: all gainers + losers symbols
candidates: list[dict] = []
ticker_inv  = {v.replace(".NS", ""): (k, v) for k, v in NIFTY50.items()}

all_data = {d.get("symbol", ""): d for d in (gainers + losers)}

for sym, raw_d in all_data.items():
    name, ticker_ns = ticker_inv.get(sym, (sym, sym + ".NS"))
    chg = float(raw_d.get("netPrice", raw_d.get("perChange", 0)))
    candidates.append({"sym": sym, "name": name, "ticker_ns": ticker_ns,
                        "chg": chg, "ltp": float(raw_d.get("ltp", 0))})

# Score each candidate
with st.spinner("Running technical analysis on candidates..."):
    scored = []
    progress = st.progress(0)
    for i, c in enumerate(candidates):
        ts = technical_score(c["ticker_ns"])
        if ts:
            # Momentum rank bonus (0–2 pts)
            rank_bonus = 2.0 if i < 3 else (1.0 if i < 10 else 0.0)
            total = round(min(ts["score"] + rank_bonus, 14.0), 1)
            scored.append({**c, **ts, "total": total})
        progress.progress((i + 1) / len(candidates))
    progress.empty()

scored.sort(key=lambda x: x["total"], reverse=True)
top5 = scored[:5]

if not top5:
    st.warning("Could not compute scores. Check yfinance connectivity.")
    st.stop()

# ── Render pick cards ─────────────────────────────────────────────────────────

for i, p in enumerate(top5, 1):
    tag_color = _tag_color(p["tag"])
    chg_arrow = "▲" if p["chg"] >= 0 else "▼"
    chg_col   = "green" if p["chg"] >= 0 else "red"

    with st.container(border=True):
        h1, h2, h3, h4, h5 = st.columns([2, 2, 2, 2, 2])

        h1.markdown(
            f"**#{i} &nbsp; {p['name']}**  \n"
            f"<span style='color:#aaa;font-size:12px'>{p['sym']}</span>",
            unsafe_allow_html=True,
        )
        h2.metric("Price", f"₹{p['ltp']:,.2f}",
                  f"{chg_arrow} {abs(p['chg']):.2f}% today")
        h3.metric("Score", f"{p['total']} / 14",
                  f"Vol {p['vol_ratio']:.1f}x avg")
        h4.markdown(
            f"<div style='background:{tag_color};color:white;padding:6px 12px;"
            f"border-radius:8px;text-align:center;font-weight:bold;margin-top:18px'>"
            f"{p['tag']}</div>",
            unsafe_allow_html=True,
        )
        h5.markdown(
            f"MACD: {'📈 Bullish' if p['macd_bull'] else '📉 Bearish'}  \n"
            f"EMA20: ₹{p['ema20']:,.0f}  \n"
            f"EMA50: ₹{p['ema50']:,.0f}",
        )

        det1, det2, det3 = st.columns([1, 3, 3])
        det1.plotly_chart(_mini_gauge(p["rsi"]), use_container_width=True)

        # Why selected
        reasons = []
        if p["rsi"] < 35:
            reasons.append("Oversold (RSI < 35) — reversal candidate")
        elif p["rsi"] < 50:
            reasons.append("RSI recovering from low — early momentum")
        elif p["rsi"] <= 65:
            reasons.append("RSI in ideal momentum zone (45–65)")
        else:
            reasons.append("RSI elevated — watch for pullback")

        if p["macd_bull"]:
            reasons.append("MACD bullish crossover confirmed")
        if p["vol_ratio"] >= 1.5:
            reasons.append(f"Volume {p['vol_ratio']:.1f}x above average — strong conviction")
        if p["ltp"] > p["ema20"] and p["ema20"] > p["ema50"]:
            reasons.append("Price above EMA20 > EMA50 — uptrend intact")
        elif p["ltp"] > p["ema20"]:
            reasons.append("Price above EMA20 — short-term bullish")
        if p["chg"] > 2:
            reasons.append(f"Strong today (+{p['chg']:.1f}%) — momentum continuation likely")

        with det2:
            st.markdown("**Why selected:**")
            for r in reasons:
                st.markdown(f"- {r}")

        with det3:
            st.markdown("**Key levels:**")
            sl  = round(min(p["ema20"], p["ema50"]) * 0.985, 2)
            tgt = round(p["ltp"] * 1.025, 2)
            st.markdown(
                f"- Entry zone: ₹{p['ltp']:,.2f} (current)\n"
                f"- Stop loss: ₹{sl:,.2f} (below EMA support)\n"
                f"- Target: ₹{tgt:,.2f} (+2.5%)\n"
                f"- Risk:Reward ≈ 1 : {round((tgt - p['ltp']) / max(p['ltp'] - sl, 1), 1)}"
            )

    st.markdown("")

st.divider()
st.caption(
    "⚠️ Disclaimer: These picks are generated algorithmically using publicly available market data "
    "for educational purposes only. This is not SEBI-registered investment advice. "
    "Always do your own research before trading."
)
