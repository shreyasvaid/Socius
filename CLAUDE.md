# CLAUDE.md — Socius

Context and working rules for AI assistants (Claude Code, Claude app projects) working on this repo. Read this first, then `docs/product-requirements.md` (what and why), `docs/high-level-design.md` (how), and `docs/designs/game-engine.md` (the game rules and engine design).

## What this is

Socius is a cross-platform (iOS + Android) fitness accountability app for small groups: couples, families, friends, roommates. The group's admin sets a period (any whole number of days) and a target N, the same for everyone. Each check-in earns a point, up to N. When the period ends (midnight in the group's time zone), the member with the fewest points does the punishment the group agreed on; nobody loses if everyone reaches N. No money is ever handled.

It is also a portfolio project for a new-grad SWE job search, so engineering quality is visible on purpose: specs, ADRs, tests, CI, typed API contract.

- **Main dev:** Shreyas (CS student, Purdue). A friend contributes; ownership split TBD.
- **Source of truth for decisions:** the game rules and engine design live only in `docs/designs/game-engine.md` (Decided Rules section). The PRD (`docs/product-requirements.md`) covers other product behavior; the HLD (`docs/high-level-design.md`) covers the rest of the technical design. If this file and those docs disagree, the docs win. Flag the conflict.

## Current status

**Phase 0: Foundation. The repo scaffold and CI exist; no application code yet.**

Done:
- [x] Design doc, split into PRD (`docs/product-requirements.md`) and HLD (`docs/high-level-design.md`)
- [x] Spec and ADR templates (`docs/specs/0000-template.md`, `docs/adr/0000-template.md`)
- [x] Game engine design, reviewed and accepted (`docs/designs/game-engine.md`); revised for group periods by ADR-0011
- [x] ADRs 0001–0011 (`docs/adr/`)
- [x] Part B, Stage 8: PRD, HLD, README, CLAUDE.md and templates updated to link the game engine design
- [x] Part A, Stage 1: scaffold, CI and branch protection (items 1–11; spec `docs/specs/0002-repo-scaffold.md`). Changes reach `main` only through PRs with a green `ci` check, squash-merged.

Next, in order (item numbers refer to the design's Detailed Implementation Plan):
1. Part A, Stages 2–7: domain module, database, API, close job, tests, generated client (items 12–47). Not started; begins when Shreyas gives the go-ahead.
2. Wire auth end-to-end (Supabase Auth → JWT verified by FastAPI → `GET /v1/me` from the app on a real iPhone dev build). That's the Phase 0 exit criterion; it needs the Expo scaffold (item 48) early.
3. First v0.1 feature spec: `docs/specs/0001-groups-and-invites.md` (groups, invites, removing and re-adding members, 8-member cap). The four-week trial (design G1) depends on it.
4. Part B, Stage 9: mobile app (items 48–52).

Update this checklist as work lands.

## Stack (decided)

- Mobile: React Native + Expo, TypeScript (strict), Expo Router, TanStack Query
- API: Python 3.14, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic
- DB: PostgreSQL 17 (needed for `transaction_timeout`). Auth: Supabase Auth (proposed, ADR-0004). Storage: S3-compatible
- Hosting: Render free web service kept awake by an uptime ping; Postgres hosted separately (Render's free Postgres expires). Run one uvicorn worker.
- Push: Expo Push. Jobs: APScheduler inside the API process (every 5 min) plus close on read; idempotent
- API client: openapi-typescript + openapi-fetch; TanStack Query hooks written by hand around one key factory
- Tooling: pnpm, uv, `just` (single entry point), ruff, pyright (strict), pytest + Hypothesis, Schemathesis, ESLint, Prettier, Jest + RNTL, Maestro (later)
- DB access: synchronous SQLAlchemy with psycopg 3
- CI: GitHub Actions. Builds: EAS → TestFlight / Android APK

## Key product rules (don't silently change these)

- **Game rules** (periods, group time zone, target N, points, undo, excusals, membership, settings timing, loser rule, tie-break) are defined once, in the Decided Rules section of `docs/designs/game-engine.md`. Don't restate them elsewhere; link to it.
- Points come **only** from check-ins. Food is never scored.
- Honor system for check-ins; proof photos optional.
- Store UTC. Each group has one time zone; its deadlines are midnights in that zone. Members' own zones only affect how the app displays times.
- Body data, goals, and food data are private to the user. The phone's time zone (stored for reminders) is never shown to anyone. See the privacy table in PRD §9; enforce it with tests.
- Calorie guardrails (floors, max loss rate) are mandatory when calorie features ship.
- No money handling, ever.

## How we work (spec-driven, lightweight)

1. **No feature code without a spec or design.** For one feature, copy `docs/specs/0000-template.md`. For work spanning several features or components, write a design doc in `docs/designs/`. Get it agreed, then implement.
2. Significant or hard-to-reverse decisions get an ADR in `docs/adr/`.
3. If implementation proves a spec, a design doc, the PRD, or the HLD wrong, **update the doc in the same PR.**
4. Domain logic (scoring, periods, calories) lives in `services/api/src/socius_api/domain/` as pure functions with no I/O. Test exhaustively, including property-based tests.
5. Every PR: lint, types, and tests pass. Add tests with the change.
6. Conventional commits (`feat:`, `fix:`, `docs:`, `chore:`, `test:`, `refactor:`). Small PRs. Branches: `feat/…`, `fix/…`, `docs/…`.
7. Never commit secrets. Update `.env.example` when adding a variable.
8. The OpenAPI-generated TS client must be regenerated when the API changes.

## How to work with Shreyas

- Be a direct peer, not a yes-man. Lead with the answer, then reasoning, then caveats. Give the strongest objection before the strongest support. State confidence; separate what you know from what you're guessing.
- Short paragraphs, no filler, no emojis.
- He must be able to explain and defend every line in an interview. When you make a non-obvious choice, say why in one or two sentences. Prefer clear code over clever code.
- **Ask before:** pushing, force-pushing, deleting branches/files, rewriting history, running destructive migrations, adding paid services, or anything that can't be undone. Never send or post anything on his behalf without asking.
- When scope starts creeping, say so and point to the roadmap (PRD §10).

## Open questions

Tracked in PRD §12. Resolve them in the doc (and an ADR if significant) rather than in code comments.

## Unconfirmed defaults (ask before treating as final)

These were chosen by the assistant and not yet approved by Shreyas:
18+ age gate · 30-day photo retention · calorie floor and max loss-rate defaults (must be verified against a reputable source before v0.2) · a removed member can still see results of periods they were part of and gets those periods' results notification (engine design, Decided Rules).

## Environment

- Dev machine: MacBook Pro (macOS), iPhone for testing. Most testers use iPhone; Android must still work.
- conda `base` env is active by default in the shell. Use uv-managed Python for services/api; don't install into conda.
- Apple Developer Program ($99/yr) not yet purchased; buy when v0.1 is ready for TestFlight testers.
