#!/usr/bin/env python3
"""
patch_lessons_months.py — month + week period selector for the Lesson Plans tab

Replaces the four fixed period pills (week / month / ytd / all) with:

  Row 1:  Jan  Feb  Mar ... (current calendar year, up to this month)  |  YTD  All time
  Row 2:  appears when a month is selected — that month's weeks,
          labelled "Mon 27 Jul – Sun 2 Aug". Click to narrow to one week,
          click again to go back to the whole month.

Weeks run Monday to Sunday and are clipped to the month at both ends, so the
first and last week of a month show only the days that fall inside it.

Only touches the Lesson Plans period logic. buildLessons() and the data layer
are unchanged.

Run from ~/Command-Centre:
    /usr/local/bin/python3 patch_lessons_months.py            # dry run
    /usr/local/bin/python3 patch_lessons_months.py --commit   # apply

Set FILE below to patch leaderboard.html instead.
"""

import sys, shutil, datetime, os

FILE = "leaderboard.html"
COMMIT = "--commit" in sys.argv

EDITS = []

# ── 1. markup: second pill row for weeks ─────────────────────────────────────
EDITS.append((
    '      <div class="tr-pills" id="lp-periods"></div>\n'
    '      <div class="tr-pills" id="lp-pills"></div>',
    '      <div class="tr-pills" id="lp-periods"></div>\n'
    '      <div class="tr-pills lp-weeks" id="lp-weeks"></div>\n'
    '      <div class="tr-pills" id="lp-pills"></div>',
    "markup: add week pill row"))

# ── 2. state vars + period helpers ───────────────────────────────────────────
OLD_VARS = """let LP_STATE='ALL', LP_PERIOD='month', LP_VIEWS=null, LP_LOADING=false;

const LP_PERIODS=[['week','This week'],['month','This month'],['ytd','Year to date'],['all','All time']];

function lpPeriodStart(p){
  const now=new Date();
  if(p==='week'){ const d=new Date(now); const dow=(d.getDay()+6)%7; // Monday = 0
    d.setDate(d.getDate()-dow); d.setHours(0,0,0,0); return d.getTime(); }
  if(p==='month') return new Date(now.getFullYear(),now.getMonth(),1).getTime();
  if(p==='ytd')   return new Date(now.getFullYear(),0,1).getTime();
  return 0;
}"""

NEW_VARS = r"""let LP_STATE='ALL', LP_VIEWS=null, LP_LOADING=false;
// LP_MODE: 'month' | 'ytd' | 'all'.  LP_MONTH = 0-11 when mode is 'month'.
// LP_WEEK = index into the selected month's weeks, or null for the whole month.
let LP_MODE='month', LP_MONTH=new Date().getMonth(), LP_WEEK=null;

const LP_MON=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const LP_DAY=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];

// Monday-start weeks, clipped to the month at both ends.
function lpWeeksOf(year,month){
  const first=new Date(year,month,1), last=new Date(year,month+1,0);
  const out=[]; let cur=new Date(first);
  while(cur<=last){
    const dow=(cur.getDay()+6)%7;                 // Mon=0
    const wStart=new Date(cur); wStart.setDate(cur.getDate()-dow);
    const wEnd=new Date(wStart); wEnd.setDate(wStart.getDate()+6);
    const s=wStart<first?new Date(first):wStart;
    const e=wEnd>last?new Date(last):wEnd;
    s.setHours(0,0,0,0); e.setHours(23,59,59,999);
    out.push({start:s.getTime(),end:e.getTime(),
      label:`${LP_DAY[s.getDay()]} ${s.getDate()} ${LP_MON[s.getMonth()]} – ${LP_DAY[e.getDay()]} ${e.getDate()} ${LP_MON[e.getMonth()]}`});
    cur=new Date(wEnd); cur.setDate(cur.getDate()+1);
  }
  return out;
}

// Returns {from,to,label} for whatever is currently selected.
function lpRange(){
  const now=new Date(), y=now.getFullYear();
  if(LP_MODE==='all') return {from:0,to:Infinity,label:'all time'};
  if(LP_MODE==='ytd') return {from:new Date(y,0,1).getTime(),to:Infinity,label:'year to date'};
  const wks=lpWeeksOf(y,LP_MONTH);
  if(LP_WEEK!=null && wks[LP_WEEK]){
    const w=wks[LP_WEEK];
    return {from:w.start,to:w.end,label:w.label.toLowerCase()};
  }
  return {from:new Date(y,LP_MONTH,1).getTime(),
          to:new Date(y,LP_MONTH+1,0,23,59,59,999).getTime(),
          label:`${LP_MON[LP_MONTH]} ${y}`};
}"""

EDITS.append((OLD_VARS, NEW_VARS, "period model: months + weeks"))

# ── 3. pill rendering ────────────────────────────────────────────────────────
OLD_PILLS = """  const qF=((document.getElementById('lp-search')||{}).value||'').toLowerCase().trim();
  const all=buildLessons();
  const cut=lpPeriodStart(LP_PERIOD);

  // period pills
  const pp=document.getElementById('lp-periods');
  if(pp){
    pp.innerHTML=LP_PERIODS.map(([k,lbl])=>
      `<div class="tr-pill ${LP_PERIOD===k?'on':''}" data-st="ALL" data-p="${k}">${lbl}</div>`).join('');
    pp.querySelectorAll('.tr-pill').forEach(p=>p.onclick=()=>{LP_PERIOD=p.dataset.p;renderLessons();});
  }"""

NEW_PILLS = r"""  const qF=((document.getElementById('lp-search')||{}).value||'').toLowerCase().trim();
  const all=buildLessons();
  const R=lpRange();
  const now=new Date(), yr=now.getFullYear();

  // month pills (current calendar year, up to this month) + YTD + All time
  const pp=document.getElementById('lp-periods');
  if(pp){
    let ph='';
    for(let m=0;m<=now.getMonth();m++){
      const on=(LP_MODE==='month'&&LP_MONTH===m)?'on':'';
      ph+=`<div class="tr-pill ${on}" data-st="ALL" data-m="${m}">${LP_MON[m]}</div>`;
    }
    ph+=`<span style="width:10px"></span>`;
    ph+=`<div class="tr-pill ${LP_MODE==='ytd'?'on':''}" data-st="ALL" data-mode="ytd">Year to date</div>`;
    ph+=`<div class="tr-pill ${LP_MODE==='all'?'on':''}" data-st="ALL" data-mode="all">All time</div>`;
    pp.innerHTML=ph;
    pp.querySelectorAll('.tr-pill').forEach(p=>p.onclick=()=>{
      if(p.dataset.mode){ LP_MODE=p.dataset.mode; LP_WEEK=null; }
      else { const m=+p.dataset.m;
             if(LP_MODE==='month'&&LP_MONTH===m){ LP_WEEK=null; }   // re-click = whole month
             LP_MODE='month'; LP_MONTH=m; LP_WEEK=null; }
      renderLessons();
    });
  }

  // week pills — only when a month is selected
  const wp=document.getElementById('lp-weeks');
  if(wp){
    if(LP_MODE==='month'){
      const wks=lpWeeksOf(yr,LP_MONTH);
      wp.style.display='flex';
      wp.innerHTML=`<div class="tr-pill lp-wk ${LP_WEEK==null?'on':''}" data-st="ALL" data-w="all">Whole month</div>`+
        wks.map((w,i)=>`<div class="tr-pill lp-wk ${LP_WEEK===i?'on':''}" data-st="ALL" data-w="${i}">${w.label}</div>`).join('');
      wp.querySelectorAll('.tr-pill').forEach(p=>p.onclick=()=>{
        LP_WEEK = p.dataset.w==='all' ? null : +p.dataset.w;
        renderLessons();
      });
    } else { wp.style.display='none'; wp.innerHTML=''; }
  }"""

EDITS.append((OLD_PILLS, NEW_PILLS, "render: month + week pills"))

# ── 4. swap cut-off comparisons for the range ────────────────────────────────
EDITS.append((
    "  list.forEach(c=>{ c.inP=c.views.filter(v=>v.date>=cut); "
    "c.last=c.views.length?Math.max(...c.views.map(v=>v.date)):0; });",
    "  const inR=d=>d>=R.from&&d<=R.to;\n"
    "  list.forEach(c=>{ c.inP=c.views.filter(v=>inR(v.date)); "
    "c.last=c.views.length?Math.max(...c.views.map(v=>v.date)):0; });",
    "coach filter: use range not cutoff"))

EDITS.append((
    "            const inP=vs.some(v=>v.date>=cut);",
    "            const inP=vs.some(v=>inR(v.date));",
    "drilldown dots: use range"))

EDITS.append((
    "  const plabel=(LP_PERIODS.find(p=>p[0]===LP_PERIOD)||['','' ])[1].toLowerCase();\n"
    "  const totalIn=all.filter(c=>c.mapped&&c.views.some(v=>v.date>=cut)).length;",
    "  const plabel=R.label;\n"
    "  const totalIn=all.filter(c=>c.mapped&&c.views.some(v=>inR(v.date))).length;",
    "headline: use range label"))

EDITS.append((
    "      <div class=\"stat-card\"><div class=\"stat-num\">"
    "${all.filter(c=>c.mapped&&!c.views.some(v=>v.date>=cut)).length}</div>"
    "<div class=\"stat-lbl\">nothing ${plabel}</div></div>\n"
    "      <div class=\"stat-card\"><div class=\"stat-num\">"
    "${(LP_VIEWS||[]).filter(v=>(v.date||0)>=cut).length}</div>"
    "<div class=\"stat-lbl\">total views ${plabel}</div></div>",
    "      <div class=\"stat-card\"><div class=\"stat-num\">"
    "${all.filter(c=>c.mapped&&!c.views.some(v=>inR(v.date))).length}</div>"
    "<div class=\"stat-lbl\">nothing in ${plabel}</div></div>\n"
    "      <div class=\"stat-card\"><div class=\"stat-num\">"
    "${(LP_VIEWS||[]).filter(v=>inR(v.date||0)).length}</div>"
    "<div class=\"stat-lbl\">total views in ${plabel}</div></div>",
    "stat cards: use range"))

EDITS.append((
    "  h+=sec(`Watched ${plabel}`, watched, 'w',",
    "  h+=sec(`Watched in ${plabel}`, watched, 'w',",
    "section label: watched"))

EDITS.append((
    "  h+=sec(`Nothing ${plabel}`, quiet, 'q',",
    "  h+=sec(`Nothing in ${plabel}`, quiet, 'q',",
    "section label: nothing"))

# ── 5. CSS for the week row ──────────────────────────────────────────────────
CSS = """
.lp-weeks{margin-top:-4px;margin-bottom:12px;padding-left:2px}
.tr-pill.lp-wk{font-size:11px;padding:5px 12px;border-color:#cfe0ea}
.tr-pill.lp-wk.on{background:var(--blue);border-color:var(--blue);color:#fff}
"""


def main():
    if not os.path.exists(FILE):
        sys.exit(f"ERROR: {FILE} not found. Run from ~/Command-Centre.")
    src = open(FILE, encoding="utf-8").read()
    original = src
    print(f"Read {FILE}: {len(src):,} chars\n")

    if 'id="lp-weeks"' in src:
        sys.exit("ABORT: this file already has the month/week selector.")
    if 'id="tab-lessons"' not in src:
        sys.exit("ABORT: Lesson Plans tab not found. Run patch_lessonplans.py first.")

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

    idx = src.find("</style>")
    if idx == -1:
        sys.exit("ABORT: no </style> found.")
    src = src[:idx] + CSS + src[idx:]
    print("  OK  inject week-pill CSS")

    print("\nVerification:")
    gates = [
        ("week row in markup", src.count('id="lp-weeks"') == 1),
        ("lpWeeksOf defined", src.count("function lpWeeksOf(") == 1),
        ("lpRange defined", src.count("function lpRange(") == 1),
        ("old lpPeriodStart gone", "function lpPeriodStart(" not in src),
        ("old LP_PERIODS gone", "LP_PERIODS" not in src),
        ("no stale cut refs", "v.date>=cut" not in src),
        ("week CSS present", ".tr-pill.lp-wk{" in src),
        ("renderLessons intact", src.count("function renderLessons()") == 1),
        ("buildLessons intact", src.count("function buildLessons()") == 1),
        ("training tab intact", src.count("function renderTraining()") == 1),
        ("auth still wired", src.count("onAuthStateChanged") >= 1),
        ("no placeholder apiKey", "PASTE_YOUR_API_KEY_HERE" not in src),
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
