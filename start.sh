#!/usr/bin/env zsh
set -euo pipefail

# NovaNews Unified Starter
# Starts all services: Database, Backend API, Frontend, and MCP Server
# Usage: ./start.sh [--mode local|agentcore] [--slack true|false]

usage() {
  cat <<'USAGE'
Usage: ./start.sh [options]

Options:
  --mode <local|agentcore>  Override NOVANEWS_BROWSER_MODE for this run only
  --local                   Shortcut for --mode local
  --agentcore               Shortcut for --mode agentcore
  --slack <true|false>      Temporarily enable or disable Slack notifications
  -h, --help                Show this help message
USAGE
}

MODE_OVERRIDE=""
SLACK_OVERRIDE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      if [[ -z "${2:-}" ]]; then
        echo "❌ Missing value for --mode" >&2
        usage
        exit 1
      fi
      MODE_OVERRIDE="$2"
      shift 2
      ;;
    --mode=*)
      MODE_OVERRIDE="${1#*=}"
      shift
      ;;
    --local)
      MODE_OVERRIDE="local"
      shift
      ;;
    --agentcore)
      MODE_OVERRIDE="agentcore"
      shift
      ;;
    --slack)
      if [[ -z "${2:-}" ]]; then
        echo "❌ Missing value for --slack" >&2
        usage
        exit 1
      fi
      SLACK_OVERRIDE="$2"
      shift 2
      ;;
    --slack=*)
      SLACK_OVERRIDE="${1#*=}"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "❌ Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

# Resolve script directory in bash/zsh/posix
if [ -n "${BASH_SOURCE-}" ]; then
  SCRIPT_PATH="${BASH_SOURCE[0]}"
else
  SCRIPT_PATH="$0"
fi
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting NovaNews Application Stack..."

mkdir -p .run logs

# Ensure leftover monitor tails are terminated before starting services
cleanup_log_watchers() {
  local patterns=(
    "tail -f logs/backend.log"
    "tail -f logs/frontend.log"
    "tail -f logs/mcp.log"
    "colorize_logs"
    "monitor.sh"
  )
  local cleaned=false
  for pattern in "${patterns[@]}"; do
    if pkill -f "$pattern" >/dev/null 2>&1; then
      cleaned=true
    fi
  done
  if [ "$cleaned" = true ]; then
    echo "🧹 Stopped residual log monitors"
  fi
}

cleanup_log_watchers

# ======================
# Environment Setup
# ======================
if [ ! -f .env ]; then
  echo "📝 .env not found. Copying env.example to .env..."
  cp env.example .env
  echo "⚠️  Edit .env to set NOVA_ACT_API_KEY (backend returns empty results without it)."
fi

# Load environment variables
set -a
source .env || true
set +a

if [ -n "$MODE_OVERRIDE" ]; then
  if [[ "$MODE_OVERRIDE" != "local" && "$MODE_OVERRIDE" != "agentcore" ]]; then
    echo "❌ Invalid browser mode override: $MODE_OVERRIDE" >&2
    echo "    Allowed values: local, agentcore" >&2
    exit 1
  fi
  export NOVANEWS_BROWSER_MODE="$MODE_OVERRIDE"
  echo "🧭 Overriding NOVANEWS_BROWSER_MODE to '$NOVANEWS_BROWSER_MODE' for this run"
else
  export NOVANEWS_BROWSER_MODE="local"
  echo "🧭 NOVANEWS_BROWSER_MODE defaulting to 'local'"
fi

if [ -n "$SLACK_OVERRIDE" ]; then
  normalized=$(echo "$SLACK_OVERRIDE" | tr '[:upper:]' '[:lower:]')
  case "$normalized" in
    true|1|yes|on)
      normalized="true"
      ;;
    false|0|no|off)
      normalized="false"
      ;;
    *)
      echo "❌ Invalid value for --slack: $SLACK_OVERRIDE" >&2
      echo "    Allowed values: true, false" >&2
      exit 1
      ;;
  esac
  export NOVANEWS_ENABLE_SLACK_NOTIFICATIONS="$normalized"
  echo "💬 Slack notifications forced to '$normalized' for this run"
else
  export NOVANEWS_ENABLE_SLACK_NOTIFICATIONS="false"
  echo "💬 Slack notifications defaulting to 'false'"
fi

# ======================
# Python Environment
# ======================
pick_python() {
  local c
  for c in "$@"; do
    if [ -x "$c" ]; then
      echo "$c"; return 0
    fi
  done
  return 1
}

resolve_python() {
  # Prefer already-available interpreters >=3.10 (python3 or python)
  local candidate
  for candidate in python3 python; do
    local sys_py
    sys_py=$(command -v "$candidate" || true)
    if [ -n "$sys_py" ]; then
      local v
      v=$($sys_py -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
      local maj=${v%%.*}
      local min=${v#*.}
      if [ -n "$maj" ] && [ -n "$min" ] && { [ "$maj" -gt 3 ] || { [ "$maj" -eq 3 ] && [ "$min" -ge 10 ]; }; }; then
        echo "$sys_py"; return 0
      fi
    fi
  done

  # Try Homebrew-installed Pythons
  local candidates=()
  candidates+=(/opt/homebrew/opt/python@3.12/bin/python3.12)
  candidates+=(/opt/homebrew/opt/python@3.11/bin/python3.11)
  candidates+=(/opt/homebrew/opt/python@3.10/bin/python3.10)
  candidates+=($(ls -1 /opt/homebrew/Cellar/python@3.12/*/bin/python3.12 2>/dev/null || true))
  candidates+=($(ls -1 /opt/homebrew/Cellar/python@3.11/*/bin/python3.11 2>/dev/null || true))
  candidates+=($(ls -1 /opt/homebrew/Cellar/python@3.10/*/bin/python3.10 2>/dev/null || true))

  local picked
  picked=$(pick_python "${candidates[@]}" 2>/dev/null || true)
  if [ -n "$picked" ]; then
    echo "$picked"; return 0
  fi

  # Install python@3.12 as last resort
  if command -v brew >/dev/null 2>&1; then
    echo "📦 Installing python@3.12 via Homebrew..."
    brew list python@3.12 >/dev/null 2>&1 || brew install python@3.12
    picked=$(pick_python /opt/homebrew/opt/python@3.12/bin/python3.12 $(ls -1 /opt/homebrew/Cellar/python@3.12/*/bin/python3.12 2>/dev/null || true) 2>/dev/null || true)
    if [ -n "$picked" ]; then
      echo "$picked"; return 0
    fi
  fi

  return 1
}

PYTHON_BIN=$(resolve_python || true)
if [ -z "$PYTHON_BIN" ]; then
  echo "❌ Python 3.10+ not found. Please install Python 3.12 (e.g. 'brew install python@3.12') and retry." >&2
  exit 1
fi

# Setup virtual environment
if [ -d .venv ]; then
  VENV_PY=".venv/bin/python"
  if [ -x "$VENV_PY" ]; then
    VENV_VER=$($VENV_PY -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
    VMAJ=${VENV_VER%%.*}
    VMIN=${VENV_VER#*.}
    if [ -z "$VMAJ" ] || [ -z "$VMIN" ] || [ "$VMAJ" -lt 3 ] || { [ "$VMAJ" -eq 3 ] && [ "$VMIN" -lt 10 ]; }; then
      echo "🔄 .venv uses Python $VENV_VER; recreating with $PYTHON_BIN..."
      rm -rf .venv
    fi
  else
    rm -rf .venv
  fi
fi

if [ ! -d .venv ]; then
  echo "🐍 Creating Python virtual environment..."
  "$PYTHON_BIN" -m venv .venv
fi

echo "📦 Installing backend dependencies..."

# Prefer an externally managed venv in ./bin if present; fallback to .venv
if [ -f "bin/activate" ]; then
  source bin/activate
elif [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
fi

python -m pip install --upgrade pip wheel >/dev/null

# Install local nova-act SDK if available
if [ -d "../0-sdk/nova-act" ]; then
  python -m pip install -e ../0-sdk/nova-act >/dev/null
fi
python -m pip install -r requirements.txt >/dev/null

# ======================
# Database (PostgreSQL)
# ======================
ensure_postgres() {
  : "${POSTGRES_PORT:=5432}"
  : "${POSTGRES_USER:=novanews}"
  : "${POSTGRES_PASSWORD:=changeme}"
  : "${POSTGRES_DB:=novanews}"
  : "${DATABASE_URL:=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:${POSTGRES_PORT}/${POSTGRES_DB}}"

  if ! command -v psql >/dev/null 2>&1; then
    echo "❌ psql not found. Please run ./setup-dev.sh to install Postgres via Homebrew."
    exit 1
  fi

  if pg_isready -h 127.0.0.1 -p "$POSTGRES_PORT" >/dev/null 2>&1; then
    echo "✅ PostgreSQL is running on port $POSTGRES_PORT"
  else
    echo "🗄️  Starting PostgreSQL..."
    STARTED_BY_APP_MARKER=".pg_started_by_novanews"
    started=false
    if command -v brew >/dev/null 2>&1; then
      for pg_version in postgresql@17 postgresql@16 postgresql; do
        brew services start "$pg_version" >/dev/null 2>&1 || true
        # Wait up to 30s for readiness
        for i in {1..30}; do
          if pg_isready -h 127.0.0.1 -p "$POSTGRES_PORT" >/dev/null 2>&1; then
            started=true
            break 2
          fi
          sleep 1
        done
      done
      if [ "$started" = true ]; then
        echo "✅ PostgreSQL started via Homebrew"
        echo "started" > "$STARTED_BY_APP_MARKER"
      fi
    fi

    if [ "$started" = false ]; then
      echo "❌ Unable to start PostgreSQL. Please run ./setup-dev.sh, then retry."
      exit 1
    fi
  fi

  # Ensure database exists
  echo "🗄️  Setting up database schema..."
  psql -h 127.0.0.1 -p "$POSTGRES_PORT" -d postgres -v ON_ERROR_STOP=1 \
    -v dbname="$POSTGRES_DB" -v dbuser="$POSTGRES_USER" -v dbpass="$POSTGRES_PASSWORD" <<'SQL' >/dev/null 2>&1
SELECT 'CREATE ROLE ' || quote_ident(:'dbuser') || ' LOGIN PASSWORD ' || quote_literal(:'dbpass')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = :'dbuser') \gexec

SELECT 'CREATE DATABASE ' || quote_ident(:'dbname') || ' OWNER ' || quote_ident(:'dbuser')
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = :'dbname') \gexec

GRANT ALL PRIVILEGES ON DATABASE :"dbname" TO :"dbuser";
SQL

  if [ -f "db/schema.sql" ]; then
    PGPASSWORD="$POSTGRES_PASSWORD" psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f db/schema.sql >/dev/null 2>&1
  fi
}

# ======================
# Clean Ports
# ======================
cleanup_port() {
  local port="$1"
  local name="$2"
  
  if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "🧹 Cleaning existing processes on port $port ($name)..."
    PIDS=$(lsof -t -iTCP:"$port" -sTCP:LISTEN || true)
    if [ -n "${PIDS:-}" ]; then
      for pid in $PIDS; do
        if ps -p "$pid" >/dev/null 2>&1; then
          kill "$pid" || true
          sleep 1
          ps -p "$pid" >/dev/null 2>&1 && kill -9 "$pid" || true
        fi
      done
    fi
  fi
}

# ======================
# Start Services
# ======================

# Start database
ensure_postgres

# Clean ports
cleanup_port 8000 "backend"
cleanup_port 8001 "frontend"

# Start Backend (FastAPI)
echo "🔧 Starting backend API on port 8000..."
(
  if [ -f "bin/activate" ]; then
    source bin/activate
  elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
  fi
  python -m uvicorn api.main:app --port 8000 --host 0.0.0.0
) > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > .run/backend.pid

# Wait for backend health check
echo -n "⏳ Waiting for backend to be ready"
for i in {1..60}; do
  if curl -sf http://127.0.0.1:8000/api/health >/dev/null 2>&1; then
    echo " ✅"
    break
  fi
  echo -n "."
  sleep 1
done

if ! curl -sf http://127.0.0.1:8000/api/health >/dev/null 2>&1; then
  echo " ❌"
  echo "Backend failed to start. Check logs/backend.log"
  exit 1
fi

# Start Frontend (Next.js)
if ! command -v npm >/dev/null 2>&1; then
  echo "❌ npm not found. Please install Node.js (e.g. 'brew install node')"
  exit 1
fi

if [ ! -d web/node_modules ]; then
  echo "📦 Installing frontend dependencies..."
  (cd web && npm ci >/dev/null)
fi

export NEXT_PUBLIC_API_BASE="http://localhost:8000"

echo "🌐 Starting frontend on port 8001..."
(cd web && npm run dev) > logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > .run/frontend.pid

# Wait for frontend
echo -n "⏳ Waiting for frontend to be ready"
for i in {1..60}; do
  if curl -sf http://127.0.0.1:8001 >/dev/null 2>&1; then
    echo " ✅"
    break
  fi
  echo -n "."
  sleep 1
done

if ! curl -sf http://127.0.0.1:8001 >/dev/null 2>&1; then
  echo " ❌"
  echo "Frontend failed to start. Check logs/frontend.log"
fi

# Start MCP Server (optional)
echo "🔌 Starting MCP server..."
if [ -x ./mcp/start-mcp-server.sh ]; then
  (
    cd mcp
    export NOVA_NEWS_API_BASE_URL="http://localhost:8000"
    export NOVA_NEWS_HTTP_TIMEOUT="300"
    if [ -f "../bin/activate" ]; then
      source ../bin/activate
    elif [ -f "../.venv/bin/activate" ]; then
      source ../.venv/bin/activate
    fi
    python novanews_mcp_server.py
  ) > logs/mcp.log 2>&1 &
  MCP_PID=$!
  echo $MCP_PID > .run/mcp.pid
  echo "✅ MCP server started"
else
  echo "⚠️  MCP server script not found, skipping..."
fi

echo ""
echo "🎉 All services are running!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 Backend API:  http://localhost:8000"
echo "🌐 Frontend:     http://localhost:8001"
echo "🔌 MCP Server:   Running (STDIO)"
echo "🗄️  Database:     PostgreSQL on port 5432"
echo ""
echo "📝 Logs: ./logs/"
echo "🛑 Stop: ./stop.sh"
echo "👀 Monitor: ./monitor.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
