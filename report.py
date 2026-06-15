# -*- coding: utf-8 -*-
"""把每日結果組成一個 HTML 儀表板（給 GitHub Pages 用）。"""
import html


def _signal(pct):
    if pct is None:
        return "—"
    if pct > 0.3:
        return "📈 偏多"
    if pct < -0.3:
        return "📉 偏空"
    return "➡️ 持平"


def build_html(date_str, rows, generated_at):
    """rows: list of dict（每檔股票一筆）。回傳完整 HTML 字串。"""
    cards = []
    for r in rows:
        if r.get("error"):
            cards.append(f"""
            <div class="card err">
              <h2>{html.escape(r['name'])} <span class="tk">{html.escape(r['ticker'])}</span></h2>
              <p class="warn">⚠️ {html.escape(r['error'])}</p>
            </div>""")
            continue

        pct = r["pct_change"]
        cls = "up" if pct > 0 else ("down" if pct < 0 else "flat")
        news = r["news"]
        samples = "".join(
            f'<li class="s{("p" if s["score"]>0 else ("n" if s["score"]<0 else "z"))}">'
            f'{html.escape(s["title"])}</li>'
            for s in news["samples"]
        )
        cards.append(f"""
        <div class="card">
          <h2>{html.escape(r['name'])} <span class="tk">{html.escape(r['ticker'])}</span></h2>
          <div class="nums">
            <div><span class="lab">最新收盤</span><b>{r['last_close']:.2f}</b></div>
            <div><span class="lab">明日預測</span><b class="{cls}">{r['predicted']:.2f}</b></div>
            <div><span class="lab">預測變動</span><b class="{cls}">{pct:+.2f}%</b></div>
            <div><span class="lab">訊號</span><b>{_signal(pct)}</b></div>
          </div>
          <img src="assets/{html.escape(r['ticker'])}.png" alt="chart" loading="lazy">
          <div class="news">
            <span class="lab">新聞情緒</span> <b>{news['label']}</b>
            <span class="muted">（{news['count']} 則，分數 {news['score']:+.2f}）</span>
            <ul>{samples}</ul>
          </div>
        </div>""")

    cards_html = "\n".join(cards)
    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>台股＋加密貨幣 每日 AI 儀表板 · {date_str}</title>
<style>
  :root {{ color-scheme: light dark; }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system, "PingFang TC", "Microsoft JhengHei", sans-serif;
         margin: 0; background:#0f1115; color:#e6e6e6; }}
  header {{ padding:24px 20px; background:#161922; border-bottom:1px solid #262b36; }}
  header h1 {{ margin:0; font-size:22px; }}
  header p {{ margin:6px 0 0; color:#9aa4b2; font-size:13px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(360px,1fr));
          gap:16px; padding:20px; max-width:1200px; margin:0 auto; }}
  .card {{ background:#161922; border:1px solid #262b36; border-radius:12px; padding:16px; }}
  .card h2 {{ margin:0 0 12px; font-size:17px; }}
  .tk {{ color:#7c8696; font-size:13px; font-weight:normal; }}
  .nums {{ display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin-bottom:12px; }}
  .nums .lab {{ display:block; color:#7c8696; font-size:11px; }}
  .nums b {{ font-size:16px; }}
  img {{ width:100%; border-radius:8px; background:#fff; }}
  .up {{ color:#ff5c5c; }}    /* 台股紅漲 */
  .down {{ color:#36d399; }}  /* 綠跌 */
  .flat {{ color:#e6e6e6; }}
  .news {{ margin-top:12px; font-size:13px; }}
  .news ul {{ margin:8px 0 0; padding-left:18px; color:#c3cad6; }}
  .news li {{ margin:3px 0; }}
  .news li.sp {{ color:#ff8a8a; }}
  .news li.sn {{ color:#5ee0aa; }}
  .muted {{ color:#7c8696; font-size:12px; }}
  .card.err {{ opacity:.7; }}
  .warn {{ color:#f0b429; }}
  footer {{ text-align:center; color:#6b7280; font-size:12px; padding:24px; }}
  .disc {{ max-width:1200px; margin:0 auto; padding:0 20px; color:#8a93a3; font-size:12px; }}
</style>
</head>
<body>
<header>
  <h1>📊 台股＋加密貨幣 每日 AI 儀表板</h1>
  <p>資料日期：{date_str}　·　產生時間：{generated_at}　·　每日自動更新</p>
</header>
<p class="disc">⚠️ 本頁為機器學習教學/實驗用途，預測僅供參考，<b>不構成任何投資建議</b>。</p>
<div class="grid">
{cards_html}
</div>
<footer>由 LSTM 股價模型 + jieba 新聞情緒分析自動產生 · Powered by TensorFlow & yfinance</footer>
</body>
</html>"""
