# Spec 0001: Groups and invites

| | |
|---|---|
| **Status** | Draft |
| **Author** | Shreyas Vaid |
| **Design refs** | PRD FR-5–FR-9, §9; [engine design](../designs/game-engine.md#decided-rules) Decided Rules, [Eligibility](../designs/game-engine.md#eligibility-and-the-loser-rule), [Data model](../designs/game-engine.md#data-model-game-engine-only), [Request rules](../designs/game-engine.md#request-rules-api), Stage 4 items 28 and 32; HLD §4–§5; ADR-0004 |
| **Phase** | v0.1 |

## Problem

The engine can score a group's periods, but nobody can make a group yet. A user needs to create one, get the right people into it, start the game when everyone is in, and manage who is playing. The admin needs to remove someone who shouldn't be there and hand the role on. This spec covers everything about a group except its periods, check-ins, excusals and results, which the engine design already defines.

The game rules that membership affects (who plays a period, removal, re-adding, joining mid-period, deleted accounts) are in the engine design's [Decided Rules](../designs/game-engine.md#decided-rules). This spec defines the requests that change membership and does not restate those rules.

## Behavior

### Create a group

1. A signed-in user enters a name, period length, target N, time zone and punishment text. The time zone defaults to the phone's zone. Bounds for N and period length are in Decided Rules.
2. The server creates the group, its settings and an `admin` membership for the creator. The group is set up but not playing.
3. The creator is now the admin. There is exactly one admin per group (Decided Rules, Roles).

### Invite and join

1. The admin opens the group and taps **Invite**. The server returns an invite code and a link that contains it. The admin shares the link however they like (messages, group chat). The app sends nothing itself.
2. A group has at most one usable invite at a time. Creating a new one revokes the old one, so "reset link" is the same action as "new invite".
3. An invite is multi-use and expires 7 days after it is created **[proposed]**. The admin can revoke it at any time.
4. A recipient opens the link, or types the code. If they aren't signed in, they sign in first and then return to the invite.
5. The app shows a preview before joining: the group's name, the admin's display name, the number of active members, whether the game has started, and the current settings (N, period length, punishment text). The punishment is shown so nobody joins without knowing what they could lose.
6. The recipient taps **Join**. They become an active member with `joined_at` set to the server time. Whether they play the current period follows from Decided Rules (Joining; Period).
7. Joining fails if the group already has 8 active members, if the user is already an active member, or if the invite is unknown, expired or revoked. Each failure has its own message (FR-15a).

### Start

1. The admin adds the members and sets the settings, then taps **Start**. Before Start, settings can be changed freely; there is no current period for a change to wait for.
2. Start needs at least 2 active members **[proposed]**. With one member there can never be a loser, so a one-person game is almost always a setup mistake.
3. The server records `started_at`. The first period begins at the next start of a day in the group's zone (Decided Rules, Period). The app shows the countdown to it.
4. Start happens once. Members can still join after Start, under the joining rules.

### Remove a member

1. The admin opens the member list and removes a member. The app asks for confirmation and says the member is excused for the current period.
2. The server sets `removed_at` on the membership. The effect on the current period is defined in Decided Rules (Membership).
3. The admin can't remove themselves. To leave, they hand over the role first; then the new admin can remove them.
4. Members can't leave on their own (Decided Rules, Membership). Deleting their account is the only way out without the admin.

### Re-add a member

1. A removed member comes back by accepting an invite, like anyone else. The admin can't put someone back without their consent **[proposed]**.
2. If the member was removed during the current period, or the group hasn't started, the server reuses their earlier membership row: it clears `removed_at` and keeps `joined_at`. This is the "re-adding restores their earlier state" rule in Decided Rules.
3. If they were removed in an earlier period, they get a new membership row with `joined_at` set to now, so they join mid-period like any new member.
4. Re-adding counts toward the 8-member cap.

### Hand over the admin role

1. The admin picks another active member and confirms.
2. In one transaction, the current admin becomes a `member` and the target becomes `admin`.
3. The former admin stays in the group as a member.

### The admin deletes their account

Account deletion itself is specified in the account-deletion spec (PRD FR-4). This spec defines only what happens to the admin role.

1. Before deleting, the app tells an admin which groups they run and offers to hand over each one.
2. If the admin deletes anyway, the role passes automatically to the active member with the earliest `joined_at`, with the lowest user ID breaking ties **[proposed]**. This happens in the same transaction as the removal.
3. If no other active member remains, the group ends **[proposed]**: `ended_at` is set, no new periods are created, and members who were in its periods can still read their results.

### Rename a group

The admin can change the group's name at any time. The other settings go through `PUT /settings`, which is a game endpoint (engine design, Stage 4 item 32).

### Edge cases

- **Join between Start and the first midnight.** The joiner plays the first period in full, because they joined before it started.
- **Two joins race for the last place.** Exactly one succeeds; the other gets `group-full`.
- **Join and remove race.** Membership writes for a group are serialized (see Data changes), so each sees the other's result.
- **A removed member's check-ins between removal and re-add.** After a same-period re-add, `removed_at` is cleared, so those check-ins count for the period. This follows from "restores their earlier state".
- **A removed member opens an old invite link.** Treated like any other acceptance.
- **The admin's own invite.** Accepting an invite for a group you're already active in returns `already-member`.
- **Settings and Start in the same minute.** The first period copies `group_settings` when its row is created, so the settings in force at the first midnight are the ones used.

## Acceptance criteria

- [ ] Given a signed-in user, when they create a group with valid settings, then the group exists with them as its only member and its admin, and `started_at` is null.
- [ ] Given settings out of range or an unknown time zone, when a group is created, then the request fails with `invalid-request` and nothing is stored.
- [ ] Given an admin, when they create an invite, then they get a 10-character code that expires in 7 days, and any earlier unrevoked invite for the group is revoked.
- [ ] Given a non-admin member, when they try to create or revoke an invite, then the request fails with `not-admin`.
- [ ] Given a valid code, when a signed-in non-member previews it, then they see the group name, admin display name, active member count, started flag and settings, and no other member's details.
- [ ] Given a valid code and a group with fewer than 8 active members, when a user accepts it, then they become an active `member` with `joined_at` set to the server time.
- [ ] Given a group with 8 active members, when a user accepts an invite, then the request fails with `group-full`.
- [ ] Given a group with 7 active members, when two users accept an invite at the same moment, then exactly one joins and the other gets `group-full`.
- [ ] Given an unknown code, when a user previews or accepts it, then the request fails with `invite-not-found`.
- [ ] Given an expired or revoked code, when a user previews or accepts it, then the request fails with `invite-expired`.
- [ ] Given an active member, when they accept another invite for the same group, then the request fails with `already-member`.
- [ ] Given a group with 2 or more active members and no `started_at`, when the admin taps Start, then `started_at` is set and `GET …/periods/current` returns `status: not_started` with `starts_at` at the next start of a day in the group's zone.
- [ ] Given a group with 1 active member, when the admin taps Start, then the request fails with `too-few-members`.
- [ ] Given a started group, when the admin taps Start again, then the request fails with `already-started`.
- [ ] Given an admin and an active member, when the admin removes the member, then `removed_at` is set, and the member's state for the current period follows Decided Rules.
- [ ] Given an admin, when they try to remove themselves, then the request fails with `target-is-admin`.
- [ ] Given a member removed during the current period, when they accept an invite, then their earlier membership row is reused with `removed_at` cleared and `joined_at` unchanged.
- [ ] Given a member removed in an earlier period, when they accept an invite, then a new membership row is created with `joined_at` set to now.
- [ ] Given an admin and an active member, when the admin hands over the role, then the target is `admin`, the former admin is `member`, and the group has exactly one admin.
- [ ] Given an admin with other active members, when the admin's account is deleted, then the active member with the earliest `joined_at` becomes admin in the same transaction.
- [ ] Given an admin who is the group's only active member, when their account is deleted, then `ended_at` is set and no new period is created for the group.
- [ ] Given a user who isn't an active member, when they call any group endpoint except the invite preview and accept, then the response is 404 `not-member` (engine design, Request rules).
- [ ] Given a removed member, when they list their groups, then the group isn't listed, and they can still read periods whose member set includes them.

## API changes

All endpoints are under `/v1`, need a valid token (ADR-0004), and return RFC 9457 problem responses as in the engine design's item 28.

| Endpoint | Who | Does | Error codes |
|---|---|---|---|
| `POST /groups` | any user | Creates the group, `group_settings` and the admin membership. Body: `name`, `target_n`, `period_days`, `tz_name`, `punishment_text`. Returns `GroupOut`. | `invalid-request` |
| `GET /groups` | any user | The caller's active groups: `id`, `name`, `started_at`, `my_role`. | — |
| `GET /groups/{id}` | active member | `GroupOut`: `id`, `name`, `started_at`, `ended_at`, `my_role`, `settings`, `members` (active only: `user_id`, `display_name`, `role`, `joined_at`). | `not-member` |
| `PATCH /groups/{id}` | admin | Renames the group. Body: `name`. | `not-admin`, `invalid-request` |
| `POST /groups/{id}/start` | admin | Sets `started_at`. Returns the first period's `starts_at`. | `not-admin`, `already-started`, `too-few-members` |
| `POST /groups/{id}/invites` | admin | Revokes any unrevoked invite, creates a new one. Returns `code`, `url`, `expires_at`. | `not-admin` |
| `GET /groups/{id}/invites/current` | admin | The usable invite, or 404 `not-found` if there is none. | `not-admin`, `not-found` |
| `DELETE /groups/{id}/invites/current` | admin | Revokes the usable invite. Idempotent. | `not-admin` |
| `GET /invites/{code}` | any user | Preview: `group_name`, `admin_display_name`, `member_count`, `started`, `target_n`, `period_days`, `punishment_text`, `expires_at`. | `invite-not-found`, `invite-expired` |
| `POST /invites/{code}/accept` | any user | Joins or re-joins the group. Returns `GroupOut`. | `invite-not-found`, `invite-expired`, `already-member`, `group-full` |
| `DELETE /groups/{id}/members/{user_id}` | admin | Removes an active member. | `not-admin`, `target-not-member`, `target-is-admin` |
| `PUT /groups/{id}/admin` | admin | Hands over the role. Body: `user_id`. | `not-admin`, `target-not-member`, `target-is-admin` |

New problem codes, added to the enum in engine design item 28:

| Code | Status | Meaning |
|---|---|---|
| `invite-not-found` | 404 | No invite has this code. |
| `invite-expired` | 410 | The invite existed but has expired or been revoked. The message tells the user to ask for a new one. |
| `already-member` | 409 | The caller is already an active member. |
| `already-started` | 409 | Start was already tapped. |
| `too-few-members` | 409 | Start needs at least 2 active members. |
| `target-is-admin` | 409 | The admin can't remove themselves or hand the role to themselves. |

**Invite codes.** 10 characters from Crockford's base32 alphabet (no I, L, O or U), generated with `secrets`, giving 50 bits. The server accepts them case-insensitively, with or without a separating hyphen, and the app shows them as `XXXXX-XXXXX`. The link is `socius://invite/<code>` until universal links are set up with the App Store build; the code alone always works.

**Settings before Start.** `PUT /groups/{id}/settings` (engine design item 32) also works before Start. It returns `applies_from: null` until Start, because the first period's start isn't known yet.

## Data changes

`groups`, `group_settings` and `memberships` are as in the engine design's data model, with one addition. `invites` is in HLD §4; this spec adds `created_at` and the indexes.

```text
groups    + ended_at        -- null while the group can play; set when no active member remains
invites   id, group_id, code, created_by, created_at, expires_at, revoked_at
          PK (id); UNIQUE (code); INDEX (group_id) WHERE revoked_at IS NULL
```

- **Checks:** `name` 1–60 characters, `punishment_text` 1–280 characters **[proposed]**, `code` exactly 10 characters, `expires_at > created_at`.
- **Codes are stored as plain text.** They are short-lived, revocable, and only grant a place in one group that the admin can take back. Hashing them would stop the admin from seeing the current code again, for little gain.
- **Serializing membership writes.** Accept, remove, hand over, Start and admin succession each lock the group row first with `SELECT … FROM groups WHERE id = :id FOR UPDATE`. That makes the 8-member cap and the single-admin rule safe under concurrent requests without a retry loop. The partial unique indexes on `memberships` stay as a backstop.
- **Handover order.** Within the transaction, the current admin is demoted before the target is promoted, because the partial unique index on the admin role is checked per statement.
- **Ended groups.** `ensure_current_period` returns `None` for a group with `ended_at` set, so the close job creates no more periods for it.
- **Timestamps** (`joined_at`, `removed_at`, `started_at`, `created_at`, `expires_at`) come from the injected `Clock`, never from the database.

## Test plan

- **Domain (pure, in `domain/membership.py` and `domain/invites.py`):**
  - `normalize_code` accepts upper and lower case, with and without the hyphen, and rejects the excluded letters and wrong lengths.
  - `generate_code` uses `secrets`, so it lives in the service layer, not `domain/` (the purity guard allows `secrets` only as `pick_loser`'s default). Its output always normalizes to itself and uses only the alphabet (property test).
  - `admin_successor(members)` picks the earliest `joined_at`, breaks ties by user ID, ignores removed members, and returns `None` when nobody is left (property test: the result is always an active non-admin member, or `None`).
  - `rejoin_reuses_row(removed_at, current_period_start, started)` covers the same-period, earlier-period and not-started cases.
- **API (pytest, `db` marker):** one test per acceptance criterion, plus:
  - each endpoint's `not-member` and `not-admin` cases;
  - the preview returns no member names other than the admin's (privacy, PRD §9);
  - `GET /groups/{id}` never returns any member's time zone or profile fields;
  - joining mid-period: the joiner shows as `joined_mid_period` in `GET …/periods/current`;
  - a same-period re-add restores the member's earlier state in the live scores.
- **Concurrency (`concurrency` marker):**
  - two accepts racing for the last place: exactly one `group-full`;
  - a handover racing a removal of the target: the group ends with exactly one admin who is an active member.
- **Schemathesis:** the new endpoints are in the schema, so the existing contract run covers them, with every documented error status.
- **Mobile (Stage 9):** the invite preview shows the punishment; Start is disabled with one member; the remove confirmation says the member is excused.

## Alternatives considered

- **Single-use invites, one per person.** Tighter, but the admin must create and send one per member, and a family group chat can't share one link. The 8-member cap and admin removal already bound the damage of a leaked multi-use link.
- **Invite by email or phone number.** Needs sending infrastructure and exposes contact details to the server. The share sheet does the job with no new data.
- **Search users by name and add them directly.** Needs a user directory, which leaks who uses the app, and adds people without consent.
- **Any member can invite.** More convenient, but the admin decides who plays, and the cap makes every place matter. Can be revisited after the trial.
- **Admin re-adds a removed member directly.** Faster, but it puts someone back into a game they could lose without asking them.
- **Hashed invite codes.** Standard for long-lived secrets. For a 7-day, revocable code that grants one group place, it costs the admin the ability to re-share the current code.
- **Auto-delete a group when its last member leaves.** Deletes history that members of past periods can still read.
- **Allow a one-person game.** Simpler Start rule, but it can never produce a loser.

## Risks

| Risk | Likelihood | How we'd notice | Mitigation |
|---|---|---|---|
| An invite link is posted publicly and a stranger joins | Low | The admin sees an unknown name in the member list | 7-day expiry, revocation, admin removal, 8-member cap, preview names the admin |
| Someone guesses a code | Very low: 50 bits against at most one live code per group | Spike in `invite-not-found` | Add a per-user rate limit on preview and accept if it happens |
| Two joins exceed the cap | Low | Concurrency test | Group row lock; partial index backstop |
| The automatic successor doesn't want the role | Medium | Group feedback | They can hand it on at once; the app prompts admins to hand over before deleting |
| An admin removes members to settle scores | Low | Group feedback | Removal makes the member excused, so it can't be used to make them lose; social, not technical |

## Out of scope

- Account deletion itself, including how a deleted member appears in past results (PRD Q12; account-deletion spec).
- Deleting or archiving a group by choice.
- Universal links (`https://` invite links); they come with the App Store build.
- Notifications for joins, removals and handovers.
- Per-user limits on groups created or joined.

## Open questions

1. **Invite expiry and reuse.** Proposed: one usable invite per group, multi-use, 7-day expiry, revocable. Confirm, or pick a different expiry or single-use invites.
2. **Admin succession on account deletion.** Proposed: the active member with the earliest `joined_at` becomes admin automatically. Alternatives: the group ends, or the deletion is blocked until the admin hands over.
3. **Minimum members for Start.** Proposed: 2. Confirm, or allow a one-person group to start.
4. **Group deletion.** Proposed: none in v0.1. A group ends only when no active member remains. Confirm, or add "end group" for the admin.
5. **Settings before Start.** Proposed: freely editable before Start, with `applies_from: null`. Confirm.
6. **Re-adding needs the member's consent.** Proposed: a removed member returns only by accepting an invite. Confirm, or let the admin re-add directly.
7. **Text limits.** Proposed: group name 1–60 characters, punishment text 1–280 characters.
8. **What the invite preview shows.** Proposed: group name, admin display name, member count, started flag, N, period length and punishment text, but no other member names. Confirm the privacy trade-off.

## Doc updates needed

Made in the PR that implements this spec, after the open questions are settled:

- **Engine design, data model:** add `groups.ended_at`; note that `ensure_current_period` returns `None` for ended groups (item 24).
- **Engine design, item 28:** add the six new problem codes.
- **Engine design, Request rules table:** replace "defined in spec 0001" with a link to this spec's API table, and list the new codes.
- **Engine design, Still open:** resolve "The admin deletes their account" by linking to this spec.
- **HLD §4:** add `created_at` to `invites`. **HLD §5:** add `POST /groups/{id}/start`, `PUT /groups/{id}/admin`, `GET /invites/{code}`, and the invite revoke and current-invite endpoints.
- **PRD glossary:** "Group" says 1–8 members; add that Start needs at least 2, if open question 3 is confirmed. **PRD FR-6:** add the 7-day expiry and one usable invite per group.
- **CLAUDE.md:** remove the item "removed member can still see results and gets the notification" from unconfirmed defaults if confirmed alongside this spec, and update the checklist.
