# Action required: coach PII has moved to a new Firestore collection

**Project:** `mini-monstars-au` · **Change made:** 9 September 2026 · **Status: live in production now**

## What changed

Eight sensitive fields have been moved off `users/{uid}` into a new collection,
`users-private/{uid}`, and **deleted from `users/{uid}`**. The document ID is unchanged — it is the
same Firebase Auth UID in both collections.

This was done because Firestore security rules allowed **any signed-in account** — every coach and
every parent, 891 accounts — to read all 890 user profiles, including tax file numbers and bank
details. Firestore has no field-level security, so separating the fields into their own collection
was the only way to restrict them.

## The eight fields that moved

| Field | Was | Is now |
|---|---|---|
| `tfn` | `users/{uid}` | `users-private/{uid}` |
| `dateOfBirth` | `users/{uid}` | `users-private/{uid}` |
| `superNumberAndProvider` | `users/{uid}` | `users-private/{uid}` |
| `claimTaxFreeThreshold` | `users/{uid}` | `users-private/{uid}` |
| `bsb` | `users/{uid}` | `users-private/{uid}` |
| `accountNumber` | `users/{uid}` | `users-private/{uid}` |
| `bankName` | `users/{uid}` | `users-private/{uid}` |
| `bankAccount` | `users/{uid}` | `users-private/{uid}` |

243 coach documents were migrated. Every value was verified present in the new location before it
was removed from the old one.

## What did NOT change

**Everything else on `users/{uid}` is exactly as it was** — `firstName`, `lastName`, `email`,
`role`, `status`, `children`, `phone`, `address`, `addressGeo`, `city`, `profilePic`,
`notificationToken`, onboarding flags, and all the rest.

**If a screen reads `users/{uid}` for a name, role or status, it needs no change.** Only code that
touches the eight fields above is affected.

## What you need to change

Anywhere the app **reads or writes** one of those eight fields, change the collection from
`users` to `users-private`. The document ID stays the same.

```js
// BEFORE
await updateDoc(doc(db, 'users', uid), {
  tfn, bsb, accountNumber, bankName, superNumberAndProvider,
  claimTaxFreeThreshold, dateOfBirth, bankAccount
});

// AFTER
await setDoc(doc(db, 'users-private', uid), {
  tfn, bsb, accountNumber, bankName, superNumberAndProvider,
  claimTaxFreeThreshold, dateOfBirth, bankAccount
}, { merge: true });
```

The onboarding / bank-details form is the main one. Please also check any profile or payroll screen
that displays a DOB or bank details.

Use `setDoc(..., { merge: true })` rather than `updateDoc` — for a coach who has not filled this in
yet, the `users-private` document will not exist and `updateDoc` throws.

## Permissions

The rule now in force:

```
match /users-private/{uid} {
  allow read, write: if request.auth != null && request.auth.uid == uid;
  allow read, write: if request.auth != null
    && get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role in ['admin','staff'];
}
```

- **A signed-in user can always read and write their own `users-private/{uid}`.** Onboarding works
  unchanged once it points at the new collection.
- Admin and staff accounts can read and write anyone's.
- Everyone else gets `PERMISSION_DENIED` — including listing the collection.

This is verified live: a signed-in coach reading another coach's `users-private` document gets 403,
and listing the collection gets 403.

## Until this is done

**Writes to the old location will not error — they will silently succeed**, because a user is still
allowed to write their own `users/{uid}` document. The data would simply land back in the exposed
collection.

A server-side job now sweeps nightly at 02:30 and moves any of these eight fields found on a
`users` document into `users-private`, deleting it from `users`. So nothing is lost in the
meantime — but **a coach's bank details may disappear from the app's view within 24 hours of being
entered**, because the app is still reading the old location. That is the visible symptom to expect
until the change is made, and the reason this shouldn't sit for long.

The sweep is a stopgap. Once the app is updated, tell us and we will retire it.

## Questions

Reply to Shane. If you need a test account with staff role to check the permission behaviour, ask.
