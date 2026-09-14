# PII split — backup, field list, and what writes them
**Date:** 2026-09-09 · **Status: PROPOSAL. No data has been moved. `users` is untouched.**

---

## 1. Backup — done and verified

| | |
|---|---|
| File | `~/mm-private-backups/users_FULL_20260909-110312.json` |
| Docs | **890** (whole collection, every field) |
| Size | 1,044,874 bytes |
| SHA-256 | `53483c3f67f8c690de838a45ba2347db6b0e0390ba3f0f8203d674cc4b458fc8` |
| Perms | `600`, directory `700` |

Verified by reloading the file and re-counting: 890 docs on reload, and per-field non-empty
tallies match live exactly (tfn 204, bsb 169, accountNumber 169, bankName 166, super 198, DOB 200,
address 435, claimTaxFreeThreshold 207, bankAccount 18).

**Deliberately stored outside `~/Command-Centre`** — that repo is served by GitHub Pages, so a
backup containing 204 TFNs and 169 bank accounts committed there would publish them. It is also
outside `~/mini-monstars-agent`, which is a git repo.

---

## 2. Proposed field list

Split into two tiers, because one of your five categories is load-bearing and the rest aren't.

### Tier 1 — move now. Verified zero breakage in this repo.

All 8 sit on **243 docs, every one a coach** (106 Active, 137 Inactive). No parent, centre or admin
doc carries any of them.

| Field | Present | Non-empty |
|---|---|---|
| `tfn` | 243 | 204 |
| `dateOfBirth` | 243 | 200 |
| `superNumberAndProvider` | 243 | 198 |
| `claimTaxFreeThreshold` | 243 | 207 |
| `bsb` | 211 | 169 |
| `accountNumber` | 211 | 169 |
| `bankName` | 211 | 166 |
| `bankAccount` | 243 | 18 |

`claimTaxFreeThreshold` is my addition to your list — it's part of the same TFN declaration and
belongs with it. Say if you'd rather it stayed.

**Verified: not one of these is read by any Command Centre page.** I grepped all 11 live pages for
both `.field` and `'field'` forms — zero matches. The three agent scripts that mention them
(`coach_fields_probe.py`, `recruitment_discovery.py`, `recruitment_sync.py`) only *read*, and
`coach_fields_probe.py` redacts them on output. No script on the box writes `users` at all — the
six that write near it target `centre-compliance-*`, `first-session-emails`, `coach-app-map` and
`recruitment-pipeline`.

### Tier 2 — `address`. **Do not move blind. It will break things.**

`address` (435 non-empty) and `addressGeo` (415) are **load-bearing on the user doc**:

- `travel.html:981-982` — `coach.address` / `coach.addressGeo` are the origin for home-to-centre
  distance, which drives reimbursement.
- `travel.html:1277-1293` — `addressGeo` for coverage-coach proximity ranking.
- `travel.html:961, 1183` — coach state is **derived by regex from the address string**.
- `leaderboard.html` — 17 `.address` + 14 `.addressGeo` references.
- Also `centres.html`, `coaches.html`, `show-a-bit-of-love.html`.

Those are all staff pages, so they *could* be repointed at `users-private` and still work under the
rule. But that's a code change across four files, not a data move — and it's the opposite of the
"needs no audit to be safe" property that makes Tier 1 clean. **My recommendation: ship Tier 1 now,
handle `address` in the app audit.** It's also the least sensitive item in your list — an address
is not a TFN.

---

## 3. What writes these fields today — the answer you need before the move

**Nothing in this repo, and nothing on this Mac.** Confirmed by exhaustive grep of all 11 pages and
every `.py` in `~/mini-monstars-agent`.

**Therefore the writer is the mobile app's onboarding form** — which is not in this repo, not on
this machine, and not something I can read or change.

### This is the blocker, and it cuts both ways

Your design note — *"any app reading users for a name or a role keeps working untouched, because
nothing it reads moved"* — is correct **for reads**. It does not hold for writes.

The onboarding form currently writes `tfn`, `bsb`, `accountNumber`, `bankName`, `super…`,
`dateOfBirth` to `users/{uid}`. After the split those fields live in `users-private/{uid}`. The form
will keep writing them to `users/{uid}`, where:

1. The rules still permit it (any authenticated user can write their own `users` doc), so **it will
   fail silently, not visibly.**
2. Re-created PII lands right back in the collection we just cleaned — and back under the permissive
   catch-all read.

So the sequence has to be: **repoint the onboarding form first, then migrate the data.** Migrating
first leaves a form quietly writing TFNs back into the exposed collection.

Two things I'd want before moving anything:

- **Who owns the mobile app codebase, and can it be changed?** If it can't be repointed quickly, a
  scheduled sweep that moves stragglers from `users` to `users-private` is the fallback — ugly, but
  it bounds the exposure window.
- **Does the app read these back?** Almost certainly yes on a profile screen. Self-read still works
  (`request.auth.uid == doc id`), but only once the app knows to read `users-private`.

---

## 4. Proposed rule (not deployed)

```
match /users-private/{uid} {
  allow read, write: if request.auth != null && request.auth.uid == uid;
  allow read, write: if request.auth != null
    && get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role in ['admin','staff'];
}
```

Self-access first so the common case costs no extra read; the staff branch costs one billed
document read per evaluation. Custom claims would remove that cost — 0 accounts currently have any.

**This rule alone is not enough.** The catch-all `match /{document=**}` would also match
`users-private` and grant any authenticated user read+write, exactly as it does today for the nine
analytics collections. `users-private` **must** be added to the catch-all's exclusion list, in both
the read and write conditions, or the split achieves nothing.

---

## 5. Recommended order

1. Confirm the Tier 1 field list (and `claimTaxFreeThreshold`).
2. Repoint the onboarding form to `users-private/{uid}`. **External dependency — the long pole.**
3. Deploy the `users-private` rule *plus* the catch-all exclusion.
4. Migrate the 243 docs, backup in hand, then verify field-by-field.
5. Delete the fields from `users` only after (4) verifies.
6. App audit for the rest of the ruleset, `address` included.

Steps 3–5 are production writes. I'll do none of them without an explicit go-ahead.
