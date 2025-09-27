# NovaNews MCP Server

Exposes tools for launching and monitoring async NovaNews searches via HTTP polling.

## Prerequisites
- Python 3.10+
- NovaNews backend running with `NOVA_ACT_API_KEY` set

## Install
```bash
pip install -r requirements.txt
```

## Run
**Recommended (all services including MCP):**
```bash
# In project root (nova-news)
./start.sh  # starts database, backend, frontend, and MCP server
```

**MCP server only (development):**
```bash
# In project root (nova-news), ensure backend is running
python -m uvicorn api.main:app --reload --port 8000

# In this directory (nova-news/mcp), start MCP server
export NOVA_NEWS_API_BASE_URL=http://localhost:8000
export NOVA_NEWS_HTTP_TIMEOUT=300   # 5 minutes
python novanews_mcp_server.py
```

### Timeout
- The MCP server uses an HTTP timeout when calling the backend.
- Default timeout: 300 seconds (5 minutes). Override with `NOVA_NEWS_HTTP_TIMEOUT`.
- Inspector launch scripts also pass `NOVA_NEWS_HTTP_TIMEOUT=300`.

## Tools
- `search_news(topic, sites?, max_items_per_site?)` → Launches job, returns `{job_id, status}`
- `get_search_status(job_id)` → `{job_id, status, total_logs, error?}`
- `get_search_results(job_id)` → `[ {title, summary, url, source}, ... ]`

## Example flows
- Launch: "search news for nova act"
- Poll: call `get_search_status(job_id)` until `completed|failed`
- Results: call `get_search_results(job_id)` when completed
