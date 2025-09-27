#!/usr/bin/env bash
set -euo pipefail

# NovaNews Unified Log Monitor
# Monitors logs from all services: Backend, Frontend, MCP Server
# Usage: 
#   ./monitor.sh           - Show all logs (tail -f)
#   ./monitor.sh backend   - Show only backend logs
#   ./monitor.sh frontend  - Show only frontend logs
#   ./monitor.sh mcp       - Show only MCP server logs
#   ./monitor.sh status    - Show service status

# Resolve script directory in bash/zsh/posix
if [ -n "${BASH_SOURCE-}" ]; then
  SCRIPT_PATH="${BASH_SOURCE[0]}"
else
  SCRIPT_PATH="$0"
fi
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Log files
BACKEND_LOG="logs/backend.log"
FRONTEND_LOG="logs/frontend.log"
MCP_LOG="logs/mcp.log"

# ======================
# Helper Functions
# ======================

print_header() {
  echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${CYAN}$1${NC}"
  echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

check_service_status() {
  local service="$1"
  local pid_file="$2"
  local port="$3"
  
  if [ -f "$pid_file" ]; then
    local pid
    pid=$(cat "$pid_file" 2>/dev/null || echo "")
    if [ -n "$pid" ] && ps -p "$pid" >/dev/null 2>&1; then
      if [ -n "$port" ] && lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
        echo -e "✅ ${GREEN}$service${NC} - Running (PID: $pid, Port: $port)"
      else
        echo -e "⚠️  ${YELLOW}$service${NC} - Process running but port $port not listening (PID: $pid)"
      fi
    else
      echo -e "❌ ${RED}$service${NC} - PID file exists but process not running"
    fi
  else
    if [ -n "$port" ] && lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
      local pids
      pids=$(lsof -t -iTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)
      echo -e "⚠️  ${YELLOW}$service${NC} - Port $port occupied by PIDs: $pids (no PID file)"
    else
      echo -e "🔴 ${RED}$service${NC} - Not running"
    fi
  fi
}

show_status() {
  print_header "🔍 NovaNews Service Status"
  
  # Check services
  check_service_status "Backend API" ".run/backend.pid" "8000"
  check_service_status "Frontend" ".run/frontend.pid" "8001"
  check_service_status "MCP Server" ".run/mcp.pid" ""
  
  # Check PostgreSQL
  echo -n "🗄️  Database (PostgreSQL): "
  if command -v pg_isready >/dev/null 2>&1 && pg_isready -h 127.0.0.1 -p 5432 >/dev/null 2>&1; then
    echo -e "${GREEN}Running${NC} (Port: 5432)"
  else
    echo -e "${RED}Not running or not accessible${NC}"
  fi
  
  echo ""
  echo -e "📝 Log files:"
  for log in "$BACKEND_LOG" "$FRONTEND_LOG" "$MCP_LOG"; do
    if [ -f "$log" ]; then
      local size
      size=$(stat -f%z "$log" 2>/dev/null || stat -c%s "$log" 2>/dev/null || echo "0")
      local readable_size
      if [ "$size" -gt 1048576 ]; then
        readable_size="$(($size / 1048576))MB"
      elif [ "$size" -gt 1024 ]; then
        readable_size="$(($size / 1024))KB"
      else
        readable_size="${size}B"
      fi
      echo "  📄 $log ($readable_size)"
    else
      echo "  📄 $log (not found)"
    fi
  done
  
  echo ""
  echo "💡 Use './monitor.sh [backend|frontend|mcp]' to view specific logs"
  echo "💡 Use 'Ctrl+C' to stop monitoring"
}

colorize_logs() {
  local service="$1"
  local color="$2"
  
  while IFS= read -r line; do
    timestamp=$(date '+%H:%M:%S')
    echo -e "${color}[$service $timestamp]${NC} $line"
  done
}

monitor_single_log() {
  local service="$1"
  local log_file="$2"
  local color="$3"
  
  if [ ! -f "$log_file" ]; then
    echo -e "${YELLOW}⚠️  Log file $log_file not found. Service may not be running.${NC}"
    echo "💡 Start services with: ./start.sh"
    exit 1
  fi
  
  print_header "👀 Monitoring $service logs (Ctrl+C to stop)"
  echo -e "📁 Log file: $log_file"
  echo ""
  
  tail -f "$log_file" | colorize_logs "$service" "$color"
}

monitor_all_logs() {
  print_header "👀 Monitoring all NovaNews logs (Ctrl+C to stop)"
  
  # Check if log files exist
  missing_logs=()
  [ ! -f "$BACKEND_LOG" ] && missing_logs+=("backend")
  [ ! -f "$FRONTEND_LOG" ] && missing_logs+=("frontend") 
  [ ! -f "$MCP_LOG" ] && missing_logs+=("mcp")
  
  if [ ${#missing_logs[@]} -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Some log files not found: ${missing_logs[*]}${NC}"
    echo "💡 Start services with: ./start.sh"
    echo ""
  fi
  
  # Use multitail if available, otherwise use tail -f with process substitution
  if command -v multitail >/dev/null 2>&1; then
    echo "📖 Using multitail for enhanced log viewing..."
    echo ""
    multitail \
      -ci green -t "Backend" "$BACKEND_LOG" \
      -ci blue -t "Frontend" "$FRONTEND_LOG" \
      -ci magenta -t "MCP" "$MCP_LOG" 2>/dev/null || {
        echo "Falling back to simple tail..."
        monitor_all_logs_simple
      }
  else
    echo "📝 Use 'brew install multitail' for enhanced multi-log viewing"
    echo ""
    monitor_all_logs_simple
  fi
}

monitor_all_logs_simple() {
  # Simple approach using tail -f with labeled output
  local pids=()
  local pgids=()

  cleanup_streams() {
    # Attempt to stop entire process groups first, then individual PIDs
    for pgid in "${pgids[@]}"; do
      if [ -n "$pgid" ]; then
        kill -TERM -"$pgid" 2>/dev/null || true
      fi
    done
    sleep 0.2
    for pgid in "${pgids[@]}"; do
      if [ -n "$pgid" ]; then
        kill -KILL -"$pgid" 2>/dev/null || true
      fi
    done

    # Fallback cleanup of any remaining direct children
    for pid in "${pids[@]}"; do
      if kill -0 "$pid" >/dev/null 2>&1; then
        pkill -P "$pid" 2>/dev/null || true
        kill "$pid" 2>/dev/null || true
        wait "$pid" 2>/dev/null || true
      fi
    done
    pids=()
    pgids=()
  }

  handle_interrupt() {
    cleanup_streams
    trap - EXIT
    exit 0
  }

  trap handle_interrupt INT TERM
  trap cleanup_streams EXIT

  start_stream() {
    local service="$1"
    local log_file="$2"
    local color="$3"

    if [ -f "$log_file" ]; then
      (
        # Ignore Ctrl+C propagating to subshell but allow TERM so cleanup works
        trap '' INT
        # Ensure line-buffered output for smooth piping
        if command -v stdbuf >/dev/null 2>&1; then
          stdbuf -oL -eL tail -f "$log_file" | colorize_logs "$service" "$color"
        else
          tail -f "$log_file" | colorize_logs "$service" "$color"
        fi
      ) &
      local pid=$!
      pids+=($pid)
      # Capture process group id for robust cleanup (works on macOS and Linux)
      local pgid
      pgid=$(ps -o pgid= -p "$pid" 2>/dev/null | tr -d ' ')
      pgids+=("$pgid")
    fi
  }

  start_stream "Backend" "$BACKEND_LOG" "$GREEN"
  start_stream "Frontend" "$FRONTEND_LOG" "$BLUE"
  start_stream "MCP" "$MCP_LOG" "$MAGENTA"

  if [ ${#pids[@]} -eq 0 ]; then
    trap - INT TERM EXIT
    echo -e "${YELLOW}⚠️  No log files available to monitor.${NC}"
    return
  fi

  wait "${pids[@]}" || true
  trap - INT TERM EXIT
}

# ======================
# Main Logic
# ======================

case "${1:-all}" in
  "backend")
    monitor_single_log "Backend API" "$BACKEND_LOG" "$GREEN"
    ;;
  "frontend")
    monitor_single_log "Frontend" "$FRONTEND_LOG" "$BLUE"
    ;;
  "mcp")
    monitor_single_log "MCP Server" "$MCP_LOG" "$MAGENTA"
    ;;
  "status")
    show_status
    ;;
  "all"|"")
    monitor_all_logs
    ;;
  *)
    echo "Usage: $0 [backend|frontend|mcp|status|all]"
    echo ""
    echo "Commands:"
    echo "  backend   - Monitor backend API logs only"
    echo "  frontend  - Monitor frontend logs only"
    echo "  mcp       - Monitor MCP server logs only"
    echo "  status    - Show service status"
    echo "  all       - Monitor all logs (default)"
    echo ""
    echo "Examples:"
    echo "  $0              # Monitor all logs"
    echo "  $0 backend      # Monitor backend only"
    echo "  $0 status       # Show service status"
    exit 1
    ;;
esac
