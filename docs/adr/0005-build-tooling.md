# ADR 0005: Build tooling: pnpm, uv and just

| | |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-11-11 |
| **Deciders** | Shreyas Vaid |
| **Supersedes** | — |
| **Superseded by** | — |

## Context
The repo holds three packages: the Expo app, the FastAPI service, and the generated API client. Humans and CI need the same commands.

## Options considered
1. **Bazel**: hermetic builds and a shared cache; Expo's build tools (Metro, EAS) don't run through it, every package needs BUILD files, and the benefits appear only with many engineers and targets.
2. **Nx or Turborepo**: task caching for JavaScript-heavy monorepos; adds configuration for little gain with three packages.
3. **Each language's own tools plus a small task runner**: pnpm workspaces for JavaScript, uv for Python, and a root `justfile` with one recipe per task.

## Decision
Option 3. `just setup`, `dev`, `test`, `lint`, `fmt`, `typecheck`, `gen-client`, `check-client`, `db-up` and `migrate` are the entry points; CI calls the same recipes. pnpm's default isolated install is used; Expo supports it from SDK 54. If a library breaks under it, `nodeLinker: hoisted` goes in `pnpm-workspace.yaml` with a comment naming the library.

## Consequences
- No shared build cache; CI rebuilds what it needs each run.
- Revisit Nx, Turborepo or Bazel when CI time becomes a bottleneck, the number of packages grows well past a handful, or several contributors work in parallel.
- `just` is one extra binary for contributors and CI to install.

Full comparison: [engine design, Alternative S](../designs/game-engine.md#alternative-s-bazel-or-nx--turborepo-as-the-build-system).

## Amendments
- 2026-11-11: corrected the pnpm linker note. Current Expo supports isolated installs, and the fallback setting lives in `pnpm-workspace.yaml`, not `.npmrc`. The decision is unchanged.
- 2026-11-11: link updated to the renamed design file and alternative letter.
