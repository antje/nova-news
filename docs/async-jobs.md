### Async Job System with WebSocket Live Updates

NovaNews implements a sophisticated asynchronous job system that allows long-running searches to execute in the background while providing real-time progress updates via WebSocket streaming. This system eliminates polling overhead, ensures scalability, and provides instant user feedback for time-intensive operations that perform actions within a web browser.

#### System Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Frontend   │───▶│   FastAPI   │───▶│ PostgreSQL  │
│  (Next.js)  │    │  Backend    │    │  Database   │
└─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │
       ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ WebSocket   │    │ Background  │    │ Job Logs    │
│ Log Stream  │    │ Tasks       │    │ Storage     │
└─────────────┘    └─────────────┘    └─────────────┘
```

#### Job Lifecycle

**1. Job Creation**
```bash
POST /api/search_jobs
{
  "topic": "nova act",
  "sites": "latent_space,forward_future",
  "max_items_per_site": 3
}
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued"
}
```

**2. Background Execution**
- FastAPI `BackgroundTasks` starts the search job
- Job status updated to `running` in database
- Nova Act orchestrator begins parallel action sequences within a web browser
- Live logs captured via custom database handler

**3. Progress Tracking**
```bash
GET /api/search_jobs/{job_id}/status
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "total_logs": 45,
  "error": null
}
```

**4. Real-time WebSocket Updates**
```bash
# WebSocket connection for live updates
ws://localhost:8000/ws/logs/{job_id}

# Receives JSON messages:
# {"type": "log", "data": "Scraping started..."}
# {"type": "status", "data": {"status": "running"}}
# {"type": "results", "data": [{"title": "..."}]}
# {"type": "complete", "data": {"final_status": "completed"}}
```

**5. Result Retrieval**
```bash
GET /api/search_jobs/{job_id}/results
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "results": [
    {
      "title": "Nova Act SDK Release Notes",
      "summary": "Latest features and improvements...",
      "url": "https://example.com/article",
      "source": "latent_space"
    }
  ],
  "error": null
}
```
- When Slack notifications are enabled, the backend posts a condensed version of these results to the configured webhook and logs the outcome.

#### Live Logging Implementation

**Database Handler (api/main.py):**
```python
class DatabaseLogHandler(logging.Handler):
    def __init__(self, db_session, job_id):
        super().__init__()
        self.db_session = db_session
        self.job_id = job_id

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
        except Exception:
            msg = record.getMessage()
        if msg is None:
            msg = ""
        append_job_log(self.db_session, self.job_id, msg)
```

**Log Capture Integration:**
```python
# Attach handler to NovaNews logger
logger = logging.getLogger("NovaNews")
handler = DatabaseLogHandler(db, job_id)
handler.setLevel(logging.INFO)
logger.addHandler(handler)

# Execute search with logging
items = news.search_articles_by_topic(topic, max_items_per_site, sources)

# Clean up
logger.removeHandler(handler)
```

#### WebSocket Live Streaming

**Backend WebSocket System:**
```python
class WebSocketNotifier:
    async def notify_job_update(self, job_id: str, message_type: str, data: any):
        message = json.dumps({"type": message_type, "data": data})
        connections = list(self._connections.get(job_id, []))
        for websocket in connections:
            try:
                await websocket.send_text(message)
            except Exception:
                pass
```

**Frontend Integration:**
```javascript
const wsUrl = API_BASE.replace(/^http/, "ws") + `/ws/logs/${job.job_id}`;
const ws = new WebSocket(wsUrl);
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  switch (message.type) {
    case "log": setLogs(prev => [...prev, message.data]); break;
    case "status": setJobStatus(message.data.status); break;
    case "results": setArticles(message.data); break;
    case "complete": setLoading(false); break;
  }
};
```

#### Error Handling

**Job Failure Management:**
```python
try:
    items = news.search_articles_by_topic(...)
    update_job_status(db, job_id, "completed")
except Exception as e:
    update_job_status(db, job_id, "failed", str(e))
    append_job_log(db, job_id, f"Job failed: {e}")
```

#### Best Practices

1. Job cleanup of old completed jobs
2. Consider log truncation for very long jobs
3. Rate limit job creation
4. Set reasonable timeouts
5. Monitor database growth and index critical columns

#### Troubleshooting
- Verify WebSocket URL `ws://localhost:8000/ws/logs/{job_id}`
- Ensure CORS allows `http://localhost:8001`
- Confirm job exists before connecting
- Check backend/ frontend logs via `./monitor.sh`
