#!/usr/bin/env bash
set -euo pipefail

# Purge and recreate the NovaNews database objects defined in db/schema.sql
# Usage: ./purge-db.sh -y

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ "${1:-}" != "-y" ]; then
  echo "This will DROP and RECREATE tables in ${POSTGRES_DB:-novanews}."
  echo "Run with -y to confirm:  ./purge.sh -y"
  exit 1
fi

if [ ! -f .env ]; then
  echo ".env not found; copying env.example to .env"
  cp env.example .env
fi

set -a
source .env
set +a

: "${POSTGRES_PORT:=5432}"
: "${POSTGRES_USER:=novanews}"
: "${POSTGRES_PASSWORD:=changeme}"
: "${POSTGRES_DB:=novanews}"
: "${DATABASE_URL:=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:${POSTGRES_PORT}/${POSTGRES_DB}}"

if ! command -v psql >/dev/null 2>&1; then
  echo "psql not found. Please run ./setup-dev.sh first." >&2
  exit 1
fi

echo "Dropping tables if exist..."
PGPASSWORD="$POSTGRES_PASSWORD" psql "$DATABASE_URL" -v ON_ERROR_STOP=1 <<'SQL'
DO $$
DECLARE
  rec RECORD;
BEGIN
  FOR rec IN (
    SELECT tablename FROM pg_tables WHERE schemaname = 'public'
      AND tablename IN ('job_results','job_logs','search_jobs','articles')
  ) LOOP
    EXECUTE format('DROP TABLE IF EXISTS %I CASCADE', rec.tablename);
  END LOOP;
END $$;
SQL

if [ -f "db/schema.sql" ]; then
  echo "Recreating schema from db/schema.sql ..."
  PGPASSWORD="$POSTGRES_PASSWORD" psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f db/schema.sql
else
  echo "db/schema.sql not found; nothing to recreate."
fi

echo "Database purge complete."


