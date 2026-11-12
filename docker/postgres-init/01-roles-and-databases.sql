-- Local and CI database setup: roles, databases and default privileges.
-- Run as the postgres superuser. Docker runs it when the volume is first created;
-- CI runs it with psql. Passwords are fixed development values and only work
-- against the local container and the CI service container.

-- The application role. The timeouts bound how long any one request can hold
-- locks (see the engine design, "Close protection", and ADR-0009).
CREATE ROLE socius_app LOGIN PASSWORD 'socius_app_local';
ALTER ROLE socius_app SET transaction_timeout = '30s';
ALTER ROLE socius_app SET statement_timeout = '30s';
ALTER ROLE socius_app SET idle_in_transaction_session_timeout = '30s';

-- The migration role. No timeouts, so long migrations can finish.
CREATE ROLE socius_migrate LOGIN PASSWORD 'socius_migrate_local';

CREATE DATABASE socius OWNER socius_migrate;
CREATE DATABASE socius_test OWNER socius_migrate;

-- Default privileges are per database, so set them in each one. Tables and
-- sequences that socius_migrate creates are usable, but not alterable, by socius_app.
\connect socius
ALTER DEFAULT PRIVILEGES FOR ROLE socius_migrate IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO socius_app;
ALTER DEFAULT PRIVILEGES FOR ROLE socius_migrate IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO socius_app;

\connect socius_test
ALTER DEFAULT PRIVILEGES FOR ROLE socius_migrate IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO socius_app;
ALTER DEFAULT PRIVILEGES FOR ROLE socius_migrate IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO socius_app;
