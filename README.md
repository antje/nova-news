# NovaNews 📰

**AI News Search System powered by Nova Act SDK**

NovaNews is a comprehensive news search and monitoring system that demonstrates the Nova Act SDK's capabilities for building production-ready applications that perform actions within a web browser. It intelligently searches AI newsletters and blogs in parallel, providing both real-time and asynchronous access to the latest AI news and insights.

<img width="1674" height="886" alt="image" src="https://github.com/user-attachments/assets/58bde53e-f265-459e-b533-25de1cbf3149" />

<img width="1686" height="1820" alt="image" src="https://github.com/user-attachments/assets/da18487c-15da-4f4a-93db-4d71dde42550" />


## 🎯 Key Capabilities

This project demonstrates:
- **Async job-based search** with live progress logs
- **Parallel browser automation** with Nova Act SDK
- **Database-backed persistence** with PostgreSQL
- **Real-time log streaming** via WebSockets
- **Multi-service orchestration** (API, Frontend, Database, MCP)
- **Structured data extraction** using Pydantic models
- **Production-ready error handling** and recovery strategies
- **Dual execution modes** for Nova Act: local Playwright automation or Amazon Bedrock AgentCore Browser tool
- **Optional Slack webhooks** that announce completed jobs with rich previews


<img width="2316" height="1676" alt="image" src="https://github.com/user-attachments/assets/184460c0-a971-4189-befe-3e9e48582f91" />


## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web UI        │───▶│  FastAPI        │───▶│  PostgreSQL     │
│   (Next.js)     │    │  Backend        │    │  Database       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Live Log Stream │    │ Async Job Queue │    │ News Sources    │
│ (WebSockets)    │    │ (Background)    │    │ - Latent Space  │
│                 │    │                 │    │ - Forward Future│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                               ▼
                    ┌─────────────────┐
                    │   Nova Act      │
                    │                 │
                    └─────────────────┘
```

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd nova-news
cp env.example .env
# Edit .env to set your NOVA_ACT_API_KEY
# Optional: set NOVANEWS_BROWSER_MODE=agentcore to use Bedrock AgentCore Browser
```

### 2. Start All Services
```bash
./start.sh
```

Need a one-off browser mode override? Use:

```bash
./start.sh --mode agentcore   # or --mode local
./start.sh --slack true        # send Slack notifications for this run
```

This single command will:
- Set up Python virtual environment and dependencies
- Start PostgreSQL database
- Launch FastAPI backend (port 8000)
- Start Next.js frontend (port 8001)
- Launch MCP server for AI assistant integration

### 3. Access the Application
- **Web UI**: http://localhost:8001
- **API**: http://localhost:8000
- **Admin Dashboard**: http://localhost:8001/admin
- **Health Check**: http://localhost:8000/api/health
- **API Docs**: http://localhost:8000/docs

### 4. Stop Services
```bash
./stop.sh
```

## 🌐 Browser Execution Modes

NovaNews now supports two ways to run the Nova Act browser workflow:

- `local` (default): Launches Nova Act sessions on your machine using the bundled Playwright runtime.
- `agentcore`: Proxies Nova Act through the Amazon Bedrock AgentCore Browser tool so automation runs inside AWS-managed sandboxes.

<img width="2122" height="494" alt="image" src="https://github.com/user-attachments/assets/4e11a70b-0866-4df6-a320-c77443080a66" />



### Switch Modes

Set `NOVANEWS_BROWSER_MODE` in your `.env` file or shell:

```bash
# Local development (default)
NOVANEWS_BROWSER_MODE=local

# Remote execution via Bedrock AgentCore Browser tool
NOVANEWS_BROWSER_MODE=agentcore
AGENTCORE_BROWSER_REGION=us-east-1  # override if your AgentCore resources live elsewhere
# Disable Playwright actuation preview inside AgentCore (enabled by default)
AGENTCORE_BROWSER_PREVIEW_ACTUATION=false
```

Restart the stack after changing the environment so the backend picks up the new mode.

### AgentCore Prerequisites

When running with `agentcore` you need the following:

1. AWS credentials permitted to use Amazon Bedrock AgentCore (see `AWS_BEARER_TOKEN_BEDROCK` in `.env`).
2. The Python dependency `bedrock-agentcore` (already listed in `requirements.txt`).
3. Network access from the backend machine to AWS endpoints.
4. Optional visual actuation support can be toggled with `AGENTCORE_BROWSER_PREVIEW_ACTUATION=true|false`.

The backend logs will confirm the active mode on startup:

```
🌐 Browser mode: agentcore (region us-east-1)
🔁 Using AgentCore Browser tool with Nova Act Playwright bridge
🔗 AgentCore Browser session: https://us-east-1.console.aws.amazon.com/bedrock-agentcore/builtInTools/browser/aws.browser.v1#sessionId=...
```

If AgentCore runs feel slow, override Nova Act limits without editing code:

```bash
# Example (optional) tuning knobs
NOVANEWS_ACT_MAX_STEPS=14
NOVANEWS_ACT_TIMEOUT_SECONDS=120
NOVANEWS_ACT_RESOLVE_MAX_STEPS=8
NOVANEWS_ACT_RESOLVE_TIMEOUT_SECONDS=60
```

## 📋 Features

### **Smart News Search**
- Topic-based search across AI sources
- Intelligent content extraction and summarization
- Parallel processing for fast results
- Support for multiple source filtering

### **Async Job System**
- Background processing for long-running searches
- Real-time progress tracking with live logs via WebSockets
- Job persistence in PostgreSQL database
- Instant live updates with no polling required
- Admin dashboard for job management and monitoring

### **Admin Dashboard**
- **Job Management**: View all search jobs with status, results count, and timestamps
- **Job Operations**: Delete completed/failed jobs, load previous results
- **Site Management**: Add, edit, delete, and configure news sources
- **Site Configuration**: Toggle active/inactive status and set default sources
- **Real-time Updates**: Live job monitoring with WebSocket integration
- **Statistics**: Job completion rates and result summaries

<img width="1686" height="1644" alt="image" src="https://github.com/user-attachments/assets/7d5ef794-2696-4f8b-a526-c647bef98d55" />


### **Production Architecture**
- FastAPI backend with WebSocket support and async capabilities
- Next.js frontend with real-time WebSocket integration
- PostgreSQL database for data persistence and live logging
- Admin dashboard for job and site management
- MCP server for AI assistant integration
- Unified service management scripts

### **Data Sources**
- **Latent Space** by Swyx - AI engineering insights
- **Forward Future** by Matthew Berman - AI tool reviews and news
- Extensible architecture for adding new sources via admin panel

## 💡 Usage Examples

### **Web UI Search**
1. Open http://localhost:8001
2. Enter a search topic (e.g., "nova act", "large language models")
3. Select sources or leave blank for all sources
4. Click "Search" to start an async job
5. Watch live logs stream in real-time via WebSocket
6. View results when completed
7. Access admin dashboard at /admin for job management

### **Direct API Usage**
```bash
# Synchronous search (legacy endpoint)
curl 'http://localhost:8000/api/search?topic=nova%20act&sites=latent_space,forward_future'

# Async job-based search (recommended)
# 1. Start a search job
curl -X POST 'http://localhost:8000/api/search_jobs' \
  -H 'Content-Type: application/json' \
  -d '{"topic": "nova act", "sites": "latent_space,forward_future", "max_items_per_site": 3}'

# 2. Check job status (returns job_id from step 1)
curl 'http://localhost:8000/api/search_jobs/{job_id}/status'

# 3. Connect to WebSocket for live logs
# WebSocket URL: ws://localhost:8000/ws/logs/{job_id}

# 4. Get final results
curl 'http://localhost:8000/api/search_jobs/{job_id}/results'
```

### **Admin Dashboard Usage**
1. Open http://localhost:8001/admin
2. **View Search Jobs**: Monitor all search activities with real-time status
3. **Manage Jobs**: Delete completed jobs or load previous results
4. **Configure Sites**: Add new news sources or modify existing ones
5. **Set Defaults**: Configure which sites are used by default
6. **Monitor Statistics**: View job completion rates and result counts

### **MCP Integration**
```python
# Use with Claude Desktop, Cursor, Kiro, or other MCP-compatible clients
# The MCP server exposes search_news tool for AI assistants
search_news(topic="machine learning", sites=["latent_space"], max_items_per_site=5)
```

<img width="2057" height="2191" alt="image" src="https://github.com/user-attachments/assets/fd84322f-af1d-444b-81cb-f97ea572ccf2" />


## 🔧 Technical Implementation

### **Key Technologies:**
- **Nova Act SDK**: Browser automation and intelligent action execution within a web browser
- **FastAPI**: Modern async Python web framework
- **PostgreSQL**: Robust database for job persistence and logging
- **Next.js**: React-based frontend with modern UI
- **SQLAlchemy**: Database ORM and query building
- **WebSockets**: Real-time log streaming, live updates, and admin notifications
- **Pydantic**: Data validation and serialization

### **Core Components:**

#### **Database Schema:**
```sql
-- Job management and tracking
search_jobs (id, topic, sites, status, created_at, updated_at)
job_logs (id, job_id, line_number, message, created_at)
job_results (id, job_id, title, summary, url, source)
articles (id, title, summary, url, source, found_at)
news_sites (id, name, code, url, is_active, is_default, created_at, updated_at)
```

#### **Data Models:**
```python
class AINewsItem:
    title: str
    source: str  # "forward_future", "latent_space"
    content: str  # Article summary/content
    url: str     # Full article URL

class SearchJobRequest:
    topic: str
    max_items_per_site: int = 3
    sites: Optional[str] = None  # comma-separated

class SearchJobResponse:
    job_id: str
    status: str  # queued|running|completed|failed
```

## 🛠️ Development & Management

### **Service Management:**
```bash
# Start everything (database, backend, frontend, MCP)
./start.sh

# Stop all services
./stop.sh

# Reset database (WARNING: destroys all data)
./purge.sh -y

# Monitor service logs (comprehensive monitoring)
./monitor.sh            # View all service logs with color coding
./monitor.sh backend    # Monitor backend API logs only
./monitor.sh frontend   # Monitor frontend logs only  
./monitor.sh mcp        # Monitor MCP server logs only
./monitor.sh status     # Show service status and health
```

### **Individual Development:**
```bash
# Backend only
cd nova-news  # from the repository root
source .venv/bin/activate
python -m uvicorn api.main:app --reload --port 8000

# Frontend only  
cd web
npm run dev

# MCP server only
cd mcp
python novanews_mcp_server.py
```

### **Project Structure:**
```
nova-news/
├── api/               # FastAPI backend with WebSocket support
├── web/               # Next.js frontend with admin dashboard
│   ├── app/page.tsx   # Main search interface
│   └── app/admin/     # Admin dashboard for job/site management
├── mcp/               # MCP server for AI integration
├── db/                # Database schema and migrations
├── logs/              # Application logs
├── .run/              # Runtime PID files
├── novanews.py        # Core web action logic (Nova Act)
├── start.sh           # Unified startup script
├── stop.sh            # Unified shutdown script
└── purge.sh           # Database reset script
```

## 🎯 Why This Architecture

1. **Production Ready**: Database persistence, error handling, monitoring
2. **Scalable**: Async job processing, WebSocket streaming
3. **Developer Friendly**: Single command setup, comprehensive logging
4. **AI Native**: Built-in MCP integration for AI assistants
5. **Modern Stack**: FastAPI, Next.js, PostgreSQL, WebSockets
6. **Extensible**: Easy to add new news sources and features

## 🔧 Customization

### **Add More News Sources (Admin Dashboard):**
1. Navigate to http://localhost:8001/admin
2. Click "Add New Site" in the News Sites Management section
3. Fill in site name, code, and URL
4. Toggle active/default status as needed
5. The new source will be immediately available for searches

### **Add More News Sources (Code):**
NovaNews pulls active sites from the `news_sites` table. Seed additional defaults with an `INSERT` into that table or pass a custom `available_sites` list to `search_articles_by_topic` when driving the news search directly.

### **Extend Database Schema:**
```sql
-- Add custom fields to articles table
ALTER TABLE articles ADD COLUMN category TEXT;
ALTER TABLE articles ADD COLUMN author TEXT;
ALTER TABLE articles ADD COLUMN published_date TIMESTAMPTZ;
```

### **Custom Search Parameters:**
```python
# Extend SearchJobRequest model in api/main.py
class SearchJobRequest(BaseModel):
    topic: str
    max_items_per_site: int = 3
    sites: Optional[str] = None
    date_range: Optional[str] = None  # "7d", "30d", "90d"
    category_filter: Optional[str] = None
```

### **Slack Notifications (Optional):**
1. Create an incoming webhook in Slack (Workspace Settings → Apps → Incoming Webhooks).
2. Add `SLACK_WEBHOOK_URL=https://hooks.slack.com/...` to your `.env` file.
3. Delivery is disabled by default to keep local runs quiet; flip `NOVANEWS_ENABLE_SLACK_NOTIFICATIONS=true` or pass `./start.sh --slack true` to enable it for that run. Use `./start.sh --slack false` to temporarily suppress notifications when needed.
4. (Optional) Tweak `SLACK_WEBHOOK_USERNAME`, `SLACK_WEBHOOK_ICON_EMOJI`, or `SLACK_WEBHOOK_PREVIEW_LIMIT` to customize the message.
5. Completed search jobs now post a rich summary with the top results into the configured channel.

---

