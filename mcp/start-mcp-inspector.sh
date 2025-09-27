#!/usr/bin/env bash
set -euo pipefail

# Start MCP Inspector pointing to NovaNews MCP server via STDIO
# Usage: ./start-mcp-inspector.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

export NOVA_NEWS_API_BASE_URL="${NOVA_NEWS_API_BASE_URL:-http://localhost:8000}"
export NOVA_NEWS_HTTP_TIMEOUT="${NOVA_NEWS_HTTP_TIMEOUT:-300}"

echo "Launching MCP Inspector (requires Node/npm installed)..."
npx @modelcontextprotocol/inspector \
  "python" \
  "$PROJECT_ROOT/mcp/novanews_mcp_server.py"


