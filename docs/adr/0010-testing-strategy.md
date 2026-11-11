# ADR 0010: Testing strategy: invariants, fake clock, real Postgres

| | |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-11-11 |
| **Deciders** | Shreyas Vaid |
| **Supersedes** | — |
| **Superseded by** | — |

## Context
The bugs that matter most here produce a wrong loser: scoring edge cases, date math, and the weekly close racing with late writes.

## Options considered
1. **A branch-coverage percentage as the gate**: easy to enforce; shows which lines ran, not whether results were checked.
2. **Written invariants checked by property tests, plus example tests per user journey**: the gate is a checklist, reviewed by a person.
3. Database tests: mocks; one rolled-back transaction per test; real commits on a real Postgres.

## Decision
- Every scoring and time rule is written as a numbered invariant and has a named test: a Hypothesis property test for rules that are pure functions, an API or concurrency test for rules that depend on the database. Every user journey has an example test. Coverage is reported, not gated.
- Time comes from an injected clock, faked in tests; no code uses the system clock or database `now()`.
- API and close tests run against real Postgres. Concurrency tests use separate connections and real commits, because a rolled-back-transaction fixture can't test races.
- Schemathesis checks the API against its schema.

Invariants and test layers: [Testing approach](../designs/weekly-game-engine.md#testing-approach). Rejected alternative: [V](../designs/weekly-game-engine.md#alternatives-considered).

## Consequences
- Each PR that adds a rule adds its invariant and test.
- The test database is truncated between tests, which is slower than rolling back.

## Amendments
- 2026-11-11: invariants that depend on the database (a duplicate check-in, removal mid-week, repeated closes) are tested with API or concurrency tests, not property tests. The decision is unchanged.
