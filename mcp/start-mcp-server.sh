#!/usr/bin/env bash
set -euo pipefail

# Start NovaNews MCP server (STDIO)
# Usage: ./start-mcp-server.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f "$PROJECT_ROOT/.env" ]; then
  echo ".env not found in project root. Copying env.example to .env..."
  cp "$PROJECT_ROOT/env.example" "$PROJECT_ROOT/.env"
  echo "Please edit $PROJECT_ROOT/.env to set NOVA_ACT_API_KEY before running searches."
fi

export NOVA_NEWS_API_BASE_URL="${NOVA_NEWS_API_BASE_URL:-http://localhost:8000}"
export NOVA_NEWS_HTTP_TIMEOUT="${NOVA_NEWS_HTTP_TIMEOUT:-300}"

echo "Starting MCP server (connecting to $NOVA_NEWS_API_BASE_URL, timeout ${NOVA_NEWS_HTTP_TIMEOUT}s) ..."
python "$SCRIPT_DIR/novanews_mcp_server.py"


