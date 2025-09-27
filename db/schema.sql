-- NovaNews Postgres schema
-- Idempotent: use IF NOT EXISTS and avoid destructive changes

CREATE TABLE IF NOT EXISTS articles (
  id BIGSERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  url TEXT UNIQUE NOT NULL,
  source TEXT NOT NULL,
  scraped_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_articles_source_scraped_at ON articles (source, scraped_at DESC);

CREATE TABLE IF NOT EXISTS search_jobs (
  id UUID PRIMARY KEY,
  topic TEXT NOT NULL,
  sites TEXT, -- comma-separated list
  max_items_per_site INTEGER NOT NULL DEFAULT 3,
  status TEXT NOT NULL DEFAULT 'queued', -- queued|running|completed|failed
  error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS job_logs (
  id BIGSERIAL PRIMARY KEY,
  job_id UUID NOT NULL REFERENCES search_jobs(id) ON DELETE CASCADE,
  line_number INTEGER NOT NULL,
  message TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(job_id, line_number)
);

CREATE TABLE IF NOT EXISTS job_results (
  id BIGSERIAL PRIMARY KEY,
  job_id UUID NOT NULL REFERENCES search_jobs(id) ON DELETE CASCADE,
  article_id BIGINT REFERENCES articles(id) ON DELETE SET NULL,
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  url TEXT NOT NULL,
  source TEXT NOT NULL
);

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'trg_search_jobs_updated_at'
  ) THEN
    CREATE TRIGGER trg_search_jobs_updated_at
    BEFORE UPDATE ON search_jobs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
  END IF;
END; $$;

-- News sites table for managing available sites
CREATE TABLE IF NOT EXISTS news_sites (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE, -- Display name (e.g., "Latent Space")
  code TEXT NOT NULL UNIQUE, -- Code used in API (e.g., "latent_space")
  url TEXT NOT NULL, -- Base URL of the site
  is_active BOOLEAN NOT NULL DEFAULT true,
  is_default BOOLEAN NOT NULL DEFAULT false, -- Whether this site is always available
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_news_sites_active ON news_sites (is_active);
CREATE INDEX IF NOT EXISTS idx_news_sites_code ON news_sites (code);

-- Trigger for news_sites updated_at
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'trg_news_sites_updated_at'
  ) THEN
    CREATE TRIGGER trg_news_sites_updated_at
    BEFORE UPDATE ON news_sites
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
  END IF;
END; $$;

-- Insert default sites if they don't exist
INSERT INTO news_sites (name, code, url, is_active, is_default)
SELECT 'Latent Space', 'latent_space', 'https://www.latent.space/', true, true
WHERE NOT EXISTS (SELECT 1 FROM news_sites WHERE code = 'latent_space');

INSERT INTO news_sites (name, code, url, is_active, is_default)
SELECT 'Forward Future', 'forward_future', 'https://forwardfuture.org/', true, false
WHERE NOT EXISTS (SELECT 1 FROM news_sites WHERE code = 'forward_future');

-- Ensure Forward Future URL is up to date
UPDATE news_sites
SET url = 'https://www.forwardfuture.ai/'
WHERE code = 'forward_future' AND url <> 'https://www.forwardfuture.ai/';


