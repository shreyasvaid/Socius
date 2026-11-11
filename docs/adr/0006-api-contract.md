# ADR 0006: API contract: OpenAPI-generated TypeScript client

| | |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-11-11 |
| **Deciders** | Shreyas Vaid |
| **Supersedes** | — |
| **Superseded by** | — |

## Context
The app and the API must not drift apart. FastAPI already emits an OpenAPI schema.

## Options considered
1. **Hand-written TypeScript types**: no tooling; drift is caught only at runtime.
2. **@hey-api/openapi-ts**: types plus one SDK function per endpoint; its configuration has changed between major versions.
3. **orval**: types plus ready-made TanStack Query hooks; large generated output, customized through its own configuration.
4. **openapi-typescript + openapi-fetch**: types only (one generated file) and a small typed fetch client; query hooks written by hand.

## Decision
Option 4 (engine design D3). `just gen-client` exports the schema without starting a server and regenerates `packages/api-client/src/schema.d.ts`, which is committed. CI fails if regenerating changes anything. Schemathesis tests the running API against the schema. TanStack Query hooks are written by hand in the app, with all cache keys in one key-factory module.

## Consequences
- Drift between app and API fails CI.
- Each endpoint needs a hand-written hook; the key factory keeps cache keys and invalidation in one place.
- Error codes are a string enum in the schema, so the app's message map fails type-checking when a new code has no message.
