# ADR 0003: FastAPI backend; the app never touches the database

| | |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-11-11 |
| **Deciders** | Shreyas Vaid |
| **Supersedes** | — |
| **Superseded by** | — |

## Context
The game rules (scoring, the weekly close, permissions, privacy) must be enforced in one place and tested. A backend-as-a-service would let the app read and write the database directly.

## Options considered
1. **Backend-as-a-service only (e.g. Supabase with row-level security)**: least server code; business rules split between SQL policies and the app, harder to property-test.
2. **Node/TypeScript API**: one language with the app; less mature property-testing and numeric tooling than Python.
3. **Python FastAPI API**: typed request models (Pydantic v2), OpenAPI generated automatically, Hypothesis for property tests.

Database access, decided separately (engine design D4): synchronous SQLAlchemy with psycopg 3, async SQLAlchemy, or both.

## Decision
A FastAPI service is the only thing that talks to Postgres; the app uses the API, Supabase Auth, and signed URLs for photo uploads. Database access is synchronous SQLAlchemy 2.x with psycopg 3, with Alembic migrations.

## Consequences
- All rules live in the API and its pure `domain/` module, and are tested there.
- One more service to host and keep awake.
- Synchronous handlers run in FastAPI's thread pool (about 40 concurrent requests by default), far above this app's needs; revisit if that ceiling is reached. Async would have made the scheduler and concurrency tests harder.
