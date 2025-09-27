### MCP Integration

The MCP server wraps the NovaNews HTTP API to launch and monitor searches via polling.

#### Tools
- `search_news(topic, sites?, max_items_per_site?)` → Launches job
- `get_search_status(job_id)` → Poll job status
- `get_search_results(job_id)` → Fetch results after completion

#### Run
```bash
cd nova-news
./start.sh  # starts database, backend, frontend, and MCP server

# Or MCP server only (development)
cd nova-news/mcp
pip install -r requirements.txt
export NOVA_NEWS_API_BASE_URL=http://localhost:8000
python novanews_mcp_server.py
```

Optional Inspector helper:
```bash
npx @modelcontextprotocol/inspector \
  "python" \
  "./mcp/novanews_mcp_server.py"
```


