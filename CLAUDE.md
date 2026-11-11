# CLAUDE.md — Socius

Context and working rules for AI assistants (Claude Code, Claude app projects) working on this repo. Read this first, then `docs/design.md`.

## What this is

Socius is a cross-platform (iOS + Android) fitness accountability app for small groups: couples, families, friends, roommates. Members share a weekly training schedule, each with their own goal. Completed scheduled workouts earn points; scoring is adherence-based; at the end of each period the lowest-adherence member does the punishment the group agreed on. No money is ever handled.

It is also a portfolio project for a new-grad SWE job search, so engineering quality is visible on purpose: specs, ADRs, tests, CI, typed API contract.

- **Main dev:** Shreyas (CS student, Purdue). A friend contributes; ownership split TBD.
- **Source of truth for decisions:** `docs/design.md`. If this file and the design doc disagree, the design doc wins. Flag the conflict.

## Current status

**Phase 0: Foundation. No application code exists yet.**

Done:
- [x] High-level design doc (`docs/design.md`)
- [x] Spec and ADR templates (`docs/specs/0000-template.md`, `docs/adr/0000-template.md`)

Next, in order:
1. Write ADRs 0001–0006 listed in design §16 (short; capture the trade-offs already discussed in the design doc).
2. Scaffold the monorepo (design §17): pnpm workspace, `apps/mobile` (Expo + TS + Expo Router), `services/api` (uv + FastAPI + SQLAlchemy + Alembic), `packages/api-client`.
3. Docker Compose for local Postgres; `.env.example`.
4. GitHub Actions CI (design §15.2) + branch protection on `main`.
5. Wire auth end-to-end (Supabase Auth → JWT verified by FastAPI → `GET /v1/me` from the app on a real iPhone dev build). That's the Phase 0 exit criterion.
6. Then first v0.1 spec: `docs/specs/0001-groups-and-invites.md`.

Update this checklist as work lands.

## Stack (decided)

- Mobile: React Native + Expo, TypeScript (strict), Expo Router, TanStack Query
- API: Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic
- DB: PostgreSQL. Auth: Supabase Auth (proposed, ADR-0004). Storage: S3-compatible
- Push: Expo Push. Jobs: cron-triggered idempotent worker
- Tooling: pnpm, uv, ruff, pyright/mypy, pytest + Hypothesis, ESLint, Prettier, Jest + RNTL, Maestro (later)
- CI: GitHub Actions. Builds: EAS → TestFlight / Android APK

## Key product rules (don't silently change these)

- Points come **only** from completed scheduled workouts. Food is never scored.
- Scoring is adherence-based: `completed / scheduled`, with skip tokens and mid-period joins removed from the denominator. Lowest adherence loses; ties share the loss; a perfect week has no loser.
- Honor system for check-ins; proof photos optional.
- Rest days: preset weekdays + group votes (strict majority of all members, closes 23:59 the day before, group time zone).
- All day/period boundaries use the **group's** IANA time zone; store UTC.
- Body data, goals, and food data are private to the user. See the privacy table in design §9; enforce it with tests.
- Calorie guardrails (floors, max loss rate) are mandatory when calorie features ship.
- No money handling, ever.

## How we work (spec-driven, lightweight)

1. **No feature code without a spec.** Copy `docs/specs/0000-template.md`, fill it in, get it agreed, then implement.
2. Significant or hard-to-reverse decisions get an ADR in `docs/adr/`.
3. If implementation proves a spec or the design doc wrong, **update the doc in the same PR.**
4. Domain logic (scoring, votes, periods, calories) lives in `services/api/src/socius_api/domain/` as pure functions with no I/O. Test exhaustively, including property-based tests.
5. Every PR: lint, types, and tests pass. Add tests with the change.
6. Conventional commits (`feat:`, `fix:`, `docs:`, `chore:`, `test:`, `refactor:`). Small PRs. Branches: `feat/…`, `fix/…`, `docs/…`.
7. Never commit secrets. Update `.env.example` when adding a variable.
8. The OpenAPI-generated TS client must be regenerated when the API changes.

## How to work with Shreyas

- Be a direct peer, not a yes-man. Lead with the answer, then reasoning, then caveats. Give the strongest objection before the strongest support. State confidence; separate what you know from what you're guessing.
- Short paragraphs, no filler, no emojis.
- He must be able to explain and defend every line in an interview. When you make a non-obvious choice, say why in one or two sentences. Prefer clear code over clever code.
- **Ask before:** pushing, force-pushing, deleting branches/files, rewriting history, running destructive migrations, adding paid services, or anything that can't be undone. Never send or post anything on his behalf without asking.
- When scope starts creeping, say so and point to the roadmap (design §18).

## Open questions

Tracked in design §20. Resolve them in the doc (and an ADR if significant) rather than in code comments.
