import pandas as pd
import ta


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    close = df["Close"].squeeze()
    high = df["High"].squeeze()
    low = df["Low"].squeeze()
    volume = df["Volume"].squeeze()

    # Trend
    df["ema_20"] = ta.trend.ema_indicator(close, window=20)
    df["ema_50"] = ta.trend.ema_indicator(close, window=50)
    df["ema_200"] = ta.trend.ema_indicator(close, window=200)
    df["adx"] = ta.trend.adx(high, low, close, window=14)

    # Momentum
    df["rsi"] = ta.momentum.rsi(close, window=14)
    macd = ta.trend.MACD(close)
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["macd_diff"] = macd.macd_diff()

    # Volatility
    bb = ta.volatility.BollingerBands(close)
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_lower"] = bb.bollinger_lband()
    df["bb_width"] = bb.bollinger_wband()
    df["atr"] = ta.volatility.average_true_range(high, low, close, window=14)

    # Volume
    df["obv"] = ta.volume.on_balance_volume(close, volume)

    df.dropna(inplace=True)
    return df
