# ADR 0007: Scoring model: shared weekly target, fewest points loses

| | |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-11-11 |
| **Deciders** | Shreyas Vaid |
| **Supersedes** | — |
| **Superseded by** | — |

## Context
The core of the product is a fair, explainable weekly result that small groups trust without checking it. An earlier draft scored adherence (completed ÷ scheduled) against per-member goals.

## Options considered
1. **Adherence against per-member goals**: fair across different goals; harder to explain and needs per-member schedules.
2. **A shared weekly target N with raw points**: one sentence to explain; members must agree on one N.
3. Tie-break options: shared loss for all tied members; a random pick; a replayable hashed draw with a stored seed.

## Decision
Summary only; the engine design's Decided Rules is authoritative if the two ever differ.

A shared target N (1–7). Points are distinct check-in days plus a weekly skip token, capped at N. No loser if fewer than two members are eligible or every eligible member reaches N; otherwise the fewest points loses, and a tie is broken with `secrets.choice`, storing the candidates and the loser. Admin excusals and mid-week joins make a member ineligible for that week.

The exact rules live only in the engine design: [Decided Rules](../designs/weekly-game-engine.md#decided-rules) and [Eligibility and the loser rule](../designs/weekly-game-engine.md#eligibility-and-the-loser-rule). Rejected alternatives: [A–C and P](../designs/weekly-game-engine.md#alternatives-considered).

## Consequences
- Scoring is a pure function, property-tested against written invariants.
- A tied member can lose by chance; the result screen labels tie-breaks.
- A draw members can verify would need a seed column later.

## Amendments
- 2026-11-11: added the note that this decision text is a summary and the engine design is authoritative.
