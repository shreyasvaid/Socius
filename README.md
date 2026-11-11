# Socius

**Fitness accountability for couples, families, and roommates. Show up, or take the punishment.**

> **Status: in design.** No application code yet. Start with the [product requirements](docs/product-requirements.md).

## What it is

Socius is a cross-platform mobile app for small groups who already know each other. The group agrees on a weekly workout target, each check-in earns a point up to that target, and at the end of the week the member with the fewest points does the punishment the group agreed on. If everyone hits the target, nobody loses.

- One shared weekly target; everyone trains on their own days
- One check-in counts in every group you're in
- A weekly skip token, and admin excusals for sickness or travel
- Results computed automatically every Monday, with a random tie-break
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
- [Weekly game engine design](docs/designs/weekly-game-engine.md)
- [Architecture decision records](docs/adr/)
- [Feature specs](docs/specs/)

## Development

The repo scaffold is in progress, so these commands don't work yet. Once it lands:

**Prerequisites:** Node (current LTS), pnpm via Corepack, [uv](https://docs.astral.sh/uv/), [just](https://github.com/casey/just), Docker.

```sh
just setup     # install JS and Python dependencies
just db-up     # start local Postgres
just migrate   # apply database migrations
just dev       # run the API and the Expo dev server
just test      # run all tests
```

## License

[MIT](LICENSE)
