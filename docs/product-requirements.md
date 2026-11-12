# Socius — Product Requirements

| | |
|---|---|
| **Status** | Draft v0.1 |
| **Authors** | Shreyas Vaid |
| **Last updated** | 2026-11-11 |
| **Audience** | Contributors |

> What Socius does and why. How it is built lives in the [high-level design](high-level-design.md). The game rules (scoring, periods, excusals, membership) are defined once, in the [game engine design](designs/game-engine.md#decided-rules); this document summarizes and links to them. Significant decisions get an ADR in `docs/adr/`; feature-level detail goes in a spec in `docs/specs/`. When implementation proves part of this wrong, update the doc in the same PR.

---

## 1. Overview

Socius is a cross-platform (iOS + Android) fitness accountability app for small groups of people who already know each other: couples, families, friends, roommates. The group's admin sets a period (a week, a month, any whole number of days) and a target (for example, 4 workouts), the same for everyone, and each member checks in whenever they train. When the period ends, at midnight in the group's time zone, the member with the fewest check-ins takes the punishment the group agreed on: buying dinner, doing a chore, whatever the group decides. If everyone hits the target, nobody loses.

The product bet is that **social stakes among people you live with or see every week** keep people training more reliably than streaks, badges, or anonymous leaderboards.

### 1.1 Problem

- Most fitness apps are single-player. Motivation fades and nothing happens when you skip.
- Existing social fitness apps tend to be feeds and leaderboards among loose connections, or money-staking apps that are punitive and solitary.
- Small groups already try to hold each other accountable through group chats and ad-hoc bets. That has no structure, no fair scoring, and gets forgotten by Wednesday.

### 1.2 Prior art

Group accountability is a crowded space (e.g., Pact, Forfeit, DealUp, Repple). Socius does not claim novelty. What it focuses on is:

1. **One shared target and deadline for people who know each other**: everyone trains toward the same number by the same deadline, on their own schedule, and one check-in counts in every group a member belongs to.
2. **Lightweight, non-monetary stakes**: punishments are social, stated, and unenforced.
3. *Differentiator still to be written (see Q11).*

---

## 2. Goals and non-goals

### 2.1 Goals (v0.1)

- G1. A group of 1–8 people can form a group, set a period and a target N, and check in workouts. A group of 1 never has a loser.
- G2. Scoring is fair because everyone has the same target N ([rules](designs/game-engine.md#decided-rules)).
- G3. A loser is determined automatically at the end of each period and announced to the group.
- G4. Body and health data stay private to the individual.
- G5. Works on iOS and Android from a single codebase.
- G6. Built to production engineering standards: written specs, automated tests, CI, and a typed API contract.

### 2.2 Non-goals

- N1. **No money handling.** Socius never collects, holds, or moves money. Punishments are free text.
- N2. **No enforcement of punishments.** The app announces; the group settles.
- N3. **No public social network.** No feeds, followers, or discovery. Groups are invite-only.
- N4. **Food logging is not scored** in any phase. Points come from workouts only.
- N5. **No anti-cheat in v0.1.** Check-ins are on the honor system (see §5.3).
- N6. Not a medical product. No diagnosis or treatment advice.

### 2.3 Success criteria for v0.1

- The founding test group (4–5 people) uses it for at least four closed 7-day periods.
- Period results are computed correctly with zero manual intervention.
- CI green on `main`; every scoring invariant in the [engine design](designs/game-engine.md#testing-approach) has a named test of the type the design gives.

---

## 3. Users

| Persona | Example | Needs |
|---|---|---|
| Couple | Two partners, one cutting, one bulking | Same target, different plans, friendly rivalry |
| Roommates | 3–4 people in an apartment | Low-friction check-ins, a punishment that matters (dishes) |
| Family | Siblings in different cities | One deadline in the group's time zone, shown to each member in their own local time |
| Solo | One user, no group | Plans and tracking without the game; supported but not the focus |

Age requirement: **18+** for v0.1 (health data + calorie targets + punishment mechanics). Revisit later.

---

## 4. Glossary

| Term | Definition |
|---|---|
| **User** | A person with an account. |
| **Profile** | A user's private body data and goal. Never visible to others. |
| **Group** | A set of 1–8 members sharing a period, a target, a time zone and a punishment. |
| **Admin** | A member who can change group settings, excuse members, and remove members. The group's creator is the first admin. (Earlier drafts called this role "Owner".) |
| **Period** | The scoring window: a whole number of days set by the admin, midnight to midnight in the group's time zone. [Rule](designs/game-engine.md#time-model). |
| **Target N** | The number of check-ins per period the group agrees on, the same for every member. [Rule](designs/game-engine.md#decided-rules). |
| **Check-in** | A user's claim that they completed a workout, counted at the moment the server receives it. Optionally carries proof photos. |
| **Points** | Check-ins in the period, capped at N. [Rule](designs/game-engine.md#decided-rules). |
| **Eligible / Excused / Joined mid-period** | Whether a member can lose a given period. [Rule](designs/game-engine.md#eligibility-and-the-loser-rule). |
| **Deadline** | The end of a period: midnight in the group's time zone. [Rule](designs/game-engine.md#time-model). |
| **Tie-break** | A random pick among members tied for the fewest points. [Rule](designs/game-engine.md#eligibility-and-the-loser-rule). |
| **Punishment** | Free text the loser of a period is expected to do. |
| **Plan** | A per-user workout plan fitted to the group's target and the user's goal (v0.4). |

---

## 5. Product requirements

Requirements are labeled `FR-x` and referenced from specs and tests.

### 5.1 Accounts and profiles (v0.1)

- FR-1. Sign up and sign in via the managed auth provider (email + Sign in with Apple; Google later).
- FR-2. Onboarding collects the profile fields in §8.1 that v0.1 actually uses. Everything else is deferred.
- FR-3. Users can edit their profile and goal at any time.
- FR-4. Users can delete their account and all associated data from inside the app (App Store requirement).

### 5.2 Groups (v0.1)

- FR-5. A user can create a group: name, period length, target N, time zone (defaults to the creator's), punishment text. The admin taps Start when everyone has joined; the first period begins at the next midnight in the group's zone.
- FR-6. An admin can invite members via a shareable invite code/link. Codes expire and can be revoked.
- FR-7. Max 8 active members per group in v0.1.
- FR-8. Members cannot leave a group on their own; the admin removes members. Each group has exactly one admin, starting with the creator; handing the role to another member is defined in spec 0001. Removal mid-period: see [Decided Rules](designs/game-engine.md#decided-rules).
- FR-9. A user may belong to more than one group.

### 5.3 Check-ins (v0.1)

- FR-10. A member can check in any number of times; each check-in is a point, up to N. [Rule](designs/game-engine.md#decided-rules).
- FR-11. A check-in counts in the period that is open when the server receives it. [Rule](designs/game-engine.md#decided-rules).
- FR-12. A check-in may include up to 3 optional proof photos, visible to members of the groups it counted in.
- FR-13. A member can undo their own check-in while every period it counts in is still open. [Rule](designs/game-engine.md#decided-rules).
- FR-14. **Honor system.** No verification in v0.1. *(Planned: a member can "challenge" a check-in without photos; resolution TBD; see Q6.)*
- FR-15. A check-in counts in every group the user belongs to.
- FR-15a. Every rejected action shows a specific message saying why (for example, "That period has already ended.").
- FR-15b. The app shows each group's deadline, and every check-in time, in the member's own local time.

### 5.4 Excusals (v0.1)

See §7.

### 5.5 Scoring and results (v0.1)

See §6.

### 5.6 Notifications (v0.1)

- FR-16. Reminder if the member hasn't checked in since midnight in the phone's current time zone by a configurable time (default 19:00). The phone reports its zone when the app opens.
- FR-17. *(Removed: rest-day vote notifications. Rest-day votes are cut from v0.1.)*
- FR-18. *(Removed: vote reminders.)*
- FR-19. Period closed → "results are in" notification to the group. The notification doesn't name the loser; the results screen does.
- FR-20. Users can mute each category.

### 5.7 Calorie targets and food logging (v0.2–v0.3)

See §8. Not scored, ever (N4).

---

## 6. Scoring

The full rules, with their edge cases and tests, are in the [game engine design](designs/game-engine.md#decided-rules). In short:

- Each check-in earns a point, up to the group's target N. Periods are a whole number of days, set by the admin, and end at midnight in the group's time zone.
- If every eligible member reaches N, nobody loses. Otherwise the eligible member with the fewest points loses; a tie at the bottom is broken by a random pick. Members who joined mid-period or were excused by an admin can't lose that period, and fewer than two eligible members means no loser.
- Results are computed automatically and never changed afterwards. Settings changes take effect from the next period.

### 6.1 Punishment

- Free text on the group, editable by an admin. Each period saves the text in force when it starts, and edits take effect from the next period, so editing mid-period doesn't change the current stakes.
- Displayed with the period's result. No tracking of whether it was done (maybe a "done" toggle later).

### 6.2 Target advisor (v0.2)

When the target is set, Socius checks each member's goal against N and suggests changes (e.g., "Body recomposition with 2 workouts a week is light. Consider 4."). Suggestions only.

---

## 7. Excusals

An admin can excuse a member from a period for any reason, so they can't lose it; the group sees it. There are no skip tokens or rest-day votes in v0.1; only check-ins count. Exact rules: [Decided Rules](designs/game-engine.md#decided-rules).

---

## 8. Profiles, calorie targets, and plans

### 8.1 Profile fields

| Field | Used for | Phase |
|---|---|---|
| Display name | Group UI | v0.1 |
| Goal: lose fat / build muscle / recomposition / maintain | Target advisor, targets, plans | v0.1 (stored), v0.2 (used) |
| Date of birth | 18+ gate; BMR | v0.1 |
| Sex used for calorie formula | BMR | v0.2 |
| Height, weight | BMR | v0.2 |
| Activity level outside workouts | TDEE multiplier | v0.2 |
| Target rate of change | Target calories | v0.2 |
| Body-fat % (optional) | Alternate BMR formula (Katch-McArdle) | v0.2 |
| Training experience | Plans | v0.4 |
| Equipment access (gym / home / none) | Plans | v0.4 |
| Injuries / limitations | Plans | v0.4 |

Rule: **only ask for a field in the phase that uses it.** Every onboarding field costs users.

### 8.2 Calorie targets (v0.2)

- BMR via **Mifflin–St Jeor**: `10·kg + 6.25·cm − 5·age + s`, where `s = +5` (male formula) or `−161` (female formula). Katch–McArdle if body-fat % is given.
- TDEE = BMR × activity multiplier (1.2 / 1.375 / 1.55 / 1.725 / 1.9).
- Target = TDEE ± adjustment derived from goal and target rate.
- **Safety guardrails (required, not optional):**
  - Cap weight-loss rate (initial default: ≤ 1% of body weight per week).
  - Enforce a calorie floor (initial default: commonly cited 1,200 / 1,500 kcal guidance). **Validate these defaults against a reputable source before shipping v0.2.**
  - Never show a target below the floor; show a neutral message instead.
  - Disclaimer: not medical advice.
- Open question Q7: how to handle users who don't want to pick a formula sex.

### 8.3 Food logging (v0.2 manual, v0.3 photo)

- v0.2: manual entry (name, calories, protein/carbs/fat), favorites, recent foods.
- v0.3: photo → backend calls a vision model → returns an **editable estimate**. The user always confirms. Estimates are shown as approximate.
- Food data is private (§9). Never scored (N4).

### 8.4 Workout plans (v0.4)

- Rule-based generator: (goal, experience, target N, minutes/session, equipment) → weekly split + exercises + set/rep ranges.
- Rule-based on purpose: deterministic, testable, explainable. ML/LLM is a possible later enhancement, not the foundation.

---

## 9. Privacy and visibility

| Data | The user | Group members | Socius developers |
|---|---|---|---|
| Height, weight, age, sex, body-fat % | ✅ | ❌ | Encrypted at rest; no casual access |
| Goal | ✅ | ❌ *(Q5: allow opt-in sharing?)* | — |
| Calorie targets, food logs, food photos | ✅ | ❌ | — |
| Display name | ✅ | ✅ | — |
| Check-ins (time, shown in each viewer's local time) | ✅ | ✅ (groups the check-in counted in) | — |
| The phone's current time zone (stored for reminders) | ✅ (stored) | ❌ never shown (reveals location) | — |
| Proof photos | ✅ | ✅ | — |
| Points and period results | ✅ | ✅ | — |
| Excusals | ✅ | ✅ (who was excused and by whom; the reason is never stored) | — |

Enforcement is described in the [high-level design §8](high-level-design.md#8-privacy-enforcement).

Retention: proof photos deleted after 30 days (Q9). Account deletion hard-deletes profile, food, and photos; check-ins are anonymized so historical group results stay consistent. A deleted account counts as a removal from every group; how it appears in past results is still open (Q12).

---

## 10. Roadmap

| Phase | Scope | Exit criteria |
|---|---|---|
| **0: Foundation** | Design doc, ADRs, monorepo scaffold, CI, local dev env, auth wired end-to-end | "Hello authenticated user" on a real iPhone via dev build; CI green |
| **v0.1: The game** | Profiles (min), groups, invites, periods and target, check-ins (+ optional photos), admin excusals, scoring, close, results, push ([engine design](designs/game-engine.md)), account deletion | Test group uses it for at least four closed 7-day periods |
| **v0.2: Targets** | Full profile, calorie/macro targets with guardrails, manual food logging, target advisor | Targets validated against reference calculators |
| **v0.3: Photo logging** | Photo → editable macro estimate via vision model | Estimates always user-confirmed |
| **v0.4: Plans** | Rule-based per-user workout plans fitted to the group's target | Plans generated for every goal × target combination in tests |
| **Later** | Check-in challenges, fixed training days, pausing a group, verifiable tie-break and suspense animation, Apple Health / Health Connect import, widgets, Android parity polish | — |

---

## 11. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Scope creep: three products in one | Never ships | Strict phase gates; v0.1 is the game only |
| Retention: novelty wears off | Test group stops | Ship v0.1 fast; measure weekly; iterate on the loop before features |
| Health harm from calorie features | User harm; App Store rejection | Guardrails in §8.2 are required; food never scored |
| Privacy leak of body data | Trust destroyed | Privacy table enforced by tests; minimal data collection |
| Time-zone or close bugs in scoring | Wrong loser; arguments | See the engine design's [Risks & Mitigations](designs/game-engine.md#risks--mitigations) |
| Photo estimate inaccuracy | Users mistrust | Always editable; labeled as estimate |
| Two-person team coordination | Merge pain | PRs, CI, specs before code, clear ownership |

---

## 12. Open questions

Game-rule questions (multiple groups, time zones, ties, rest-day votes) are decided in the [engine design](designs/game-engine.md#decided-rules), which also lists its own still-open items.

| # | Question | Current lean |
|---|---|---|
| Q5 | Can a user opt in to sharing their goal with the group? | Yes, opt-in, v0.2 |
| Q6 | Check-in challenges: mechanics and resolution | Defer to after v0.1 |
| Q7 | Calorie formula for users who don't select a formula sex | Average of both formulas, clearly labeled |
| Q9 | Proof photo retention period | 30 days |
| Q10 | Ownership split between the two contributors (is a second person still contributing?) | TBD |
| Q11 | Differentiator: one sentence on what Socius does that other accountability apps don't | TBD |
| Q12 | How a deleted account appears in past period results | Likely "Anonymous member"; decided in the account-deletion spec |
