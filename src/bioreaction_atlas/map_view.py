"""Offline reaction-structure interaction for the standalone scientific figure."""
import json
from pathlib import Path
from .cards import draw_reaction
from .corpus import sha


def attach_diagrams(records, folder):
    """Cache local SVGs by structure, preserving a visible error for failed drawings."""
    folder = Path(folder)
    (folder / 'reaction_structures').mkdir(parents=True, exist_ok=True)
    for record in records:
        relative = f"reaction_structures/{sha(record['reaction_smiles'].encode())[:24]}.svg"
        target = folder / relative
        try:
            if not target.exists():
                draw_reaction(record['reaction_smiles'], target)
            record['diagram_path'] = relative
        except (ValueError, RuntimeError) as error:
            record['diagram_path'] = None
            record['diagram_error'] = str(error)


def write_interactive_map(figure, records, path):
    # JSON is data, never interpolated into executable JS or unescaped HTML.
    payload = json.dumps(records, ensure_ascii=False).replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
    plot = figure.to_html(full_html=False, include_plotlyjs=True, div_id='reaction-map',
                          config={'responsive': True, 'displaylogo': False})
    document = '''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BioReaction Atlas — reaction map</title><style>
*{box-sizing:border-box}body{margin:0;background:#f3f6f8;color:#20384a;font:15px/1.5 system-ui,sans-serif}
main{max-width:1440px;margin:20px auto;padding:0 20px}header{display:flex;gap:18px;align-items:center;flex-wrap:wrap}
header strong{font-size:20px}header p{margin:0;color:#536779}a{color:#087386}
.notice{font-size:13px;color:#536779;margin:8px 0 14px}.plot-shell,#details{background:white;border:1px solid #dce4ea;border-radius:12px;overflow:hidden}
#reaction-map{width:100%}#details{margin:16px 0;padding:22px}h2{font-size:18px;margin:0 0 6px}h3{font-size:15px;margin:16px 0 6px}
#detail-image{display:block;width:100%;max-height:300px;object-fit:contain;background:white}
.metadata{display:grid;grid-template-columns:1fr 1fr;gap:12px 24px;margin-top:12px}.field{min-width:0;overflow-wrap:anywhere}.field b{display:block;font-size:12px;color:#65798b}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f6f8fa;padding:12px;border-radius:6px;font:12px/1.5 ui-monospace,monospace}
select{font:inherit;max-width:100%;padding:6px;border:1px solid #b6c7d2;border-radius:4px}#detail-id{overflow-wrap:anywhere}
#hover-card{position:fixed;z-index:100;pointer-events:none;width:min(690px,calc(100vw - 24px));padding:12px 16px;background:white;border:1px solid #9fb9c6;border-radius:10px;box-shadow:0 8px 32px #17354933}
#hover-card img{display:block;width:100%;height:160px;object-fit:contain;background:white}#hover-source{font-size:12px;overflow-wrap:anywhere;color:#536779}#hover-card p{margin:4px 0;font-size:12px;color:#536779}
.error{color:#a33827}button{cursor:pointer;font:inherit;background:white;border:1px solid #b6c7d2;border-radius:5px;padding:4px 12px;float:right}
[hidden]{display:none!important}@media(max-width:700px){main{padding:0 8px;margin:10px auto}.metadata{grid-template-columns:1fr}#details{padding:14px}#hover-card img{height:130px}}
</style></head><body><main>
<header><strong>BioReaction Atlas</strong><p>悬停看反应结构 · 点击固定下方详情 · 点击图例筛选来源</p></header>
<p class="notice">这是所选参考数据的结构分布；二维距离不代表酶催化可行性。图中结构保留原始 reactants / products 中的组分，中间 agents 段不绘制，不能据此认定完整反应条件。</p>
<div class="plot-shell">''' + plot + '''</div>
<section id="details" aria-label="Selected reaction details">
<h2>反应详情 / Reaction details</h2><p id="detail-empty">点击任意点，在这里固定反应结构并查看来源记录。悬停可快速比较其他点。</p>
<div id="detail-content" hidden><button id="clear-selection" type="button">清除选择</button>
<p id="detail-id"></p><img id="detail-image" alt="所选反应结构"><p id="detail-error" class="error" hidden></p>
<a id="detail-open" target="_blank" rel="noopener">在新标签页查看完整反应图 SVG</a>
<p id="detail-summary"></p><label for="evidence-select">来源记录（每条条件分别显示）：</label> <select id="evidence-select"></select>
<div class="metadata">
<div class="field"><b>来源 / Source</b><span id="detail-source"></span></div>
<div class="field"><b>定位 / Source location</b><span id="detail-locator"></span></div>
<div class="field"><b>核查状态 / Review status</b><span id="detail-review"></span></div>
<div class="field"><b>原始标签（不保证是反应名称）/ Raw label</b><span id="detail-label"></span></div>
</div><h3>该来源记录的体系与条件 / Recorded context</h3><pre id="detail-context"></pre>
<p class="notice">缺少的条件表示当前记录未提供，不表示实验中未使用。imported 记录尚未核查原文 / SI。</p>
<details><summary>结构 SMILES / Structure used for the map</summary><pre id="detail-smiles"></pre></details>
</div></section></main>
<div id="hover-card" hidden role="tooltip"><strong id="hover-domain"></strong><img id="hover-image" alt="悬停反应结构"><p id="hover-error" class="error" hidden></p><div id="hover-source"></div><p>点击点固定下方详情；同一结构可能对应多个实验条件。</p></div>
<script id="reaction-records" type="application/json">''' + payload + '''</script><script>''' + INTERACTIONS + '''</script></body></html>'''
    Path(path).write_text(document, encoding='utf-8')


INTERACTIONS = r'''
(() => {
  const records = new Map(JSON.parse(document.getElementById('reaction-records').textContent).map(r => [r.record_id, r]));
  const el = id => document.getElementById(id);
  const plot = el('reaction-map'), hover = el('hover-card');
  const labels = {enzyme_reference:'酶反应参考 / Enzyme reference',patent_reference:'专利反应参考 / Patent reference',enzymatic:'酶反应 / Enzymatic',nonenzymatic:'非酶反应 / Nonenzymatic',control:'对照 / Control'};
  let selected = null, pointer = {x:0,y:0};
  function placeHover() {
    const width=hover.offsetWidth, height=hover.offsetHeight;
    let left=pointer.x+18, top=pointer.y-height-18;
    if (left+width>window.innerWidth-12) left=pointer.x-width-18;
    if (top<12) top=pointer.y+18;
    hover.style.left=Math.max(12,Math.min(left,window.innerWidth-width-12))+'px';
    hover.style.top=Math.max(12,Math.min(top,window.innerHeight-height-12))+'px';
  }
  plot.addEventListener('mousemove', event => {
    pointer={x:event.clientX,y:event.clientY};
    if (!hover.hidden) placeHover();
  });
  function diagram(record, prefix) {
    const img=el(prefix+'-image'), error=el(prefix+'-error');
    error.hidden=true; img.hidden=!record.diagram_path;
    if (record.diagram_path) {
      img.onerror=()=>{img.hidden=true;error.hidden=false;error.textContent='结构图未能加载；请保留 HTML 旁的 reaction_structures 文件夹。';};
      img.src=record.diagram_path;
    } else {
      img.removeAttribute('src');error.hidden=false;error.textContent='该反应结构绘制失败，请查看 SMILES。';
    }
  }
  function sourceText(container, source) {
    container.replaceChildren();
    const text=String(source || 'Not reported');
    const candidate=/^(?:dx\.)?doi\.org\//i.test(text) ? 'https://'+text : text;
    try {
      const url=new URL(candidate);
      if (['http:','https:'].includes(url.protocol)) {
        const link=document.createElement('a');link.href=url.href;link.textContent=text;link.target='_blank';link.rel='noopener noreferrer';container.append(link);return;
      }
    } catch (_) {}
    container.textContent=text;
  }
  function showEvidence() {
    if (!selected) return;
    const evidence=selected.evidence[Number(el('evidence-select').value)];
    sourceText(el('detail-source'),evidence.source);
    el('detail-locator').textContent=evidence.source_locator || 'Not reported';
    el('detail-review').textContent=evidence.review_status || 'Not reported';
    el('detail-label').textContent=evidence.label || 'Not reported';
    const context=evidence.context || {};
    el('detail-context').textContent=Object.keys(context).length ? JSON.stringify(context,null,2) : '当前来源记录未提供体系与条件 / Context and conditions not provided in this record.';
  }
  plot.on('plotly_hover', event => {
    const record=records.get(event.points[0].customdata);if (!record) return;
    hover.dataset.recordId=record.record_id;
    el('hover-domain').textContent=labels[record.domain] || record.domain;
    el('hover-source').textContent=(record.source || 'Source not reported')+' · '+record.evidence_rows+' 条来源记录';
    diagram(record,'hover');hover.hidden=false;placeHover();
  });
  plot.on('plotly_unhover',()=>{hover.hidden=true;});
  plot.on('plotly_relayout',()=>{hover.hidden=true;});
  window.addEventListener('scroll',()=>{hover.hidden=true;},true);
  plot.on('plotly_click', event => {
    const record=records.get(event.points[0].customdata);if (!record) return;
    selected=record;el('details').dataset.recordId=record.record_id;
    el('detail-empty').hidden=true;el('detail-content').hidden=false;
    el('detail-id').textContent=(labels[record.domain] || record.domain)+' · '+record.record_id;
    diagram(record,'detail');
    el('detail-open').hidden=!record.diagram_path;
    if (record.diagram_path) el('detail-open').href=record.diagram_path;
    else el('detail-open').removeAttribute('href');
    el('detail-summary').textContent=record.evidence_rows+' 条来源记录归并为此结构点；以下显示所选来源的条件，未将多条条件混合。';
    el('detail-smiles').textContent=record.reaction_smiles;
    const select=el('evidence-select');select.replaceChildren();
    record.evidence.forEach((e,i)=>{const option=document.createElement('option');option.value=i;option.textContent=(i+1)+'. '+e.record_id+(e.context?.scaffold ? ' · '+e.context.scaffold : '');select.append(option);});
    showEvidence();
  });
  el('evidence-select').addEventListener('change',showEvidence);
  el('clear-selection').addEventListener('click',()=>{selected=null;delete el('details').dataset.recordId;el('detail-content').hidden=true;el('detail-empty').hidden=false;});
})();
'''
