### Scraper Pipeline (NovaNews)

`novanews.py` orchestrates topic-based scraping with the Nova Act SDK. It coordinates browser sessions, parallelizes site scrapes, and normalizes the results that feed the API and admin UI.

#### Initialization & Configuration
```python
class NovaNews:
    def __init__(
        self,
        api_key: str | None = None,
        logs_directory: str | None = None,
        headless: bool = False,
        browser_mode: Optional[str] = None,
        agentcore_region: Optional[str] = None,
        console_logging: Optional[bool] = None,
    ) -> None:
        self.api_key = api_key or os.getenv("NOVA_ACT_API_KEY")
        requested_mode = browser_mode or os.getenv("NOVANEWS_BROWSER_MODE") or BrowserMode.LOCAL.value
        mode, invalid_mode = BrowserMode.parse(requested_mode)
        self.browser_mode = mode.value
        self._browser_session_factory = self._load_agentcore_session_factory()
        # Logging, actuation limits, and directory setup follow…
```

Key behaviors:
- Supports `local` Playwright runs or remote `agentcore` execution via `NOVANEWS_BROWSER_MODE`.
- Automatically logs the active mode and the AgentCore console URL for new remote sessions.
- Exposes environment-tunable Nova Act limits (`NOVANEWS_ACT_*`).

#### AgentCore Browser Tool Integration
When `browser_mode` resolves to `agentcore`, NovaNews requests sessions from `bedrock_agentcore.tools.browser_client`:
```python
@contextmanager
def _nova_act_session(self, starting_page: str, headless: bool) -> Iterator[NovaAct]:
    if self._browser_mode_enum is BrowserMode.AGENTCORE:
        with self._browser_session_factory(self.agentcore_region) as client:
            self._record_agentcore_session(client)
            ws_url, headers = client.generate_ws_headers()
            with NovaAct(
                starting_page=starting_page,
                nova_act_api_key=self.api_key,
                cdp_endpoint_url=ws_url,
                cdp_headers=headers,
                preview={"playwright_actuation": True} if self.agentcore_preview_actuation else None,
            ) as nova:
                yield nova
    else:
        with NovaAct(starting_page=starting_page, nova_act_api_key=self.api_key, headless=headless,
                     logs_directory=str(self.logs_directory)) as nova:
            yield nova
```
The helper `_record_agentcore_session` captures the generated session ID and prints an AWS console deep link so operators can inspect remote runs.

#### Public API
```python
def search_articles_by_topic(
    self,
    topic: str,
    headless: bool | None = None,
    max_items_per_site: int = 3,
    sources: list[str] | None = None,
    available_sites: list[tuple[str, str]] | None = None,
) -> List[AINewsItem]:
    if headless is not None:
        self.headless = headless
    return self._scrape_sites_by_topic_parallel(...)
```
- `available_sites` lets the API inject database-managed sites instead of the built-in fallback list.
- `sources` filters the scrape to selected site codes.

#### Site Discovery
```python
def _get_available_sites(self) -> List[tuple[str, str]]:
    with SessionLocal() as db:
        rows = db.execute("SELECT url, code FROM news_sites WHERE is_active = true ORDER BY name")
        return [(row[0], row[1]) for row in rows]
```
If the database lookup fails, the scraper falls back to Latent Space and Forward Future.

#### Parallel Orchestration
```python
def _scrape_sites_by_topic_parallel(...):
    with ThreadPoolExecutor(max_workers=max(1, source_count)) as executor:
        futures = {executor.submit(scrape_single, url, name): name for url, name in source_mappings}
        for future in as_completed(futures):
            all_news_items.extend(future.result())
```
Each worker opens its own Nova Act session (local or AgentCore) for the assigned site.

#### Per-site Search
```python
def _scrape_site_for_topic(...):
    prompt = (
        "Search this site for the topic '{topic}'. "
        "If there is a dedicated search UX, use it. Otherwise find the most recent relevant article."
    )
    result = nova.act(
        prompt,
        schema=AINewsItemModel.model_json_schema(),
        max_steps=self.act_max_steps,
        timeout=self.act_timeout_seconds,
    )
    news_items = self._collect_items_from_result(result, source_name=source_name, ...)
    news_items = self._resolve_item_urls(nova, news_items, url)
    self._enrich_items_with_dom(nova, news_items, topic=topic, page_url=url, source_name=source_name)
```
Failures short-circuit with a fallback item so downstream systems always receive structured data.

#### URL Resolution & Enrichment
- `_resolve_item_urls`: fills missing URLs by inspecting anchors relative to the page URL.
- `_enrich_items_with_dom`: pulls DOM summaries and scores likely article links to improve metadata.

#### Data Models
```python
@dataclass(slots=True)
class AINewsItem:
    title: str
    source: str
    content: str
    url: str

class AINewsItemModel(BaseModel):
    title: str
    source: str
    content: str
    url: str
```
These models feed Pydantic DTOs in the API layer and drive the Slack webhook summaries.
