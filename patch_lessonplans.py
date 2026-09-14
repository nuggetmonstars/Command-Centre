#!/usr/bin/env python3
"""
patch_lessonplans.py — add a Lesson Plans tab to coaches.html

Shows which coaches are watching lesson plan activity videos, over a
selectable period (this week / this month / year to date / all time).

Data:
  watched-video          7,800+ docs, keyed by SHORT app id
  coach-app-map          shortId -> coachId (the durable crosswalk)
  learn-categories       program names (Sports, Music, Gymnastics, Yoga, Sensory Fusion)
  learn-subcategories    week names, parentId -> category
  learn-activities       video names

watched-video is LAZY-LOADED — it only downloads the first time the tab is
opened, so the other tabs stay fast.

Sections (all period-relative):
  Watched this period       — views, last watched, program spread
  Nothing this period       — has history, but not in this window
  No record at all          — mapped, but never watched anything
  Can't verify              — no coach-app-map entry; NOT counted as neglect

Run from ~/Command-Centre:
    /usr/local/bin/python3 patch_lessonplans.py            # dry run
    /usr/local/bin/python3 patch_lessonplans.py --commit   # apply

Set FILE below to patch leaderboard.html instead.
"""

import sys, shutil, datetime, os

FILE = "coaches.html"
COMMIT = "--commit" in sys.argv

EDITS = []

# ── 1. nav button ────────────────────────────────────────────────────────────
EDITS.append((
    '    <button class="nav-tab" data-tab="training">Training</button>',
    '    <button class="nav-tab" data-tab="training">Training</button>\n'
    '    <button class="nav-tab" data-tab="lessons">Lesson Plans</button>',
    "nav: add Lesson Plans button"))

# ── 2. panel ─────────────────────────────────────────────────────────────────
EDITS.append((
    '    <div id="training-content"><div class="loading"><div class="spinner"></div><p>Loading…</p></div></div>\n  </div>',
    '''    <div id="training-content"><div class="loading"><div class="spinner"></div><p>Loading…</p></div></div>
  </div>

  <!-- LESSON PLANS TAB -->
  <div id="tab-lessons" style="display:none">
    <div style="padding:0 24px 6px">
      <input id="lp-search" class="filter-select" type="text" placeholder="🔍  Search coaches by name…" style="width:100%;margin-bottom:12px">
      <div class="tr-pills" id="lp-periods"></div>
      <div class="tr-pills" id="lp-pills"></div>
    </div>
    <div id="lessons-content"><div class="loading"><div class="spinner"></div><p>Loading…</p></div></div>
  </div>''',
    "panel: add Lesson Plans tab"))

# ── 3. fetch the reference collections (small) ───────────────────────────────
EDITS.append((
    "    getDocs(collection(db,'coach-testing-submissions'))\n  ]);",
    "    getDocs(collection(db,'coach-testing-submissions')),\n"
    "    getDocs(collection(db,'coach-app-map')),\n"
    "    getDocs(collection(db,'learn-categories')),\n"
    "    getDocs(collection(db,'learn-subcategories')),\n"
    "    getDocs(collection(db,'learn-activities'))\n  ]);",
    "fetch: map + learn reference data"))

EDITS.append((
    "bcSnap,baSnap,bwSnap,tcaSnap,tvpSnap,tcSnap,tsSnap] = await Promise.all([",
    "bcSnap,baSnap,bwSnap,tcaSnap,tvpSnap,tcSnap,tsSnap,"
    "amSnap,lcSnap,lsSnap,laSnap] = await Promise.all([",
    "destructure: 4 lesson-plan snapshots"))

EDITS.append((
    "  tsSnap.forEach(d=>testSubs.push({id:d.id,...d.data()}));",
    """  tsSnap.forEach(d=>testSubs.push({id:d.id,...d.data()}));
  const appMap={},learnCats={},learnSubs={},learnActs={};
  amSnap.forEach(d=>{const x=d.data(); if(x.coachId) appMap[d.id]=x.coachId;});
  lcSnap.forEach(d=>{learnCats[d.id]=((d.data().name)||'').trim();});
  lsSnap.forEach(d=>{learnSubs[d.id]={name:(d.data().name||'').trim(),parentId:d.data().parentId};});
  laSnap.forEach(d=>{learnActs[d.id]=(d.data().name||'').trim();});""",
    "populate: lesson plan reference maps"))

EDITS.append((
    "brainCats,brainActs,brainWatched,testActs,testProg,testDone,testSubs};",
    "brainCats,brainActs,brainWatched,testActs,testProg,testDone,testSubs,"
    "appMap,learnCats,learnSubs,learnActs};",
    "RAW: expose lesson plan reference data"))

# ── 4. the tab itself ────────────────────────────────────────────────────────
LESSONS_JS = r'''
// ── LESSON PLANS TAB ──────────────────────────────────────────────────────────
let LP_STATE='ALL', LP_PERIOD='month', LP_VIEWS=null, LP_LOADING=false;

const LP_PERIODS=[['week','This week'],['month','This month'],['ytd','Year to date'],['all','All time']];

function lpPeriodStart(p){
  const now=new Date();
  if(p==='week'){ const d=new Date(now); const dow=(d.getDay()+6)%7; // Monday = 0
    d.setDate(d.getDate()-dow); d.setHours(0,0,0,0); return d.getTime(); }
  if(p==='month') return new Date(now.getFullYear(),now.getMonth(),1).getTime();
  if(p==='ytd')   return new Date(now.getFullYear(),0,1).getTime();
  return 0;
}

async function lpLoadViews(){
  if(LP_VIEWS||LP_LOADING) return;
  LP_LOADING=true;
  try{
    const snap=await getDocs(collection(db,'watched-video'));
    const out=[]; snap.forEach(d=>out.push(d.data()));
    LP_VIEWS=out;
  }catch(e){ console.error('watched-video load failed',e); LP_VIEWS=[]; }
  LP_LOADING=false;
  renderLessons();
}

function buildLessons(){
  const {appMap,learnCats,learnSubs,learnActs}=RAW;
  const roster=(COACHES||[]).map(c=>({id:c.id,fullName:c.fullName,state:c.state}));
  const byCoach={}; roster.forEach(c=>{byCoach[c.id]={...c,views:[],mapped:false};});
  Object.values(appMap).forEach(cid=>{ if(byCoach[cid]) byCoach[cid].mapped=true; });

  (LP_VIEWS||[]).forEach(v=>{
    const cid=appMap[v.userId]; if(!cid) return;
    const t=byCoach[cid]; if(!t) return;
    const sub=learnSubs[v.parentId]||{};
    t.views.push({
      date:v.date||0,
      prog:learnCats[v.categoryId]||'Other',
      week:sub.name||'(unknown week)',
      name:learnActs[v.activityId]||'(video)'
    });
  });
  return Object.values(byCoach);
}

function renderLessons(){
  const el=document.getElementById('lessons-content');
  if(!el) return;
  if(!LP_VIEWS){ lpLoadViews();
    el.innerHTML='<div class="loading"><div class="spinner"></div><p>Loading lesson plan activity…</p></div>'; return; }

  const qF=((document.getElementById('lp-search')||{}).value||'').toLowerCase().trim();
  const all=buildLessons();
  const cut=lpPeriodStart(LP_PERIOD);

  // period pills
  const pp=document.getElementById('lp-periods');
  if(pp){
    pp.innerHTML=LP_PERIODS.map(([k,lbl])=>
      `<div class="tr-pill ${LP_PERIOD===k?'on':''}" data-st="ALL" data-p="${k}">${lbl}</div>`).join('');
    pp.querySelectorAll('.tr-pill').forEach(p=>p.onclick=()=>{LP_PERIOD=p.dataset.p;renderLessons();});
  }

  // state pills
  const STATES=['VIC','NSW','QLD','SA','WA'];
  const counts={}; STATES.forEach(s=>counts[s]=all.filter(c=>(c.state||'')===s).length);
  const sp=document.getElementById('lp-pills');
  if(sp){
    sp.innerHTML=`<div class="tr-pill ${LP_STATE==='ALL'?'on':''}" data-st="ALL">All States</div>`+
      STATES.map(s=>`<div class="tr-pill ${LP_STATE===s?'on':''}" data-st="${s}">${s}: ${counts[s]}</div>`).join('');
    sp.querySelectorAll('.tr-pill').forEach(p=>p.onclick=()=>{LP_STATE=p.dataset.st;renderLessons();});
  }

  let list=all;
  if(LP_STATE!=='ALL') list=list.filter(c=>(c.state||'')===LP_STATE);
  if(qF) list=list.filter(c=>(c.fullName||'').toLowerCase().includes(qF));

  list.forEach(c=>{ c.inP=c.views.filter(v=>v.date>=cut); c.last=c.views.length?Math.max(...c.views.map(v=>v.date)):0; });

  const abc=(a,b)=>(a.fullName||'').localeCompare(b.fullName||'');
  const watched = list.filter(c=>c.mapped&&c.inP.length).sort(abc);
  const quiet   = list.filter(c=>c.mapped&&!c.inP.length&&c.views.length).sort(abc);
  const never   = list.filter(c=>c.mapped&&!c.views.length).sort(abc);
  const unknown = list.filter(c=>!c.mapped).sort(abc);

  const fdate=t=>t?new Date(Number(t)).toLocaleDateString('en-AU',{day:'2-digit',month:'2-digit',year:'numeric'}):'—';
  const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));
  const STL=['VIC','NSW','QLD','SA','WA'];

  const card=(c,i,pfx,meta)=>{
    const st=STL.includes(c.state)?c.state:'none';
    // drill-down: full history, program -> week, period views marked
    const byProg={};
    c.views.forEach(v=>{ (byProg[v.prog]=byProg[v.prog]||{})[v.week]=(byProg[v.prog][v.week]||[]); byProg[v.prog][v.week].push(v); });
    let body='';
    const progs=Object.keys(byProg).sort();
    if(progs.length){
      progs.forEach(p=>{
        const wks=byProg[p];
        const tot=Object.values(wks).reduce((a,b)=>a+b.length,0);
        body+=`<b>${esc(p)}</b> <span class="tr-dim">${tot} view${tot===1?'':'s'}</span><ul>`;
        Object.entries(wks)
          .sort((a,b)=>Math.max(...b[1].map(v=>v.date))-Math.max(...a[1].map(v=>v.date)))
          .slice(0,12)
          .forEach(([wk,vs])=>{
            const lastW=Math.max(...vs.map(v=>v.date));
            const inP=vs.some(v=>v.date>=cut);
            body+=`<li>${esc(wk)} <span class="tr-dim">${vs.length}×, ${fdate(lastW)}</span>`+
                  `${inP?' <b style="color:#3d8b2f">•</b>':''}</li>`;
          });
        const nw=Object.keys(wks).length;
        if(nw>12) body+=`<li class="tr-dim">…and ${nw-12} more weeks</li>`;
        body+=`</ul>`;
      });
      body+=`<div class="tr-dim" style="margin-top:4px">Green dot = viewed in the selected period. Lifetime total ${c.views.length} views.</div>`;
    } else if(!c.mapped){
      body=`<div class="tr-dim">This coach has no app ID on record yet, so their activity can't be matched. It isn't evidence they haven't watched anything — the map fills in as they use the app.</div>`;
    } else {
      body=`<div class="tr-dim">No lesson plan videos watched.</div>`;
    }
    const id=`${pfx}-${i}`;
    return `<div class="tr-cc st-${st}" id="lpc-${id}">
      <div class="tr-cn" data-lp="${id}"><span class="tr-caret">&#9656;</span>${esc(c.fullName)}</div>
      <div class="tr-cmeta" data-lp="${id}">${esc(meta(c))}</div>
      <div class="tr-cbody">${body}</div>
    </div>`;
  };

  const sec=(title,arr,pfx,meta,red)=>{
    let s=`<div class="${red?'tr-none':''}"><div class="tr-sec">${title} <span class="n">${arr.length}</span></div></div>`;
    s+= arr.length ? `<div class="tr-grid">${arr.map((c,i)=>card(c,i,pfx,meta)).join('')}</div>`
                   : `<div class="tr-dim" style="margin-bottom:10px">None in this view</div>`;
    return s;
  };

  const plabel=(LP_PERIODS.find(p=>p[0]===LP_PERIOD)||['','' ])[1].toLowerCase();
  const totalIn=all.filter(c=>c.mapped&&c.views.some(v=>v.date>=cut)).length;
  const mappedN=all.filter(c=>c.mapped).length;

  let h=`<div style="padding:0 24px 24px">
    <div class="stats-row" style="margin-bottom:4px">
      <div class="stat-card"><div class="stat-num">${totalIn}</div><div class="stat-lbl">watched ${plabel}</div></div>
      <div class="stat-card"><div class="stat-num">${all.filter(c=>c.mapped&&!c.views.some(v=>v.date>=cut)).length}</div><div class="stat-lbl">nothing ${plabel}</div></div>
      <div class="stat-card"><div class="stat-num">${(LP_VIEWS||[]).filter(v=>(v.date||0)>=cut).length}</div><div class="stat-lbl">total views ${plabel}</div></div>
      <div class="stat-card"><div class="stat-num">${mappedN}/${all.length}</div><div class="stat-lbl">coaches trackable</div></div>
    </div>`;

  h+=sec(`Watched ${plabel}`, watched, 'w',
        c=>`${c.state||'—'} · ${c.inP.length} view${c.inP.length===1?'':'s'} · last ${fdate(c.last)}`);
  h+=sec(`Nothing ${plabel}`, quiet, 'q',
        c=>`${c.state||'—'} · last watched ${fdate(c.last)} · ${c.views.length} lifetime`, true);
  h+=sec(`No lesson plan activity on record`, never, 'n',
        c=>`${c.state||'—'} · never watched`, true);
  h+=sec(`Can't verify — no app ID mapped yet`, unknown, 'u',
        c=>`${c.state||'—'} · unverified`);

  h+=`<p class="tr-dim" style="margin-top:14px;max-width:760px">Coaches under "can't verify" have no entry in the app ID map. Their activity can't be matched yet, so they are deliberately kept out of the counts above rather than shown as having watched nothing. The map fills in automatically as coaches use the app.</p>`;
  h+=`</div>`;
  el.innerHTML=h;

  el.querySelectorAll('[data-lp]').forEach(n=>n.onclick=()=>{
    const c=document.getElementById('lpc-'+n.dataset.lp);
    if(c) c.classList.toggle('open');
  });
}

'''

EDITS.append((
    "function renderAll() {",
    LESSONS_JS.lstrip("\n") + "function renderAll() {",
    "insert lesson plan functions"))

EDITS.append((
    "  renderLeaderboard(); renderDeveloping(); renderAlerts(); renderRewards(); renderTraining();",
    "  renderLeaderboard(); renderDeveloping(); renderAlerts(); renderRewards(); renderTraining();\n"
    "  if(LP_VIEWS) renderLessons();",
    "renderAll: refresh lessons if already loaded"))

# ── 5. tab switching ─────────────────────────────────────────────────────────
EDITS.append((
    """    ['leaderboard','developing','alerts','rewards','training'].forEach(t=>{
      const e=document.getElementById('tab-'+t); if(e) e.style.display=t===tab?'block':'none';
    });""",
    """    ['leaderboard','developing','alerts','rewards','training','lessons'].forEach(t=>{
      const e=document.getElementById('tab-'+t); if(e) e.style.display=t===tab?'block':'none';
    });
    if(tab==='lessons') renderLessons();""",
    "tab switch: include lessons + lazy load"))

EDITS.append((
    """  ['leaderboard','developing','alerts','rewards','training'].forEach(t=>{
    const e=document.getElementById('tab-'+t); if(e) e.style.display=t==='leaderboard'?'block':'none';
  });""",
    """  ['leaderboard','developing','alerts','rewards','training','lessons'].forEach(t=>{
    const e=document.getElementById('tab-'+t); if(e) e.style.display=t==='leaderboard'?'block':'none';
  });""",
    "need-support pill: include lessons"))

# ── 6. search wiring ─────────────────────────────────────────────────────────
EDITS.append((
    """['tr-search'].forEach(id=>{
  const e=document.getElementById(id);
  if(e) e.addEventListener('input',()=>{ if(COACHES) renderTraining(); });
});""",
    """['tr-search'].forEach(id=>{
  const e=document.getElementById(id);
  if(e) e.addEventListener('input',()=>{ if(COACHES) renderTraining(); });
});
(function(){ const e=document.getElementById('lp-search');
  if(e) e.addEventListener('input',()=>{ if(COACHES&&LP_VIEWS) renderLessons(); }); })();""",
    "wire lp-search"))


def main():
    if not os.path.exists(FILE):
        sys.exit(f"ERROR: {FILE} not found. Run from ~/Command-Centre.")
    src = open(FILE, encoding="utf-8").read()
    original = src
    print(f"Read {FILE}: {len(src):,} chars\n")

    if 'id="tab-lessons"' in src:
        sys.exit("ABORT: this file already has the Lesson Plans tab.")

    problems = []
    for old, _new, label in EDITS:
        n = src.count(old)
        if n != 1:
            problems.append(f"  [{n} matches] {label}")
    if problems:
        print("ABORT — anchors did not match exactly once:")
        print("\n".join(problems))
        sys.exit(1)

    for old, new, label in EDITS:
        src = src.replace(old, new, 1)
        print(f"  OK  {label}")

    print("\nVerification:")
    gates = [
        ("nav button", src.count('data-tab="lessons"') == 1),
        ("panel", src.count('id="tab-lessons"') == 1),
        ("renderLessons defined", src.count("function renderLessons()") == 1),
        ("buildLessons defined", src.count("function buildLessons()") == 1),
        ("lazy loader defined", src.count("async function lpLoadViews()") == 1),
        ("map fetched", "getDocs(collection(db,'coach-app-map'))" in src),
        ("learn refs fetched", "getDocs(collection(db,'learn-subcategories'))" in src),
        ("watched-video lazy-loaded only",
         src.count("getDocs(collection(db,'watched-video'))") == 1 and "async function lpLoadViews" in src),
        ("period pills", "LP_PERIODS" in src),
        ("training tab intact", src.count("function renderTraining()") == 1),
        ("auth still wired", src.count("onAuthStateChanged") >= 1),
        ("no placeholder apiKey", "PASTE_YOUR_API_KEY_HERE" not in src),
        ("fiveStars fix intact", "fiveStarFbs||[]).filter(f=>f.coachId===cid)" in src),
    ]
    for label, ok in gates:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
    if not all(ok for _l, ok in gates):
        sys.exit("\nABORT — verification failed. Nothing written.")

    if not COMMIT:
        print("\n--- DRY RUN. Nothing written. Re-run with --commit to apply. ---")
        return

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    base = FILE.replace(".html", "")
    backup = f"{base}.BACKUP.{stamp}.html"
    shutil.copy2(FILE, backup)
    open(FILE, "w", encoding="utf-8").write(src)
    print(f"\nBacked up to {backup}")
    print(f"Wrote {FILE}  ({len(original):,} -> {len(src):,} chars)")
    print("\nNow: hard-refresh, open Lesson Plans, then commit.")


if __name__ == "__main__":
    main()
