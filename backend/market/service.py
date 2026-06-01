import pandas as pd
import yfinance as yf

from backend.market.indicators import add_indicators

# NSE symbol map → Yahoo Finance tickers
_SYMBOL_MAP = {
    "NIFTY": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
}

_TF_MAP = {
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "4h": "4h",
    "1D": "1d",
    "1W": "1wk",
    "1M": "1mo",
}


class MarketDataService:
    async def get_ohlc(self, symbol: str, timeframe: str, bars: int = 200) -> pd.DataFrame:
        ticker = _SYMBOL_MAP.get(symbol, symbol)
        tf = _TF_MAP.get(timeframe, timeframe)
        period = "60d" if timeframe in ("15m", "30m", "1h") else "2y"
        df = yf.download(ticker, period=period, interval=tf, progress=False, auto_adjust=True)
        df = df.tail(bars)
        df = add_indicators(df)
        return df

    async def get_latest_price(self, symbol: str) -> float:
        ticker = _SYMBOL_MAP.get(symbol, symbol)
        info = yf.Ticker(ticker).fast_info
        return float(info.last_price)
