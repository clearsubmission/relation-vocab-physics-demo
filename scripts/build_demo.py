#!/usr/bin/env python3
"""Build esr_demo.html: a single self-contained page with all demo_data/*.json inlined.
Run from physt_kg/:  python build_demo.py  [--data demo_data] [--out esr_demo.html]"""
import argparse, json, os

TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Relational Physics Probe</title>
<style>
:root{
  --bg:#f6f5f1; --panel:#ffffff; --ink:#1d1d1b; --muted:#6b6a65; --line:#e3e1da;
  --accent:#2f5d8a; --good:#2e7d4f; --bad:#b4442f; --warn:#b07a1a; --chip:#efede6;
  --r-events:#7a7a72; --r-kin:#2f7d8a; --r-rel:#6a4fa3; --r-rel128:#b5562e;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#141413; --panel:#1e1e1c; --ink:#ecebe6; --muted:#9b9a93; --line:#33322e;
    --accent:#7fb0de; --good:#6cc28f; --bad:#e3826c; --warn:#e0b25a; --chip:#2a2926;
    --r-events:#a8a79f; --r-kin:#6cc0cc; --r-rel:#a993dd; --r-rel128:#e69a6c;
  }
}
:root[data-theme="dark"]{
  --bg:#141413; --panel:#1e1e1c; --ink:#ecebe6; --muted:#9b9a93; --line:#33322e;
  --accent:#7fb0de; --good:#6cc28f; --bad:#e3826c; --warn:#e0b25a; --chip:#2a2926;
  --r-events:#a8a79f; --r-kin:#6cc0cc; --r-rel:#a993dd; --r-rel128:#e69a6c;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
header{padding:18px 20px 10px;max-width:1280px;margin:0 auto}
h1{font-size:20px;margin:0 0 4px;letter-spacing:-.01em}
.sub{color:var(--muted);max-width:820px}
main{max-width:1280px;margin:0 auto;padding:6px 16px 28px;display:grid;gap:14px;
  grid-template-columns:minmax(0,1.15fr) minmax(0,1fr)}
@media (max-width:900px){main{grid-template-columns:1fr}}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px}
.panel h2{font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:0 0 10px;font-weight:600}
.row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
select,button{font:inherit;color:var(--ink);background:var(--chip);border:1px solid var(--line);border-radius:7px;padding:6px 10px}
button{cursor:pointer}
button.on{background:var(--ink);color:var(--panel);border-color:var(--ink)}
.tagnote{color:var(--muted);font-size:13px;margin-top:6px;min-height:20px}
canvas{width:100%;height:auto;display:block;border-radius:8px;background:var(--bg);border:1px solid var(--line)}
input[type=range]{width:100%;accent-color:var(--accent)}
.scrub{position:relative;margin-top:10px}
.cutmark{position:absolute;top:-4px;width:2px;height:26px;background:var(--bad);pointer-events:none}
.legend{display:flex;gap:14px;flex-wrap:wrap;color:var(--muted);font-size:12px;margin-top:8px}
.qlist{display:flex;flex-direction:column;gap:6px;max-height:190px;overflow:auto}
.q{display:flex;justify-content:space-between;gap:8px;text-align:left;width:100%}
.q.sel{outline:2px solid var(--accent);background:color-mix(in srgb,var(--accent) 12%,var(--chip))}
.ranks{display:flex;gap:3px}
.rk{width:22px;text-align:center;border-radius:4px;font-size:12px;font-variant-numeric:tabular-nums;padding:1px 0}
.rungs{display:grid;grid-template-columns:repeat(4,1fr);gap:6px}
.rungs button{font-size:13px;padding:7px 6px;border-left:4px solid var(--c)}
.bars{display:flex;flex-direction:column;gap:7px;margin-top:10px}
.bar{display:grid;grid-template-columns:110px 1fr 56px;gap:8px;align-items:center}
.track{height:14px;background:var(--chip);border-radius:4px;overflow:hidden}
.fill{height:100%;background:var(--accent);transition:width .35s}
.bar.truth .fill{background:var(--good)}
.bar .lab{font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.verdict{margin-top:10px;font-size:13px;min-height:20px}
.facts{max-height:330px;overflow:auto;font-size:13px}
.rel{margin-bottom:8px}
.relh{font-weight:600;font-size:12px;display:flex;gap:6px;align-items:center}
.dot{width:8px;height:8px;border-radius:50%;background:var(--c);display:inline-block}
.chips{display:flex;flex-wrap:wrap;gap:4px;margin-top:4px}
.chip{background:var(--chip);border-radius:5px;padding:1px 6px;font-variant-numeric:tabular-nums}
.chip.subj{outline:1.5px solid var(--accent)}
.chip.new{background:color-mix(in srgb,var(--c) 22%,var(--chip))}
.note{color:var(--muted);font-size:12px;margin-top:8px}
.kv{display:flex;gap:14px;flex-wrap:wrap;color:var(--muted);font-size:12px}
.full{grid-column:1/-1}
</style>
</head>
<body>
<header>
  <h1>Reading physics through relations</h1>
  <div class="sub">An inspectable relational interface between perception and physical prediction.
  Pick a scene, choose a query, and switch the vocabulary rung: the forecast is made only from the
  facts listed on the right. Ground-truth CLEVRER states; fully inductive model (no object seen in training).</div>
</header>
<main>
  <section class="panel">
    <h2>Scene</h2>
    <div class="row">
      <select id="vid" aria-label="Scene"></select>
      <button id="play">Play</button>
      <button id="tocut">Jump to cutoff</button>
      <span class="kv"><span id="flab"></span><span id="blab"></span></span>
    </div>
    <div class="tagnote" id="tagnote"></div>
    <canvas id="cv" width="760" height="520"></canvas>
    <div class="scrub"><input type="range" id="fr" min="0" max="127" value="0" aria-label="Frame"><div class="cutmark" id="cut"></div></div>
    <div class="legend">
      <span>solid = in camera view</span><span>dashed = out of view (facts carried by the graph)</span>
      <span>arrow = velocity</span><span style="color:var(--bad)">red line = forecast cutoff</span>
    </div>
  </section>

  <section class="panel">
    <h2>Forecast</h2>
    <div class="qlist" id="qs"></div>
    <div style="height:12px"></div>
    <div class="rungs" id="rungs"></div>
    <div class="bars" id="bars"></div>
    <div class="row" style="margin-top:10px"><button id="reveal">Reveal answer</button></div>
    <div class="verdict" id="verdict"></div>
    <div class="note">Bars: softmax over KARMA scores for the queried object's possible collision partners.
    The small grid in each query shows the true partner's rank on each rung (1 = top).</div>
  </section>

  <section class="panel full">
    <h2>What the model sees: history facts up to the cutoff</h2>
    <div class="row">
      <label><input type="checkbox" id="attr"> show static attributes</label>
      <label><input type="checkbox" id="onlys" checked> only facts about queried objects</label>
    </div>
    <div class="facts" id="facts" style="margin-top:8px"></div>
    <div class="note">The history is treated as a <b>set</b>: shuffling event order leaves every prediction unchanged
    (identical test MRR on all four rungs). Temporal content enters through the vocabulary, e.g.
    <i>heading_toward</i> with a constant-velocity look-ahead. Tinted chips are facts this rung adds over the previous one.</div>
  </section>
</main>
<script>
const DATA = /*__DATA__*/null;
const TAGS = {
  vocabulary_helps:"Vocabulary helps: richer relations move the true partner to the top.",
  long_horizon:"Long horizon: collisions far after the cutoff, where the long look-ahead rung matters.",
  failure:"Failure case: even the richest vocabulary misses here. Look for what pairwise facts cannot express.",
  occlusion:"Object permanence: a queried object is out of camera view before the cutoff, yet its facts persist in the graph."
};
const RUNGC = {events:"--r-events",kin:"--r-kin",rel:"--r-rel",rel128:"--r-rel128"};
const COLORS = {gray:"#8e8e8e",red:"#d0473a",blue:"#3b6fd1",green:"#3f9e4d",brown:"#8a5a35",purple:"#8a4fb7",cyan:"#2fb3c4",yellow:"#e0b52b"};
const $ = id => document.getElementById(id);
const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();

let V=null, Q=0, R="rel128", F=0, playing=false, revealed=false, bounds=null, timer=null;

function init(){
  const sel=$("vid"); const groups={};
  DATA.index.videos.forEach(v=>{(groups[v.tag]=groups[v.tag]||[]).push(v)});
  Object.keys(TAGS).forEach(t=>{ if(!groups[t]) return;
    const g=document.createElement("optgroup"); g.label=t.replace("_"," ");
    groups[t].forEach(v=>{const o=document.createElement("option"); o.value=v.video;
      o.textContent=`Scene ${v.video} (${v.n_queries} quer${v.n_queries>1?"ies":"y"})`; g.appendChild(o)});
    sel.appendChild(g)});
  sel.onchange=()=>load(sel.value);
  $("fr").oninput=e=>{F=+e.target.value; draw()};
  $("play").onclick=togglePlay;
  $("tocut").onclick=()=>{setFrame(cutFrame()); stop()};
  $("reveal").onclick=()=>{revealed=!revealed; renderForecast(); draw()};
  $("attr").onchange=renderFacts; $("onlys").onchange=renderFacts;
  const rg=$("rungs");
  DATA.videos[DATA.index.videos[0].video].rungs.forEach(r=>{
    const b=document.createElement("button"); b.textContent=r.label; b.dataset.k=r.key;
    b.style.setProperty("--c",`var(${RUNGC[r.key]})`);
    b.onclick=()=>{R=r.key; renderAll()}; rg.appendChild(b)});
  load(sel.value);
}
function load(vid){
  V=DATA.videos[vid]; Q=0; revealed=false; stop();
  let xs=[],ys=[];
  V.frames.forEach(fr=>Object.values(fr).forEach(o=>{xs.push(o[0]);ys.push(o[1])}));
  const pad=0.6; bounds={x0:Math.min(...xs)-pad,x1:Math.max(...xs)+pad,y0:Math.min(...ys)-pad,y1:Math.max(...ys)+pad};
  $("fr").max=V.frames.length-1; $("tagnote").textContent=TAGS[V.tag]||"";
  renderQueries(); setFrame(cutFrame()); renderAll();
}
function cutFrame(){ const q=V.queries[Q]; const c=(q?q.cutoff_bin:V.cutoff_bin)??8;
  return Math.min(V.frames.length-1, Math.floor(((c+1)*V.bin_size-1)/V.frame_step)); }
function setFrame(f){F=f; $("fr").value=f; draw()}
function togglePlay(){ playing?stop():start() }
function start(){ playing=true; $("play").textContent="Pause";
  timer=setInterval(()=>{ if(F>=V.frames.length-1){stop();return} setFrame(F+1)},1000/30) }
function stop(){ playing=false; $("play").textContent="Play"; clearInterval(timer) }

function renderAll(){ [...$("rungs").children].forEach(b=>b.classList.toggle("on",b.dataset.k===R));
  renderQueries(); renderForecast(); renderFacts(); draw(); }

function rankCell(r){ const s=document.createElement("span"); s.className="rk";
  const c=r<=1?css("--good"):r<=2?css("--warn"):css("--bad");
  s.style.background=`color-mix(in srgb, ${c} 28%, transparent)`; s.textContent=Number.isInteger(r)?r:r.toFixed(1); return s; }
function objName(oid){ const o=V.objects.find(x=>x.oid==oid); return o?`#${oid} ${o.color} ${o.shape}`:`#${oid}`; }

function renderQueries(){
  const box=$("qs"); box.innerHTML="";
  V.queries.forEach((q,i)=>{ const b=document.createElement("button"); b.className="q"+(i===Q?" sel":"");
    const l=document.createElement("span"); l.textContent=`${objName(q.subject)} collides with ? (+${q.horizon} bins)`;
    const rk=document.createElement("span"); rk.className="ranks";
    V.rungs.forEach(r=>rk.appendChild(rankCell(q.preds[r.key].rank)));
    b.append(l,rk); b.onclick=()=>{Q=i; revealed=false; setFrame(cutFrame()); renderAll()}; box.appendChild(b)});
}
function softmax(a){ const m=Math.max(...a); const e=a.map(x=>Math.exp(x-m)); const s=e.reduce((p,c)=>p+c,0); return e.map(x=>x/s); }
function renderForecast(){
  const q=V.queries[Q], box=$("bars"); box.innerHTML=""; if(!q) return;
  const p=q.preds[R], pr=softmax(p.scores);
  const order=p.cands.map((c,i)=>i).sort((a,b)=>pr[b]-pr[a]);
  order.forEach(i=>{ const c=p.cands[i]; const d=document.createElement("div");
    d.className="bar"+(revealed&&c===q.target?" truth":"");
    d.innerHTML=`<span class="lab">${objName(c)}${revealed&&c===q.target?" ✓":""}</span>
      <div class="track"><div class="fill" style="width:${(pr[i]*100).toFixed(1)}%"></div></div>
      <span style="text-align:right;font-variant-numeric:tabular-nums">${(pr[i]*100).toFixed(0)}%</span>`;
    box.appendChild(d)});
  $("reveal").textContent=revealed?"Hide answer":"Reveal answer";
  if(revealed){ const r=p.rank; $("verdict").innerHTML = r<=1
      ? `<span style="color:var(--good)">Correct: true partner ranked first on this rung.</span>`
      : `<span style="color:var(--bad)">True partner ranked ${r} on this rung.</span>`;
  } else $("verdict").textContent="";
}
function renderFacts(){
  const q=V.queries[Q], box=$("facts"); box.innerHTML=""; if(!q) return;
  const showA=$("attr").checked, onlyS=$("onlys").checked;
  const keys=V.rungs.map(r=>r.key), ri=keys.indexOf(R), prev=ri>0?keys[ri-1]:null;
  const key=f=>f.slice(0,4).join("|");
  const prevSet=new Set(prev?(V.facts[prev]||[]).map(key):[]);
  const hist=(V.facts[R]||[]).filter(f=>f[4]==="history"&&f[3]<=q.cutoff_bin);
  const sel=new Set([String(q.subject),...q.preds[R].cands.map(String)]);
  const groups={};
  hist.forEach(f=>{ if(!showA&&f[1].startsWith("has_")) return;
    if(onlyS&&!sel.has(f[0])&&!sel.has(f[2])) return; (groups[f[1]]=groups[f[1]]||[]).push(f)});
  const introduced={has_shape:"events",has_material:"events",has_color:"events",collides_with:"events",enters_scene:"events",exits_scene:"events",
    near:"kin",stationary:"kin",speed_slow:"kin",speed_medium:"kin",speed_fast:"kin",approaching:"rel",heading_toward:"rel"};
  const names=Object.keys(groups).sort();
  if(!names.length){ box.innerHTML=`<div class="note">No non-attribute facts about these objects before the cutoff on this rung.</div>`; return; }
  names.forEach(rn=>{ const d=document.createElement("div"); d.className="rel";
    const c=`var(${RUNGC[introduced[rn]||"events"]})`; d.style.setProperty("--c",c);
    d.innerHTML=`<div class="relh"><span class="dot"></span>${rn} <span style="color:var(--muted);font-weight:400">(${groups[rn].length})</span></div>`;
    const ch=document.createElement("div"); ch.className="chips";
    groups[rn].sort((a,b)=>a[3]-b[3]).forEach(f=>{ const s=document.createElement("span");
      s.className="chip"+(f[0]==q.subject||f[2]==q.subject?" subj":"")+(prev&&!prevSet.has(key(f))?" new":"");
      s.textContent=`#${f[0]} → ${/^\d+$/.test(f[2])?"#"+f[2]:f[2].replace(/^(shape|color|material)_/,"")}  t${f[3]}`;
      ch.appendChild(s)}); d.appendChild(ch); box.appendChild(d)});
}

function draw(){
  const cv=$("cv"), ctx=cv.getContext("2d"), W=cv.width, H=cv.height;
  ctx.clearRect(0,0,W,H);
  const b=bounds, s=Math.min(W/(b.x1-b.x0),H/(b.y1-b.y0));
  const ox=(W-s*(b.x1-b.x0))/2, oy=(H-s*(b.y1-b.y0))/2;
  const P=(x,y)=>[ox+(x-b.x0)*s, H-(oy+(y-b.y0)*s)];
  const fr=V.frames[F]||{}, q=V.queries[Q], cf=cutFrame();
  const frame=F*V.frame_step;
  $("flab").textContent=`frame ${frame}`; $("blab").textContent=`bin ${Math.floor(frame/V.bin_size)}${F<=cf?" · history":" · future"}`;
  $("cut").style.left=`calc(${(cf/(V.frames.length-1))*100}% - 1px)`;
  ctx.lineWidth=1.5;
  Object.keys(fr).forEach(k=>{ ctx.beginPath(); ctx.strokeStyle=css("--line");
    for(let i=Math.max(0,F-40);i<=F;i++){ const o=V.frames[i][k]; if(!o) continue; const [x,y]=P(o[0],o[1]); i===Math.max(0,F-40)?ctx.moveTo(x,y):ctx.lineTo(x,y)} ctx.stroke()});
  V.collisions.forEach(c=>{ if(Math.abs(c.frame-frame)<=4){ const a=fr[c.objects[0]], d=fr[c.objects[1]]; if(!a||!d) return;
    const [x1,y1]=P(a[0],a[1]),[x2,y2]=P(d[0],d[1]); const mx=(x1+x2)/2,my=(y1+y2)/2;
    ctx.fillStyle=`color-mix(in srgb, ${css("--warn")} 45%, transparent)`; ctx.beginPath(); ctx.arc(mx,my,26,0,7); ctx.fill(); }});
  const R0=Math.max(10,s*0.32);
  V.objects.forEach(ob=>{ const o=fr[ob.oid]; if(!o) return; const [x,y]=P(o[0],o[1]);
    const vis=o[4]===1, col=COLORS[ob.color]||"#888";
    ctx.save(); ctx.globalAlpha=vis?1:0.45; ctx.setLineDash(vis?[]:[5,4]);
    ctx.fillStyle=vis?col:"transparent"; ctx.strokeStyle=col; ctx.lineWidth=2.5;
    ctx.beginPath();
    if(ob.shape==="cube") ctx.rect(x-R0,y-R0,2*R0,2*R0); else ctx.arc(x,y,R0,0,7);
    ctx.fill(); ctx.stroke();
    if(ob.shape==="cylinder"){ ctx.beginPath(); ctx.arc(x,y,R0*0.5,0,7); ctx.strokeStyle=vis?"rgba(255,255,255,.75)":col; ctx.lineWidth=2; ctx.stroke(); }
    ctx.restore();
    const vx=o[2],vy=o[3], sp=Math.hypot(vx,vy);
    if(sp>0.05){ const L=Math.min(70,sp*s*0.45), ux=vx/sp, uy=-vy/sp, ex=x+ux*(R0+L), ey=y+uy*(R0+L);
      ctx.strokeStyle=css("--ink"); ctx.lineWidth=1.6; ctx.setLineDash([]); ctx.beginPath(); ctx.moveTo(x+ux*R0,y+uy*R0); ctx.lineTo(ex,ey); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(ex,ey); ctx.lineTo(ex-ux*8-uy*5,ey-uy*8+ux*5); ctx.lineTo(ex-ux*8+uy*5,ey-uy*8-ux*5); ctx.closePath(); ctx.fillStyle=css("--ink"); ctx.fill(); }
    if(q && ob.oid===q.subject){ ctx.strokeStyle=css("--accent"); ctx.lineWidth=3; ctx.setLineDash([]); ctx.beginPath(); ctx.arc(x,y,R0+7,0,7); ctx.stroke(); }
    if(q && revealed && ob.oid===q.target){ ctx.strokeStyle=css("--good"); ctx.lineWidth=3; ctx.setLineDash([3,3]); ctx.beginPath(); ctx.arc(x,y,R0+7,0,7); ctx.stroke(); ctx.setLineDash([]); }
    ctx.fillStyle=css("--ink"); ctx.font="600 12px system-ui"; ctx.fillText("#"+ob.oid, x+R0+4, y-R0-2);
  });
  if(F>cf){ ctx.fillStyle=`color-mix(in srgb, ${css("--bad")} 6%, transparent)`; ctx.fillRect(0,0,W,H);
    ctx.fillStyle=css("--bad"); ctx.font="600 12px system-ui"; ctx.fillText("after cutoff: model has not seen this", 10, 18); }
}
init();
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="demo_data")
    ap.add_argument("--out", default="esr_demo.html")
    a = ap.parse_args()
    index = json.load(open(os.path.join(a.data, "index.json")))
    videos = {v["video"]: json.load(open(os.path.join(a.data, f"video_{v['video']}.json")))
              for v in index["videos"]}
    blob = json.dumps({"index": index, "videos": videos}, separators=(",", ":")).replace("</", "<\\/")
    open(a.out, "w").write(TEMPLATE.replace("/*__DATA__*/null", blob))
    print(f"wrote {a.out}  ({os.path.getsize(a.out)/1e6:.2f} MB, {len(videos)} scenes)")


if __name__ == "__main__":
    main()
