#!/usr/bin/env zsh
set -euo pipefail

# NovaNews Unified Stopper
# Stops all services: Frontend, Backend, MCP Server, and Database (if started by app)
# Usage: ./stop.sh

# Resolve script directory in bash/zsh/posix
if [ -n "${BASH_SOURCE-}" ]; then
  SCRIPT_PATH="${BASH_SOURCE[0]}"
else
  SCRIPT_PATH="$0"
fi
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
cd "$SCRIPT_DIR"

echo "🛑 Stopping NovaNews Application Stack..."

# Load environment variables if available
if [ -f .env ]; then
  set -a
  source .env || true
  set +a
fi

mkdir -p .run

# ======================
# Stop Process by PID File
# ======================
stop_pid_file() {
  local file="$1"
  local name="$2"
  if [ -f "$file" ]; then
    local pid
    pid=$(cat "$file" || true)
    if [ -n "${pid:-}" ] && ps -p "$pid" >/dev/null 2>&1; then
      echo "🔻 Stopping $name (PID $pid)..."
      kill "$pid" || true
      # Give it a moment, then force if needed
      sleep 2
      if ps -p "$pid" >/dev/null 2>&1; then
        echo "💥 Force killing $name (PID $pid)"
        kill -9 "$pid" || true
      fi
      echo "✅ $name stopped"
    else
      echo "⚠️  $name PID not found or already stopped"
    fi
    rm -f "$file"
  else
    echo "ℹ️  $name not running (no PID file)"
  fi
}

# ======================
# Force Stop Port
# ======================
force_stop_port() {
  local port="$1"
  local name="$2"
  
  echo "🔍 Checking for processes on port $port ($name)..."
  local pids
  pids=$(lsof -t -iTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)
  
  if [ -n "${pids:-}" ]; then
    echo "🧹 Force stopping processes on port $port: $pids"
    for pid in $pids; do
      if ps -p "$pid" >/dev/null 2>&1; then
        echo "  💀 Killing PID $pid on port $port"
        kill "$pid" 2>/dev/null || true
        sleep 1
        # Force kill if still running
        if ps -p "$pid" >/dev/null 2>&1; then
          echo "  💥 Force killing PID $pid"
          kill -9 "$pid" 2>/dev/null || true
        fi
      fi
    done
    echo "✅ Port $port cleared"
  else
    echo "✅ Port $port is clear"
  fi
}

# ======================
# Stop Services
# ======================

# Stop services by PID files
stop_pid_file .run/frontend.pid "Frontend"
stop_pid_file .run/backend.pid "Backend API"
stop_pid_file .run/mcp.pid "MCP Server"

# Force clean ports
force_stop_port 8000 "Backend"
force_stop_port 8001 "Frontend"

# Stop PostgreSQL if we started it
STARTED_BY_APP_MARKER=".pg_started_by_novanews"

if [ -f "$STARTED_BY_APP_MARKER" ]; then
  echo "🗄️  Stopping PostgreSQL (started by app)..."
  if command -v brew >/dev/null 2>&1; then
    for pg_version in postgresql@17 postgresql@16 postgresql; do
      brew services stop "$pg_version" >/dev/null 2>&1 || true
    done
    echo "✅ PostgreSQL stopped"
  fi
  rm -f "$STARTED_BY_APP_MARKER"
else
  echo "ℹ️  PostgreSQL not started by app, leaving running"
fi

# Clean up any remaining processes that might interfere
echo "🧹 Final cleanup..."

# Kill any uvicorn processes
uvicorn_pids=$(pgrep -f "uvicorn.*api.main:app" 2>/dev/null || true)
if [ -n "${uvicorn_pids:-}" ]; then
  echo "🔻 Stopping remaining uvicorn processes: $uvicorn_pids"
  for pid in $uvicorn_pids; do
    kill "$pid" 2>/dev/null || true
  done
fi

# Kill any Next.js dev processes
nextjs_pids=$(pgrep -f "next.*dev" 2>/dev/null || true)
if [ -n "${nextjs_pids:-}" ]; then
  echo "🔻 Stopping remaining Next.js processes: $nextjs_pids"
  for pid in $nextjs_pids; do
    kill "$pid" 2>/dev/null || true
  done
fi

# Kill any MCP server processes
mcp_pids=$(pgrep -f "novanews_mcp_server.py" 2>/dev/null || true)
if [ -n "${mcp_pids:-}" ]; then
  echo "🔻 Stopping remaining MCP server processes: $mcp_pids"
  for pid in $mcp_pids; do
    kill "$pid" 2>/dev/null || true
  done
fi

echo ""
echo "🎉 All NovaNews services stopped!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Start again: ./start.sh"
echo "📝 Logs preserved in: ./logs/"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
