# ADR 0009: The close: facts not counters, scheduled plus on read

| | |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-11-11 |
| **Deciders** | Shreyas Vaid |
| **Supersedes** | — |
| **Superseded by** | — |

## Context
Every group's period must close exactly once, on time, without manual work, even if the job runs twice or the host puts the process to sleep, and a late write must never silently change a result.

## Options considered
- **What is stored**: running per-group score counters, or only facts (check-ins, excusals) with scores computed by one pure function.
- **Protecting the close from late writes (D1)**: a time check plus a 5-minute delay; a per-period lock ("seal"); database triggers.
- **What triggers the close (D2)**: the host's scheduled job; an external scheduler calling an endpoint; a scheduler inside the API process.

## Decision
- Store facts only; compute scores for the live leaderboard and at close with the same function.
- D1: reject writes after the period's end (checked at request start and again before commit), close 5 minutes later, bound every write transaction to 30 seconds with PostgreSQL 17's `transaction_timeout` set on the database role, and rescore recently closed periods to detect anything that slipped through.
- D2: APScheduler inside the API process every 5 minutes, kept awake by an uptime ping, plus close on read when a due period is requested.
- The result is saved on the period row with `UPDATE … WHERE closed_at IS NULL`, so a second close changes nothing; a blocking per-transaction advisory lock makes a second close wait instead of duplicating work. The heartbeat monitor is told about failures and overdue periods.

Full design: [The close](../designs/game-engine.md#the-close).

## Consequences
- A late write is detected and reported, not prevented.
- Results are correct whenever anyone looks; notification timing depends on the process being awake.
- Whether the chosen host allows keep-alive pings must be verified before deploying.

## Amendments
- 2026-11-11: corrected the timeout mechanism. `statement_timeout` bounds single statements, not transactions, so PostgreSQL 17's `transaction_timeout` is used, set on the role so it survives connection poolers. The lock is the blocking form, so close on read waits for a concurrent close instead of returning empty. The decision is unchanged.
- 2026-11-11: wording updated from weeks to periods after ADR-0011 (remaining "tokens" and "cutoff" wording fixed in a second pass the same day), and the result is now saved on the period row rather than in a separate table. The decision is unchanged.
