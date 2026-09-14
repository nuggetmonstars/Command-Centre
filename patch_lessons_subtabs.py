#!/usr/bin/env python3
"""
patch_lessons_subtabs.py — Videos / PDFs sub-tabs inside each coach card

The expanded card currently stacks the video list and the PDF list one after
the other, which gets long for heavy users. This splits them into two panes
with a small tab strip at the top of the card body:

    [ Videos 12 ]  [ PDFs 5 ]

Counts shown are for the selected period. The pane that opens first is
whichever has activity in that period (Videos wins a tie); if neither does,
Videos opens with its lifetime history.

Purely a presentation change — buildLessons(), the period model and the
section logic are all untouched.

Run from ~/Command-Centre:
    /usr/local/bin/python3 patch_lessons_subtabs.py            # dry run
    /usr/local/bin/python3 patch_lessons_subtabs.py --commit   # apply

Set FILE below to patch leaderboard.html instead.
"""

import sys, shutil, datetime, os

FILE = "coaches.html"
COMMIT = "--commit" in sys.argv

EDITS = []

# ── 1. wrap the video list in its own pane ───────────────────────────────────
EDITS.append((
    "    let body='';\n"
    "    const progs=Object.keys(byProg).sort();",
    "    let vbody='';\n"
    "    const progs=Object.keys(byProg).sort();",
    "video pane: rename accumulator (open)"))

EDITS.append((
    "    if(progs.length){\n"
    "      progs.forEach(p=>{\n"
    "        const wks=byProg[p];\n"
    "        const tot=Object.values(wks).reduce((a,b)=>a+b.length,0);\n"
    "        body+=`<b>${esc(p)}</b> <span class=\"tr-dim\">${tot} view${tot===1?'':'s'}</span><ul>`;",
    "    if(progs.length){\n"
    "      progs.forEach(p=>{\n"
    "        const wks=byProg[p];\n"
    "        const tot=Object.values(wks).reduce((a,b)=>a+b.length,0);\n"
    "        vbody+=`<b>${esc(p)}</b> <span class=\"tr-dim\">${tot} view${tot===1?'':'s'}</span><ul>`;",
    "video pane: program header"))

EDITS.append((
    "            body+=`<li>${esc(wk)} <span class=\"tr-dim\">${vs.length}×, ${fdate(lastW)}</span>`+\n"
    "                  `${inP?' <b style=\"color:#3d8b2f\">•</b>':''}</li>`;",
    "            vbody+=`<li>${esc(wk)} <span class=\"tr-dim\">${vs.length}×, ${fdate(lastW)}</span>`+\n"
    "                  `${inP?' <b style=\"color:#3d8b2f\">•</b>':''}</li>`;",
    "video pane: week rows"))

EDITS.append((
    "        const nw=Object.keys(wks).length;\n"
    "        if(nw>12) body+=`<li class=\"tr-dim\">…and ${nw-12} more weeks</li>`;\n"
    "        body+=`</ul>`;\n"
    "      });",
    "        const nw=Object.keys(wks).length;\n"
    "        if(nw>12) vbody+=`<li class=\"tr-dim\">…and ${nw-12} more weeks</li>`;\n"
    "        vbody+=`</ul>`;\n"
    "      });",
    "video pane: week overflow"))

EDITS.append((
    "      body+=`<div class=\"tr-dim\" style=\"margin-top:4px\">Green dot = viewed in the selected period. "
    "Lifetime total ${c.views.length} video views.</div>`;\n"
    "    } else if(!c.pdfs.length&&!c.mapped){",
    "      vbody+=`<div class=\"tr-dim\" style=\"margin-top:4px\">Green dot = viewed in the selected period. "
    "Lifetime total ${c.views.length} video views.</div>`;\n"
    "    } else if(!c.pdfs.length&&!c.mapped){",
    "video pane: footer"))

EDITS.append((
    "      body=`<div class=\"tr-dim\">This coach has no app ID on record yet, so their activity can't be matched. "
    "It isn't evidence they haven't watched anything — the map fills in as they use the app.</div>`;\n"
    "    } else {\n"
    "      body=`<div class=\"tr-dim\">No lesson plan videos watched.</div>`;\n"
    "    }",
    "      vbody=`<div class=\"tr-dim\">This coach has no app ID on record yet, so their activity can't be matched. "
    "It isn't evidence they haven't watched anything — the map fills in as they use the app.</div>`;\n"
    "    } else {\n"
    "      vbody=`<div class=\"tr-dim\">No lesson plan videos watched.</div>`;\n"
    "    }",
    "video pane: empty states"))

# ── 2. PDF list into its own accumulator + assemble the sub-tabs ─────────────
OLD_PDF = """    // PDF plan views
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
    const id=`${pfx}-${i}`;"""

NEW_PDF = """    // PDF plan views
    let pbody='';
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
    }
    if(R.from<LP_PDF_FROM){
      pbody+=`<div class="tr-dim" style="margin-top:6px">PDF tracking only began 29 Jun 2026, so counts before then are absent by default, not zero.</div>`;
    }

    const id=`${pfx}-${i}`;
    // default pane: whichever has activity this period (videos win a tie)
    const startPdf = (!c.inP.length && c.inPdf.length) ? true : false;
    const body=`<div class="lp-subtabs">
        <div class="lp-sub ${startPdf?'':'on'}" data-sub="v" data-for="${id}">Videos <span class="lp-n">${c.inP.length}</span></div>
        <div class="lp-sub ${startPdf?'on':''}" data-sub="p" data-for="${id}">PDFs <span class="lp-n">${c.inPdf.length}</span></div>
      </div>
      <div class="lp-pane lp-pane-v" ${startPdf?'style="display:none"':''}>${vbody}</div>
      <div class="lp-pane lp-pane-p" ${startPdf?'':'style="display:none"'}>${pbody}</div>`;"""

EDITS.append((OLD_PDF, NEW_PDF, "PDF pane + sub-tab assembly"))

# ── 3. click handling ────────────────────────────────────────────────────────
EDITS.append((
    "  el.querySelectorAll('[data-lp]').forEach(n=>n.onclick=()=>{\n"
    "    const c=document.getElementById('lpc-'+n.dataset.lp);\n"
    "    if(c) c.classList.toggle('open');\n"
    "  });",
    "  el.querySelectorAll('[data-lp]').forEach(n=>n.onclick=()=>{\n"
    "    const c=document.getElementById('lpc-'+n.dataset.lp);\n"
    "    if(c) c.classList.toggle('open');\n"
    "  });\n"
    "  el.querySelectorAll('.lp-sub').forEach(n=>n.onclick=(ev)=>{\n"
    "    ev.stopPropagation();\n"
    "    const card=document.getElementById('lpc-'+n.dataset.for); if(!card) return;\n"
    "    const pdf=n.dataset.sub==='p';\n"
    "    card.querySelectorAll('.lp-sub').forEach(s=>s.classList.toggle('on',s===n));\n"
    "    const pv=card.querySelector('.lp-pane-v'), pp=card.querySelector('.lp-pane-p');\n"
    "    if(pv) pv.style.display=pdf?'none':'block';\n"
    "    if(pp) pp.style.display=pdf?'block':'none';\n"
    "  });",
    "sub-tab click handling"))

# ── 4. CSS ───────────────────────────────────────────────────────────────────
CSS = """
.lp-subtabs{display:flex;gap:6px;margin:-2px 0 10px}
.lp-sub{font-family:'MarkerFelt',cursive;font-size:12px;padding:5px 13px;border-radius:30px;cursor:pointer;border:2px solid #cfe0ea;background:#fff;color:var(--blue);user-select:none;display:flex;align-items:center;gap:6px}
.lp-sub.on{background:var(--blue);border-color:var(--blue);color:#fff}
.lp-sub .lp-n{background:rgba(0,0,0,.12);border-radius:10px;padding:0 7px;font-size:11px}
.lp-sub.on .lp-n{background:rgba(255,255,255,.25)}
.lp-pane ul{margin:4px 0 10px 17px;padding:0}
"""


def main():
    if not os.path.exists(FILE):
        sys.exit(f"ERROR: {FILE} not found. Run from ~/Command-Centre.")
    src = open(FILE, encoding="utf-8").read()
    original = src
    print(f"Read {FILE}: {len(src):,} chars\n")

    if ".lp-subtabs{" in src:
        sys.exit("ABORT: this file already has the card sub-tabs.")
    if "LP_TABS" not in src:
        sys.exit("ABORT: run patch_lessons_pdf.py first.")

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
    print("  OK  inject sub-tab CSS")

    print("\nVerification:")
    gates = [
        ("sub-tab CSS", ".lp-subtabs{" in src),
        ("sub-tab markup", "lp-sub " in src and 'data-sub="v"' in src),
        ("two panes", src.count("lp-pane-v") >= 2 and src.count("lp-pane-p") >= 2),
        ("click handler", "el.querySelectorAll('.lp-sub')" in src),
        ("stopPropagation present", "ev.stopPropagation();" in src),
        ("vbody used", src.count("vbody") >= 6),
        ("pbody used", src.count("pbody") >= 5),
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
    print("\nNow: hard-refresh, open Lesson Plans, expand a coach.")


if __name__ == "__main__":
    main()
