# -*- coding: utf-8 -*-
"""中文財經新聞情緒分析：抓 Google News 標題 + jieba 斷詞 + 規則式情緒分數。

這是輕量、可持續、不需外部模型的 v1 版本；之後可換成你 notebook 裡訓練的
LSTM/Embedding 情感模型，把 score_headline() 換掉即可。
"""
import urllib.parse
import jieba

# 財經情緒詞典（可自由增補）
POSITIVE = {
    "漲", "大漲", "上漲", "飆漲", "創新高", "新高", "利多", "獲利", "成長",
    "看好", "樂觀", "強勁", "回升", "突破", "買超", "受惠", "暢旺", "賺",
}
NEGATIVE = {
    "跌", "大跌", "下跌", "重挫", "崩跌", "創新低", "新低", "利空", "虧損",
    "衰退", "看壞", "悲觀", "疲弱", "下滑", "賣超", "衝擊", "下修", "賠",
}


def fetch_headlines(query, limit=12):
    """用 Google News RSS 抓中文標題（穩定、免金鑰）。"""
    import feedparser
    q = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    feed = feedparser.parse(url)
    return [e.title for e in feed.entries[:limit]]


def score_headline(title):
    """回傳 +1 / 0 / -1：依正負詞淨值判斷單則標題情緒。"""
    words = set(jieba.cut(title))
    pos = len(words & POSITIVE)
    neg = len(words & NEGATIVE)
    if pos > neg:
        return 1
    if neg > pos:
        return -1
    return 0


def analyze(query, limit=12):
    """回傳該標的的新聞情緒摘要。"""
    titles = fetch_headlines(query, limit)
    if not titles:
        return {"count": 0, "score": 0.0, "label": "無資料", "samples": []}
    scores = [score_headline(t) for t in titles]
    avg = sum(scores) / len(scores)
    if avg > 0.15:
        label = "偏多 🟢"
    elif avg < -0.15:
        label = "偏空 🔴"
    else:
        label = "中性 ⚪"
    # 取幾則代表性標題（有情緒的優先）
    samples = sorted(zip(titles, scores), key=lambda x: -abs(x[1]))[:4]
    return {
        "count": len(titles),
        "score": round(avg, 3),
        "label": label,
        "samples": [{"title": t, "score": s} for t, s in samples],
    }
