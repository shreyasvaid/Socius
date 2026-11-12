# Socius: the single entry point for local development and CI.
# Run `just` to list recipes.

api := "services/api"

# Local-only connection strings for `db-check`. The passwords are the fixed
# development values from docker/postgres-init/01-roles-and-databases.sql.
test_db_app := "postgresql://socius_app:socius_app_local@localhost:5432/socius_test"
test_db_migrate := "postgresql://socius_migrate:socius_migrate_local@localhost:5432/socius_test"

# How to run psql. Locally it runs inside the Compose container, so no client
# install is needed; CI sets PSQL=psql to use the runner's client.
psql := env("PSQL", "docker compose exec -T postgres psql")

default:
    @just --list

# Install JS and Python dependencies; fails if a lockfile is out of date
setup:
    pnpm install --frozen-lockfile
    cd {{ api }} && uv sync --locked

# Start local Postgres and wait until it is healthy
db-up:
    docker compose up -d --wait

# Stop local Postgres, keeping its data
db-down:
    docker compose down

# Drop the local database volume and recreate the databases and roles
db-reset:
    docker compose down --volumes
    just db-up

# Check that the role timeouts are in force (30s for the app role, none for migrations)
db-check:
    #!/usr/bin/env bash
    set -euo pipefail
    query="SELECT current_setting('transaction_timeout') || ' ' || current_setting('statement_timeout') || ' ' || current_setting('idle_in_transaction_session_timeout')"
    check() {
        actual=$({{ psql }} "$2" -tA -v ON_ERROR_STOP=1 -c "$query")
        if [ "$actual" != "$3" ]; then
            echo "db-check: $1 timeouts are '$actual', expected '$3'" >&2
            exit 1
        fi
        echo "db-check: $1 timeouts ok ($actual)"
    }
    check socius_app "{{ test_db_app }}" "30s 30s 30s"
    check socius_migrate "{{ test_db_migrate }}" "0 0 0"

# Run the API tests
test-api:
    cd {{ api }} && uv run pytest

# Run all tests
test: test-api

# Lint and check formatting
lint:
    cd {{ api }} && uv run ruff check .
    cd {{ api }} && uv run ruff format --check .

# Fix lint issues that ruff can fix (such as import order), then format
fmt:
    cd {{ api }} && uv run ruff check --fix .
    cd {{ api }} && uv run ruff format .

# Type-check
typecheck:
    cd {{ api }} && uv run pyright

# Run every check CI runs, in the same order (needs `just db-up` first)
ci: setup db-check lint typecheck test
