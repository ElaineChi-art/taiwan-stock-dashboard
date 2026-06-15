# -*- coding: utf-8 -*-
"""台股每日 AI 儀表板 —— 設定檔。改這裡就能調整關注清單與參數。"""

# 你要追蹤的標的：
#   ticker = Yahoo 代碼（抓歷史資料/做 AI 預測用；台股上市加 .TW、上櫃 .TWO、美股直接代碼）
#   name   = 顯示與抓新聞用，可自由命名
#   market = "tw" 台股 / "us" 美股 / "crypto" 加密貨幣（決定時區、漲跌顏色、即時來源）
#   binance= 只有 crypto 需要，前端即時圖直連 Binance 用的交易對
WATCHLIST = [
    {"ticker": "0050.TW", "name": "元大台灣50", "market": "tw"},
    {"ticker": "2330.TW", "name": "台積電",     "market": "tw"},
    {"ticker": "2317.TW", "name": "鴻海",       "market": "tw"},
    {"ticker": "2454.TW", "name": "聯發科",     "market": "tw"},
    {"ticker": "NVDA",    "name": "輝達",       "market": "us"},
    {"ticker": "TSLA",    "name": "特斯拉",     "market": "us"},
    {"ticker": "AMD",     "name": "超微",       "market": "us"},
    {"ticker": "BTC-USD", "name": "比特幣",     "market": "crypto", "binance": "BTCUSDT"},
    {"ticker": "ETH-USD", "name": "以太幣",     "market": "crypto", "binance": "ETHUSDT"},
]

# 模型參數
LOOKBACK = 20        # 用過去幾天預測下一天
HISTORY_PERIOD = "2y"  # 抓多久的歷史資料來訓練
EPOCHS = 40          # 訓練回合數（CI 上想更快可調小）
CHART_DAYS = 60      # 圖表顯示最近幾天

# 新聞情緒：每檔抓幾則最新標題來分析
NEWS_LIMIT = 12
