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

Firestore collections in use: `events`, `users`, `education-centers`, `education-trials`, `feedbacks`, `head-coach-feedbacks`, `children-checks`, `coach-viewed-activity-tabs`, `coach-settings`, `one-on-one-meetings`.

The Firebase config (apiKey, authDomain, projectId) is committed in each HTML file. This is expected for Firebase web apps — access control is enforced by Firestore security rules, not by hiding the key.

**Charts/maps via CDN:** Chart.js 4.4.0, Leaflet 1.9.4, and the Google Maps JS API (geometry library).

**Pages:**
- `index.html` / `leaderboard.html` — coach leaderboard / command centre dashboards. These two are **near-duplicates** (~80 differing lines) and usually must be kept in sync. Both carry a baked-in `<script id="payload-data" type="application/json">` precomputed JSON blob *and* do live Firestore reads.
- `centres.html` — education centres view.
- `coaches.html` — coach leaderboard.
- `one-on-one-meetings.html` — 1-on-1 meetings tracker.
- `travel.html` — travel / payroll / PT-hours / profitability tracker (tabbed).
- `show-a-bit-of-love.html` — churn / retention view; `fetch`es `churn_data.json`.
- `tracker_main.html` — equipment tracker. Does **not** use Firebase.

**`churn_data.json`** (~550 KB) is a precomputed snapshot (`generated` timestamp, `centres[]`, `churn`, `active_roster`). It is **regenerated and auto-committed daily by an external process** (commits titled "Auto refresh churn data <date>"). Do not hand-edit it — changes will be overwritten.

## Working in these files

- There is **no shared code**. Firebase config, the login screen, brand CSS variables (`--blue`, `--yellow`, `--red`, `--green`, `--ink`, etc.), and helpers are **copy-pasted across pages**. A change to common behavior must be replicated in every file that needs it — and `index.html`/`leaderboard.html` kept in sync.
- When grepping, the embedded base64 lines flood results. Filter them out (e.g. `grep -vE '^[A-Za-z0-9+/=]{80,}$'`) and focus on the `<script type="module">` block at the end of the file.
