# -*- coding: utf-8 -*-
"""把每日結果組成一個 HTML 儀表板（給 GitHub Pages 用）。"""
import html
import json


_LIVE_JS = r"""
const SYMBOLS = /*SYMBOLS*/;
const fmt = n => (Math.abs(n) >= 100 ? n.toLocaleString('en-US',{maximumFractionDigits:2})
                                     : n.toFixed(2));
const chartEl = document.getElementById('livechart');
const chart = LightweightCharts.createChart(chartEl, {
  autoSize: true,
  layout: { background:{ color:'#161922' }, textColor:'#c3cad6' },
  grid: { vertLines:{ color:'#222733' }, horzLines:{ color:'#222733' } },
  rightPriceScale: { borderColor:'#2a2f3a' },
  timeScale: { borderColor:'#2a2f3a', timeVisible:true, secondsVisible:false },
  crosshair: { mode: 0 }
});
let series = null, timer = null, current = null;

function clearSeries(){
  if (series){ chart.removeSeries(series); series = null; }
  if (timer){ clearInterval(timer); timer = null; }
}
async function fetchCrypto(b){
  const r = await fetch(`https://api.binance.com/api/v3/klines?symbol=${b}&interval=1m&limit=240`);
  const d = await r.json();
  return d.map(k => ({ time:k[0]/1000+28800, open:+k[1], high:+k[2], low:+k[3], close:+k[4] }));
}
async function fetchTW(url){
  const r = await fetch(url + `?t=${Date.now()}`);
  if (!r.ok) throw new Error('no-data');
  const j = await r.json();
  return { points:(j.points||[]).map(p => ({ time:p[0], value:p[1] })), updated:j.updated };
}
async function load(sym){
  clearSeries();
  current = sym;
  const meta = document.getElementById('livemeta');
  try {
    if (sym.type === 'crypto'){
      series = chart.addCandlestickSeries({ upColor:'#ff5c5c', downColor:'#36d399',
        borderVisible:false, wickUpColor:'#ff5c5c', wickDownColor:'#36d399' });
      series.setData(await fetchCrypto(sym.binance));
      meta.textContent = '來源：Binance · 真即時（每 15 秒更新）';
      timer = setInterval(async () => { if (current!==sym) return;
        try { series.setData(await fetchCrypto(sym.binance)); } catch(e){} }, 15000);
    } else {
      series = chart.addAreaSeries({ lineColor:'#4aa3ff',
        topColor:'rgba(74,163,255,.35)', bottomColor:'rgba(74,163,255,0)' });
      const { points, updated } = await fetchTW(sym.url);
      if (!points.length) throw new Error('empty');
      series.setData(points);
      meta.textContent = '來源：盤中 5 分 K · 約延遲 15 分（資料時間 ' + (updated||'') + '）';
      timer = setInterval(async () => { if (current!==sym) return;
        try { const t = await fetchTW(sym.url); if (t.points.length) series.setData(t.points); } catch(e){} }, 60000);
    }
    chart.timeScale().fitContent();
  } catch(e){
    meta.textContent = '⚠️ 此標的盤中資料準備中（僅在該市場交易時段更新）。';
  }
  document.querySelectorAll('.symbtn').forEach(b => b.classList.toggle('on', b.dataset.key === sym.key));
}
async function updateQuotes(){
  for (const s of SYMBOLS){
    try {
      let last, pct;
      if (s.type === 'crypto'){
        const j = await (await fetch(`https://api.binance.com/api/v3/ticker/24hr?symbol=${s.binance}`)).json();
        last = +j.lastPrice; pct = +j.priceChangePercent;
      } else {
        const r = await fetch(s.url + `?t=${Date.now()}`); if (!r.ok) continue;
        const j = await r.json(); const p = j.points||[]; if (!p.length) continue;
        last = p[p.length-1][1]; pct = (last - p[0][1]) / p[0][1] * 100;
      }
      const pe = document.getElementById('qp_'+s.key), ce = document.getElementById('qc_'+s.key);
      if (pe) pe.textContent = fmt(last);
      // 美股(inv) 綠漲紅跌；台股/加密貨幣 紅漲綠跌
      const isRed = s.inv ? (pct < 0) : (pct >= 0);
      if (ce){ ce.textContent = (pct>=0?'+':'') + pct.toFixed(2) + '%'; ce.className = 'qc ' + (isRed?'up':'down'); }
    } catch(e){}
  }
}
document.getElementById('symbtns').innerHTML = SYMBOLS.map(s =>
  `<button class="symbtn" data-key="${s.key}"><span class="qn">${s.name}</span>` +
  `<span class="qp" id="qp_${s.key}">—</span><span class="qc" id="qc_${s.key}"></span></button>`).join('');
document.querySelectorAll('.symbtn').forEach(b =>
  b.addEventListener('click', () => load(SYMBOLS.find(x => x.key === b.dataset.key))));
if (SYMBOLS.length){ load(SYMBOLS[0]); updateQuotes(); setInterval(updateQuotes, 15000); }
"""


def _live_charts(rows):
    """自建即時圖：加密貨幣抓 Binance（真即時）、台股讀自家 docs/data JSON（約延遲15分）。"""
    syms = []
    for r in rows:
        m = r.get("market", "tw")
        if m == "crypto":
            syms.append({"key": r["ticker"], "name": r["name"],
                         "type": "crypto", "binance": r.get("binance", "")})
        else:
            syms.append({"key": r["ticker"], "name": r["name"], "type": "stock",
                         "url": f"data/{r['ticker']}.json", "inv": m == "us"})
    if not syms:
        return ""
    js = _LIVE_JS.replace("/*SYMBOLS*/", json.dumps(syms, ensure_ascii=False))
    return f"""
    <section class="live" id="live">
      <h2 class="sec">🔴 即時行情（加密貨幣真即時 · 台股約延遲 15 分 · 自動更新）</h2>
      <div class="symbtns" id="symbtns"></div>
      <div id="livechart"></div>
      <p class="muted" id="livemeta" style="margin-top:8px">載入中…</p>
    </section>
    <script src="https://unpkg.com/lightweight-charts@4.2.0/dist/lightweight-charts.standalone.production.js"></script>
    <script>{js}</script>"""


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
        inv = r.get("market") == "us"  # 美股綠漲紅跌
        if pct > 0:
            cls = "down" if inv else "up"
        elif pct < 0:
            cls = "up" if inv else "down"
        else:
            cls = "flat"
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
    live_html = _live_charts(rows)
    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>台股＋加密貨幣 每日 AI 儀表板 · {date_str}</title>
<style>
  :root {{ color-scheme: light dark; }}
  * {{ box-sizing: border-box; }}
  .topnav {{ display:flex; gap:6px; background:#0b0d12; padding:8px 16px;
            border-bottom:1px solid #262b36; position:sticky; top:0; z-index:10; }}
  .topnav a {{ color:#9aa4b2; text-decoration:none; font-size:14px; font-weight:600;
              padding:7px 16px; border-radius:8px; }}
  .topnav a:hover {{ background:#161922; color:#e6e6e6; }}
  .topnav a.active {{ background:#1f2e3a; color:#7fb5ff; }}
  html {{ scroll-behavior:smooth; }}
  #live, #ai {{ scroll-margin-top:60px; }}
  .toc-trigger {{ position:fixed; left:0; top:50%; transform:translateY(-50%); z-index:40;
                 background:#161922; border:1px solid #2a3140; border-left:none;
                 border-radius:0 12px 12px 0; padding:16px 7px; cursor:pointer; color:#9aa4b2;
                 writing-mode:vertical-rl; letter-spacing:3px; font-size:12px; font-weight:600;
                 transition:.25s; box-shadow:4px 0 16px rgba(0,0,0,.3); }}
  .toc-trigger:hover {{ color:#fff; background:#1f2937; }}
  .toc-trigger .th {{ writing-mode:horizontal-tb; font-size:14px; }}
  .toc {{ position:fixed; left:0; top:48px; height:calc(100vh - 48px); width:240px; z-index:41;
         background:rgba(17,20,27,.96); backdrop-filter:blur(12px); border-right:1px solid #2a3140;
         padding:16px 14px; overflow:auto; transform:translateX(-100%);
         transition:transform .32s cubic-bezier(.4,0,.2,1); box-shadow:10px 0 40px rgba(0,0,0,.5); }}
  .toc-trigger:hover + .toc, .toc:hover {{ transform:translateX(0); }}
  .toctitle {{ font-size:12px; color:#7c8696; margin-bottom:10px; font-weight:600; letter-spacing:1px; }}
  .toc a {{ display:flex; align-items:center; gap:9px; color:#c3cad6; text-decoration:none;
           font-size:13.5px; padding:9px 10px; border-radius:9px; transition:.16s; }}
  .toc a:hover {{ background:#1f2937; color:#fff; transform:translateX(3px); }}
  .toc .d {{ width:8px; height:8px; border-radius:50%; flex:none; }}
  .toc .d.crypto {{ background:#ff9ecb; }}
  .toc .d.ai {{ background:#7fb5ff; }}
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
  .live {{ max-width:1200px; margin:8px auto 0; padding:0 20px; }}
  .sec {{ font-size:16px; margin:18px 0 10px; }}
  .symbtns {{ display:flex; flex-wrap:wrap; gap:8px; margin-bottom:10px; }}
  .symbtn {{ background:#161922; border:1px solid #262b36; border-radius:10px;
            padding:8px 12px; color:#e6e6e6; cursor:pointer; display:flex;
            flex-direction:column; align-items:flex-start; min-width:96px; }}
  .symbtn.on {{ border-color:#4aa3ff; box-shadow:inset 0 0 0 1px #4aa3ff; }}
  .symbtn .qn {{ font-size:12px; color:#9aa4b2; }}
  .symbtn .qp {{ font-size:15px; font-weight:600; }}
  .symbtn .qc {{ font-size:12px; }}
  #livechart {{ height:480px; width:100%; border:1px solid #262b36;
               border-radius:12px; overflow:hidden; background:#161922; }}
</style>
</head>
<body>
<nav class="topnav">
  <a class="active" href="https://elainechi-art.github.io/taiwan-stock-dashboard/">📈 股市儀表板</a>
  <a href="https://elainechi-art.github.io/research-radar/">📡 研究雷達</a>
</nav>
<div class="toc-trigger" aria-hidden="true"><span class="th">☰</span><span class="tl">目錄</span></div>
<aside class="toc"><div class="toctitle">目錄</div>
  <a href="#live"><span class="d crypto"></span>🔴 即時行情</a>
  <a href="#ai"><span class="d ai"></span>🤖 AI 每日預測 + 新聞情緒</a>
</aside>
<header>
  <h1>📊 台股＋加密貨幣 每日 AI 儀表板</h1>
  <p>資料日期：{date_str}　·　產生時間：{generated_at}　·　每日自動更新</p>
</header>
<p class="disc">⚠️ 本頁為機器學習教學/實驗用途，預測僅供參考，<b>不構成任何投資建議</b>。即時圖：加密貨幣為 Binance 即時資料；台股為盤中 5 分 K、約延遲 15 分鐘（免費資料上限）。</p>
{live_html}
<div class="live" id="ai"><h2 class="sec">🤖 AI 每日預測 + 新聞情緒</h2></div>
<div class="grid">
{cards_html}
</div>
<footer>由 LSTM 股價模型 + jieba 新聞情緒分析自動產生 · Powered by TensorFlow & yfinance</footer>
</body>
</html>"""
