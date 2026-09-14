#!/usr/bin/env python3
"""
patch_lessons_detail.py — period-filtered drilldown with named videos

Two changes to the Lesson Plans card body:

1. FILTER TO THE SELECTED PERIOD.
   Previously the drilldown showed lifetime history with a green dot marking
   the selected period, which made the list look identical whichever month or
   week you clicked. Now it shows only what falls inside the selection.

2. NAME THE VIDEOS.
   Previously rows were grouped to the week and showed a view count, so the
   actual video was invisible. Now each video is its own row:

       Program · Sports
          AFL Week 1 — Introduction                    21/07/2026
          AFL Week 1 — Warm Up Follow the Leader       21/07/2026

   Repeat views of the same video collapse to "3×" with the latest date.
   PDFs keep week-level grouping (there is no video name to add) and are
   filtered to the period the same way.

The card face keeps LIFETIME totals and is relabelled "last active" so it
reads clearly against a period view.

Run from ~/Command-Centre:
    /usr/local/bin/python3 patch_lessons_detail.py            # dry run
    /usr/local/bin/python3 patch_lessons_detail.py --commit   # apply

Set FILE below to patch leaderboard.html instead.
"""

import sys, shutil, datetime, os

FILE = "coaches.html"
COMMIT = "--commit" in sys.argv

EDITS = []

# ── 1. video pane: filter to period, group program -> week -> video ──────────
OLD_VID = """    const byProg={};
    c.views.forEach(v=>{ (byProg[v.prog]=byProg[v.prog]||{})[v.week]=(byProg[v.prog][v.week]||[]); byProg[v.prog][v.week].push(v); });
    let vbody='';
    const progs=Object.keys(byProg).sort();
    if(progs.length){
      progs.forEach(p=>{
        const wks=byProg[p];
        const tot=Object.values(wks).reduce((a,b)=>a+b.length,0);
        vbody+=`<b>${esc(p)}</b> <span class="tr-dim">${tot} view${tot===1?'':'s'}</span><ul>`;
        Object.entries(wks)
          .sort((a,b)=>Math.max(...b[1].map(v=>v.date))-Math.max(...a[1].map(v=>v.date)))
          .slice(0,12)
          .forEach(([wk,vs])=>{
            const lastW=Math.max(...vs.map(v=>v.date));
            const inP=vs.some(v=>inR(v.date));
            vbody+=`<li>${esc(wk)} <span class="tr-dim">${vs.length}×, ${fdate(lastW)}</span>`+
                  `${inP?' <b style="color:#3d8b2f">•</b>':''}</li>`;
          });
        const nw=Object.keys(wks).length;
        if(nw>12) vbody+=`<li class="tr-dim">…and ${nw-12} more weeks</li>`;
        vbody+=`</ul>`;
      });
      vbody+=`<div class="tr-dim" style="margin-top:4px">Green dot = viewed in the selected period. Lifetime total ${c.views.length} video views.</div>`;
    } else if(!c.pdfs.length&&!c.mapped){
      vbody=`<div class="tr-dim">This coach has no app ID on record yet, so their activity can't be matched. It isn't evidence they haven't watched anything — the map fills in as they use the app.</div>`;
    } else {
      vbody=`<div class="tr-dim">No lesson plan videos watched.</div>`;
    }"""

NEW_VID = r"""    // videos in the selected period only, grouped program -> week -> video
    const pv=c.views.filter(v=>inR(v.date));
    const byProg={};
    pv.forEach(v=>{
      const wk=(byProg[v.prog]=byProg[v.prog]||{});
      const vids=(wk[v.week]=wk[v.week]||{});
      const k=v.name||'(video)';
      if(!vids[k]) vids[k]={n:0,last:0};
      vids[k].n++; if(v.date>vids[k].last) vids[k].last=v.date;
    });
    let vbody='';
    const progs=Object.keys(byProg).sort();
    if(progs.length){
      progs.forEach(p=>{
        const wks=byProg[p];
        const tot=Object.values(wks).reduce((a,w)=>a+Object.values(w).reduce((x,y)=>x+y.n,0),0);
        vbody+=`<div class="lp-prog">Program · ${esc(p)} <span class="tr-dim">${tot} view${tot===1?'':'s'}</span></div><ul>`;
        Object.entries(wks)
          .sort((a,b)=>Math.max(...Object.values(b[1]).map(v=>v.last))-Math.max(...Object.values(a[1]).map(v=>v.last)))
          .forEach(([wk,vids])=>{
            Object.entries(vids)
              .sort((a,b)=>b[1].last-a[1].last)
              .forEach(([nme,d])=>{
                vbody+=`<li><span class="lp-wkn">${esc(wk)}</span> — ${esc(nme)}`+
                       `<span class="tr-dim"> ${d.n>1?d.n+'×, ':''}${fdate(d.last)}</span></li>`;
              });
          });
        vbody+=`</ul>`;
      });
      vbody+=`<div class="tr-dim" style="margin-top:4px">${pv.length} view${pv.length===1?'':'s'} in ${esc(R.label)}. Lifetime total ${c.views.length}.</div>`;
    } else if(!c.pdfs.length&&!c.mapped){
      vbody=`<div class="tr-dim">This coach has no app ID on record yet, so their activity can't be matched. It isn't evidence they haven't watched anything — the map fills in as they use the app.</div>`;
    } else {
      vbody=`<div class="tr-dim">No videos watched in ${esc(R.label)}.`+
            `${c.views.length?` Lifetime total ${c.views.length} views.`:''}</div>`;
    }"""

EDITS.append((OLD_VID, NEW_VID, "video pane: period filter + named videos"))

# ── 2. PDF pane: filter to period ────────────────────────────────────────────
OLD_PDF = """    let pbody='';
    if(c.pdfs.length){
      const pw={};
      c.pdfs.forEach(p=>{ const k=`${p.prog} · ${p.week}`; (pw[k]=pw[k]||[]).push(p); });
      pbody+=`<ul>`;
      Object.entries(pw)
        .sort((a,b)=>Math.max(...b[1].map(v=>v.date))-Math.max(...a[1].map(v=>v.date)))
        .slice(0,12)
        .forEach(([k,vs])=>{
          const lastP=Math.max(...vs.map(v=>v.date));
          pbody+=`<li>${esc(k)} <span class="tr-dim">${vs.length}×, ${fdate(lastP)}</span>`+
                `${vs.some(v=>inR(v.date))?' <b style="color:#3d8b2f">•</b>':''}</li>`;
        });
      const np=Object.keys(pw).length;
      if(np>12) pbody+=`<li class="tr-dim">…and ${np-12} more</li>`;
      pbody+=`</ul>`;
      pbody+=`<div class="tr-dim">Green dot = opened in the selected period. Lifetime total ${c.pdfs.length} PDF opens.</div>`;
    } else {
      pbody+=`<div class="tr-dim">No lesson plan PDFs opened.</div>`;
    }"""

NEW_PDF = r"""    let pbody='';
    const pp2=c.pdfs.filter(v=>inR(v.date));
    if(pp2.length){
      const pgrp={};
      pp2.forEach(p=>{ (pgrp[p.prog]=pgrp[p.prog]||{}); const w=pgrp[p.prog];
        if(!w[p.week]) w[p.week]={n:0,last:0};
        w[p.week].n++; if(p.date>w[p.week].last) w[p.week].last=p.date; });
      Object.keys(pgrp).sort().forEach(p=>{
        const wks=pgrp[p];
        const tot=Object.values(wks).reduce((a,b)=>a+b.n,0);
        pbody+=`<div class="lp-prog">Program · ${esc(p)} <span class="tr-dim">${tot} open${tot===1?'':'s'}</span></div><ul>`;
        Object.entries(wks).sort((a,b)=>b[1].last-a[1].last).forEach(([wk,d])=>{
          pbody+=`<li><span class="lp-wkn">${esc(wk)}</span>`+
                 `<span class="tr-dim"> ${d.n>1?d.n+'×, ':''}${fdate(d.last)}</span></li>`;
        });
        pbody+=`</ul>`;
      });
      pbody+=`<div class="tr-dim">${pp2.length} open${pp2.length===1?'':'s'} in ${esc(R.label)}. Lifetime total ${c.pdfs.length}.</div>`;
    } else {
      pbody+=`<div class="tr-dim">No lesson plan PDFs opened in ${esc(R.label)}.`+
             `${c.pdfs.length?` Lifetime total ${c.pdfs.length} opens.`:''}</div>`;
    }"""

EDITS.append((OLD_PDF, NEW_PDF, "PDF pane: period filter"))

# ── 3. card face: relabel the lifetime date ──────────────────────────────────
EDITS.append((
    "${c.inPdf.length} PDF${c.inPdf.length===1?'':'s'} · last ${fdate(c.last)}`);",
    "${c.inPdf.length} PDF${c.inPdf.length===1?'':'s'} · last active ${fdate(c.last)}`);",
    "card face: 'last active'"))

# ── 4. CSS ───────────────────────────────────────────────────────────────────
CSS = """
.lp-prog{font-family:'MarkerFelt',cursive;font-size:13px;color:var(--blue);margin:8px 0 2px;text-transform:uppercase;letter-spacing:.5px}
.lp-wkn{font-weight:700;color:var(--ink)}
.lp-pane li{margin-bottom:4px;line-height:1.35}
"""


def main():
    if not os.path.exists(FILE):
        sys.exit(f"ERROR: {FILE} not found. Run from ~/Command-Centre.")
    src = open(FILE, encoding="utf-8").read()
    original = src
    print(f"Read {FILE}: {len(src):,} chars\n")

    if ".lp-prog{" in src:
        sys.exit("ABORT: this file already has the detailed drilldown.")
    if ".lp-subtabs{" not in src:
        sys.exit("ABORT: run patch_lessons_subtabs.py first.")

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
    print("  OK  inject drilldown CSS")

    print("\nVerification:")
    gates = [
        ("period-filtered videos", "const pv=c.views.filter(v=>inR(v.date));" in src),
        ("period-filtered PDFs", "const pp2=c.pdfs.filter(v=>inR(v.date));" in src),
        ("video names rendered", "— ${esc(nme)}" in src),
        ("program headers", src.count("Program · ${esc(p)}") == 2),
        ("green-dot logic gone", "color:#3d8b2f" not in src.split("function renderLessons()")[1]),
        ("empty state names period", "No videos watched in ${esc(R.label)}" in src),
        ("last active label", "last active ${fdate(c.last)}" in src),
        ("drilldown CSS", ".lp-prog{" in src),
        ("sub-tabs intact", ".lp-subtabs{" in src),
        ("renderLessons intact", src.count("function renderLessons()") == 1),
        ("buildLessons intact", src.count("function buildLessons()") == 1),
        ("month selector intact", src.count("function lpWeeksOf(") == 1),
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
    print("\nNow: hard-refresh, pick a week, expand a coach.")


if __name__ == "__main__":
    main()
