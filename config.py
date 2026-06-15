# -*- coding: utf-8 -*-
"""台股每日 AI 儀表板 —— 設定檔。改這裡就能調整關注清單與參數。"""

# 你要追蹤的標的：
#   ticker = Yahoo 代碼（抓歷史資料/做 AI 預測用；台股上市加 .TW、上櫃 .TWO）
#   name   = 顯示與抓新聞用，可自由命名
#   tv     = TradingView 即時圖代碼（台股用 TWSE:，加密貨幣用 BINANCE: 即時來源）
WATCHLIST = [
    {"ticker": "0050.TW", "name": "元大台灣50", "tv": "TWSE:0050"},
    {"ticker": "2330.TW", "name": "台積電",     "tv": "TWSE:2330"},
    {"ticker": "2317.TW", "name": "鴻海",       "tv": "TWSE:2317"},
    {"ticker": "2454.TW", "name": "聯發科",     "tv": "TWSE:2454"},
    {"ticker": "BTC-USD", "name": "比特幣",     "tv": "BINANCE:BTCUSDT"},
    {"ticker": "ETH-USD", "name": "以太幣",     "tv": "BINANCE:ETHUSDT"},
]

# 模型參數
LOOKBACK = 20        # 用過去幾天預測下一天
HISTORY_PERIOD = "2y"  # 抓多久的歷史資料來訓練
EPOCHS = 40          # 訓練回合數（CI 上想更快可調小）
CHART_DAYS = 60      # 圖表顯示最近幾天

# 新聞情緒：每檔抓幾則最新標題來分析
NEWS_LIMIT = 12
