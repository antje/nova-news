### Backend API (FastAPI)

The backend provides comprehensive REST APIs for search operations, job management, site configuration, real-time WebSocket communication, and optional Slack notifications. It integrates with PostgreSQL for persistence and uses the `NovaNews` scraper for content extraction in either local Playwright mode or the remote Bedrock AgentCore Browser tool.

#### Core Endpoints
**Search & Jobs:**
- `GET /api/health` — health check
- `GET /api/search` — synchronous topic search (legacy)
- `POST /api/search_jobs` — create async search job
- `GET /api/search_jobs/{job_id}/status` — job status
- `GET /api/search_jobs/{job_id}/results` — job results
- `WS /ws/logs/{job_id}` — real-time job updates via WebSocket

**Admin APIs:**
- `GET /api/admin/search_jobs` — list all jobs with stats
- `DELETE /api/admin/search_jobs/{job_id}` — delete job
- `GET /api/admin/sites` — manage news sites
- `POST /api/admin/sites` — create new site
- `PUT /api/admin/sites/{site_id}` — update site
- `DELETE /api/admin/sites/{site_id}` — delete site

**Site Management:**
- `GET /api/sites` — get active sites for search UI

#### WebSocket Real-time Communication
```python
@app.websocket("/ws/logs/{job_id}")
async def websocket_logs(websocket: WebSocket, job_id: str):
    await websocket.accept()
    # Register connection for real-time notifications
    await websocket_notifier.add_connection(job_id, websocket)
    
    # Send initial job state and all existing logs
    # Real-time updates sent automatically via background tasks
```

**WebSocket Message Types:**
- `{"type": "status", "data": {"status": "running", "error": null}}`
- `{"type": "log", "data": "Scraping latent_space for topic: AI"}`
- `{"type": "results", "data": [{"title": "...", "url": "..."}]}`
- `{"type": "complete", "data": {"final_status": "completed"}}`

#### Admin Dashboard APIs
```python
@app.get("/api/admin/search_jobs")
def get_admin_search_jobs(db: Session = Depends(get_db)):
    """Get all search jobs with result counts for admin dashboard"""
    return get_all_search_jobs(db)

@app.post("/api/admin/sites")
def create_site(req: CreateNewsSiteRequest, db: Session = Depends(get_db)):
    """Create a new news site"""
    return create_news_site(db, req)
```

#### Database Integration
**Job Management:**
- Jobs persist in PostgreSQL with full lifecycle tracking
- Live logs captured via custom database handler
- Real-time WebSocket notifications on status changes
- Admin operations for job deletion and monitoring

**Site Configuration:**
- Dynamic news site management via database
- Admin controls for active/inactive and default status
- Extensible architecture for adding new sources
- Site validation and duplicate prevention

#### Running the backend
**Recommended (all services):**
```bash
cd nova-news
cp env.example .env  # set NOVA_ACT_API_KEY
./start.sh           # starts database, backend, frontend, and MCP
```

**Backend only (development):**
```bash
cd nova-news
source .venv/bin/activate
python -m uvicorn api.main:app --reload --port 8000
```

#### Configuration
- `NOVA_ACT_API_KEY` must be present in env or `.env` (see `env.example`)
- `DATABASE_URL` for PostgreSQL connection (auto-configured by start.sh)
- `NOVANEWS_BROWSER_MODE` toggles between `local` and `agentcore` execution; `AGENTCORE_BROWSER_REGION` and `AGENTCORE_BROWSER_PREVIEW_ACTUATION` tune remote sessions
- Logs written to `api_logs/` and database `job_logs` table
- WebSocket CORS configured for frontend integration
- Slack delivery controlled by `NOVANEWS_ENABLE_SLACK_NOTIFICATIONS`, `SLACK_WEBHOOK_URL`, `SLACK_WEBHOOK_USERNAME`, `SLACK_WEBHOOK_ICON_EMOJI`, and `SLACK_WEBHOOK_PREVIEW_LIMIT`

#### Response Formats
**Search Job Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued"
}
```

**Admin Job List:**
```json
[{
  "job_id": "...", 
  "topic": "AI research",
  "status": "completed",
  "result_count": 5,
  "created_at": "2024-01-15T10:30:00Z"
}]
```

**Site Configuration:**
```json
[{
  "id": 1,
  "name": "Latent Space",
  "code": "latent_space", 
  "url": "https://latent.space/",
  "is_active": true,
  "is_default": true
}]
```

#### Error Handling
- Missing API key returns empty list for legacy endpoints
- Job failures captured in database with error messages
- WebSocket disconnections handled gracefully
- Slack webhook errors are swallowed after being logged to avoid failing the job pipeline
- Admin operations include validation and constraint checking
- Comprehensive error responses with detailed messages

#### Performance Features
- Background job processing prevents request timeouts
- WebSocket streaming eliminates polling overhead
- Database indexing optimized for job queries
- Connection pooling for concurrent operations
- AgentCore mode reuses the same orchestration logic while offloading browser automation to AWS-managed infrastructure

#### Slack Webhook Notifications
```python
def send_slack_summary(db, job_id, topic, results, log):
    if not settings.enable_slack_notifications or not settings.slack_configured:
        return

    preview_items = list(results[: settings.slack_preview_limit])
    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": f"Topic: {topic}"}},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "\n".join(
                    ["*Status*: completed", f"*Results*: {len(results)}", f"*Job ID*: `{job_id}`"]
                ),
            },
        },
    ]
    if preview_items:
        article_lines = []
        for item in preview_items:
            title = item.title or "Untitled article"
            link = item.url or ""
            source = item.source or "unknown"
            summary = _truncate(getattr(item, "summary", "") or getattr(item, "content", ""))
            headline = f"• <{link}|{title}> — {source}" if link else f"• *{title}* — {source}"
            article_lines.append(f"{headline}\n>{summary}" if summary else headline)
        remaining = len(results) - settings.slack_preview_limit
        if remaining > 0:
            article_lines.append(
                f"• …and {remaining} more article{'s' if remaining != 1 else ''} in the dashboard"
            )
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(article_lines)}})

    payload = {
        "text": f"NovaNews job '{topic}' completed with {len(results)} result(s).",
        "username": settings.slack_username,
        "blocks": blocks,
    }
    if settings.slack_icon_emoji:
        payload["icon_emoji"] = settings.slack_icon_emoji

    if _post_slack_webhook(settings.slack_webhook_url, payload):
        log(db, job_id, "Slack notification has been sent")
```
- Toggle delivery globally via `NOVANEWS_ENABLE_SLACK_NOTIFICATIONS` (the default `.env` disables it for local runs).
- Limit or expand previews with `SLACK_WEBHOOK_PREVIEW_LIMIT` (1–10 articles).
- Use `./start.sh --slack true|false` for temporary overrides without touching `.env`.
