import re, datetime, shutil
F = "leaderboard.html"
html = open(F, encoding="utf-8").read()
css_anchor = ".card-payroll   { border-color: var(--green); }"
css_add = (css_anchor
    + "\n.card-recruitment { border-color: #FF9933; }"
    + "\n.card-recruitment:hover { box-shadow: 6px 8px 0 rgba(255,153,51,0.28); }")
tile = '''
    <a href="recruitment.html" class="card card-recruitment">
      <div class="card-icon">\U0001F4CB</div>
      <div class="card-title">Recruitment Pipeline</div>
      <div class="card-desc">Coach onboarding from application through to active coach, with live stage tracking, state plus town filters.</div>
      <div class="card-tags">
        <span class="card-tag">Pipeline</span>
        <span class="card-tag">By State</span>
        <span class="card-tag">Onboarding</span>
        <span class="card-tag">WWCC</span>
      </div>
      <div class="card-arrow">\u2192</div>
    </a>
'''
if "card-recruitment" in html:
    print("Tile already present."); raise SystemExit
if css_anchor not in html:
    print("CSS anchor not found, stopping."); raise SystemExit(1)
html = html.replace(css_anchor, css_add, 1)
pat = re.compile(r'(<a href="coach-payroll\.html" class="card card-payroll">.*?</a>)', re.S)
if not pat.search(html):
    print("Coach Payroll tile not found, stopping."); raise SystemExit(1)
html = pat.sub(lambda m: m.group(1) + "\n" + tile, html, count=1)
stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
shutil.copy(F, f"{F}.bak.{stamp}")
open(F, "w", encoding="utf-8").write(html)
print(f"Backed up to {F}.bak.{stamp}")
print("recruitment tile present:", html.count('href="recruitment.html"'))
