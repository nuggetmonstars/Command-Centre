#!/usr/bin/env python3
"""
patch_training.py — add a Training tab to coaches.html

Shows coach engagement with:
  * Coach Academy   — brain-activities / brain-categories, watched via
                      coach-watched-brain-video (long coachId)
  * Medal Testing   — testing-coach-activities, with watch progress
                      (coach-testing-video-progress), completion
                      (coach-testing-completed) and quiz accuracy
                      (coach-testing-submissions)
  * Not Started     — active coaches with no record in any of the above

All five collections key on the long auth UID, so no coach-app-map is needed.
Lesson-plan video watching (watched-video, short IDs) is deliberately NOT
included here — that needs the ID map and lands separately.

Run from ~/Command-Centre:
    /usr/local/bin/python3 patch_training.py            # dry run
    /usr/local/bin/python3 patch_training.py --commit   # apply

Backs up before writing. Aborts unless every anchor matches exactly once.
Set FILE below to patch leaderboard.html instead.
"""

import sys, shutil, datetime, os

FILE = "leaderboard.html"
COMMIT = "--commit" in sys.argv

EDITS = []

# ── 1. nav button ────────────────────────────────────────────────────────────
EDITS.append((
    """    <button class="nav-tab" data-tab="rewards">Rewards</button>
  </div>""",
    """    <button class="nav-tab" data-tab="rewards">Rewards</button>
    <button class="nav-tab" data-tab="training">Training</button>
  </div>""",
    "nav: add Training button"))

# ── 2. tab panel ─────────────────────────────────────────────────────────────
EDITS.append((
    """  <!-- REWARDS TAB -->
  <div id="tab-rewards" style="display:none">
    <div id="reward-content"><div class="loading"><div class="spinner"></div><p>Loading…</p></div></div>
  </div>
</div>""",
    """  <!-- REWARDS TAB -->
  <div id="tab-rewards" style="display:none">
    <div id="reward-content"><div class="loading"><div class="spinner"></div><p>Loading…</p></div></div>
  </div>

  <!-- TRAINING TAB -->
  <div id="tab-training" style="display:none">
    <div class="tr-controls" style="padding:0 24px 14px">
      <select id="tr-state" class="filter-select">
        <option value="">All states</option>
        <option value="VIC">VIC</option><option value="NSW">NSW</option>
        <option value="QLD">QLD</option><option value="SA">SA</option>
        <option value="WA">WA</option>
      </select>
      <input id="tr-search" class="filter-select" type="text" placeholder="Search coach…" style="min-width:200px">
    </div>
    <div id="training-content"><div class="loading"><div class="spinner"></div><p>Loading…</p></div></div>
  </div>
</div>""",
    "panel: add Training tab div"))

# ── 3. fetch the five training collections ───────────────────────────────────
EDITS.append((
    """    getDocs(collection(db,'five-star-feedbacks'))
  ]);""",
    """    getDocs(collection(db,'five-star-feedbacks')),
    getDocs(collection(db,'brain-categories')),
    getDocs(collection(db,'brain-activities')),
    getDocs(collection(db,'coach-watched-brain-video')),
    getDocs(collection(db,'testing-coach-activities')),
    getDocs(collection(db,'coach-testing-video-progress')),
    getDocs(collection(db,'coach-testing-completed')),
    getDocs(collection(db,'coach-testing-submissions'))
  ]);""",
    "fetch: 7 training collections"))

EDITS.append((
    "const [uSnap,fbSnap,hcSnap,evSnap,attSnap,vtSnap,chkSnap,trSnap,fsSnap] = await Promise.all([",
    "const [uSnap,fbSnap,hcSnap,evSnap,attSnap,vtSnap,chkSnap,trSnap,fsSnap,"
    "bcSnap,baSnap,bwSnap,tcaSnap,tvpSnap,tcSnap,tsSnap] = await Promise.all([",
    "destructure: 7 training snapshots"))

EDITS.append((
    "  fsSnap.forEach(d=>fiveStarFbs.push({id:d.id,...d.data()}));",
    """  fsSnap.forEach(d=>fiveStarFbs.push({id:d.id,...d.data()}));
  const brainCats={},brainActs={},brainWatched=[],testActs={},testProg=[],testDone=[],testSubs=[];
  bcSnap.forEach(d=>{brainCats[d.id]={id:d.id,...d.data()};});
  baSnap.forEach(d=>{brainActs[d.id]={id:d.id,...d.data()};});
  bwSnap.forEach(d=>brainWatched.push({id:d.id,...d.data()}));
  tcaSnap.forEach(d=>{testActs[d.id]={id:d.id,...d.data()};});
  tvpSnap.forEach(d=>testProg.push({id:d.id,...d.data()}));
  tcSnap.forEach(d=>testDone.push({id:d.id,...d.data()}));
  tsSnap.forEach(d=>testSubs.push({id:d.id,...d.data()}));""",
    "populate: training arrays"))

EDITS.append((
    "  RAW={users,feedbacks,hcFbs,allEvents,attended,viewTabs,checks,trials,fiveStarFbs};",
    "  RAW={users,feedbacks,hcFbs,allEvents,attended,viewTabs,checks,trials,fiveStarFbs,"
    "brainCats,brainActs,brainWatched,testActs,testProg,testDone,testSubs};",
    "RAW: expose training data"))

# ── 4. renderTraining + dispatch ─────────────────────────────────────────────
RENDER_FN = r"""
// ── TRAINING TAB ──────────────────────────────────────────────────────────────
function buildTraining() {
  const {users,brainCats,brainActs,brainWatched,testActs,testProg,testDone,testSubs}=RAW;
  const roster=(COACHES||[]).map(c=>({id:c.id,fullName:c.fullName,state:c.state}));

  const byCoach={};
  roster.forEach(c=>{byCoach[c.id]={...c,academy:[],testing:[],quizRight:0,quizTotal:0,completed:[]};});

  brainWatched.forEach(w=>{
    const t=byCoach[w.coachId]; if(!t) return;
    const act=brainActs[w.activityId]||{};
    const cat=brainCats[w.categoryId]||{};
    t.academy.push({name:w.activityName||act.name||'(unnamed)',
                    cat:(cat.name||'Other').trim(), date:w.date||0});
  });

  const progByCoach={};
  testProg.forEach(p=>{ (progByCoach[p.userId]=progByCoach[p.userId]||[]).push(p); });
  Object.entries(progByCoach).forEach(([uid,ps])=>{
    const t=byCoach[uid]; if(!t) return;
    ps.forEach(p=>{
      const a=testActs[p.activityId]||{};
      t.testing.push({name:a.name?('Module '+a.name):'(module)',
                      secs:Math.round(p.maxWatchedSeconds||0),
                      unlocked:!!p.questionsUnlocked, date:p.updatedAt||0});
    });
  });

  testDone.forEach(d=>{
    const t=byCoach[d.userId]; if(!t) return;
    let acts=d.activities;
    if(typeof acts==='string'){ try{acts=JSON.parse(acts.replace(/'/g,'"'));}catch(e){acts=[];} }
    (acts||[]).forEach(id=>{ const a=testActs[id]||{}; t.completed.push(a.name?('Module '+a.name):id); });
  });

  testSubs.forEach(s=>{
    const t=byCoach[s.userId]; if(!t) return;
    t.quizTotal++;
    if(s.isCorrect===true||String(s.isCorrect).toLowerCase()==='true') t.quizRight++;
  });

  return Object.values(byCoach);
}

function renderTraining() {
  const el=document.getElementById('training-content');
  const stF=(document.getElementById('tr-state')||{}).value||'';
  const qF=((document.getElementById('tr-search')||{}).value||'').toLowerCase().trim();
  let all=buildTraining();
  if(stF) all=all.filter(c=>(c.state||'')===stF);
  if(qF)  all=all.filter(c=>(c.fullName||'').toLowerCase().includes(qF));

  const active=all.filter(c=>c.academy.length||c.testing.length||c.completed.length);
  const none=all.filter(c=>!(c.academy.length||c.testing.length||c.completed.length));
  const acad=all.filter(c=>c.academy.length).length;
  const done=all.filter(c=>c.completed.length).length;

  const fdate=t=>t?new Date(Number(t)).toLocaleDateString('en-AU',{day:'2-digit',month:'2-digit',year:'numeric'}):'';
  const mmss=s=>`${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`;

  let h=`<div class="rewards-wrap">
    <p class="rewards-intro">Coach Academy videos and medal coach testing. Counts are all-time and are not affected by the period filter.</p>
    <div class="stats-row" style="margin-bottom:16px">
      <div class="stat-card"><div class="stat-num">${acad}</div><div class="stat-lbl">opened Coach Academy</div></div>
      <div class="stat-card"><div class="stat-num">${done}</div><div class="stat-lbl">completed medal testing</div></div>
      <div class="stat-card"><div class="stat-num">${none.length}</div><div class="stat-lbl">no training on record</div></div>
      <div class="stat-card"><div class="stat-num">${all.length}</div><div class="stat-lbl">active coaches</div></div>
    </div>`;

  if(active.length){
    h+=`<h3 style="margin:18px 0 10px">Started training (${active.length})</h3>`;
    active.sort((a,b)=>(b.academy.length+b.completed.length)-(a.academy.length+a.completed.length));
    active.forEach(c=>{
      const cats={};
      c.academy.forEach(a=>{(cats[a.cat]=cats[a.cat]||[]).push(a);});
      const quiz=c.quizTotal?` · quiz ${c.quizRight}/${c.quizTotal}`:'';
      h+=`<details class="tr-row" style="background:#fff;border:2px solid var(--blue);border-radius:10px;padding:10px 14px;margin-bottom:8px">
        <summary style="cursor:pointer;font-weight:700;color:var(--blue)">
          ${c.fullName} <span style="font-weight:500;opacity:.75">— ${c.state||'?'} · ${c.academy.length} academy video${c.academy.length===1?'':'s'} · ${c.completed.length}/2 modules${quiz}</span>
        </summary>
        <div style="padding:10px 4px 2px;font-size:14px">`;
      if(Object.keys(cats).length){
        Object.entries(cats).forEach(([cat,vids])=>{
          h+=`<div style="margin-bottom:8px"><b>${cat}</b><ul style="margin:4px 0 0 18px">`;
          vids.sort((a,b)=>b.date-a.date).forEach(v=>{h+=`<li>${v.name} <span style="opacity:.6">${fdate(v.date)}</span></li>`;});
          h+=`</ul></div>`;
        });
      } else { h+=`<div style="opacity:.7;margin-bottom:8px">No Academy videos watched</div>`; }
      if(c.testing.length){
        h+=`<div><b>Medal testing</b><ul style="margin:4px 0 0 18px">`;
        c.testing.sort((a,b)=>b.date-a.date).forEach(t=>{
          const fin=c.completed.some(x=>x===t.name);
          h+=`<li>${t.name} — watched ${mmss(t.secs)}${t.unlocked?', questions unlocked':''}${fin?' <b style="color:var(--green)">✓ completed</b>':''} <span style="opacity:.6">${fdate(t.date)}</span></li>`;
        });
        h+=`</ul></div>`;
      } else { h+=`<div style="opacity:.7">No medal testing started</div>`; }
      h+=`</div></details>`;
    });
  }

  if(none.length){
    h+=`<h3 style="margin:22px 0 8px">No training on record (${none.length})</h3>
        <p style="font-size:14px;opacity:.8;margin-bottom:10px">These coaches have no Coach Academy or medal testing activity recorded.</p>
        <div style="display:flex;flex-wrap:wrap;gap:6px">`;
    none.sort((a,b)=>(a.fullName||'').localeCompare(b.fullName||''));
    none.forEach(c=>{h+=`<span style="background:#fff;border:1.5px solid var(--red);border-radius:14px;padding:4px 11px;font-size:13px;color:var(--blue)">${c.fullName} <span style="opacity:.6">${c.state||'?'}</span></span>`;});
    h+=`</div>`;
  }

  h+=`</div>`;
  el.innerHTML=h;
}

"""

EDITS.append((
    "function renderAll() {",
    RENDER_FN.lstrip("\n") + "function renderAll() {",
    "insert buildTraining + renderTraining"))

EDITS.append((
    "  ['lb-content','dev-content','alert-content','reward-content'].forEach(id=>document.getElementById(id).innerHTML='');\n"
    "  renderLeaderboard(); renderDeveloping(); renderAlerts(); renderRewards();",
    "  ['lb-content','dev-content','alert-content','reward-content','training-content'].forEach(id=>{const e=document.getElementById(id); if(e) e.innerHTML='';});\n"
    "  renderLeaderboard(); renderDeveloping(); renderAlerts(); renderRewards(); renderTraining();",
    "renderAll: include training"))

# ── 5. tab switching (two arrays) ────────────────────────────────────────────
EDITS.append((
    """    ['leaderboard','developing','alerts','rewards'].forEach(t=>{
      document.getElementById('tab-'+t).style.display=t===tab?'block':'none';
    });""",
    """    ['leaderboard','developing','alerts','rewards','training'].forEach(t=>{
      const e=document.getElementById('tab-'+t); if(e) e.style.display=t===tab?'block':'none';
    });""",
    "tab switch: include training"))

EDITS.append((
    """  ['leaderboard','developing','alerts','rewards'].forEach(t=>{
    document.getElementById('tab-'+t).style.display=t==='leaderboard'?'block':'none';
  });""",
    """  ['leaderboard','developing','alerts','rewards','training'].forEach(t=>{
    const e=document.getElementById('tab-'+t); if(e) e.style.display=t==='leaderboard'?'block':'none';
  });""",
    "need-support pill: include training"))

# ── 6. filter events ─────────────────────────────────────────────────────────
EDITS.append((
    "['dev-search','dev-state'].forEach(id=>{",
    "['tr-search','tr-state'].forEach(id=>{\n"
    "  const e=document.getElementById(id);\n"
    "  if(e) e.addEventListener('input',()=>{ if(COACHES) renderTraining(); });\n"
    "});\n"
    "['dev-search','dev-state'].forEach(id=>{",
    "wire tr-search / tr-state filters"))


def main():
    if not os.path.exists(FILE):
        sys.exit(f"ERROR: {FILE} not found. Run from ~/Command-Centre.")

    src = open(FILE, encoding="utf-8").read()
    original = src
    print(f"Read {FILE}: {len(src):,} chars\n")

    problems = []
    for old, _new, label in EDITS:
        n = src.count(old)
        if n != 1:
            problems.append(f"  [{n} matches] {label}")
    if problems:
        print("ABORT — anchors did not match exactly once:")
        print("\n".join(problems))
        print("\nNothing written. File may already be patched, or has drifted.")
        sys.exit(1)

    for old, new, label in EDITS:
        src = src.replace(old, new, 1)
        print(f"  OK  {label}")

    print("\nVerification:")
    gates = [
        ("Training nav button", src.count('data-tab="training"') == 1),
        ("Training panel", src.count('id="tab-training"') == 1),
        ("renderTraining defined", src.count("function renderTraining()") == 1),
        ("renderTraining called", src.count("renderTraining();") >= 2),
        ("brain collections fetched", "getDocs(collection(db,'coach-watched-brain-video'))" in src),
        ("testing collections fetched", "getDocs(collection(db,'coach-testing-completed'))" in src),
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
    print("\nNow: hard-refresh, open the Training tab, then commit.")


if __name__ == "__main__":
    main()
