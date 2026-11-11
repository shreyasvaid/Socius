# ADR 0011: Group periods in the group's time zone; only check-ins count

| | |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-11-11 |
| **Deciders** | Shreyas Vaid |
| **Supersedes** | ADR-0007, ADR-0008 |
| **Superseded by** | — |

## Context
The first version of the game used fixed Monday–Sunday weeks, dated each check-in with the phone's local date (one per day), closed every group at one global instant (Monday 12:00 UTC), and gave each member a weekly skip token. Review showed that this model carried most of the design's complexity: about 26 hours each weekend when two weeks are open at once, edge cases for groups created or settings changed during that overlap, results reaching eastern time zones late on Monday, and per-day dating for members in different zones. Admins also want periods other than a week.

## Options considered
1. **Keep the global weekly model** (ADR-0007 and ADR-0008): members' days match their own calendars; weeks only, and the overlap logic stays.
2. **One deadline per group, in the group's time zone, with periods of any whole number of days; count check-ins, not days**: a deadline everyone in the group can state ("midnight Sunday, Chicago time"); members in other zones work to someone else's midnight, and daylight-saving changes need testing.

## Decision
Option 2.
- Each group stores a time zone (set from the creator's phone) and the admin sets the period length in whole days. Periods run midnight to midnight in that zone, back to back, and are stored as rows.
- A check-in counts in every group whose period is open when the server receives it. There is no per-day limit; points are check-ins capped at N.
- Skip tokens are removed. Admin excusals remain. The loser rule, the tie-break (`secrets.choice`) and the close mechanism (ADR-0009) are unchanged.
- Changes to N, period length, time zone or punishment apply from the next period.

The exact rules live only in the [engine design's Decided Rules](../designs/game-engine.md#decided-rules); this decision text is a summary.

## Consequences
- The weekend overlap, the global cutoff and per-day dating are gone, along with the edge cases they caused.
- Members outside the group's zone see the deadline converted to their own time; the app must make that obvious.
- Period boundaries follow the group zone's daylight-saving changes, so the domain tests cover DST.
- A check-in that reaches the server after the deadline (for example, made offline) counts in the next period.
- A member can log several check-ins in one day; that is accepted under the honor system.
