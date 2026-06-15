# -*- coding: utf-8 -*-
"""抓台股『盤中』5 分 K 收盤價，存成網站可讀的 JSON（給前端即時圖用）。

加密貨幣不在這裡處理——前端直接打 Binance 公開 API 拿真即時資料。
台股免費資料約延遲 15~20 分鐘，這已是免費上限。
由 .github/workflows/intraday.yml 在台股盤中每 15 分鐘執行一次。
"""
import os
import json
import datetime

import config

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "docs", "data")


def fetch_intraday(ticker):
    """回傳最後一個交易日的 [[顯示用epoch秒, 收盤價], ...]。

    顯示用 epoch = 真實UTC + 該市場當地時區偏移，讓時間軸呈現當地盤中時間
    （台股 09:00–13:30、美股 09:30–16:00）。
    """
    import yfinance as yf
    df = yf.download(ticker, period="5d", interval="5m",
                     progress=False, auto_adjust=False)
    if df is None or len(df) == 0:
        return []
    if getattr(df.columns, "nlevels", 1) > 1:
        df.columns = df.columns.get_level_values(0)
    df.columns = [str(c).lower() for c in df.columns]
    s = df["close"].dropna()
    if len(s) == 0:
        return []
    # 只保留「最後一個交易日」的盤中資料
    last_day = s.index[-1].date()
    s = s[[ts.date() == last_day for ts in s.index]]
    pts = []
    for ts, val in s.items():
        off = ts.utcoffset().total_seconds() if ts.utcoffset() else 0
        epoch = int(ts.timestamp()) + int(off)
        pts.append([epoch, round(float(val), 2)])
    return pts


def run():
    os.makedirs(DATA, exist_ok=True)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    for item in config.WATCHLIST:
        if item.get("market") == "crypto":
            continue  # 加密貨幣由前端直連 Binance，不需後端資料
        ticker, name = item["ticker"], item["name"]
        try:
            pts = fetch_intraday(ticker)
            out = {"name": name, "ticker": ticker, "updated": now, "points": pts}
            with open(os.path.join(DATA, f"{ticker}.json"), "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False)
            print(f"  {name} ({ticker}): {len(pts)} 點，最後 {pts[-1][1] if pts else '—'}")
        except Exception as e:
            print(f"  ⚠️ {ticker} 失敗：{e}")
    print(f"盤中資料已更新 → docs/data/  ({now})")


if __name__ == "__main__":
    run()
