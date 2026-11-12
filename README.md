# Socius

**Fitness accountability for couples, families, and roommates. Show up, or take the punishment.**

> **Status: early development.** The repo scaffold and CI are in place; no app features yet. Start with the [product requirements](docs/product-requirements.md).

## What it is

Socius is a cross-platform mobile app for small groups who already know each other. The group's admin sets a period (a week, a month, any number of days) and a workout target. Each check-in earns a point up to that target, and when the period ends the member with the fewest points does the punishment the group agreed on. If everyone hits the target, nobody loses.

- One shared target and deadline; everyone trains on their own schedule
- One check-in counts in every group you're in
- Admin excusals for sickness or travel
- Results computed automatically at each deadline, with a random tie-break
- Body and food data stay private; only check-ins and results are shared
- No money. Punishments are social.

## Planned stack

| Layer | Tech |
|---|---|
| Mobile | React Native · Expo · TypeScript |
| API | Python · FastAPI · SQLAlchemy · Alembic |
| Data | PostgreSQL · S3-compatible storage |
| Quality | pytest · Hypothesis · Schemathesis · Jest · GitHub Actions |
| Tooling | pnpm · uv · just |

## Docs

- [Product requirements](docs/product-requirements.md)
- [High-level design](docs/high-level-design.md)
- [Game engine design](docs/designs/game-engine.md)
- [Architecture decision records](docs/adr/)
- [Feature specs](docs/specs/)

## Development

**Prerequisites:** Node 24 with Corepack enabled (`corepack enable`), [uv](https://docs.astral.sh/uv/), [just](https://github.com/casey/just), Docker. uv installs Python 3.14 itself; no local `psql` is needed.

```sh
just setup      # install JS and Python dependencies from the lockfiles
just db-up      # start local Postgres 17 (databases socius and socius_test)
just db-check   # confirm the database roles' timeouts are in force
just lint       # ruff check and format check
just typecheck  # pyright
just test       # run all tests
just ci         # everything CI runs, in the same order
```

`just fmt` fixes formatting and import order, `just db-down` stops Postgres, and `just db-reset` wipes it and recreates the databases and roles. Copy `.env.example` to `.env` for local settings. Run `just` to list every recipe.

## License

[MIT](LICENSE)
