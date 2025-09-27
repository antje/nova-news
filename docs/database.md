### Database Integration (PostgreSQL)

NovaNews uses PostgreSQL for job persistence, live logging, article storage, and news site management. The database ensures that search jobs survive restarts, provides real-time progress tracking via WebSocket notifications, and supports comprehensive admin operations.

#### Schema Overview

The database consists of five main tables:

**Job Management:**
- `search_jobs` - Track search job metadata and status
- `job_logs` - Store real-time log messages from scraping operations
- `job_results` - Store final search results per job

**Article Storage:**
- `articles` - Deduplicated article storage with metadata
- `news_sites` - Admin-managed catalog of sources with active/default flags

#### Table Definitions

```sql
-- Job tracking and status
CREATE TABLE search_jobs (
  id UUID PRIMARY KEY,
  topic TEXT NOT NULL,
  sites TEXT, -- comma-separated list
  max_items_per_site INTEGER NOT NULL DEFAULT 3,
  status TEXT NOT NULL DEFAULT 'queued', -- queued|running|completed|failed
  error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Real-time log streaming
CREATE TABLE job_logs (
  id BIGSERIAL PRIMARY KEY,
  job_id UUID NOT NULL REFERENCES search_jobs(id) ON DELETE CASCADE,
  line_number INTEGER NOT NULL,
  message TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(job_id, line_number)
);

-- Search results per job
CREATE TABLE job_results (
  id BIGSERIAL PRIMARY KEY,
  job_id UUID NOT NULL REFERENCES search_jobs(id) ON DELETE CASCADE,
  article_id BIGINT REFERENCES articles(id) ON DELETE SET NULL,
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  url TEXT NOT NULL,
  source TEXT NOT NULL
);

-- Deduplicated article storage
CREATE TABLE articles (
  id BIGSERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  url TEXT UNIQUE NOT NULL,
  source TEXT NOT NULL,
  scraped_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Admin-managed news sites
CREATE TABLE news_sites (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  code TEXT NOT NULL UNIQUE,
  url TEXT NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT true,
  is_default BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_news_sites_active ON news_sites (is_active);
CREATE INDEX IF NOT EXISTS idx_news_sites_code ON news_sites (code);
```

#### Job Lifecycle

1. **Job Creation**: `POST /api/search_jobs` creates entry in `search_jobs` with status `queued`
2. **Job Start**: Background task updates status to `running` and begins logging to `job_logs`
3. **Progress Tracking**: Scraper logs are captured in real-time via database handler
4. **Job Completion**: Results stored in `job_results`, status updated to `completed`
5. **Error Handling**: Failures update status to `failed` with error message

#### Live Log System

The live log system works by:

1. **Database Handler**: Custom logging handler captures Nova Act scraper logs
2. **Incremental Storage**: Each log message gets a sequential line number
3. **WebSocket Streaming**: `/ws/logs/{job_id}` streams logs and status updates to the frontend
4. **Status Endpoint**: `GET /api/search_jobs/{job_id}/status` exposes `total_logs` for progress UIs

#### Database Operations

**Setup (automatic via start.sh):**
```bash
./start.sh  # Automatically configures PostgreSQL and applies schema
```
The schema seeds default news sites (`latent_space`, `forward_future`) if they do not already exist so the UI has data on first launch.

**Manual Setup:**
```bash
# Install PostgreSQL (macOS)
brew install postgresql@17
brew services start postgresql@17

# Create database and user
psql -d postgres -c "CREATE USER novanews WITH PASSWORD 'changeme';"
psql -d postgres -c "CREATE DATABASE novanews OWNER novanews;"

# Apply schema
PGPASSWORD=changeme psql -h localhost -U novanews -d novanews -f db/schema.sql
```

**Reset Database:**
```bash
./purge.sh -y  # WARNING: Destroys all data
```

#### Configuration

Database connection is controlled by environment variables:

```bash
# Database URL (default)
DATABASE_URL=postgresql://novanews:changeme@localhost:5432/novanews

# Individual components (optional)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=novanews
POSTGRES_PASSWORD=changeme
POSTGRES_DB=novanews
```

#### Monitoring

**Check Database Status:**
```bash
# Connection test
psql $DATABASE_URL -c "SELECT version();"

# Job count
psql $DATABASE_URL -c "SELECT status, COUNT(*) FROM search_jobs GROUP BY status;"

# Recent activity
psql $DATABASE_URL -c "SELECT * FROM search_jobs ORDER BY created_at DESC LIMIT 10;"
```

**Log Analysis:**
```bash
# View logs for specific job
psql $DATABASE_URL -c "SELECT message FROM job_logs WHERE job_id = 'your-job-id' ORDER BY line_number;"

# Find error patterns
psql $DATABASE_URL -c "SELECT message FROM job_logs WHERE message LIKE '%ERROR%' LIMIT 20;"
```

#### Performance

Existing optimized indexes:

```sql
-- Article recency per source
CREATE INDEX IF NOT EXISTS idx_articles_source_scraped_at ON articles (source, scraped_at DESC);

-- News site management
CREATE INDEX IF NOT EXISTS idx_news_sites_active ON news_sites (is_active);
CREATE INDEX IF NOT EXISTS idx_news_sites_code ON news_sites (code);
```

#### Backup & Recovery

**Backup:**
```bash
pg_dump $DATABASE_URL > novanews_backup.sql
```

**Restore:**
```bash
psql $DATABASE_URL < novanews_backup.sql
```

**Selective Cleanup:**
```bash
# Remove old completed jobs (keep last 100)
psql $DATABASE_URL -c "
DELETE FROM search_jobs 
WHERE status = 'completed' 
AND id NOT IN (
  SELECT id FROM search_jobs 
  WHERE status = 'completed' 
  ORDER BY created_at DESC 
  LIMIT 100
);"
```
