### NovaNews Documentation

NovaNews is a production-ready AI news search system built on the Nova Act SDK. It provides both synchronous and asynchronous search capabilities with live progress tracking via WebSockets, database persistence, real-time log streaming, and comprehensive admin dashboard. The system intelligently scrapes AI news sources and exposes results via a FastAPI backend, Next.js frontend with admin panel, and MCP integration.

#### Key components
- Backend API: `api/main.py` (FastAPI with async job support and WebSocket streaming)
- Admin Dashboard: `web/app/admin/` (Job and site management interface)
- Database: PostgreSQL with job persistence and live logging
- Scraper/logic: `novanews.py` (`NovaNews` class powered by Nova Act)
- Browser automation: switch between local Playwright sessions and Bedrock AgentCore Browser via `NOVANEWS_BROWSER_MODE`
- Web UI: `web/` (Next.js with real-time WebSocket integration)
- MCP server: `mcp/novanews_mcp_server.py` (AI assistant integration)
- Management: Unified `start.sh`, `stop.sh`, `purge.sh` scripts
- Notifications: optional Slack webhooks triggered when jobs finish

#### Quick start
1) **All Services (Recommended)**
```bash
cd nova-news  # repository root
cp env.example .env   # Edit to set your NOVA_ACT_API_KEY
# Optionally set NOVANEWS_BROWSER_MODE=agentcore for Bedrock-managed browsing
./start.sh            # Starts database, backend, frontend, and MCP server
# Use ./start.sh --mode agentcore to force Bedrock, --slack true to enable Slack alerts for this run
```

To override the browser mode just for this launch, append `--mode agentcore` (or `--mode local`).

For slower sites, you can also set optional Nova Act tuning variables before launch (default values in parentheses):

```
NOVANEWS_ACT_MAX_STEPS=12
NOVANEWS_ACT_TIMEOUT_SECONDS=90
NOVANEWS_ACT_RESOLVE_MAX_STEPS=6
NOVANEWS_ACT_RESOLVE_TIMEOUT_SECONDS=45
AGENTCORE_BROWSER_PREVIEW_ACTUATION=true
```

When running in AgentCore mode, NovaNews prints a deep link to the browser session in the AWS console for quick inspection.

This will start:
- PostgreSQL database (auto-configured)
- FastAPI backend on http://localhost:8000
- Next.js frontend on http://localhost:8001  
- MCP server for AI assistant integration

2) **Access Points**
- Web UI: http://localhost:8001
- Admin Dashboard: http://localhost:8001/admin
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/api/health

3) **Stop Services**
```bash
./stop.sh             # Stops all services cleanly
```

4) **Try the API directly**
```bash
# Legacy synchronous search
curl 'http://localhost:8000/api/search?topic=nova%20act&sites=latent_space,forward_future'

# New async job-based search (recommended)
curl -X POST 'http://localhost:8000/api/search_jobs' \
  -H 'Content-Type: application/json' \
  -d '{"topic": "nova act", "sites": "latent_space,forward_future"}'
```

#### How it works

**Async Job System with WebSocket Streaming (Recommended):**
- Job creation: `POST /api/search_jobs` creates database-backed search jobs
- Real-time updates: WebSocket endpoint `/ws/logs/{job_id}` streams live logs, status, and results
- Admin management: `/api/admin/search_jobs` endpoints for viewing and deleting jobs
- Job status: `GET /api/search_jobs/{job_id}/status` for status and `total_logs`
- Results: `GET /api/search_jobs/{job_id}/results` for final results

**Legacy Sync Endpoint:**
- Direct search: `GET /api/search?topic=...&sites=...` (simple/legacy flow)

#### Database Schema
NovaNews uses PostgreSQL for job persistence and live logging:

```sql
-- Job management
search_jobs (id, topic, sites, max_items_per_site, status, error, created_at, updated_at)
job_logs (id, job_id, line_number, message, created_at)
job_results (id, job_id, article_id, title, summary, url, source)

-- Article storage  
articles (id, title, summary, url, source, found_at)

-- Admin-managed sites
news_sites (id, name, code, url, is_active, is_default, created_at, updated_at)
```

See `db/schema.sql` for the complete schema definition.

#### Project structure
- `api/` FastAPI app with async job endpoints, WebSocket support, and admin APIs
- `web/` Next.js UI with live log streaming, job status tracking, and admin dashboard
- `web/app/admin/` Comprehensive admin interface for job and site management
- `mcp/` MCP tool server exposing async search capabilities
- `db/` Database schema and migration scripts (includes news_sites table)
- `logs/` Application logs (backend, frontend, MCP)
- `.run/` Runtime PID files for service management
- `novanews.py` Core scraping logic powered by Nova Act SDK
- `start.sh` Unified startup script for all services
- `stop.sh` Unified shutdown script
- `purge.sh` Database reset script

#### Environment
- Required: `NOVA_ACT_API_KEY` (get from Nova Act dashboard)
- Required: `DATABASE_URL` (auto-configured by start.sh)
- Optional: `AWS_BEARER_TOKEN_BEDROCK` for Bedrock integration
- Optional: `POSTGRES_*` variables for custom database config
- Optional: `NOVANEWS_ENABLE_SLACK_NOTIFICATIONS` and `SLACK_WEBHOOK_*` for Slack delivery control

Continue to:
- Backend API details: `docs/backend.md`
- Database integration: `docs/database.md`
- Async job system: `docs/async-jobs.md`
- Service monitoring: `docs/monitoring.md`
- Scraper pipeline internals: `docs/pipeline.md`
- MCP integration: `docs/mcp.md`
- Web UI: `docs/web.md`
- Troubleshooting: `docs/troubleshooting.md`
