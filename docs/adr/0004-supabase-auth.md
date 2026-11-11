# ADR 0004: Supabase for authentication (and possibly storage)

| | |
|---|---|
| **Status** | Proposed |
| **Date** | 2026-11-11 |
| **Deciders** | Shreyas Vaid |
| **Supersedes** | — |
| **Superseded by** | — |

## Context
Users sign in with email and Sign in with Apple (PRD FR-1). Writing authentication is a time sink and a security risk.

## Options considered
1. **Roll our own**: full control; password storage, reset flows and Apple sign-in are all ours to get right.
2. **Clerk**: polished; another vendor with its own pricing.
3. **Supabase Auth**: free tier, email and Apple sign-in, JWTs the API can verify; Supabase can also host Postgres and storage.

## Decision (proposed)
Supabase Auth issues JWTs; the FastAPI service verifies each token's signature, audience and expiry, and maps its subject to a `users` row. Whether Postgres and photo storage also live on Supabase (versus another host or Cloudflare R2) is still open.

Checked against Supabase documentation on 2026-11-11:
- Supabase supports asymmetric signing keys and publishes them at `https://<project>.supabase.co/auth/v1/.well-known/jwks.json`; the legacy shared secret is no longer recommended. The JWKS endpoint returns no keys for a project still on the shared secret.
- Tokens carry `iss` = `https://<project>.supabase.co/auth/v1`. The API verifies signature, issuer, audience and expiry with PyJWT's JWKS client, allowing ES256 and RS256, and caches keys for at most 10 minutes.

To settle before this ADR is accepted:
- Confirm in the project dashboard that asymmetric signing keys are enabled, and confirm the `aud` value.
- Where Postgres and storage are hosted, including free-tier pausing, backups, and whether the connection URL is a transaction-mode pooler (which needs psycopg's `prepare_threshold=None`).
- Supabase's current policy on pausing inactive free projects, which would take sign-in down.

## Consequences
- Sign-in depends on Supabase's availability.
- The API never sees passwords.
