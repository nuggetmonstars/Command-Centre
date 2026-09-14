#!/usr/bin/env python3
"""
patch_rewards.py — fix the Rewards tab on coaches.html

Makes fiveStars read the real `five-star-feedbacks` collection instead of
counting keyword-scored feedback notes.

Run from ~/Command-Centre:
    /usr/local/bin/python3 patch_rewards.py            # dry run
    /usr/local/bin/python3 patch_rewards.py --commit   # apply

Backs up to coaches.BACKUP.<timestamp>.html before writing.
Aborts if any anchor is missing or appears more than once.
"""

import sys, shutil, datetime, os

FILE = "coaches.html"
COMMIT = "--commit" in sys.argv

EDITS = [
    # 1. snapshot variable
    ("const [uSnap,fbSnap,hcSnap,evSnap,attSnap,vtSnap,chkSnap,trSnap] = await Promise.all([",
     "const [uSnap,fbSnap,hcSnap,evSnap,attSnap,vtSnap,chkSnap,trSnap,fsSnap] = await Promise.all([",
     "add fsSnap to destructuring"),

    # 2. fetch the collection
    ("""    getDocs(collection(db,'education-trials'))
  ]);""",
     """    getDocs(collection(db,'education-trials')),
    getDocs(collection(db,'five-star-feedbacks'))
  ]);""",
     "fetch five-star-feedbacks"),

    # 3. declare array
    ("const users={},feedbacks=[],hcFbs=[],allEvents=[],attended=[],viewTabs=[],checks={},trials=[];",
     "const users={},feedbacks=[],hcFbs=[],allEvents=[],attended=[],viewTabs=[],checks={},trials=[],fiveStarFbs=[];",
     "declare fiveStarFbs"),

    # 4. populate array
    ("  trSnap.forEach(d=>trials.push({id:d.id,...d.data()}));",
     "  trSnap.forEach(d=>trials.push({id:d.id,...d.data()}));\n  fsSnap.forEach(d=>fiveStarFbs.push({id:d.id,...d.data()}));",
     "populate fiveStarFbs"),

    # 5. expose on RAW
    ("  RAW={users,feedbacks,hcFbs,allEvents,attended,viewTabs,checks,trials};",
     "  RAW={users,feedbacks,hcFbs,allEvents,attended,viewTabs,checks,trials,fiveStarFbs};",
     "expose fiveStarFbs on RAW"),

    # 6. unpack in computeCoaches
    ("  const {users,feedbacks,hcFbs,allEvents,attended,viewTabs,checks,trials}=RAW;",
     "  const {users,feedbacks,hcFbs,allEvents,attended,viewTabs,checks,trials,fiveStarFbs}=RAW;",
     "unpack fiveStarFbs in computeCoaches"),

    # 7. the real fix — count actual reviews, keep the old metric under an honest name
    ("    const fiveStars=allFbs.filter(f=>window.scoreDescription(f.desc||f.description)===5).length;",
     "    const fiveStars=(fiveStarFbs||[]).filter(f=>f.coachId===cid).length;\n"
     "    const positiveNotes=allFbs.filter(f=>window.scoreDescription(f.desc||f.description)===5).length;",
     "fiveStars reads real reviews; old count renamed positiveNotes"),

    # 8. carry positiveNotes through on the returned record
    ("      alerts, programs:[...progs], fiveStars, wwccExpired,",
     "      alerts, programs:[...progs], fiveStars, positiveNotes, wwccExpired,",
     "return positiveNotes alongside fiveStars"),
]

# 9. renderRewards — rebuilt to show the real ladder + capture gap
OLD_RENDER = """function renderRewards() {
  const el=document.getElementById('reward-content');
  el.innerHTML=`<div class="rewards-wrap"><p class="rewards-intro">Coaches who accumulate 10 or more five-star reviews earn a $300 cash reward.</p><div class="reward-grid" id="rg"></div></div>`;
  const coaches=(COACHES||[]).filter(c=>c.fiveStars>=5).sort((a,b)=>b.fiveStars-a.fiveStars);
  if(!coaches.length){document.getElementById('rg').innerHTML='<div class="empty">No coaches near the reward threshold yet</div>';return;}"""

NEW_RENDER = """function renderRewards() {
  const el=document.getElementById('reward-content');
  const all=(COACHES||[]);
  const withReviews=all.filter(c=>c.fiveStars>0).length;
  const noReviews=all.length-withReviews;
  el.innerHTML=`<div class="rewards-wrap"><p class="rewards-intro">Coaches who accumulate 10 or more five-star reviews earn a $300 cash reward. Counts are lifetime and are not affected by the period filter.</p><p class="rewards-intro" style="font-weight:500;font-size:14px;opacity:.85">${withReviews} of ${all.length} active coaches have at least one review logged \\u2014 ${noReviews} have none on record. Reviews only appear here once someone enters them, so gaps reflect capture, not performance.</p><div class="reward-grid" id="rg"></div></div>`;
  const coaches=all.filter(c=>c.fiveStars>=1).sort((a,b)=>b.fiveStars-a.fiveStars);
  if(!coaches.length){document.getElementById('rg').innerHTML='<div class="empty">No five-star reviews logged yet</div>';return;}"""

EDITS.append((OLD_RENDER, NEW_RENDER, "renderRewards: real counts, 1+ ladder, capture-gap line"))


def main():
    if not os.path.exists(FILE):
        sys.exit(f"ERROR: {FILE} not found. Run this from ~/Command-Centre.")

    src = open(FILE, encoding="utf-8").read()
    original = src

    print(f"Read {FILE}: {len(src):,} chars\n")

    # verify every anchor before touching anything
    problems = []
    for old, _new, label in EDITS:
        n = src.count(old)
        if n != 1:
            problems.append(f"  [{n} matches] {label}")
    if problems:
        print("ABORT — anchors did not match exactly once:")
        print("\n".join(problems))
        print("\nNothing written. The file may already be patched, or has drifted.")
        sys.exit(1)

    for old, new, label in EDITS:
        src = src.replace(old, new, 1)
        print(f"  OK  {label}")

    # sanity gates
    print("\nVerification:")
    gates = [
        ("five-star-feedbacks fetched", src.count("getDocs(collection(db,'five-star-feedbacks'))") == 1),
        ("fiveStars reads real data", "fiveStarFbs||[]).filter(f=>f.coachId===cid)" in src),
        ("old keyword count renamed", "const positiveNotes=allFbs.filter" in src),
        ("auth still wired", src.count("onAuthStateChanged") >= 1),
        ("no placeholder apiKey", "PASTE_YOUR_API_KEY_HERE" not in src),
        ("file size sane", abs(len(src) - len(original)) < 3000),
    ]
    for label, ok in gates:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
    if not all(ok for _l, ok in gates):
        sys.exit("\nABORT — verification failed. Nothing written.")

    if not COMMIT:
        print("\n--- DRY RUN. Nothing written. Re-run with --commit to apply. ---")
        return

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = f"coaches.BACKUP.{stamp}.html"
    shutil.copy2(FILE, backup)
    open(FILE, "w", encoding="utf-8").write(src)
    print(f"\nBacked up to {backup}")
    print(f"Wrote {FILE}  ({len(original):,} -> {len(src):,} chars)")
    print("\nNow: hard-refresh the page, check the Rewards tab, then commit.")


if __name__ == "__main__":
    main()
