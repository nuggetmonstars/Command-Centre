# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

The Mini Monstars "Command Centre" — an internal tools hub for a children's sports/gymnastics franchise (Australia). Each page is a **standalone, self-contained single-file HTML app**: inline CSS, inline vanilla JS, and embedded base64 images all in one `.html`. There is **no build system, no package.json, no framework, no test suite, and no bundler**. The 1–1.8 MB file sizes are almost entirely embedded base64 assets; the actual application logic lives at the bottom of each file in `<script type="module">`.

## Running / developing

There is nothing to build, lint, or test. Edit the HTML directly. To run locally, serve over HTTP (the pages use ES module imports and `fetch`, so `file://` will not work):

```bash
python3 -m http.server 8000   # then open http://localhost:8000/index.html
```

The repo is deployed by serving these files statically (GitHub repo `nuggetmonstars/Command-Centre`). There is no CI in this repo other than the external churn refresh below.

## Architecture

**Auth + data (most pages).** Pages authenticate against the Firebase project `mini-monstars-au` using the modular Firebase JS SDK loaded from the gstatic CDN inside `<script type="module">`. Flow: `signInWithEmailAndPassword` on a login screen → `onAuthStateChanged` toggles `#login-screen`/`#app` → the page then reads Firestore collections **directly from the client** and renders with vanilla DOM code. Several pages auto-refresh on a timer (e.g. `setInterval(fullRefresh, 10*60*1000)`).

Firestore collections in use: `events`, `users`, `education-centers`, `education-trials`, `feedbacks`, `head-coach-feedbacks`, `children-checks`, `coach-viewed-activity-tabs`, `coach-settings`, `one-on-one-meetings`, `tracker-equipment`, `tracker-transfers`, `tracker-orders`, plus the sales/CRM collections (`sales-entries`, `offer-centres`, `daily-activity`, `sales-crm-centres`, `payroll-fortnights`, `pt-contracts`, `xero-coach-map`, `xero-crossref`, `commission-runs`, `invoice-chase`, `invoice-chase-history`).

The Firebase config (apiKey, authDomain, projectId) is committed in each HTML file. This is expected for Firebase web apps — access control is enforced by Firestore security rules, not by hiding the key.

**Charts/maps via CDN:** Chart.js 4.4.0, Leaflet 1.9.4, and the Google Maps JS API (geometry library).

**Pages:**
- `index.html` / `leaderboard.html` — coach leaderboard / command centre dashboards. These two are **near-duplicates** (~80 differing lines) and usually must be kept in sync. Both carry a baked-in `<script id="payload-data" type="application/json">` precomputed JSON blob *and* do live Firestore reads. `leaderboard.html` also holds the sales CRM + per-rep tabs + the Call List.
- `centres.html` — education centres view.
- `coaches.html` — coach leaderboard.
- `coach-payroll.html` — payroll-fortnight dashboard (Payroll Hours / Xero Check / Commission / Invoice Chase tabs).
- `one-on-one-meetings.html` — 1-on-1 meetings tracker.
- `travel.html` — travel / payroll / PT-hours / profitability tracker (tabbed).
- `show-a-bit-of-love.html` — churn / retention view; `fetch`es `churn_data.json`.
- `tracker_main.html` — equipment tracker. **Uses Firebase** — reads/writes `tracker-equipment` / `tracker-transfers` / `tracker-orders`.

**`churn_data.json`** (~550 KB) is a precomputed snapshot (`generated` timestamp, `centres[]`, `churn`, `active_roster`). It is **regenerated and auto-committed daily by an external process** (commits titled "Auto refresh churn data <date>"). Do not hand-edit it — changes will be overwritten.

## Working in these files

- There is **no shared code**. Firebase config, the login screen, brand CSS variables (`--blue`, `--yellow`, `--red`, `--green`, `--ink`, etc.), and helpers are **copy-pasted across pages**. A change to common behavior must be replicated in every file that needs it — and `index.html`/`leaderboard.html` kept in sync.
- When grepping, the embedded base64 lines flood results. Filter them out (e.g. `grep -vE '^[A-Za-z0-9+/=]{80,}$'`) and focus on the `<script type="module">` block at the end of the file.

---

# Standing rules — autonomy, deploy, safety

> Purpose: stop re-asking questions that already have permanent answers.

## 1. Autonomy — when to stop, when to just do it

**Stop and ask ONLY for:**
- **Irreversible actions**: `git commit` / `git push`, deleting data, sending email to real recipients, `launchctl load` of a job that emails or writes, any `--commit`-style flag on a production write.
- **Genuine ambiguity about intent**: a business decision only Shane can make (e.g. "is MP3 the same item as MP3 Player?", "should this centre count as saved?").

**Everything else: fix it, decide it, document it in your report, and keep going.** Do not stop for:
- A missing helper script → write it (read-only ones especially) and continue.
- A wrong path, a typo, a fixable error → fix and re-run.
- A brief that contradicts the repo's actual state → follow the repo, flag the divergence in your report. (The brief's *intent* wins over its literal wording.)
- Formatting, naming, or structural choices with no business impact.

**Never bypass a safety guard** to keep going. If a script refuses to run without a backup, produce the real backup — don't fake the file to satisfy the check.

## 2. Reporting

- Long output → write it to a file (`report.md`, `out.log`) rather than dumping to terminal. Shane uploads the file; he does not want to copy-paste terminal scrollback.
- Report **evidence, not assertions**. "Verified" means a command and its output. `grep -c`, `curl`, a doc count — show the number.
- One report at the end of the sequence, not a stop after every step.

## 3. Deploy + verify

- `~/Command-Centre` **is** a git repo → GitHub Pages at `https://nuggetmonstars.github.io/Command-Centre/`.
- `~/mini-monstars-agent` is **NOT** a git repo. Nothing is pushed from there. Scripts run locally via launchd. Never suggest pushing it (it holds `credentials.json`, `.env`).
- Data flow: `churn_score.py` writes `churn_data.json` in the agent folder → `daily_refresh.sh` copies it into `~/Command-Centre` and pushes it. That's the only file that crosses over.
- **Verify deploys via the Pages URL in incognito**, never `raw.githubusercontent.com` (it caches). Standard check: `curl -s "<pages-url>" | grep -c "<string>"`. Pages lags 1–2 min after a push.
- **Never commit or push without explicit go-ahead.** Leave changes in the working tree and say so.

## 4. Repo conventions that are deliberate — do not "fix" them

- **The committed Firebase API key is intentional** (see Architecture — access is enforced by Firestore rules, not key-hiding). If a brief says "use a placeholder", ignore it and match the existing files.
- Firebase project is **`mini-monstars-au`** — never `mini-monstars`.
- Firebase SDK must be `<script type="module">` with `import` statements. Compat-style `<script src>` against modular SDK URLs throws syntax errors.

## 5. Source of truth / file hygiene

- **The deployed file in `~/Command-Centre` is canonical.** Edit it in place. Never regenerate a page from scratch — full exports silently drop auth wiring and base64 blobs.
- **Stray duplicates are a known hazard.** A stale copy of `show-a-bit-of-love.html` in the agent folder caused hours of wrong-file edits. Before editing, confirm you're in the file that's actually deployed. If you find a duplicate outside the repo, flag it for deletion.
- `coach-payroll.html`: **anchored edits only** (exact strings/anchors). Never a fresh full-file export. Two deploy gates must pass before commit: (1) `grep -c` of the four placeholder tokens = 0, (2) `grep -c "onAuthStateChanged\|firebase-auth.js"` ≥ 2. Refresh the baseline snapshot (`~/mini-monstars-agent/coach-payroll.BASELINE.html`) after each deploy.
- `leaderboard.html` is a merged SPA with duplicate element IDs — scope changes carefully.

## 6. Environment

- **`/usr/local/bin/python3`** for anything using `firebase_admin` (NOT `/usr/bin/python3`).
- launchd jobs only fire when the Mac is awake. A 7am job runs on next wake if the lid was shut. Say so rather than letting it look broken.
- `sed`/`perl` substitution can succeed silently without changing the file — verify with `grep` after, or use a heredoc rewrite.
- Large pushes: `git config http.postBuffer 524288000`.
- Downloads land in `~/Downloads` and need `mv` into place.

## 7. Live-system hazards

- The equipment agent (`com.minimonstars.agent`) polls `equipment@minimonstars.com` every 30s and writes to `tracker-equipment` / `tracker-transfers`. **Unload it before any bulk write to those collections**, reload after.
- `churn_score.py` is read-only on Firestore and writes only `churn_data.json`. Keep it that way.
- A full `churn_score.py` run takes ~20 min (per-feedback Haiku calls). Kick it off in the background and report when done; don't sit polling.
- Before any destructive production write: **a real backup must exist first.** No exceptions.
