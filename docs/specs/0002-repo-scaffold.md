# Spec 0002: Repository scaffold and CI

| | |
|---|---|
| **Status** | Agreed |
| **Author** | Shreyas Vaid |
| **Design refs** | [Engine design](../designs/game-engine.md#part-a-stage-1-repository-scaffold-and-ci), Part A, Stage 1 (items 1–11); [ADR-0005](../adr/0005-build-tooling.md) build tooling; [ADR-0009](../adr/0009-close.md) close protection (role timeouts); HLD §7 (quality strategy) |
| **Phase** | Phase 0 |

## Problem

No code can land safely yet. There is no workspace, no single command to run checks, no local database and no CI, so nothing stops a broken change from reaching `main`. This spec sets up the repository so that every later stage starts from the same commands locally and in CI, and so that `main` only accepts changes that pass them.

The engine design lists the Stage 1 files. This spec turns that list into concrete settings and checkable acceptance criteria, and records the few choices the design left open. Where this spec refines the design, the design is updated in the same PR.

## Behavior

A contributor with the prerequisites installed (Node, Corepack, uv, just, Docker) can:

1. Clone the repo and run `just setup`. It installs the JavaScript and Python dependencies from the lockfiles and fails if either lockfile is out of date.
2. Run `just db-up` to start Postgres 17 in Docker with two databases (`socius` for development, `socius_test` for tests) and two roles (the application role with 30-second timeouts, and the migration role without them).
3. Run `just db-check` to confirm the application role's timeouts are in force.
4. Run `just lint`, `just typecheck` and `just test`, which pass on the scaffold.
5. Run `just ci` to run the same checks CI runs, in the same order.
6. Open a PR and see a `ci` check. `main` accepts the PR only when that check is green.

### Choices made here

| Topic | Choice | Why |
|---|---|---|
| Node | 24, in `.node-version`; `engines.node` `>=24 <25` | The LTS line on the dev machine and supported by current Expo. Move to Node 26 in its own PR once Expo supports it. |
| pnpm | `packageManager: pnpm@12.18.0`, through Corepack | An exact pin, so local and CI installs match. |
| Python | 3.14, in `services/api/.python-version`; `requires-python = ">=3.14"` | It has been stable for a year, so the binary wheels the API needs (psycopg, pydantic-core) exist. 3.15 is too new for that. |
| Python project | `services/api` only, no uv workspace at the root | There is one Python package. A root workspace can be added if a second one appears. |
| Lockfiles | `pnpm-lock.yaml` and `services/api/uv.lock` are committed. `just setup` runs `pnpm install --frozen-lockfile` and `uv sync --locked`. | The same versions install everywhere; a dependency change must update the lockfile in the same PR. |
| ruff | `select = ["E", "F", "W", "I", "B", "UP", "SIM", "RUF"]`, line length 100 | Errors, imports, likely bugs and modern syntax, without the noisier rule sets. |
| pyright | `strict` on `src/`, `standard` on `tests/` | Strict where the product code lives; tests use fixtures and Hypothesis, which strict mode makes noisy. |
| Role names | `socius_app` (application), `socius_migrate` (migrations) | Local and CI only. Hosted databases get their own credentials later. |
| Database ownership | Both databases are owned by `socius_migrate`. Default privileges give `socius_app` `SELECT, INSERT, UPDATE, DELETE` on new tables and `USAGE, SELECT` on new sequences. | Migrations create the tables; the application can use them but can't change the schema. Default privileges are per database, so they are set in each. |
| Role setup in CI | CI runs the same SQL file as Docker (`docker/postgres-init/01-roles-and-databases.sql`) with `psql` after checkout. The service container uses the default `postgres` database. | One file defines roles, databases and timeouts, so local and CI can't drift. This replaces the design's `POSTGRES_DB: socius_test` plus a separate CI step. |
| Migration URL | New variable `MIGRATION_DATABASE_URL` for `just migrate` (used from Stage 3) | `just migrate` runs as the migration role, so it needs its own connection string. |
| Branch protection | Require a PR and the `ci` check, require linear history, block force pushes and deletion of `main`, apply to admins, so the author can't bypass them either. No required approvals. Confirmed by the author. | A solo project can't approve its own PRs; the green check is the gate. A rule that can be bypassed doesn't protect `main`. Linear history keeps it readable. |
| Merging | Squash merge only, PR title as the commit subject, head branches deleted on merge. Confirmed by the author. | One conventional commit per PR on `main`, and no leftover branches. The commits inside a PR stay visible on the closed PR. |

## Acceptance criteria

- [ ] Given a fresh clone with the prerequisites installed, when the contributor runs `just setup`, then JavaScript and Python dependencies install with no changes to either lockfile.
- [ ] Given a lockfile that doesn't match its manifest, when `just setup` runs, then it fails.
- [ ] Given Docker is running, when the contributor runs `just db-up`, then Postgres 17 is healthy on port 5432 with databases `socius` and `socius_test` and roles `socius_app` and `socius_migrate`.
- [ ] Given the database is up, when the contributor runs `just db-check`, then it connects to `socius_test` as `socius_app` and confirms that `transaction_timeout`, `statement_timeout` and `idle_in_transaction_session_timeout` are each `30s`, and that the same three are `0` for `socius_migrate`.
- [ ] Given the database has data, when the contributor runs `just db-reset`, then the volume is dropped and the databases and roles are recreated empty.
- [ ] Given the scaffold, when the contributor runs `just lint`, `just typecheck` and `just test`, then each passes. `just test` runs the smoke test.
- [ ] Given a deliberate ruff error, pyright error or failing test on a branch, when a PR is opened, then the `ci` check fails.
- [ ] Given a PR, when CI runs, then it runs `just setup`, `just db-check`, `just lint`, `just typecheck` and `just test`, in that order, and `just ci` runs the same steps locally.
- [ ] Given branch protection is on, when anyone pushes directly to `main`, then GitHub rejects the push.
- [ ] Given the repo, when you search for a recipe, a CI step or a config file, then nothing exists only as a placeholder: every recipe has something to run.
- [ ] Given `.env.example`, then it lists every variable in design item 6 plus `MIGRATION_DATABASE_URL`, each with a one-line comment and a safe local default or an empty value. No real secrets.

## API changes

None. `services/api` contains only the package marker and a smoke test.

## Data changes

No tables. The init SQL creates:

- roles `socius_app` (login, `transaction_timeout`, `statement_timeout` and `idle_in_transaction_session_timeout` set to `30s` with `ALTER ROLE … SET`) and `socius_migrate` (login, no timeouts)
- databases `socius` and `socius_test`, owned by `socius_migrate`
- default privileges in each database, as in "Choices made here"

Local passwords are fixed development values in the SQL file and `.env.example`. They only work on the local Docker container and the CI service container.

## Files

| File | Design item | Notes |
|---|---|---|
| `package.json` | 1 | `private`, `packageManager`, `engines.node`; no scripts |
| `.node-version` | 1 | `24` |
| `pnpm-workspace.yaml` | 2, 3 | `apps/*`, `packages/*`; default isolated linker |
| `pnpm-lock.yaml` | 2 | generated |
| `justfile` | 4 | Stage 1 recipes: `setup`, `db-up`, `db-down`, `db-reset`, `db-check`, `test-api`, `test`, `lint`, `fmt`, `typecheck`, `ci` |
| `.gitignore` | 5 | add `services/api/openapi.json` |
| `.env.example` | 6 | plus `MIGRATION_DATABASE_URL` |
| `docker-compose.yml` | 7 | `postgres:17`, named volume, health check, port 5432, mounts `docker/postgres-init` |
| `docker/postgres-init/01-roles-and-databases.sql` | 8 | renamed from the design's `01-create-test-db.sql`, since it now creates both databases and the roles |
| `.github/workflows/ci.yml` | 9 | one job named `ci`; `concurrency` cancels superseded runs on the same branch |
| `services/api/pyproject.toml`, `.python-version`, `uv.lock` | 11 | dependencies and tool settings from the design |
| `services/api/src/socius_api/__init__.py` | 11 | `__version__` |
| `services/api/tests/test_smoke.py` | 11 | imports the package and checks `__version__` |
| `README.md` | — | Development section: prerequisites and the Stage 1 commands |
| `docs/designs/game-engine.md` | — | items 4, 6, 8 and 9 updated to match this spec (`db-check`, `MIGRATION_DATABASE_URL`, the renamed SQL file, CI running that file) |
| `CLAUDE.md` | — | checklist: Stage 1 done |

Branch protection (design item 10) is a GitHub setting, applied with `gh api` after the scaffold PR merges, so that PR itself isn't blocked by a check that doesn't exist yet.

## Test plan

- **Smoke test:** `tests/test_smoke.py` proves the package imports and pytest, uv and pyright are wired up. Stage 2 adds the first real tests; the smoke test can go then.
- **Role setup:** `just db-check` runs in CI on every PR, so a change to the SQL that drops a timeout fails CI.
- **CI catches failures:** before merging, push one throwaway commit with a ruff error to the PR branch, confirm `ci` fails, then remove it. Record the failing run's link in the PR description.
- **Fresh clone:** before merging, clone the branch into a temporary directory and run `just setup`, `just db-reset`, `just db-check` and `just ci` there.

## Alternatives considered

- **Keep `POSTGRES_DB: socius_test` and a separate CI step for roles (the design's version).** It works, but the role setup would be written twice, once in SQL and once in YAML, and could drift. Running one SQL file in both places costs one `psql` call.
- **Add the Python project in Stage 2, as the design first had it.** CI would have nothing to lint or test in Stage 1 and would either fail or be a placeholder.
- **Pin GitHub Actions by commit SHA.** Stronger against a compromised action, but harder to read and update. Major-version tags for now; revisit with Dependabot when the repo gets outside contributors.
- **Pre-commit hooks.** Faster feedback, but a second place to configure the same checks. `just fmt` and CI cover it.
- **Python 3.15.** Newest, but some binary wheels may lag a few months after release.

## Risks

| Risk | Likelihood | How we'd notice | Mitigation |
|---|---|---|---|
| The CI runner's `psql` is older than 17 and rejects `transaction_timeout` | Low: `ALTER ROLE … SET` runs on the server, and the client version doesn't matter for plain SQL | `just db-check` fails in CI | Run the file with `docker exec` into the service container instead |
| Docker Desktop 20.10 (2022) misbehaves with the Compose file | Low: `postgres:17` already runs on it | `just db-up` fails | Update Docker Desktop |
| Branch protection set before the first PR merges blocks that PR | Medium if done in the wrong order | The PR can't merge | Apply protection after the merge, as above |
| A lockfile drifts and CI installs different versions than local | Low | `just setup` fails in CI | Frozen and locked installs everywhere |

## Out of scope

- Migrations, `just migrate` and anything under `services/api` beyond the smoke test (Stages 2–4)
- ESLint, Prettier and `tsc` (Stage 7, with the first TypeScript package)
- The Expo app and `just dev` (Stages 4 and 9)
- Hosted databases, deployment and secrets management
- Dependabot, CodeQL and other repository automation

## Open questions

None.
