# ADR 0007: Scoring model: shared weekly target, fewest points loses

| | |
|---|---|
| **Status** | Superseded |
| **Date** | 2026-11-11 |
| **Deciders** | Shreyas Vaid |
| **Supersedes** | — |
| **Superseded by** | [ADR-0011](0011-group-periods.md) |

## Context
The core of the product is a fair, explainable weekly result that small groups trust without checking it. An earlier draft scored adherence (completed ÷ scheduled) against per-member goals.

## Options considered
1. **Adherence against per-member goals**: fair across different goals; harder to explain and needs per-member schedules.
2. **A shared weekly target N with raw points**: one sentence to explain; members must agree on one N.
3. Tie-break options: shared loss for all tied members; a random pick; a replayable hashed draw with a stored seed.

## Decision
Superseded by [ADR-0011](0011-group-periods.md). This text records the decision as it was made.

A shared target N (1–7). Points are distinct check-in days plus a weekly skip token, capped at N. No loser if fewer than two members are eligible or every eligible member reaches N; otherwise the fewest points loses, and a tie is broken with `secrets.choice`, storing the candidates and the loser. Admin excusals and mid-week joins make a member ineligible for that week.

The current rules are in the engine design's [Decided Rules](../designs/game-engine.md#decided-rules) (see ADR-0011). The alternatives this record rejected are the engine design's [Alternatives A–C and N](../designs/game-engine.md#alternatives-considered); the skip token is now [Alternative F](../designs/game-engine.md#alternative-f-a-skip-token-per-period).

## Consequences
- Scoring is a pure function, property-tested against written invariants.
- A tied member can lose by chance; the result screen labels tie-breaks.
- A draw members can verify would need a seed column later.

## Amendments
- 2026-11-11: added the note that this decision text is a summary and the engine design is authoritative.
- 2026-11-11: superseded by ADR-0011; the alternatives this record rejected are kept as the engine design's Alternatives A–C (scoring) and N (seeded tie-break), and the model itself is Alternatives D–F; links updated to the renamed design file (`docs/designs/game-engine.md`).
