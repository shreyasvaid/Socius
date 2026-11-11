# ADR 0008: Time model: phone local date and one global weekly cutoff

| | |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-11-11 |
| **Deciders** | Shreyas Vaid |
| **Supersedes** | — |
| **Superseded by** | — |

## Context
Members of one group can live in different time zones and travel, and one check-in must count in every group a member belongs to.

## Options considered
1. **One time zone per group**: one day boundary per group; days don't match members' own calendars, and a check-in would need dating in several zones.
2. **Per-group close when every member's own Sunday has ended**: earlier results for eastern groups; the close time moves when members travel.
3. **Phone local date plus a single global cutoff**: simple and constant; results arrive late in eastern zones.

## Decision
Option 3. A check-in is dated with the phone's local date (honor system). Weeks run Monday to Sunday and are keyed by their Monday's date, which handles the roughly 26-hour weekend overlap when two weeks are open. Every group's week closes at Monday 12:00 UTC, when Sunday has ended everywhere on Earth. Code takes the time from an injected clock, never from the system or the database.

Full model: [Time model](../designs/weekly-game-engine.md#time-model). Rejected alternatives: [D–F](../designs/weekly-game-engine.md#alternatives-considered).

## Consequences
- No group time zone to store or convert.
- Results reach California around 04:00 Monday and Sydney around 23:00 Monday.
- A member can change their phone's clock or zone; that is accepted under the honor system.
