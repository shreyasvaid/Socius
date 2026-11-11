# ADR 0002: React Native and Expo for the mobile app

| | |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-11-11 |
| **Deciders** | Shreyas Vaid |
| **Supersedes** | — |
| **Superseded by** | — |

## Context
iOS and Android are both required (PRD G5). Most testers use iPhone, but Android must work. There is one main developer.

## Options considered
1. **Native Swift/SwiftUI (plus Kotlin later)**: best platform fidelity; two codebases, and Android would lag.
2. **Flutter**: one codebase; Dart instead of TypeScript, so no sharing with the generated API types.
3. **React Native with Expo (TypeScript)**: one codebase, TypeScript end to end with the generated API client, cloud builds (EAS) and push notifications included.

## Decision
React Native with Expo and TypeScript (strict), Expo Router for navigation, TanStack Query for server state. The exact Expo SDK version is pinned when the app is scaffolded and recorded here as an addendum note before the ADR is relied on.

## Consequences
- One codebase and one language with the API client.
- Native modules outside Expo's set need a development build; that's acceptable.
- Expo SDK upgrades are periodic work.
