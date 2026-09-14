# Command Centre — usage-tracking inventory
**Date:** 2026-09-09 · **Method:** repo grep + read-only Admin SDK queries against `mini-monstars-au`
**Nothing was written to Firestore.** All numbers below are live counts, not estimates.

---

## Headline

**Nothing anywhere records Command Centre usage.** Not a session, not a page view, not a
login timestamp. The sign-in handler toggles two divs and loads data — that is all it does.
So of your three questions, **none can be answered for the Command Centre today.**

Two of them can be answered *product-wide* (coach app + parent app + centre portal + Command
Centre lumped together), server-side only. That is a different question and probably not the
one you're asking.

---

## 1. What identifies a user, and where

**Both — and they are joined by document ID.**

| Layer | Where | Notes |
|---|---|---|
| Firebase Auth | project `mini-monstars-au` | 891 accounts. Email/password only. **0 custom claims.** |
| Profile | Firestore `users/{uid}` | 890 docs. **Doc ID *is* the Auth UID.** |

Verified join: 890 of 891 Auth accounts have a matching `users/` doc. One Auth account has no
profile doc.

`users/{uid}` field presence (of 890 docs):

| Field | Docs | Field | Docs |
|---|---|---|---|
| `email` | 890 | `centerId` | 153 |
| `firstName` | 890 | `roleAccess` | 153 |
| `lastName` | 890 | `phone` | 439 |
| `role` | 890 | `profilePic` | 345 |
| `children` | 890 | `notificationToken` | 274 |
| `status` | 817 | `startDate` | 428 |
| `created` | 760 | `inactiveDate` | 242 |
| `centerName` | 714 | `avgRating` | 206 |

`created` is an **ISO-8601 string**, not a Firestore Timestamp — e.g. `'2026-05-15T00:32:35.658Z'`.
It's absent on 130 docs. Sort on it with care.

`roleAccess` is centre-portal permission (`"admin"` ×136, `"staff"` ×17), **not** Command Centre
access. There is no Command Centre permission field anywhere.

---

## 2. Is anything recording usage?

**For the Command Centre: no. Plainly, nothing.**

Checked and confirmed absent:
- No `sessions`, `analytics`, `events-log`, `audit`, or equivalent collection (all 109 top-level
  collections enumerated — none is a usage log for these pages).
- No `lastSeen`, `lastLogin`, `loginCount`, `lastActive` field on `users/` — the only fields
  matching those patterns are `inactiveDate`, `inactiveHistory`, `accountNumber`, `bankAccount`
  (false positives).
- No page writes anything on sign-in. Every `onAuthStateChanged` handler across all pages does:
  hide login div → show app div → `loadRaw()` → render. No write.
- No Google Analytics, no `logEvent`, no Firebase Analytics import in any file.

**There IS usage tracking — but for the coach mobile app, not the Command Centre.** These
collections carry per-user timestamps and are already read by `coaches.html` / `leaderboard.html`:

| Collection | Docs | Timestamp field | Measures |
|---|---|---|---|
| `watched-video` | 9,658 | `date` (epoch ms) | lesson-plan video views |
| `coaches-attendance` | 6,411 | — | coach attendance |
| `coach-viewed-activity-tabs` | 2,430 | `date` (epoch ms) | PDF/tab opens in app |
| `watched-testing-video` | 114 | — | testing videos |
| `watched-entertainment-video` | 64 | — | entertainment videos |
| `coach-testing-video-progress` | 48 | `updatedAt` | module progress |
| `coach-watched-brain-video` | 37 | `date` (epoch ms) | brain academy |

These answer *"which coaches use the coach app"*. They say nothing about who opens the Command
Centre. Note `watched-video` keys on an app `userId` that needs `coach-app-map` (77 docs) to
resolve to a coach — `coach-viewed-activity-tabs` carries `coachId` directly.

---

## 3. What Auth metadata is reachable from the client

**For the signed-in user only:** `auth.currentUser.metadata.creationTime` and `.lastSignInTime`.
That's it, and it's only ever *themselves*.

**For everyone else: not reachable from the client. Full stop.** There is no client SDK method to
list users or read another account's metadata. `listUsers()` is Admin SDK only.

**So it needs something on the box** — and the box already has it:
`~/mini-monstars-agent/firebase_credentials.json`, a `service_account` for
`firebase-adminsdk-vw3j0@mini-monstars-au.iam.gserviceaccount.com`. Verified working; that's how
the numbers in this document were produced.

### The catch that matters most

`lastSignInTime` is **one timestamp per Auth account for the entire Firebase project.** The coach
app, the parent app, the centre portal and the Command Centre all share this one Auth pool and all
call `signInWithEmailAndPassword` against it. A coach signing into the mobile app on her phone
bumps the exact same field the Command Centre would.

**`lastSignInTime` therefore cannot tell you anything about Command Centre usage.** It is a
product-wide liveness signal, nothing more.

Current distribution across all 891 accounts:

| Last sign-in | Accounts |
|---|---|
| 0–7 days | 30 |
| 7–30 days | 60 |
| 30–90 days | 140 |
| 90–365 days | 300 |
| over 1 year | 245 |
| **never signed in** | **116** |

---

## 4. How coaches, parents and centres are distinguished

**One `users` collection, one `role` string field.** Not separate collections, not inferred.

| `role` | `status` | Docs |
|---|---|---|
| `coach` | `Inactive` | 331 |
| `coach` | `Active` | **111** |
| `parent` | `''` (empty) | 223 |
| `parent` | absent | 53 |
| `center` | `Active` | 152 |
| `admin` | absent | 16 |
| `staff` | absent | 4 |

Watch out: `status` is inconsistent — `'Active'`, `'Inactive'`, `''`, or missing entirely
depending on role. Only coaches and centres use it meaningfully.

`role='center'` is a **login account for a centre**, distinct from the centre *venue* record.
Venues live in `education-centers` (698 docs). Related: `education-centers-admins` (138),
`education-centers-rooms` (44).

**The Command Centre audience is `admin` + `staff` = 20 accounts.** Everything else in the Auth
pool is app/portal users who never open these pages.

---

## 5. Record counts

**109 top-level collections exist** — far more than CLAUDE.md documents. Selected:

| Collection | Docs | | Collection | Docs |
|---|---|---|---|---|
| `events` | 13,462 | | `education-centers` | 698 |
| `watched-video` | 9,658 | | `recruitment-pipeline` | 579 |
| `feedbacks` | 7,237 | | `head-coach-feedbacks` | 476 |
| `coaches-attendance` | 6,411 | | `xero-centre-map` | 474 |
| `sales-crm-centres` | 4,906 | | `daily-activity` | 471 |
| `coach-viewed-activity-tabs` | 2,430 | | `coach-conduct-signatures` | 370 |
| `centre-compliance-emails` | 2,333 | | `first-session-emails` | 320 |
| `learn-activities` | 2,336 | | `holidays` | 278 |
| `center-week-activity-mail-queue` | 1,173 | | `learn-subcategories` | 250 |
| `center-calendar-mail-queue` | 1,008 | | `feedbacks-general` | 212 |
| `tracker-transfers` | 982 | | `invoice-chase-history` | 191 |
| `children-checks` | 905 | | `sales-entries` | 185 |
| **`users`** | **890** | | `churn-fault` | 178 |
| `chats` | 701 | | `tracker-equipment` | 157 |

### Two things to flag

1. **`one-on-one-meetings` does not exist.** Zero docs, not among the 109 collections — yet
   CLAUDE.md lists it and `one-on-one-meetings.html` makes 3 `collection()` calls. That page is
   reading nothing.
2. **No page gates on role.** Zero occurrences of a role/allowlist check in the auth handler of
   any of the 9 Command Centre pages. Any of the 891 authenticated accounts — including 442
   coaches and 276 parents — reaches the app shell on any page if they have the URL. Whether they
   actually *see* payroll and financial data depends entirely on your Firestore security rules,
   which I couldn't read from here. **Worth checking those rules.**

---

## Your three questions

### ❌ Who is using it the most, and how much
**Cannot be answered — today or retroactively.** No usage is recorded. There is no data to query,
no proxy that isolates the Command Centre, and no backfill. `lastSignInTime` is product-wide and
gives a single most-recent moment, not a count.

### ⚠️ Who signed up and never used it
**Not for the Command Centre. Product-wide only, server-side.** The Admin SDK gives 116 accounts
that never signed in *to anything*, overwhelmingly coaches and parents. For the 20 admin/staff who
are the actual Command Centre audience, "never used it" is unanswerable — a sign-in from the coach
app is indistinguishable from one here.

### ⚠️ Who used it and stopped
**Same limitation.** Product-wide you have 245 accounts dark over a year and 300 in the 90–365 day
band. Requires the service account on this Mac. It tells you nothing about Command Centre
abandonment specifically.

---

## What it would take

The only way to answer any of these is to **start recording**, and it necessarily starts from zero
— there is no history to recover.

The minimum is one write on page load: a doc keyed by `{uid}_{page}_{date}` in a new collection,
carrying uid, email, role, page name and `serverTimestamp()`. Idempotent per user/page/day, so
auto-refresh timers don't inflate counts. That single write makes all three questions answerable
from roughly a fortnight of accumulation, and it isolates the Command Centre from the mobile apps
because only these pages write it.

**On your hard constraint:** a usage page reading that collection live under the signed-in user is
exactly the pattern you want — it's Firestore at runtime, nothing baked. No seed array, no
fallback, no cached snapshot. The page would be empty on day one and fill up honestly, which is
the correct behaviour and worth saying out loud before it looks broken.
