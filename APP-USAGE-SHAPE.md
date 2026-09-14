# App usage — what the data can actually answer
**Date:** 2026-09-09 · read-only Admin SDK profiling · **nothing built, nothing written**

---

## Headline, before the detail

Your re-scope is right — this data is far richer than the Command Centre's. But it splits three ways:

| Audience | Verdict |
|---|---|
| **Coaches** | ✅ **Answerable, well.** 85 of 111 active coaches have activity records; 55 active in the last 7 days. |
| **Parents** | ❌ **Not answerable. Zero records.** 0 of 276 parent accounts have a single activity record in any collection. |
| **Centres** | ❌ **Effectively not answerable.** 4 of 152 centre accounts have any record. |

**The parent app records nothing.** I checked every collection that could plausibly hold parent
activity — `likes`, `chats`, `comments`, `posts`, `bookings`, `shop-orders`, `center-downloads`,
`center-feedbacks`, `gallery`, `express-interest-booking`. The social-feed collections *do* carry
real Auth UIDs, but they resolve to **coaches and admins, not parents** (`likes`: 594 coach / 10
admin / 0 parent). That's the internal coach feed, not a parent surface.

So the page is a **coach app usage page**. A parent or centre breakdown would be three empty
columns, and I'd rather say that now than build it.

---

## Collection shapes

### `watched-video` — 9,658 docs · **the attribution problem**

| Field | Type | Notes |
|---|---|---|
| `userId` | str | ⚠️ **app-local id, NOT an Auth UID** |
| `activityId` | str | → `learn-activities` (2,336) |
| `categoryId` | str | → `learn-categories` (9) |
| `parentId` | str | → `learn-subcategories` — a **lesson week, not a parent user** |
| `date` | int | epoch ms |

**Range: 2024-05-25 → 2026-09-09.** Your longest history by far.

**But `userId` doesn't join to `users`** — 1 of 320 distinct ids matches. It resolves only via
`coach-app-map` (77 docs), and that covers **72 of 320** users:

| Year | Attributable | Not attributable |
|---|---|---|
| 2024 | 50 | 261 |
| 2025 | 665 | 1,291 |
| 2026 | 5,487 | 1,904 |
| **Total** | **6,202 (64%)** | **3,456 (36%)** |

The map is also **stale** — `coach-app-map.lastSeen` runs 2026-06-29 → **2026-07-31** and its
`source` field says all 77 rows were derived from `coach-viewed-activity-tabs`, which itself only
starts 2026-06-29. So the map can only ever name coaches who used the app after late June 2026.
Pre-2026 history is mostly permanently anonymous.

**Consequence:** "who watches the most" is sound for 2026, shaky for 2025, unusable for 2024. The
map is rebuildable and refreshable — that's the single highest-value fix — but it cannot recover
users who never appeared in `coach-viewed-activity-tabs`.

### `coach-viewed-activity-tabs` — 2,430 docs · **the clean one**

| Field | Type | Notes |
|---|---|---|
| `coachId` | str | ✅ **real Auth UID — 120 of 123 resolve** (115 coach, 4 centre, 1 admin) |
| `userId` | str | app-local id (the `coach-app-map` key) |
| `date` | int | epoch ms |
| `tab` | str | `VIDEOS`, PDF tabs |
| `categoryName` / `subCategoryName` | str | denormalised — no join needed |

**Range: 2026-06-29 → 2026-09-09.** Only ~10 weeks, but it carries both id spaces *and* readable
names. This is the backbone of any usage page.

### `coach-watched-brain-video` — 37 docs
`coachId` (✅ 14/14 resolve), `activityId`, `activityName`, `categoryId`, `date`.
**Range 2026-07-12 → 2026-09-04.** Too small to rank on — a supporting signal only.

### `coach-testing-video-progress` — 48 docs
`userId` (✅ 29/30 resolve to Auth UIDs), `updatedAt`, `maxWatchedSeconds`, `questionsUnlocked`.
**Range 2026-06-29 → 2026-09-07.** Note `userId` here *is* an Auth UID — the opposite of
`watched-video`. The naming is inconsistent across collections; worth care.

### `events` — 13,462 docs
`coaches` (list, **321 distinct, 303 resolve**), `educationCenter` (623 distinct), `start`/`end`
(ISO string *and* Timestamp — mixed types), `sessionStatus`, `activity`, `title`.
This is **work delivered, not app usage.** Valuable as the denominator: app engagement per session
coached separates "quiet because inactive" from "working but ignoring the app".

### `feedbacks` — 7,237 docs
`coach` (**dict** — id is at `coach.value`, 214 of 228 resolve), `center`, `created` (ISO string),
`avgRating`, plus 5 pillar scores. **Range 2020-10-24 → 2027-01-27** — the future dates are dirty
data worth a look. Again an outcome measure, not usage.

### Also present, not in your list
- `watched-testing-video` (114) and `watched-entertainment-video` (64) — same app-local `userId`
  problem, 22% resolvable.
- `coaches-attendance` (6,411) — **unusable as-is.** No identity field; coach UIDs are *field
  names* (`{uid}`, `{uid}-entry`, `{uid}-exit`) rather than values. Queryable only by reading all
  6,411 docs client-side.

---

## The three questions, re-scoped to coaches

### ✅ Who is using the coach app most, and how much
**Answerable.** Rank by combined event count across `coach-viewed-activity-tabs` + `watched-video`
(via the map) + brain/testing. Solid for the last ~10 weeks on `coach-viewed-activity-tabs` alone;
back to 2024 on `watched-video` with the 36% attribution caveat stated on the page.

### ✅ Who signed up and never used it
**Answerable, and immediately useful: 26 of 111 active coaches (23%) have no activity record at
all.** Cross-referenced with `users.created` and `startDate` this separates new starters from
long-term non-adopters. Caveat: some of those 26 may be pre-June-2026 `watched-video` users lost
to the attribution gap — rebuilding the map would tighten this.

### ✅ Who used it and stopped, and when
**Answerable.** Last-activity per coach across all signals:

| Last activity | Active coaches |
|---|---|
| 0–7 days | 55 |
| 7–30 days | 20 |
| 30–90 days | 8 |
| 90–365 days | 2 |
| **never** | **26** |
| **total** | **111** |

Across all 442 coaches (incl. 331 inactive), 172 have any record — the rest are mostly departed
staff, so filter on `status='Active'`.

---

## Before I build — three things worth your call

1. **Parents and centres get no columns.** Nothing to show. Confirm that's acceptable, or we treat
   "why does the parent app record nothing" as a separate question.
2. **Rebuild `coach-app-map`?** It's stale (July 31) and covers 72/320 `watched-video` users. A
   refresh materially improves the historical view. It's a write to a live collection, so I won't
   touch it without a go-ahead and a backup.
3. **Attribution caveat on-page.** I'd rather the page state "36% of pre-2026 video views can't be
   attributed" than silently under-count a coach. Confirm you want it visible.

Design constraint noted and unchanged: live Firestore reads under the signed-in user, nothing baked.

---

## Parked, as instructed
- **Command Centre instrumentation** (one `serverTimestamp` write per user/page/day) — agreed
  design, not now.
- **`one-on-one-meetings` does not exist.** Zero docs, absent from all 109 collections, yet
  `one-on-one-meetings.html` makes 3 `collection()` calls against it and CLAUDE.md documents it.
  Noted, not fixed.
