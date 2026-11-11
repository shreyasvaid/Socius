# Socius

**Fitness accountability for couples, families, and roommates. Show up, or take the punishment.**

> **Status: in design.** No application code yet. Start with the [product requirements](docs/product-requirements.md).

## What it is

Socius is a cross-platform mobile app for small groups who already know each other. Everyone sets their own goal, the group shares a weekly training schedule, and each completed scheduled workout earns a point. At the end of the week, the member with the lowest adherence does the punishment the group agreed on.

- Personal goals and plans inside one shared group schedule
- Adherence-based scoring that's fair across different goals
- Preset rest days plus group-voted rest days
- Body and food data stay private; only check-ins and results are shared
- No money. Punishments are social.

## Planned stack

| Layer | Tech |
|---|---|
| Mobile | React Native · Expo · TypeScript |
| API | Python · FastAPI · SQLAlchemy · Alembic |
| Data | PostgreSQL · S3-compatible storage |
| Quality | pytest · Hypothesis · Jest · GitHub Actions |

## Docs

- [Product requirements](docs/product-requirements.md)
- [High-level design](docs/high-level-design.md)
- [Architecture decision records](docs/adr/)
- [Feature specs](docs/specs/)

## License

[MIT](LICENSE)
