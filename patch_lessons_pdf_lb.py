#!/usr/bin/env python3
"""
patch_lessons_pdf.py — split Lesson Plans into PDF views + videos watched

Two distinct signals:
  * PDFs viewed   — coach-viewed-activity-tabs where tab == 'PDF'
                    (the lesson plan itself; what a coach opens to prepare)
  * Videos watched— watched-video (the activity demo videos)

Overview tab views are deliberately EXCLUDED for now. To include them later,
change LP_TABS in the generated code from ['PDF'] to ['PDF','OVERVIEW'].

IMPORTANT: coach-viewed-activity-tabs only has data from 29 Jun 2026 onward.
Earlier months will legitimately show zero PDFs. The tab says so rather than
implying nobody prepared.

coach-viewed-activity-tabs is already fetched eagerly (it feeds P6 and the ID
map), so this adds no new network cost.

Run from ~/Command-Centre:
    /usr/local/bin/python3 patch_lessons_pdf.py            # dry run
    /usr/local/bin/python3 patch_lessons_pdf.py --commit   # apply

Set FILE below to patch leaderboard.html instead.
"""

import sys, shutil, datetime, os

FILE = "leaderboard.html"
COMMIT = "--commit" in sys.argv

EDITS = []

# ── 1. buildLessons: collect PDF views alongside video views ─────────────────
OLD_BUILD = """function buildLessons(){
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
}"""

NEW_BUILD = r"""// Which activity-tab types count as a plan view. Add 'OVERVIEW' to include those.
const LP_TABS=['PDF'];
// coach-viewed-activity-tabs has no data before this date — used to caption
// periods where a zero is an absence of tracking, not an absence of prep.
const LP_PDF_FROM=new Date(2026,5,29).getTime();   // 29 Jun 2026

function buildLessons(){
  const {appMap,learnCats,learnSubs,learnActs,viewTabs}=RAW;
  const roster=(COACHES||[]).map(c=>({id:c.id,fullName:c.fullName,state:c.state}));
  const byCoach={}; roster.forEach(c=>{byCoach[c.id]={...c,views:[],pdfs:[],mapped:false};});
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

  // PDF plan views — these docs carry coachId directly, no map needed.
  (viewTabs||[]).forEach(v=>{
    if(!LP_TABS.includes(v.tab)) return;
    const t=byCoach[v.coachId]; if(!t) return;
    t.mapped=true;   // seen in the app, so trackable regardless of short-id map
    t.pdfs.push({
      date:v.date||0,
      prog:(v.categoryName||learnCats[v.categoryId]||'Other').trim(),
      week:(v.subCategoryName||'(unknown week)').trim()
    });
  });
  return Object.values(byCoach);
}"""

EDITS.append((OLD_BUILD, NEW_BUILD, "buildLessons: collect PDF views"))

# ── 2. per-coach period counts ───────────────────────────────────────────────
EDITS.append((
    "  const inR=d=>d>=R.from&&d<=R.to;\n"
    "  list.forEach(c=>{ c.inP=c.views.filter(v=>inR(v.date)); "
    "c.last=c.views.length?Math.max(...c.views.map(v=>v.date)):0; });",
    "  const inR=d=>d>=R.from&&d<=R.to;\n"
    "  list.forEach(c=>{\n"
    "    c.inP=c.views.filter(v=>inR(v.date));\n"
    "    c.inPdf=c.pdfs.filter(v=>inR(v.date));\n"
    "    const dates=c.views.map(v=>v.date).concat(c.pdfs.map(v=>v.date));\n"
    "    c.last=dates.length?Math.max(...dates):0;\n"
    "  });",
    "period counts: videos + PDFs"))

# ── 3. section membership — either signal counts ─────────────────────────────
EDITS.append((
    "  const watched = list.filter(c=>c.mapped&&c.inP.length).sort(abc);\n"
    "  const quiet   = list.filter(c=>c.mapped&&!c.inP.length&&c.views.length).sort(abc);\n"
    "  const never   = list.filter(c=>c.mapped&&!c.views.length).sort(abc);",
    "  const anyP=c=>c.inP.length||c.inPdf.length;\n"
    "  const anyEver=c=>c.views.length||c.pdfs.length;\n"
    "  const watched = list.filter(c=>c.mapped&&anyP(c)).sort(abc);\n"
    "  const quiet   = list.filter(c=>c.mapped&&!anyP(c)&&anyEver(c)).sort(abc);\n"
    "  const never   = list.filter(c=>c.mapped&&!anyEver(c)).sort(abc);",
    "sections: either signal counts as active"))

# ── 4. drill-down: PDF list ──────────────────────────────────────────────────
EDITS.append((
    "      body+=`<div class=\"tr-dim\" style=\"margin-top:4px\">Green dot = viewed in the selected period. "
    "Lifetime total ${c.views.length} views.</div>`;\n"
    "    } else if(!c.mapped){",
    "      body+=`<div class=\"tr-dim\" style=\"margin-top:4px\">Green dot = viewed in the selected period. "
    "Lifetime total ${c.views.length} video views.</div>`;\n"
    "    } else if(!c.pdfs.length&&!c.mapped){",
    "drilldown: reword video footer"))

EDITS.append((
    "    const id=`${pfx}-${i}`;\n"
    "    return `<div class=\"tr-cc st-${st}\" id=\"lpc-${id}\">",
    """    // PDF plan views
    if(c.pdfs.length){
      const pw={};
      c.pdfs.forEach(p=>{ const k=`${p.prog} · ${p.week}`; (pw[k]=pw[k]||[]).push(p); });
      body+=`<div style="margin-top:10px"><b>Lesson plan PDFs opened</b><ul>`;
      Object.entries(pw)
        .sort((a,b)=>Math.max(...b[1].map(v=>v.date))-Math.max(...a[1].map(v=>v.date)))
        .slice(0,12)
        .forEach(([k,vs])=>{
          const lastP=Math.max(...vs.map(v=>v.date));
          body+=`<li>${esc(k)} <span class="tr-dim">${vs.length}×, ${fdate(lastP)}</span>`+
                `${vs.some(v=>inR(v.date))?' <b style="color:#3d8b2f">•</b>':''}</li>`;
        });
      const np=Object.keys(pw).length;
      if(np>12) body+=`<li class="tr-dim">…and ${np-12} more</li>`;
      body+=`</ul></div>`;
    } else if(c.mapped){
      body+=`<div class="tr-dim" style="margin-top:10px">No lesson plan PDFs opened.</div>`;
    }
    if(R.from<LP_PDF_FROM){
      body+=`<div class="tr-dim" style="margin-top:6px">PDF tracking only began 29 Jun 2026, so PDF counts before then are absent by default, not zero.</div>`;
    }
    const id=`${pfx}-${i}`;
    return `<div class="tr-cc st-${st}" id="lpc-${id}">""",
    "drilldown: add PDF section"))

# ── 5. card face meta ────────────────────────────────────────────────────────
EDITS.append((
    "  h+=sec(`Watched in ${plabel}`, watched, 'w',\n"
    "        c=>`${c.state||'—'} · ${c.inP.length} view${c.inP.length===1?'':'s'} · last ${fdate(c.last)}`);",
    "  h+=sec(`Active in ${plabel}`, watched, 'w',\n"
    "        c=>`${c.state||'—'} · ${c.inP.length} video${c.inP.length===1?'':'s'} · "
    "${c.inPdf.length} PDF${c.inPdf.length===1?'':'s'} · last ${fdate(c.last)}`);",
    "card face: videos + PDFs"))

EDITS.append((
    "  h+=sec(`Nothing in ${plabel}`, quiet, 'q',\n"
    "        c=>`${c.state||'—'} · last watched ${fdate(c.last)} · ${c.views.length} lifetime`, true);",
    "  h+=sec(`Nothing in ${plabel}`, quiet, 'q',\n"
    "        c=>`${c.state||'—'} · last active ${fdate(c.last)} · "
    "${c.views.length} videos, ${c.pdfs.length} PDFs lifetime`, true);",
    "card face: quiet section"))

EDITS.append((
    "  h+=sec(`No lesson plan activity on record`, never, 'n',\n"
    "        c=>`${c.state||'—'} · never watched`, true);",
    "  h+=sec(`No lesson plan activity on record`, never, 'n',\n"
    "        c=>`${c.state||'—'} · no videos or PDFs`);",
    "card face: never section"))

# ── 6. stat cards ────────────────────────────────────────────────────────────
OLD_STATS = """      <div class="stat-card"><div class="stat-num">${totalIn}</div><div class="stat-lbl">watched ${plabel}</div></div>
      <div class="stat-card"><div class="stat-num">${all.filter(c=>c.mapped&&!c.views.some(v=>inR(v.date))).length}</div><div class="stat-lbl">nothing in ${plabel}</div></div>
      <div class="stat-card"><div class="stat-num">${(LP_VIEWS||[]).filter(v=>inR(v.date||0)).length}</div><div class="stat-lbl">total views in ${plabel}</div></div>
      <div class="stat-card"><div class="stat-num">${mappedN}/${all.length}</div><div class="stat-lbl">coaches trackable</div></div>"""

NEW_STATS = """      <div class="stat-card"><div class="stat-num">${totalIn}</div><div class="stat-lbl">active in ${plabel}</div></div>
      <div class="stat-card"><div class="stat-num">${all.filter(c=>c.mapped&&!(c.views.some(v=>inR(v.date))||c.pdfs.some(v=>inR(v.date)))).length}</div><div class="stat-lbl">nothing in ${plabel}</div></div>
      <div class="stat-card"><div class="stat-num">${(LP_VIEWS||[]).filter(v=>inR(v.date||0)).length}</div><div class="stat-lbl">videos watched</div></div>
      <div class="stat-card"><div class="stat-num">${((RAW.viewTabs)||[]).filter(v=>LP_TABS.includes(v.tab)&&inR(v.date||0)).length}</div><div class="stat-lbl">PDFs opened</div></div>
      <div class="stat-card"><div class="stat-num">${mappedN}/${all.length}</div><div class="stat-lbl">coaches trackable</div></div>"""

EDITS.append((OLD_STATS, NEW_STATS, "stat cards: split videos / PDFs"))

EDITS.append((
    "  const totalIn=all.filter(c=>c.mapped&&c.views.some(v=>inR(v.date))).length;",
    "  const totalIn=all.filter(c=>c.mapped&&(c.views.some(v=>inR(v.date))||c.pdfs.some(v=>inR(v.date)))).length;",
    "headline: count either signal"))

# ── 7. footnote about PDF tracking start ─────────────────────────────────────
EDITS.append((
    '  h+=`<p class="tr-dim" style="margin-top:14px;max-width:760px">Coaches under "can\'t verify"',
    '  if(R.from<LP_PDF_FROM){\n'
    '    h+=`<p class="tr-dim" style="margin-top:12px;max-width:760px"><b>Note:</b> lesson plan PDF tracking '
    'only began on 29 Jun 2026. For periods before that, a zero PDF count means the data was not being '
    'recorded yet — not that coaches did not open their plans.</p>`;\n'
    '  }\n'
    '  h+=`<p class="tr-dim" style="margin-top:14px;max-width:760px">Coaches under "can\'t verify"',
    "footnote: PDF tracking start date"))


def main():
    if not os.path.exists(FILE):
        sys.exit(f"ERROR: {FILE} not found. Run from ~/Command-Centre.")
    src = open(FILE, encoding="utf-8").read()
    original = src
    print(f"Read {FILE}: {len(src):,} chars\n")

    if "LP_TABS" in src:
        sys.exit("ABORT: this file already has the PDF/video split.")
    if 'id="lp-weeks"' not in src:
        sys.exit("ABORT: run patch_lessonplans.py and patch_lessons_months.py first.")

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
        ("LP_TABS defined", src.count("const LP_TABS=['PDF'];") == 1),
        ("OVERVIEW excluded", "'OVERVIEW'" not in src.split("const LP_TABS")[1][:40]),
        ("pdfs collected", "t.pdfs.push({" in src),
        ("PDF tracking date", "LP_PDF_FROM" in src),
        ("card face split", "PDF${c.inPdf.length===1?'':'s'}" in src),
        ("stat card for PDFs", "PDFs opened" in src),
        ("renderLessons intact", src.count("function renderLessons()") == 1),
        ("buildLessons intact", src.count("function buildLessons()") == 1),
        ("month selector intact", src.count("function lpWeeksOf(") == 1),
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
