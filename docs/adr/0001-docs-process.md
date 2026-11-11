# ADR 0001: Lightweight docs process: PRD, HLD, design docs, specs, ADRs

| | |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-11-11 |
| **Deciders** | Shreyas Vaid |
| **Supersedes** | — |
| **Superseded by** | — |

## Context
Socius is built by one or two people with no deadline, to production standards. Decisions need to be written down so they can be explained and not silently reversed, without process that costs more than the code.

## Options considered
1. **No written design; decide in code and commit messages**: fastest to start; reasons get lost and decisions drift.
2. **One combined design document**: one file to keep consistent; product rules and technical design change at different rates and are read by different people.
3. **Separate documents by purpose**: more files, but each has one job and one reader.

## Decision
Option 3:
- `docs/product-requirements.md` (PRD): what the product does and why.
- `docs/high-level-design.md` (HLD): how the system is built.
- `docs/designs/`: a design doc for work spanning several features or components (the first is the game engine).
- `docs/specs/`: one spec per feature, written and agreed before its code.
- `docs/adr/`: one record per significant or hard-to-reverse decision. An accepted ADR's decision is never changed in place; a new ADR supersedes it. Factual corrections that don't change the decision may be made in place and are listed under "Amendments".

Each rule lives in one document; others link to it rather than restating it.

## Consequences
- Every feature PR points to a spec or design, and updates it if implementation proves it wrong.
- Readers follow links instead of reading everything in one place.
- Copies of rules are avoided on purpose: the PRD summarizes the game and links to the engine design.

## Amendments
- 2026-11-11: clarified that factual corrections which don't change a decision may be made in place and recorded under "Amendments". The decision is unchanged.
- 2026-11-11: wording updated after ADR-0011 ("the game engine" instead of "the weekly game engine").
