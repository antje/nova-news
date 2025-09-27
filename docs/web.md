### Web UI (Next.js)

The modern React frontend provides a search interface and comprehensive admin dashboard. It uses WebSocket connections for real-time updates and integrates with the FastAPI backend for job management.

#### Async Job Creation and WebSocket Integration
**Job Creation:**
```javascript
// Create async search job
const response = await fetch(`${API_BASE}/api/search_jobs`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ topic, sites, max_items_per_site })
});
const job = await response.json();
```

**Real-time WebSocket Updates:**
```javascript
// Connect to WebSocket for live logs and updates
const wsUrl = API_BASE.replace(/^http/, "ws") + `/ws/logs/${job.job_id}`;
const ws = new WebSocket(wsUrl);

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  switch (message.type) {
    case "log": setLogs(prev => [...prev, message.data]); break;
    case "status": setJobStatus(message.data.status); break;
    case "results": setArticles(message.data); break;
  }
};
```

#### Admin Dashboard Features
**Job Management:**
- View all search jobs with status, results count, and timestamps
- Delete completed/failed jobs with confirmation
- Load previous job results by clicking on completed jobs
- Real-time job status updates via WebSocket

**Site Management:**
- Add new news sources with name, code, and URL
- Edit existing site information inline
- Toggle active/inactive status for sites
- Set default sites (at least one required)
- Delete non-default sites

**Navigation:**
- Access admin at `/admin` route
- Return to main search interface with "Back to Search"
- Deep linking support for loading specific job results

#### Run locally
**Recommended (all services):**
```bash
cd nova-news
./start.sh  # starts database, backend, frontend, and MCP
```

**Frontend only (development):**
```bash
cd nova-news/web
npm run dev  # starts Next.js on :8001
```

**Key Features:**
- Real-time WebSocket communication (no polling required)
- Admin dashboard for comprehensive system management
- Live log streaming during search operations
- Job persistence and result loading
- Dynamic site configuration
- Optional Slack notifications for completed jobs (backend-controlled)

Ensure the backend is running on `http://localhost:8000` (CORS is enabled in `api/main.py`).

