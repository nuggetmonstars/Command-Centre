#!/usr/bin/env python3
"""
patch_lessons_statefilter.py — make the Lesson Plans stat cards follow the state pills

The five headline cards (active / nothing / videos watched / PDFs opened /
coaches trackable) are currently computed from the whole roster, so they stay
frozen while the cards below change as you click through states.

This scopes them to the selected state. The search box deliberately does NOT
affect them — typing a name should not collapse the headline numbers.

The two raw-count cards ("videos watched", "PDFs opened") previously counted
every record in the collections regardless of who it belonged to. They now sum
only the selected state's coaches, so they agree with the cards below.

Run from ~/Command-Centre:
    /usr/local/bin/python3 patch_lessons_statefilter.py            # dry run
    /usr/local/bin/python3 patch_lessons_statefilter.py --commit   # apply

Set FILE below to patch leaderboard.html instead.
"""

import sys, shutil, datetime, os

FILE = "coaches.html"
COMMIT = "--commit" in sys.argv

EDITS = []

# ── 1. build a state-scoped basis for the stats ──────────────────────────────
EDITS.append((
    "  let list=all;\n"
    "  if(LP_STATE!=='ALL') list=list.filter(c=>(c.state||'')===LP_STATE);\n"
    "  if(qF) list=list.filter(c=>(c.fullName||'').toLowerCase().includes(qF));",
    "  // stats follow the state pills but NOT the search box\n"
    "  const statBase = LP_STATE==='ALL' ? all : all.filter(c=>(c.state||'')===LP_STATE);\n"
    "  let list=statBase;\n"
    "  if(qF) list=list.filter(c=>(c.fullName||'').toLowerCase().includes(qF));",
    "add state-scoped stat basis"))

# ── 2. headline count ────────────────────────────────────────────────────────
EDITS.append((
    "  const totalIn=all.filter(c=>c.mapped&&(c.views.some(v=>inR(v.date))||c.pdfs.some(v=>inR(v.date)))).length;",
    "  const totalIn=statBase.filter(c=>c.mapped&&(c.views.some(v=>inR(v.date))||c.pdfs.some(v=>inR(v.date)))).length;",
    "headline: scope to state"))

EDITS.append((
    "  const mappedN=all.filter(c=>c.mapped).length;",
    "  const mappedN=statBase.filter(c=>c.mapped).length;",
    "trackable numerator: scope to state"))

# ── 3. the five stat cards ───────────────────────────────────────────────────
OLD_STATS = """      <div class="stat-card"><div class="stat-num">${all.filter(c=>c.mapped&&!(c.views.some(v=>inR(v.date))||c.pdfs.some(v=>inR(v.date)))).length}</div><div class="stat-lbl">nothing in ${plabel}</div></div>
      <div class="stat-card"><div class="stat-num">${(LP_VIEWS||[]).filter(v=>inR(v.date||0)).length}</div><div class="stat-lbl">videos watched</div></div>
      <div class="stat-card"><div class="stat-num">${((RAW.viewTabs)||[]).filter(v=>LP_TABS.includes(v.tab)&&inR(v.date||0)).length}</div><div class="stat-lbl">PDFs opened</div></div>
      <div class="stat-card"><div class="stat-num">${mappedN}/${all.length}</div><div class="stat-lbl">coaches trackable</div></div>"""

NEW_STATS = """      <div class="stat-card"><div class="stat-num">${statBase.filter(c=>c.mapped&&!(c.views.some(v=>inR(v.date))||c.pdfs.some(v=>inR(v.date)))).length}</div><div class="stat-lbl">nothing in ${plabel}</div></div>
      <div class="stat-card"><div class="stat-num">${statBase.reduce((a,c)=>a+c.views.filter(v=>inR(v.date)).length,0)}</div><div class="stat-lbl">videos watched</div></div>
      <div class="stat-card"><div class="stat-num">${statBase.reduce((a,c)=>a+c.pdfs.filter(v=>inR(v.date)).length,0)}</div><div class="stat-lbl">PDFs opened</div></div>
      <div class="stat-card"><div class="stat-num">${mappedN}/${statBase.length}</div><div class="stat-lbl">coaches trackable</div></div>"""

EDITS.append((OLD_STATS, NEW_STATS, "stat cards: scope all five to state"))


def main():
    if not os.path.exists(FILE):
        sys.exit(f"ERROR: {FILE} not found. Run from ~/Command-Centre.")
    src = open(FILE, encoding="utf-8").read()
    original = src
    print(f"Read {FILE}: {len(src):,} chars\n")

    if "const statBase" in src:
        sys.exit("ABORT: this file already has state-scoped stats.")
    if 'id="tab-lessons"' not in src:
        sys.exit("ABORT: Lesson Plans tab not found.")

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
    # everything between renderLessons and the end of its stat block
    body = src.split("function renderLessons()")[1][:9000]
    gates = [
        ("statBase defined", "const statBase" in src),
        ("headline scoped", "const totalIn=statBase.filter(" in src),
        ("trackable scoped", "${mappedN}/${statBase.length}" in src),
        ("videos card scoped", "statBase.reduce((a,c)=>a+c.views.filter(v=>inR(v.date)).length,0)" in src),
        ("PDFs card scoped", "statBase.reduce((a,c)=>a+c.pdfs.filter(v=>inR(v.date)).length,0)" in src),
        ("no raw LP_VIEWS count", "(LP_VIEWS||[]).filter(v=>inR(v.date||0)).length" not in src),
        ("no raw viewTabs count", "((RAW.viewTabs)||[]).filter(v=>LP_TABS.includes(v.tab)&&inR" not in src),
        ("search still separate", "if(qF) list=list.filter(" in src),
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
    print("\nNow: hard-refresh, click through the state pills.")


if __name__ == "__main__":
    main()
