# Firestore rules — live exposure review
**Date:** 2026-09-09 · **Ruleset:** `3faa20a0-03ea-430c-b196-232318e95053`, deployed **2026-07-27**
**Source:** fetched live from the Firebase Rules API with the service account. **Nothing changed.**

---

## Verdict

**The rules are open.** Confirmed, and worse than the missing page-level role checks implied.

The last block is a catch-all:

```
match /{document=**} {
  allow read: if request.auth != null && !(request.path[3] == "centre-profit") && ...8 more;
  allow write: if request.auth != null;
}
```

Any one of the **891 authenticated accounts — 442 coaches, 276 parents, 152 centres** — can read
*and write* every collection in the project except nine analytics ones that are read-blocked only.

There is no role check anywhere in the ruleset. `request.auth != null` is the entire access model.
So the nine pages having no role gate isn't a code-quality note — the database behind them applies
no gate either.

---

## What is exposed, per collection

### 🔴 Readable AND writable by any of the 891 accounts (via catch-all)

| Collection | Docs | What's in it |
|---|---|---|
| **`users`** | 890 | **See PII below — the worst of it** |
| `payroll-fortnights` | 5 | payroll runs |
| `pt-contracts` | 10 | PT contracts (also has its own explicit `read, write: if auth != null`) |
| `commission-runs` | 2 | commission calculations |
| `xero-coach-rates` | 61 | **per-coach pay rates** |
| `xero-coach-map` / `xero-centre-map` | 62 / 474 | Xero identity mapping |
| `invoice-chase` / `-history` | 47 / 191 | debtor chasing |
| `sales-crm-centres` | 4,906 | full sales CRM |
| `sales-entries` | 185 | sales ledger |
| `recruitment-pipeline` | 579 | candidate pipeline (explicit rule, same effect) |
| `feedbacks` | 7,237 | coach performance feedback |
| `children-checks` | 905 | child records |
| `tracker-equipment` etc. | 157 / 982 | equipment |
| …and every other collection not named below | | |

**The PII in `users` is the sharp end.** Any coach or parent can read all 890 profiles:

| Field | Non-empty | |
|---|---|---|
| **`tfn`** (Tax File Number) | **204** | |
| `dateOfBirth` | 200 | |
| `superNumberAndProvider` | 198 | |
| `bsb` / `accountNumber` / `bankName` | 169 / 169 / 166 | **bank details** |
| `claimTaxFreeThreshold` | 207 | |
| `address` | 435 | |
| `phone` | 405 | |

TFNs and bank accounts for ~200 staff, readable by every coach and parent with a login. Under
Australian privacy law that is the part I'd treat as urgent.

### 🔴 The nine "private" analytics collections are read-blocked but **WRITE-OPEN**

`centre-profit`, `unit-economics`, `scorecard`, `churn-analytics`, `churn-fault`, `churn-monthly`,
`sales-analytics`, `financials`, `forecast`.

Each has `allow write: if false` in its own block — but **that does not do what it looks like it
does.** Firestore rules are a permissive union: if *any* matching rule grants access, access is
granted. There is no deny. The catch-all `match /{document=**}` also matches these paths and its
`allow write: if request.auth != null` grants the write. **`allow write: if false` grants nothing
and revokes nothing.**

The read exclusions work correctly (they're written into the catch-all's read condition, which is
the right pattern). The writes do not. Any authenticated user can overwrite your churn and
financial analytics.

### 🟠 Public — no login at all

| Collection | Docs | Access |
|---|---|---|
| `events` | 13,462 | **read: if true** — session data, kids, centres, coaches |
| `education-centers` | 698 | **read: if true** |
| `bookings` / `booking-schedule` | 5 / 4 | **read: if true** |
| `bookings-temp` | 5 | **read AND write: if true** |
| `bookings-holiday-temp` | 13 | **read AND write: if true** |
| `express-interest-booking` | 3 | **write: if true** |

Three collections are writable by anyone on the internet with the project ID — which is in every
page's committed config. Unauthenticated write is worth closing regardless of the rest.

---

## Smallest change that closes it

I have **not** applied this. Two edits, in priority order.

### Edit 1 — restrict the catch-all to staff (closes the PII and payroll exposure)

Add a helper and swap the catch-all's condition:

```
function isStaff() {
  return request.auth != null
    && get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role in ['admin','staff'];
}

match /{document=**} {
  allow read, write: if isStaff();
}
```

**What it breaks:** everything the coach app, parent app and centre portal do. Those apps read
`users`, `events`, `education-centers`, `feedbacks`, `watched-video` and write attendance and
social-feed docs as non-staff users. A blanket staff-only catch-all **will break the mobile apps**
— so it has to be paired with explicit per-collection rules re-opening exactly what the apps need,
which means auditing the app's reads and writes first. That audit is the real work here, and it is
not a tonight job.

**Cost:** `get()` inside rules is a billed document read per evaluation and adds latency. Custom
claims (set once via Admin SDK, read as `request.auth.token.role`) are the cheaper long-run
answer — currently 0 accounts have any claims set.

### Edit 2 — the genuinely small one, safe to ship tonight

Two changes that break nothing:

1. **Kill the three unauthenticated writes.** Change `allow write: if true` to
   `if request.auth != null` on `bookings-temp`, `bookings-holiday-temp`,
   `express-interest-booking`. Only risk: an anonymous pre-signup booking flow. `bookings-temp`
   has 5 docs and `express-interest-booking` 3, so if that flow exists it is barely used —
   worth a quick check before shipping.

2. **Actually close the analytics writes.** Add the same nine path exclusions to the catch-all's
   `write` condition that already exist on `read`. Nothing writes those collections from a client
   — the agent writes them with the service account, which bypasses rules entirely. **Zero
   breakage.**

### What I'd suggest

Ship Edit 2 tonight — it's contained and breaks nothing. Edit 1 needs the app-behaviour audit
first; done blind it takes the coach app down. The PII is the thing that actually matters, and if
you want it closed faster than a full audit allows, a targeted rule on `users` alone (staff read
all; everyone else reads only their own doc) is a middle step — though that too needs checking
against what the apps read from other people's profiles.

Say the word and I'll do the audit and draft the rules for review. I won't deploy anything.

---

# UPDATE — contained edits DEPLOYED 2026-09-09

**New live ruleset:** `d9e7608f-91e5-40d6-b8b5-2af9ffc6a7c6` (was `3faa20a0-…`)
**Rollback file:** `…/scratchpad/rulescheck/firestore.rules.LIVE-BACKUP` (the exact prior ruleset)

Verified after deploy by re-fetching the live ruleset from the Rules API: it is **byte-identical**
to the file I intended to deploy, and diffs from the previous ruleset by exactly the two edits.

### Edit A — nine analytics collections are now write-closed
The nine `request.path[3]` exclusions that already guarded the catch-all's `read` are now mirrored
onto its `write`. `centre-profit`, `unit-economics`, `scorecard`, `churn-analytics`, `churn-fault`,
`churn-monthly`, `sales-analytics`, `financials`, `forecast` can no longer be written by any client.
The agent writes them with the service account, which bypasses rules — **zero breakage.**

### Edit B — anonymous writes: narrowed, not closed
**I did not blanket-close these, and you should know why.** The pre-signup check you asked for
found the flow is **real and public-facing**:

- `express-interest-booking` — lead capture: `parentName`, `email`, `phoneNumber`, `postcode`,
  `age`, `day`, `time`. No `userId`. Last write **2025-05-26** (~15 months ago).
- `bookings-temp` / `bookings-holiday-temp` — checkout staging: `items`, `sum`, `parentName`,
  `email`, `phoneNumber`. No timestamp field at all.

A blanket `write: if request.auth != null` would silently kill a lead-capture form that may still
be live on the public marketing site — which is not in this repo, so I can't confirm either way.
Lost leads would be invisible.

So instead of `allow write: if true` each of the three now has:

```
allow create: if true;
allow update, delete: if false;
```

The public form still submits exactly as before. What's gone is anyone on the internet being able
to **overwrite or delete** those documents — which was the actual abuse vector. This is strictly
safer than the prior state and strictly safer than doing nothing, without the breakage risk.

### Still open — deliberately, pending the app audit
- `bookings-temp` and `bookings-holiday-temp` remain **`read: if true`** — parent names, emails and
  phone numbers readable with no login. I left read alone because a payment-return page may read
  back what it wrote; changing it blind risks the checkout. **Worth closing soon** — it's a live
  PII leak, just a smaller one than `users`.
- `events` (13,462) and `education-centers` remain `read: if true`.
- The catch-all still grants all 891 accounts read+write on everything else, `users` included.
  That is what the PII split addresses — see `PII-SPLIT-PROPOSAL.md`.

---

# Cloud Audit Logs — can we tell if anyone read the data?

**I could not determine this, and I'd rather say so than guess.**

The service account has no logging permissions. Four queries against the Logging API — Firestore
`DATA_ACCESS`, any data-access log, `ADMIN_ACTIVITY`, and any log at all — returned an identical
`403 Permission denied for all log views`. Because that includes `ADMIN_ACTIVITY`, which is always
on and always has entries, **the 403 proves a permissions wall, not an absence of logs.** No
conclusion can be drawn from it either way. `getIamPolicy` (where `auditConfigs` live) was also 403.

The `gcloud` CLI is authenticated as `info@minimonstars.com`, which likely does have the access —
but its token needs interactive reauth and its default project is set to `mini-monstars`, not
`mini-monstars-au`.

### What is true regardless

- Firestore **Data Access audit logs are OFF by default.** They must be explicitly switched on.
  Given no one has been looking at this, the strong prior is **they were never enabled** — in which
  case reads were never recorded and the question is unanswerable for all past time.
- Even if enabled, Data Access logs have a **default 30-day retention**. Anything older is gone.
- Admin Activity logs (400-day retention) are always on, but they record configuration changes, not
  document reads. They would not show a coach reading `users`.

### To settle it — two commands, ~30 seconds

Run in this session with the `!` prefix so the output lands here:

```
! gcloud auth login
```
then
```
! gcloud projects get-iam-policy mini-monstars-au --format=json | grep -A15 auditConfigs
```

Empty output = Data Access logging was never enabled = **no read of this data was ever recorded.**
If something comes back, tell me and I'll pull the date range and query the actual reads.

**My expectation: it was never on.** If a disclosure assessment ever needs it, "we cannot rule out
reads, and we have no logs either way" is the honest position — and enabling it now at least starts
the clock.

---

# UPDATE 2 — 2026-09-09, later: bookings read closed + PII split MIGRATED

**Live ruleset:** `projects/mini-monstars-au/rulesets/` — third deploy of the day.
Rollback files kept: `rules.PRE-BOOKINGREAD.bak` (state before this deploy),
`firestore.rules.LIVE-BACKUP` (original, pre-everything).

## Bookings enumeration — closed, `get` preserved

Applied `allow get: if true; allow list: if false;` to `bookings-temp`,
`bookings-holiday-temp` and `bookings`. **`booking-schedule` deliberately left alone** — it holds
no PII (`startWeekIndex`/`endWeekIndex`/`title`) and the public booking form almost certainly needs
to list it.

Verified with unauthenticated Firestore REST calls (no `Authorization` header), before and after:

| Probe | Before | After |
|---|---|---|
| GET `bookings-temp/{id}` | 200 | **200** ✓ |
| GET `bookings-holiday-temp/{id}` | 200 | **200** ✓ |
| GET `bookings/{id}` | 200 | **200** ✓ |
| LIST `bookings-temp` | 200 | **403** ✓ |
| LIST `bookings-holiday-temp` | 200 | **403** ✓ |
| LIST `bookings` | 200 | **403** ✓ |
| LIST `booking-schedule` (control) | 200 | 200 ✓ |

The payment-return path (read one document by ID, no session) is unaffected. Harvesting parent
names, emails and phone numbers by enumeration is closed.

## PII split — done

Rules deployed **before** the data moved, so `users-private` was never briefly exposed under the
catch-all. `users-private` is excluded from the catch-all's read **and** write conditions.

Migration ran in two passes with a fresh backup first
(`~/mm-private-backups/users_PREMIGRATION_20260909-112931.json`, 890 docs,
sha256 `d89dea386b1d73e6c4757ca9d5f106aa04e79e37793907a073e197ce267d2683`):

1. **Copy** — 243 `users-private` docs written, then verified field-for-field against source.
   243/243 matched exactly.
2. **Delete** — the delete pass refuses to clear any field not already confirmed byte-identical in
   `users-private`. 0 refused, 243 cleared.

Post-check: **0 residual Tier-1 fields across all 890 `users` docs**; 890 users docs intact;
243 `users-private` docs.

### Verification — live, with real signed-in tokens

Three migrated coaches (Katelyn Brennan, Sherwynne OGrady, Kiara Alabakov): Tier-1 fields **gone**
from `users/`, **present** in `users-private/`, and `firstName`/`lastName`/`email`/`role`/`status`
all still on `users/`.

Signed in as a **non-staff coach**:

| Operation | Result |
|---|---|
| GET own `users-private` doc | 200 ✓ |
| GET another coach's `users-private` doc | **403** ✓ |
| LIST `users-private` | **403** ✓ |
| GET another user's `users/` doc | 200 (unchanged) ✓ |
| — Tier-1 fields visible in it | **none** ✓ |

Signed in as **admin**: GET a coach's `users-private` 200 ✓, LIST 200 ✓.

`address` / `addressGeo` held back as agreed — still on `users/`, `travel.html` and
`leaderboard.html` unaffected.

## Nightly sweep — live

`~/mini-monstars-agent/pii_sweep.py`, launchd `com.minimonstars.piisweep`, **02:30 daily, loaded**.
Moves any Tier-1 field found on a `users` doc into `users-private` and deletes it, but only after
confirming the value landed. Logs to `pii_sweep.log`. Supports `--dry-run`.

**First real run: `sweep: clean — no Tier-1 PII found on any users/ doc`.** Expected, since the
migration had just completed — its value is from tomorrow, catching whatever the unfixed
onboarding form writes.

To stop it: `launchctl unload ~/Library/LaunchAgents/com.minimonstars.piisweep.plist`
(note: launchd only fires while the Mac is awake — a 02:30 job runs on next wake if the lid is shut).

## Still open

- `events` (13,462) and `education-centers` (698) remain publicly readable (`read: if true`).
- The catch-all still grants all 891 accounts read+write on everything not explicitly excluded —
  `children-checks`, `feedbacks`, payroll, the sales CRM. **`users` is no longer the worst of it,
  but the model is still "any login sees everything".** That's the app audit.
- The `match /bookings-holiday/{booking}` block is dead code — the actual collection is
  `bookings-holidays` (with an s), so it falls through to the catch-all. Harmless today; worth
  fixing so it doesn't mislead.

---

# When the exposure started — full ruleset history

**History is complete.** 35 rulesets retained, oldest `2024-05-14T04:53:13Z` — and that oldest one
is the Firestore locked-mode default (`allow read, write: if false`), which is what a newly created
project starts with. So this goes back to the birth of the project; **nothing is missing or aged
out.** (Firebase retains up to 2,500 rulesets; 35 is nowhere near the cap.)

## Timeline of the catch-all `match /{document=**}`

| Ruleset created (UTC) | id | catch-all READ | catch-all WRITE |
|---|---|---|---|
| 2024-05-14 04:53 | `bb5fe273` | `if false` | `if false` |
| 2024-05-14 08:46 | `bd80af4b` | **`allow read;` — public, no auth** | `if false` |
| 2024-05-14 09:35 | `55b9ed8e` | **`allow read;` — public, no auth** | `if auth != null` |
| **2024-05-15 20:12:41** | **`c956953d`** | **`if auth != null`** | **`if auth != null`** |
| 2024-05-15 20:16:53 | `7ad12d09` | `if auth != null` | `if auth != null && …role == 'admin'` |
| 2024-05-15 20:17:27 | `264133c8` | `if auth != null` | `if auth != null && …role == 'admin'` |
| **2024-07-26 01:40:17** | **`543e513e`** | **`if auth != null`** | **`if auth != null` — role check removed** |
| 2024-11-25 → 2026-07-13 | 10 rulesets | `if auth != null` | `if auth != null` |
| 2026-07-19 23:20 → 2026-07-27 | 9 rulesets | + 9 analytics read exclusions | `if auth != null` |
| 2026-09-09 01:04 | `d9e7608f` | + exclusions | **+ exclusions (my fix)** |
| 2026-09-09 01:28 | `2f112152` | + `users-private` | + `users-private` |

## The answer

**Earliest ruleset with the catch-all `read, write: if request.auth != null` and no role check:
`c956953d`, created 2024-05-15 20:12:41 UTC (16 May 2024, 06:12 AEST).**

But that state lasted **4 minutes and 12 seconds** — a role check was added to `write` at 20:16:53.
So for the date the exposure *actually started and persisted*, there are two distinct answers, and
the read one is the one that matters:

- **Unrestricted authenticated READ began 2024-05-15 20:12:41 UTC and never stopped.** The
  20:16 change only added a role check to `write`; read stayed `if request.auth != null` from that
  moment continuously to today. **That is 846 days — 2 years, 3½ months.** Every signed-in account
  could read every collection, `users` included, for that entire period.
- **WRITE was role-restricted to admins for 71 days** (2024-05-15 → 2024-07-26), then the check was
  removed in `543e513e` on **2024-07-26 01:40:17 UTC** and never returned. **Unrestricted
  authenticated write ran 774 days**, until I closed the analytics half this evening.

Before all that, from 2024-05-14 08:46 to 2024-05-15 20:12, the catch-all read was bare
`allow read;` — **readable with no login at all**, for about 35 hours.

## Caveat on precision

The Rules API exposes ruleset **creation** times. It does not expose a historical *release* log —
`releases.list` returns only what is currently released. So strictly, these are the dates each
ruleset was **created**, not proven-deployed.

In practice `firebase deploy` creates and releases in one step, and the sequence is a clean
single-track progression with no orphans, so creation time is a sound proxy. If you need
release-time proof for a disclosure assessment, that would come from Admin Activity audit logs
(`SetLiveRules` events, 400-day retention) — which would cover back to roughly August 2025, not to
2024. Worth pulling if it ever matters formally.

## For the record

The PII fields themselves are older than the exposure window in places — `users` docs carry
`created` dates back to 2025-02. The whole time TFNs and bank details sat in `users`, any of the
891 accounts could read them.
