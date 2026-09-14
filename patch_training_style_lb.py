#!/usr/bin/env python3
"""
patch_training_style.py — restyle the Training tab on coaches.html

Replaces the first-cut Training render with:
  * State pills (All States + VIC/NSW/QLD/SA/WA) styled off tracker_main's .sf,
    each filling its own state colour when active, with per-state counts.
  * Four-column card grid using the .cc / .cn / .cc-caret / .cc-body pattern
    from the equipment tracker. Cards tinted by state:
        VIC blue, NSW green, QLD pink, SA yellow, WA orange
  * Two sections, alphabetical within each:
        "Started training"        — any Academy video or medal testing record
        "No training on record"   — nothing at all
  * Status line on each card face; caret expands to per-video detail.

Only touches the Training tab. buildTraining() and the data layer are unchanged.

Run from ~/Command-Centre:
    /usr/local/bin/python3 patch_training_style.py            # dry run
    /usr/local/bin/python3 patch_training_style.py --commit   # apply

Set FILE below to patch leaderboard.html instead.
"""

import sys, shutil, datetime, os, re

FILE = "leaderboard.html"
COMMIT = "--commit" in sys.argv

EDITS = []

# ── 1. CSS ───────────────────────────────────────────────────────────────────
CSS = """
/* ── TRAINING TAB ─────────────────────────────────────────────────────────── */
.tr-pills{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:14px}
.tr-pill{font-family:'MarkerFelt',cursive;padding:6px 15px;border-radius:30px;font-size:12px;cursor:pointer;border:2px solid var(--lightblue);background:#fff;color:var(--blue);user-select:none}
.tr-pill.on{color:#fff}
.tr-pill.on[data-st="ALL"]{background:var(--red);border-color:var(--red)}
.tr-pill.on[data-st="VIC"]{background:#1f8fd6;border-color:#1f8fd6}
.tr-pill.on[data-st="NSW"]{background:#6FC04F;border-color:#6FC04F}
.tr-pill.on[data-st="QLD"]{background:#E5568F;border-color:#E5568F}
.tr-pill.on[data-st="SA"]{background:#FFD119;border-color:#FFD119;color:var(--ink)}
.tr-pill.on[data-st="WA"]{background:#FF9933;border-color:#FF9933}
.tr-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:13px;margin-bottom:8px}
.tr-cc{background:var(--white);border-radius:18px;border:3px solid #e7eef3;overflow:hidden;box-shadow:var(--shadow);color:#fff}
.tr-cc.st-VIC{background:#1f8fd6;border-color:#1f8fd6}
.tr-cc.st-NSW{background:#6FC04F;border-color:#6FC04F}
.tr-cc.st-QLD{background:#E5568F;border-color:#E5568F}
.tr-cc.st-SA{background:#FFD119;border-color:#FFD119;color:var(--ink)}
.tr-cc.st-WA{background:#FF9933;border-color:#FF9933}
.tr-cc.st-none{background:#8fa3b0;border-color:#8fa3b0}
.tr-cn{font-family:'MarkerFelt',cursive;font-size:16px;padding:13px 15px 4px;cursor:pointer;line-height:1.25}
.tr-caret{font-size:12px;opacity:.9;margin-right:4px;display:inline-block;vertical-align:middle;transition:transform .12s}
.tr-cc.open .tr-caret{transform:rotate(90deg)}
.tr-cmeta{font-size:11px;letter-spacing:.7px;text-transform:uppercase;opacity:.85;padding:0 15px 12px;cursor:pointer}
.tr-cbody{display:none;background:#fff;color:var(--ink);padding:12px 15px;font-size:13px;border-top:3px solid rgba(0,0,0,.08)}
.tr-cc.open .tr-cbody{display:block}
.tr-cbody b{color:var(--blue)}
.tr-cbody ul{margin:4px 0 10px 17px;padding:0}
.tr-cbody li{margin-bottom:3px}
.tr-sec{font-family:'MarkerFelt',cursive;font-size:17px;color:var(--blue);margin:22px 0 11px;display:flex;align-items:center;gap:9px}
.tr-sec .n{background:var(--blue);color:#fff;border-radius:12px;font-size:12px;padding:2px 10px}
.tr-none .tr-sec .n{background:var(--red)}
.tr-dim{opacity:.55;font-size:12px}
"""

EDITS.append((
    "/* ── TRAINING TAB",  # sentinel — must NOT already exist
    None, None))  # placeholder, replaced below

EDITS = []  # reset; sentinel handled separately

EDITS.append((
    """  <!-- TRAINING TAB -->
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
  </div>""",
    """  <!-- TRAINING TAB -->
  <div id="tab-training" style="display:none">
    <div style="padding:0 24px 6px">
      <input id="tr-search" class="filter-select" type="text" placeholder="🔍  Search coaches by name…" style="width:100%;margin-bottom:12px">
      <div class="tr-pills" id="tr-pills"></div>
    </div>
    <div id="training-content"><div class="loading"><div class="spinner"></div><p>Loading…</p></div></div>
  </div>""",
    "panel: swap dropdown for pill row"))

# ── 2. replace renderTraining wholesale ──────────────────────────────────────
NEW_RENDER = r'''function renderTraining() {
  const el=document.getElementById('training-content');
  if(!el) return;
  const qF=((document.getElementById('tr-search')||{}).value||'').toLowerCase().trim();
  const all=buildTraining();

  // pills (counts are pre-search, post-nothing — the full roster per state)
  const STATES=['VIC','NSW','QLD','SA','WA'];
  const counts={}; STATES.forEach(s=>counts[s]=all.filter(c=>(c.state||'')===s).length);
  const pw=document.getElementById('tr-pills');
  if(pw){
    pw.innerHTML=`<div class="tr-pill ${TR_STATE==='ALL'?'on':''}" data-st="ALL">All States</div>`+
      STATES.map(s=>`<div class="tr-pill ${TR_STATE===s?'on':''}" data-st="${s}">${s}: ${counts[s]}</div>`).join('');
    pw.querySelectorAll('.tr-pill').forEach(p=>p.onclick=()=>{TR_STATE=p.dataset.st;renderTraining();});
  }

  let list=all;
  if(TR_STATE!=='ALL') list=list.filter(c=>(c.state||'')===TR_STATE);
  if(qF) list=list.filter(c=>(c.fullName||'').toLowerCase().includes(qF));

  const has=c=>c.academy.length||c.testing.length||c.completed.length;
  const abc=(a,b)=>(a.fullName||'').localeCompare(b.fullName||'');
  const started=list.filter(has).sort(abc);
  const none=list.filter(c=>!has(c)).sort(abc);

  const fdate=t=>t?new Date(Number(t)).toLocaleDateString('en-AU',{day:'2-digit',month:'2-digit',year:'numeric'}):'';
  const mmss=s=>`${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`;
  const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));

  const card=(c,i,pfx)=>{
    const st=STATES.includes(c.state)?c.state:'none';
    const meta=has(c)
      ? `${c.state||'—'} · ${c.academy.length} academy · ${c.completed.length}/2 modules`
      : `${c.state||'—'} · no training`;
    const cats={}; c.academy.forEach(a=>{(cats[a.cat]=cats[a.cat]||[]).push(a);});
    let body='';
    if(Object.keys(cats).length){
      Object.entries(cats).forEach(([cat,vids])=>{
        body+=`<b>${esc(cat)}</b><ul>`;
        vids.sort((a,b)=>b.date-a.date).forEach(v=>{body+=`<li>${esc(v.name)} <span class="tr-dim">${fdate(v.date)}</span></li>`;});
        body+=`</ul>`;
      });
    } else { body+=`<div class="tr-dim" style="margin-bottom:8px">No Academy videos watched</div>`; }
    if(c.testing.length){
      body+=`<b>Medal testing</b><ul>`;
      c.testing.sort((a,b)=>b.date-a.date).forEach(t=>{
        const fin=c.completed.some(x=>x===t.name);
        body+=`<li>${esc(t.name)} — watched ${mmss(t.secs)}${t.unlocked?', questions unlocked':''}`+
              `${fin?' <b style="color:#3d8b2f">✓ completed</b>':''} <span class="tr-dim">${fdate(t.date)}</span></li>`;
      });
      body+=`</ul>`;
    } else { body+=`<div class="tr-dim">No medal testing started</div>`; }
    if(c.quizTotal) body+=`<div style="margin-top:6px"><b>Quiz</b> ${c.quizRight}/${c.quizTotal} correct</div>`;
    const id=`${pfx}-${i}`;
    return `<div class="tr-cc st-${st}" id="trc-${id}">
      <div class="tr-cn" data-tr="${id}"><span class="tr-caret">&#9656;</span>${esc(c.fullName)}</div>
      <div class="tr-cmeta" data-tr="${id}">${esc(meta)}</div>
      <div class="tr-cbody">${body}</div>
    </div>`;
  };

  let h=`<div style="padding:0 24px 24px">
    <div class="stats-row" style="margin-bottom:4px">
      <div class="stat-card"><div class="stat-num">${all.filter(c=>c.academy.length).length}</div><div class="stat-lbl">opened Coach Academy</div></div>
      <div class="stat-card"><div class="stat-num">${all.filter(c=>c.completed.length).length}</div><div class="stat-lbl">completed medal testing</div></div>
      <div class="stat-card"><div class="stat-num">${all.filter(c=>!has(c)).length}</div><div class="stat-lbl">no training on record</div></div>
      <div class="stat-card"><div class="stat-num">${all.length}</div><div class="stat-lbl">active coaches</div></div>
    </div>`;

  h+=`<div class="tr-sec">Started training <span class="n">${started.length}</span></div>`;
  h+= started.length ? `<div class="tr-grid">${started.map((c,i)=>card(c,i,'s')).join('')}</div>`
                     : `<div class="tr-dim" style="margin-bottom:8px">None in this view</div>`;

  h+=`<div class="tr-none"><div class="tr-sec">No training on record <span class="n">${none.length}</span></div></div>`;
  h+= none.length ? `<div class="tr-grid">${none.map((c,i)=>card(c,i,'n')).join('')}</div>`
                  : `<div class="tr-dim">None in this view</div>`;

  h+=`</div>`;
  el.innerHTML=h;

  el.querySelectorAll('[data-tr]').forEach(n=>n.onclick=()=>{
    const c=document.getElementById('trc-'+n.dataset.tr);
    if(c) c.classList.toggle('open');
  });
}'''

EDITS.append(("__RENDER__", NEW_RENDER, "replace renderTraining"))

# ── 3. module-scope state var ────────────────────────────────────────────────
EDITS.append((
    "// ── TRAINING TAB ──────────────────────────────────────────────────────────────\nfunction buildTraining() {",
    "// ── TRAINING TAB ──────────────────────────────────────────────────────────────\nlet TR_STATE='ALL';\nfunction buildTraining() {",
    "add TR_STATE module var"))

# ── 4. filter wiring — tr-state select no longer exists ──────────────────────
EDITS.append((
    """['tr-search','tr-state'].forEach(id=>{
  const e=document.getElementById(id);
  if(e) e.addEventListener('input',()=>{ if(COACHES) renderTraining(); });
});""",
    """['tr-search'].forEach(id=>{
  const e=document.getElementById(id);
  if(e) e.addEventListener('input',()=>{ if(COACHES) renderTraining(); });
});""",
    "drop tr-state from filter wiring"))


def main():
    if not os.path.exists(FILE):
        sys.exit(f"ERROR: {FILE} not found. Run from ~/Command-Centre.")

    src = open(FILE, encoding="utf-8").read()
    original = src
    print(f"Read {FILE}: {len(src):,} chars\n")

    if ".tr-pill{" in src:
        sys.exit("ABORT: this file already has the restyled Training tab.")

    # --- replace renderTraining by regex (function body is large) ---
    m = re.search(r"function renderTraining\(\) \{.*?\n\}\n", src, re.S)
    if not m:
        sys.exit("ABORT: could not locate renderTraining() to replace.")
    print(f"  OK  located renderTraining ({len(m.group(0)):,} chars)")
    src = src[:m.start()] + NEW_RENDER + "\n" + src[m.end():]

    # --- string anchors ---
    for old, new, label in EDITS:
        if old == "__RENDER__":
            continue
        n = src.count(old)
        if n != 1:
            print(f"\nABORT — anchor matched {n} times: {label}")
            sys.exit(1)
        src = src.replace(old, new, 1)
        print(f"  OK  {label}")

    # --- inject CSS before </style> (last one before the body) ---
    idx = src.find("</style>")
    if idx == -1:
        sys.exit("ABORT: no </style> found.")
    src = src[:idx] + CSS + src[idx:]
    print("  OK  inject Training CSS")

    print("\nVerification:")
    gates = [
        ("pill CSS present", ".tr-pill{" in src),
        ("state colours present", src.count(".tr-cc.st-") >= 6),
        ("card grid present", ".tr-grid{" in src),
        ("renderTraining defined once", src.count("function renderTraining()") == 1),
        ("TR_STATE declared", "let TR_STATE='ALL';" in src),
        ("pill container in markup", src.count('id="tr-pills"') == 1),
        ("old select removed", 'id="tr-state"' not in src),
        ("buildTraining intact", src.count("function buildTraining()") == 1),
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
    print("\nNow: hard-refresh, open Training, then commit.")


if __name__ == "__main__":
    main()
