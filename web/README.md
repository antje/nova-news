# NovaNews Web

Next.js frontend for NovaNews with async job support and live log streaming.

**Features:**
- Topic-based search with source selection
- Async job creation with live progress tracking
- Real-time log streaming via WebSockets
- Job status monitoring and result display

**API Integration:**
- Creates async jobs: `POST /api/search_jobs`
- WebSocket live updates (no polling): `ws://localhost:8000/ws/logs/{job_id}`
- Job status (optional UI progress): `GET /api/search_jobs/{job_id}/status`
- Final results: `GET /api/search_jobs/{job_id}/results`

**Setup:**
```bash
# Start all services (recommended)
cd nova-news
./start.sh

# Or frontend only
cd web
npm run dev  # http://localhost:8001
```
