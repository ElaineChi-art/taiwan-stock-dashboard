# -*- coding: utf-8 -*-
"""抓股價 + 用 LSTM 預測隔天收盤價。"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # 無視窗環境（CI）也能畫圖
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler

# 安靜一點
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")


def fetch_close(ticker, period="2y"):
    """回傳一檔股票的每日收盤價 Series（index 為日期）。"""
    import yfinance as yf
    df = yf.download(ticker, period=period, auto_adjust=False, progress=False)
    if df is None or len(df) == 0:
        return None
    if getattr(df.columns, "nlevels", 1) > 1:
        df.columns = df.columns.get_level_values(0)
    df.columns = [str(c).lower() for c in df.columns]
    return df["close"].dropna()


def _make_windows(arr, lookback):
    X, y = [], []
    for i in range(len(arr) - lookback):
        X.append(arr[i:i + lookback, 0])
        y.append(arr[i + lookback, 0])
    return np.array(X), np.array(y)


def train_and_predict(close, lookback=20, epochs=40):
    """訓練 LSTM 並預測「下一個交易日」收盤價。

    回傳 dict：last_close, predicted, backtest（最近期的預測 vs 實際，用來畫圖）。
    """
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense

    prices = close.values.reshape(-1, 1).astype("float32")
    if len(prices) < lookback + 30:
        return None  # 資料太少，不預測

    scaler = MinMaxScaler((0, 1))
    scaled = scaler.fit_transform(prices)

    X, y = _make_windows(scaled, lookback)
    X = X.reshape(X.shape[0], X.shape[1], 1)

    # 留最後 30 天做回測（看模型在沒看過的近期準不準）
    split = max(1, len(X) - 30)
    X_tr, y_tr = X[:split], y[:split]

    model = Sequential([LSTM(32, input_shape=(lookback, 1)), Dense(1)])
    model.compile(optimizer="adam", loss="mean_squared_error")
    model.fit(X_tr, y_tr, epochs=epochs, batch_size=16, verbose=0)

    # 回測區間的預測
    bt_pred_scaled = model.predict(X[split:], verbose=0)
    bt_pred = scaler.inverse_transform(bt_pred_scaled).ravel()
    bt_actual = scaler.inverse_transform(y[split:].reshape(-1, 1)).ravel()
    bt_dates = close.index[lookback + split:]

    # 預測下一個交易日：用最後 lookback 天
    last_window = scaled[-lookback:].reshape(1, lookback, 1)
    next_scaled = model.predict(last_window, verbose=0)
    predicted = float(scaler.inverse_transform(next_scaled)[0, 0])

    last_close = float(prices[-1, 0])
    return {
        "last_close": last_close,
        "predicted": predicted,
        "pct_change": (predicted - last_close) / last_close * 100,
        "bt_dates": bt_dates,
        "bt_pred": bt_pred,
        "bt_actual": bt_actual,
    }


def save_chart(close, result, ticker, name, out_path, chart_days=60):
    """畫最近股價 + 回測預測線 + 下一日預測點，存成 PNG。"""
    # 圖內文字用英文，避免 matplotlib 缺中文字型顯示成方框（中文名稱在 HTML 顯示）
    plt.figure(figsize=(8, 4))
    recent = close.tail(chart_days)
    plt.plot(recent.index, recent.values, color="#1f77b4", label="Actual close")

    if result and len(result["bt_dates"]) > 0:
        plt.plot(result["bt_dates"], result["bt_pred"], color="#ff7f0e",
                 linestyle="--", label="Model backtest")

    if result:
        # 下一交易日預測點（畫在最後一天的後一格）
        next_x = recent.index[-1] + pd.Timedelta(days=1)
        plt.scatter([next_x], [result["predicted"]], color="red", zorder=5,
                    label="Next-day forecast")

    plt.title(f"{ticker}")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.legend(loc="best", fontsize=8)
    plt.xticks(rotation=30, fontsize=7)
    plt.tight_layout()
    plt.savefig(out_path, dpi=110)
    plt.close()
