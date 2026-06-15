# -*- coding: utf-8 -*-
"""每日主程式：抓資料 → 預測 → 新聞情緒 → 產出儀表板。

用法：
    python daily_run.py
輸出：
    docs/index.html          （GitHub Pages 首頁，最新一天）
    docs/assets/<ticker>.png （每檔走勢圖）
    reports/<日期>.json      （歷史紀錄）
"""
import os
import json
import datetime
import traceback

import config
import stock_model
import news_sentiment
import report

ROOT = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(ROOT, "docs")
ASSETS = os.path.join(DOCS, "assets")
REPORTS = os.path.join(ROOT, "reports")


def run():
    os.makedirs(ASSETS, exist_ok=True)
    os.makedirs(REPORTS, exist_ok=True)

    today = datetime.date.today().isoformat()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    rows = []

    for item in config.WATCHLIST:
        ticker, name = item["ticker"], item["name"]
        print(f"==> 處理 {name} ({ticker})")
        row = {"ticker": ticker, "name": name,
               "market": item.get("market", "tw"), "binance": item.get("binance", "")}
        try:
            close = stock_model.fetch_close(ticker, config.HISTORY_PERIOD)
            if close is None or len(close) == 0:
                raise RuntimeError("抓不到股價資料")

            result = stock_model.train_and_predict(
                close, lookback=config.LOOKBACK, epochs=config.EPOCHS)
            if result is None:
                raise RuntimeError("歷史資料不足，無法訓練")

            stock_model.save_chart(
                close, result, ticker, name,
                os.path.join(ASSETS, f"{ticker}.png"),
                chart_days=config.CHART_DAYS)

            news = news_sentiment.analyze(name, config.NEWS_LIMIT)

            row.update({
                "last_close": result["last_close"],
                "predicted": result["predicted"],
                "pct_change": result["pct_change"],
                "news": news,
            })
            print(f"    最新 {result['last_close']:.2f} → 預測 {result['predicted']:.2f} "
                  f"({result['pct_change']:+.2f}%)  新聞 {news['label']}")
        except Exception as e:
            row["error"] = str(e)
            print(f"    ⚠️ 失敗：{e}")
            traceback.print_exc()
        rows.append(row)

    # 產出 HTML
    html_str = report.build_html(today, rows, now)
    with open(os.path.join(DOCS, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_str)

    # 存歷史 JSON（圖表的 numpy/日期不存，留純數值）
    hist = [{k: v for k, v in r.items() if k != "news" or True} for r in rows]
    with open(os.path.join(REPORTS, f"{today}.json"), "w", encoding="utf-8") as f:
        json.dump(hist, f, ensure_ascii=False, indent=2, default=str)

    ok = sum(1 for r in rows if not r.get("error"))
    print(f"\n完成：{ok}/{len(rows)} 檔成功，儀表板已更新 → docs/index.html")


if __name__ == "__main__":
    run()
