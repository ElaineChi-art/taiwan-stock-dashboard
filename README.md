# 📊 台股每日 AI 儀表板

每天自動：抓台股股價 → 用 **LSTM** 預測隔天收盤 → 用 **jieba** 分析財經新聞情緒 → 產出一個網頁儀表板。
由 GitHub Actions 每天定時執行，成果發佈到 GitHub Pages，**不必開電腦**。

> ⚠️ 教學/實驗用途，預測僅供參考，**不構成投資建議**。

## 功能
- **股價預測**：對 `config.py` 裡的每檔股票訓練 LSTM，預測下一個交易日收盤價與漲跌訊號。
- **回測圖**：畫出最近 60 天實際價、模型回測預測、以及明日預測點。
- **新聞情緒**：抓 Google News 中文標題，用 jieba 斷詞 + 財經情緒詞典算偏多/偏空。
- **每日自動更新**：GitHub Actions 排程，產出 `docs/index.html` 並推回 repo。

## 專案結構
```
config.py            # 關注清單與參數（改這裡就好）
stock_model.py       # 抓股價 + LSTM 預測 + 畫圖
news_sentiment.py    # 中文新聞情緒分析
report.py            # 產生 HTML 儀表板
daily_run.py         # 主程式（串起全部）
docs/index.html      # 儀表板網頁（GitHub Pages 首頁）
reports/<日期>.json  # 每日歷史紀錄
.github/workflows/daily.yml  # 每日自動執行
```

## 本機執行
```bash
pip install -r requirements.txt
python daily_run.py
# 開 docs/index.html 看結果
```

## 上雲（每天自動跑）
1. 把這個資料夾推到一個 GitHub repo。
2. repo → **Settings → Pages** → Source 選 **Deploy from a branch**，分支 `main`、資料夾 `/docs`。
3. repo → **Settings → Actions → General** → Workflow permissions 選 **Read and write**。
4. 完成。之後每個工作日 17:00（台灣時間）會自動更新，也可在 **Actions** 分頁手動按 **Run workflow**。

網址會是：`https://<你的帳號>.github.io/<repo 名稱>/`

## 想調整
- 換股票 / 加股票：改 `config.py` 的 `WATCHLIST`。
- 預測更準：調 `LOOKBACK`、`EPOCHS`，或在 `stock_model.py` 換成 GRU、加更多特徵。
- 情緒更準：把 `news_sentiment.score_headline()` 換成你訓練好的中文情感模型。
