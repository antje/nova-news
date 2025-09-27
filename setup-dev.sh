#!/usr/bin/env bash
set -euo pipefail

# One-time local setup for NovaNews dev environment (macOS/Homebrew)
# - Installs Postgres via Homebrew if missing
# - Starts Postgres and creates role/db from .env
# - Applies schema in db/schema.sql

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f .env ]; then
  echo ".env not found. Copying env.example to .env..."
  cp env.example .env
  echo "Edit .env to set NOVA_ACT_API_KEY and DB settings, then re-run this script."
  exit 1
fi

# Load environment robustly (supports quoted values and leading spaces before '#')
set -a
# shellcheck disable=SC1091
source .env
set +a

: "${POSTGRES_PORT:=5432}"
: "${POSTGRES_USER:=novanews}"
: "${POSTGRES_PASSWORD:=changeme}"
: "${POSTGRES_DB:=novanews}"

echo "Ensuring Homebrew is available..."
if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew not found. Please install Homebrew from https://brew.sh and retry."
  exit 1
fi

echo "Installing Postgres if needed..."
if ! command -v psql >/dev/null 2>&1; then
  brew update || true
  brew install postgresql@17 || brew install postgresql@16 || brew install postgresql || true
  brew link postgresql@17 --force --overwrite >/dev/null 2>&1 || true
  brew link postgresql@16 --force --overwrite >/dev/null 2>&1 || true
fi

echo "Starting Postgres via Homebrew services..."
brew services start postgresql@17 >/dev/null 2>&1 || true
brew services start postgresql@16 >/dev/null 2>&1 || true
brew services start postgresql >/dev/null 2>&1 || true

echo "Waiting for Postgres to be ready on port $POSTGRES_PORT..."
for i in {1..30}; do
  if pg_isready -h 127.0.0.1 -p "$POSTGRES_PORT" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! pg_isready -h 127.0.0.1 -p "$POSTGRES_PORT" >/dev/null 2>&1; then
  echo "Postgres is not ready. Please check your local installation."
  exit 1
fi

echo "Creating role and database if not exist..."
psql -h 127.0.0.1 -p "$POSTGRES_PORT" -d postgres -v ON_ERROR_STOP=1 \
  -v dbname="$POSTGRES_DB" -v dbuser="$POSTGRES_USER" -v dbpass="$POSTGRES_PASSWORD" <<'SQL'
-- Create role if it does not exist
SELECT 'CREATE ROLE ' || quote_ident(:'dbuser') || ' LOGIN PASSWORD ' || quote_literal(:'dbpass')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = :'dbuser') \gexec

-- Create database if it does not exist
SELECT 'CREATE DATABASE ' || quote_ident(:'dbname') || ' OWNER ' || quote_ident(:'dbuser')
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = :'dbname') \gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE :"dbname" TO :"dbuser";
SQL

if [ -f "db/schema.sql" ]; then
  echo "Applying schema..."
  PGPASSWORD="$POSTGRES_PASSWORD" psql "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:${POSTGRES_PORT}/${POSTGRES_DB}" -v ON_ERROR_STOP=1 -f db/schema.sql
fi

echo "Setup complete. You can now run ./start-backend.sh"


