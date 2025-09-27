#!/usr/bin/env python3
"""NovaNews - production-grade AI newsletter aggregation powered by the Nova Act SDK."""

from __future__ import annotations

import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Iterator, List, Optional
from urllib.parse import urljoin

from pydantic import BaseModel

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - optional dependency
    pass

from nova_act import ActError, NovaAct

LOCAL_BROWSER_MODE = "local"
AGENTCORE_BROWSER_MODE = "agentcore"

class BrowserMode(str, Enum):
    """Supported browser execution modes for Nova Act."""

    LOCAL = LOCAL_BROWSER_MODE
    AGENTCORE = AGENTCORE_BROWSER_MODE

    @classmethod
    def parse(cls, raw_value: Optional[str]) -> tuple["BrowserMode", Optional[str]]:
        """Return the resolved browser mode and any invalid input that triggered a fallback."""
        if raw_value is None:
            return cls.LOCAL, None
        candidate = raw_value.strip().lower()
        for mode in cls:
            if mode.value == candidate:
                return mode, None
        return cls.LOCAL, candidate


@dataclass(slots=True)
class AINewsItem:
    """Represents a news item from AI sources."""

    title: str
    source: str
    content: str
    url: str


class AINewsItemModel(BaseModel):
    """Pydantic model for structured data extraction used by Nova Act."""

    title: str
    source: str
    content: str
    url: str


# Utility helpers -----------------------------------------------------------------


def _env_flag(name: str, *, default: bool = False) -> bool:
    """Interpret an environment variable as a boolean flag."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, *, default: int) -> int:
    """Read an integer from the environment with a safe fallback."""
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


# NovaNews orchestration -----------------------------------------------------------


class NovaNews:
    """Core scraper/orchestrator for NovaNews topic searches."""

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
        if not self.api_key:
            raise ValueError("NOVA_ACT_API_KEY not found in environment variables")

        requested_mode = browser_mode or os.getenv("NOVANEWS_BROWSER_MODE") or BrowserMode.LOCAL.value
        mode, invalid_mode = BrowserMode.parse(requested_mode)
        self.browser_mode = mode.value
        self._invalid_mode = invalid_mode
        self._browser_mode_enum = mode

        self.agentcore_region = (
            agentcore_region
            or os.getenv("AGENTCORE_BROWSER_REGION")
            or os.getenv("AWS_REGION")
            or "us-east-1"
        )
        self.agentcore_preview_actuation = _env_flag(
            "AGENTCORE_BROWSER_PREVIEW_ACTUATION", default=True
        )

        self.console_logging_enabled = (
            console_logging
            if console_logging is not None
            else _env_flag("NOVANEWS_CONSOLE_LOGS", default=False)
        )

        self.headless = headless
        self.logs_directory = Path(logs_directory or (Path.cwd() / "nova_news_logs"))
        self.logs_directory.mkdir(parents=True, exist_ok=True)

        self.logger = self._setup_logging()
        self._browser_session_factory = self._load_agentcore_session_factory()
        self._agentcore_sessions_logged: set[str] = set()
        self.latest_agentcore_console_url: Optional[str] = None

        if self._invalid_mode:
            self._log_and_print(
                f"⚠️ Unrecognized NOVANEWS_BROWSER_MODE='{self._invalid_mode}', defaulting to '{LOCAL_BROWSER_MODE}'",
                "WARNING",
            )

        mode_details = f"🌐 Browser mode: {self.browser_mode}"
        if self._browser_mode_enum is BrowserMode.AGENTCORE:
            mode_details += f" (region {self.agentcore_region})"
        self._log_and_print(mode_details)
        if (
            self._browser_mode_enum is BrowserMode.AGENTCORE
            and self.agentcore_preview_actuation
        ):
            self._log_and_print("🔁 Using AgentCore Browser tool with Nova Act Playwright bridge")

        self.act_max_steps = _env_int("NOVANEWS_ACT_MAX_STEPS", default=12)
        self.act_timeout_seconds = _env_int(
            "NOVANEWS_ACT_TIMEOUT_SECONDS", default=90
        )
        self.resolve_max_steps = _env_int(
            "NOVANEWS_ACT_RESOLVE_MAX_STEPS", default=6
        )
        self.resolve_timeout_seconds = _env_int(
            "NOVANEWS_ACT_RESOLVE_TIMEOUT_SECONDS", default=45
        )

    # ---------------------------------------------------------------------
    # Internal helpers

    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger("NovaNews")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()

        log_file = self.logs_directory / f"novanews_{datetime.now():%Y%m%d_%H%M%S}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(file_handler)

        if self.console_logging_enabled:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
            logger.addHandler(console_handler)

        self.log_file_path = str(log_file)
        return logger

    def _load_agentcore_session_factory(self):
        if self._browser_mode_enum is not BrowserMode.AGENTCORE:
            return None
        try:
            from bedrock_agentcore.tools.browser_client import (  # type: ignore
                browser_session,
            )

            return browser_session
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "AgentCore browser mode requires the 'bedrock-agentcore' package. "
                "Install it via 'pip install bedrock-agentcore' or set NOVANEWS_BROWSER_MODE=local."
            ) from exc

    def _log_and_print(self, message: str, level: str = "INFO") -> None:
        level = level.upper()
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(message)

    @staticmethod
    def _maybe_console(message: str) -> None:
        try:
            print(message)
        except Exception:  # pragma: no cover - console best effort
            pass

    @contextmanager
    def _nova_act_session(self, starting_page: str, headless: bool) -> Iterator[NovaAct]:
        if self._browser_mode_enum is BrowserMode.AGENTCORE:
            if not self._browser_session_factory:
                raise RuntimeError(
                    "AgentCore browser mode is configured but browser session factory is unavailable"
                )

            preview_cfg = (
                {"playwright_actuation": True} if self.agentcore_preview_actuation else None
            )
            with self._browser_session_factory(self.agentcore_region) as client:
                self._record_agentcore_session(client)
                ws_url, headers = client.generate_ws_headers()
                session_kwargs = {
                    "starting_page": starting_page,
                    "nova_act_api_key": self.api_key,
                    "cdp_endpoint_url": ws_url,
                    "cdp_headers": headers,
                }
                if preview_cfg:
                    session_kwargs["preview"] = preview_cfg
                with NovaAct(**session_kwargs) as nova:
                    yield nova
        else:
            with NovaAct(
                starting_page=starting_page,
                nova_act_api_key=self.api_key,
                headless=headless,
                logs_directory=str(self.logs_directory),
            ) as nova:
                yield nova

    def _record_agentcore_session(self, client: Any) -> None:
        session_id = getattr(client, "session_id", None)
        if not session_id:
            current_session = getattr(client, "current_session", None)
            session_id = getattr(current_session, "session_id", None) if current_session else None
        if not session_id or session_id in self._agentcore_sessions_logged:
            return

        console_url = self._build_agentcore_console_url(session_id)
        self._agentcore_sessions_logged.add(session_id)
        self.latest_agentcore_console_url = console_url
        self._log_and_print(f"🔗 AgentCore Browser session: {console_url}")

    def _build_agentcore_console_url(self, session_id: str) -> str:
        region = self.agentcore_region or os.getenv("AWS_REGION") or "us-east-1"
        return (
            f"https://{region}.console.aws.amazon.com/bedrock-agentcore/"
            f"builtInTools/browser/aws.browser.v1#sessionId={session_id}"
        )

    # ------------------------------------------------------------------
    # Public surface

    def _scrape_latent_space(self, headless: bool) -> List[AINewsItem]:
        news_items: List[AINewsItem] = []
        with self._nova_act_session(
            starting_page="https://latent.space/",
            headless=headless,
        ) as nova:
            try:
                self._log_and_print("🌐 Navigating to Latent Space homepage...")
                self._log_and_print("⏳ Waiting for page to fully load...")
                nova.act("Wait for the page to fully load")

                self._log_and_print("🔍 Searching for recent articles...")
                result = nova.act(
                    "Close any popups first. Then use the site's search feature if available (click search icon or press '/'), or if no search is available, find the most recent blog post on the homepage. Extract its title, brief summary, and URL.",
                    schema=AINewsItemModel.model_json_schema(),
                    max_steps=self.act_max_steps,
                    timeout=self.act_timeout_seconds,
                )
                extracted = self._collect_items_from_result(
                    result,
                    source_name="latent_space",
                    default_url="https://latent.space/",
                    topic="AI insights from Swyx",
                )
                if extracted:
                    self._log_and_print("✅ Successfully extracted article from Latent Space")
                news_items.extend(extracted)
            except ActError as exc:
                self._log_and_print(f"Error scraping Latent Space: {exc}", "ERROR")
                news_items.append(
                    AINewsItem(
                        title="AI Technology Update",
                        source="latent_space",
                        content="Latest AI insights and development trends",
                        url="https://latent.space/",
                    )
                )
        return news_items

    def _collect_items_from_result(
        self,
        result: Any,
        *,
        source_name: str,
        default_url: str,
        topic: str,
        max_items: int | None = None,
    ) -> List[AINewsItem]:
        items: List[AINewsItem] = []
        max_allowed = max_items or 3

        if getattr(result, "matches_schema", False):
            parsed = getattr(result, "parsed_response", None)
            if isinstance(parsed, dict):
                items.append(
                    AINewsItem(
                        title=parsed.get("title", f"{source_name} Article"),
                        source=source_name,
                        content=parsed.get("content", topic),
                        url=parsed.get("url", default_url),
                    )
                )
            elif isinstance(parsed, list):
                for payload in parsed[:max_allowed]:
                    items.append(
                        AINewsItem(
                            title=payload.get("title", f"{source_name} Article"),
                            source=source_name,
                            content=payload.get("content", topic),
                            url=payload.get("url", default_url),
                        )
                    )
        else:
            raw = getattr(result, "response", None)
            if isinstance(raw, str):
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, dict):
                        items.append(
                            AINewsItem(
                                title=parsed.get("title", f"{source_name} Post"),
                                source=source_name,
                                content=parsed.get("content", topic),
                                url=parsed.get("url", default_url),
                            )
                        )
                    elif isinstance(parsed, list):
                        for index, payload in enumerate(parsed[:max_allowed]):
                            items.append(
                                AINewsItem(
                                    title=payload.get("title", f"{source_name} Post {index + 1}"),
                                    source=source_name,
                                    content=payload.get("content", f"{topic}"),
                                    url=payload.get("url", default_url),
                                )
                            )
                except (json.JSONDecodeError, TypeError):
                    pass

        if not items:
            items.append(
                AINewsItem(
                    title=f"{source_name} - {topic}",
                    source=source_name,
                    content=topic,
                    url=default_url,
                )
            )
        return items

    def _fallback_topic_item(
        self, *, source_name: str, topic: str, default_url: str
    ) -> AINewsItem:
        return AINewsItem(
            title=f"{source_name} - {topic}",
            source=source_name,
            content=f"Topic '{topic}' related article on {source_name}",
            url=default_url,
        )

    def _resolve_item_urls(
        self, nova: NovaAct, items: List[AINewsItem], page_url: str
    ) -> List[AINewsItem]:
        resolved: List[AINewsItem] = []
        for item in items:
            item_url = item.url or ""
            if not item_url or item_url.strip() == "" or item_url.strip() == page_url:
                try:
                    href = nova.page.evaluate(
                        r"""(title) => {
                            const norm = (s) => (s || '').toLowerCase().trim();
                            const target = norm(title);
                            if (!target) return null;
                            const anchors = Array.from(document.querySelectorAll('a[href]'));
                            for (const a of anchors) {
                                const text = norm(a.textContent);
                                if (!text) continue;
                                if (text.includes(target) || target.includes(text)) {
                                    const href = a.getAttribute('href') || '';
                                    if (href && !href.startsWith('#')) return href;
                                }
                            }
                            const nodes = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,h6,article,li,.post,.entry'));
                            for (const n of nodes) {
                                const t = norm(n.textContent);
                                if (!t) continue;
                                if (t.includes(target) || target.includes(t)) {
                                    const a = n.closest('a') || n.querySelector('a');
                                    if (a) {
                                        const href = a.getAttribute('href') || '';
                                        if (href && !href.startsWith('#')) return href;
                                    }
                                }
                            }
                            return null;
                        }""",
                        item.title,
                    )
                    if isinstance(href, str) and href:
                        item.url = urljoin(nova.page.url, href)
                    else:
                        item.url = urljoin(nova.page.url, item_url or "/")
                except Exception:
                    item.url = urljoin(nova.page.url, item_url or "/")
            else:
                item.url = urljoin(nova.page.url, item_url)
            resolved.append(item)
        return resolved

    def _enrich_items_with_dom(
        self,
        nova: NovaAct,
        items: List[AINewsItem],
        *,
        topic: str,
        page_url: str,
        source_name: str,
    ) -> None:
        try:
            dom_items = nova.page.evaluate(
                r"""(topic) => {
                    const abs = (href) => {
                        try { return new URL(href, document.baseURI).href; } catch { return null; }
                    };
                    const bad = /nav|menu|footer|header|subscribe|logo|breadcrumb|share|social|sidebar|tag|category|author|comment/i;
                    const anchors = Array.from(document.querySelectorAll('a'))
                        .filter(a => a && a.getAttribute('href'))
                        .filter(a => !a.getAttribute('href').startsWith('#'))
                        .filter(a => !/^mailto:|^javascript:/i.test(a.getAttribute('href')))
                        .map(a => ({
                            el: a,
                            href: a.getAttribute('href') || '',
                            text: (a.textContent || '').trim(),
                            cls: a.className || ''
                        }))
                        .filter(x => x.text && x.text.length >= 5)
                        .filter(x => !bad.test(x.cls));

                    const scored = anchors.map(x => {
                        const url = abs(x.href);
                        if (!url) return null;
                        const t = x.text.toLowerCase();
                        const score = (t.includes((topic||'').toLowerCase()) ? 2 : 0) + (t.length/100);
                        let summary = '';
                        const container = x.el.closest('article,li,.post,.entry,.card,section,div');
                        if (container) {
                            const txt = (container.textContent || '').trim();
                            if (txt && txt.length > x.text.length) {
                                summary = txt.replace(/\s+/g,' ').slice(0,220);
                            }
                        }
                        return { title: x.text, url, summary, score };
                    }).filter(Boolean);

                    const seen = new Set();
                    const uniq = [];
                    for (const it of scored.sort((a,b) => b.score - a.score)) {
                        try {
                            const u = new URL(it.url);
                            const key = u.hostname + u.pathname;
                            if (seen.has(key)) continue;
                            seen.add(key);
                            uniq.push({ title: it.title, url: it.url, summary: it.summary });
                        } catch {}
                        if (uniq.length >= 10) break;
                    }
                    return uniq;
                }""",
                topic,
            )
            if isinstance(dom_items, list) and dom_items:
                lookup = {entry.get("title", "").strip().lower(): entry for entry in dom_items}
                for item in items:
                    key = (item.title or "").strip().lower()
                    if key in lookup:
                        entry = lookup[key]
                        if entry.get("url"):
                            item.url = entry["url"]
                        if entry.get("summary") and len(entry["summary"]) > len(item.content or ""):
                            item.content = entry["summary"]

            if source_name == "forward_future":
                ff_href = nova.page.evaluate(
                    r"""(title) => {
                        if (!title) return null;
                        const abs = (href) => { try { return new URL(href, document.baseURI).href; } catch { return null; } };
                        const term = title.toLowerCase().split(/[^a-z0-9]+/).filter(Boolean);
                        const tset = new Set(term);
                        const anchors = Array.from(document.querySelectorAll('a[href]'))
                          .map(a => ({ a, href: a.getAttribute('href')||'', text: (a.textContent||'').toLowerCase().trim() }))
                          .filter(x => x.href && x.href.includes('/p/'));
                        let best = null; let bestScore = -1;
                        for (const x of anchors) {
                          const u = abs(x.href); if (!u) continue;
                          try {
                            const url = new URL(u);
                            const p = url.pathname || '';
                            const words = new Set(x.text.split(/[^a-z0-9]+/).filter(Boolean));
                            let overlap = 0; tset.forEach(w => { if (words.has(w)) overlap++; });
                            const score = overlap + (p.length/100);
                            if (score > bestScore) { bestScore = score; best = u; }
                          } catch {}
                        }
                        return best;
                    }""",
                    items[0].title if items else "",
                )
                if isinstance(ff_href, str) and ff_href.startswith("http") and items:
                    items[0].url = ff_href
        except Exception:
            pass

        try:
            heuristics = nova.page.evaluate(
                r"""(baseUrl) => {
                        const abs = (href) => { try { return new URL(href, document.baseURI).href; } catch { return null; } };
                        const badPath = /(^mailto:|^javascript:)|(#$|#)/i;
                        const isTagOrAuthor = /(\/tag\/|\/tags\/|\/author\/|\/?category\/?)/i;
                        const looksArticle = (u) => {
                            try {
                                const url = new URL(u);
                                const p = url.pathname;
                                if (/\/p\//.test(p)) return 10;
                                if (/\/20\d{2}\//.test(p)) return 9;
                                const segs = p.split('/').filter(Boolean);
                                if (segs.length >= 2 && /[a-zA-Z-]{6,}/.test(p)) return 7;
                                return 0;
                            } catch { return 0; }
                        };
                        const anchors = Array.from(document.querySelectorAll('a[href]'))
                            .map(a => abs(a.getAttribute('href')))
                            .filter(Boolean)
                            .filter(u => !badPath.test(u))
                            .filter(u => !isTagOrAuthor.test(u));
                        const scored = [];
                        const seen = new Set();
                        for (const u of anchors) {
                            try {
                                const url = new URL(u);
                                const key = url.hostname + url.pathname;
                                if (seen.has(key)) continue;
                                seen.add(key);
                                const s = looksArticle(u);
                                if (s > 0) scored.push({ url: u, score: s });
                            } catch {}
                        }
                        scored.sort((a,b) => b.score - a.score);
                        return scored.slice(0, 10).map(x => x.url);
                    }""",
                page_url,
            )
            if isinstance(heuristics, list) and heuristics:
                idx = 0
                for item in items:
                    if not item.url or item.url.strip() == "" or item.url.strip() == page_url:
                        if idx < len(heuristics):
                            item.url = heuristics[idx]
                            idx += 1
        except Exception:
            pass

        try:
            titles = [ni.title for ni in items if ni.title]
            if titles:
                resolve_prompt = (
                    "Find the URL links for these article titles: "
                    + ", ".join(titles)
                    + ". Return title and absolute URL for each."
                )
                resolve_schema = {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "url": {"type": "string"},
                        },
                        "required": ["title", "url"],
                    },
                }
                resolve_result = nova.act(
                    resolve_prompt,
                    schema=resolve_schema,
                    max_steps=min(self.resolve_max_steps, self.act_max_steps),
                    timeout=min(
                        self.resolve_timeout_seconds, self.act_timeout_seconds
                    ),
                )
                if getattr(resolve_result, "matches_schema", False) and isinstance(
                    resolve_result.parsed_response, list
                ):
                    mapping: dict[str, str] = {}
                    for entry in resolve_result.parsed_response:
                        try:
                            title = (entry.get("title") or "").strip().lower()
                            url_value = urljoin(
                                nova.page.url, (entry.get("url") or "").strip()
                            )
                            if title and url_value:
                                mapping[title] = url_value
                        except Exception:
                            continue
                    if mapping:
                        for item in items:
                            key = (item.title or "").strip().lower()
                            if key in mapping:
                                item.url = mapping[key]
                                continue
                            for mt, mu in mapping.items():
                                if key and (key in mt or mt in key):
                                    item.url = mu
                                    break
        except Exception:
            pass

    def _scrape_site_for_topic(
        self,
        nova: NovaAct,
        url: str,
        source_name: str,
        topic: str,
        max_items: int = 3,
    ) -> List[AINewsItem]:
        try:
            self._log_and_print(f"🔍 Searching {source_name} for topic: {topic}")
            nova.go_to_url(url)

            if source_name == "latent_space":
                prompt = (
                    "First, close any popups. Then use the site's search feature to search "
                    f"for '{topic}'. Click on the search icon or press '/' to open search, type '{topic}', "
                    "and press Enter. From the search results, extract the title, brief summary, and URL of the first result."
                )
            else:
                prompt = (
                    "First, close any popups. Then find and use the search feature on this site to search for "
                    f"'{topic}'. Type '{topic}' in the search box and press Enter. From the search results, extract the title, "
                    "brief summary, and URL of the first result."
                )

            result = nova.act(
                prompt,
                schema=AINewsItemModel.model_json_schema(),
                max_steps=self.act_max_steps,
                timeout=self.act_timeout_seconds,
            )

            news_items = self._collect_items_from_result(
                result,
                source_name=source_name,
                default_url=url,
                topic=topic,
                max_items=max_items,
            )
            news_items = self._resolve_item_urls(nova, news_items, url)
            self._enrich_items_with_dom(
                nova,
                news_items,
                topic=topic,
                page_url=url,
                source_name=source_name,
            )
            return news_items
        except ActError as exc:
            self._log_and_print(
                f"❌ Error scraping {source_name} for topic '{topic}': {exc}", "ERROR"
            )
            return [
                self._fallback_topic_item(
                    source_name=source_name, topic=topic, default_url=url
                )
            ]
        except Exception as exc:
            self._log_and_print(
                f"❌ Error scraping {source_name} for topic '{topic}': {exc}", "ERROR"
            )
            return []

    def _get_available_sites(self) -> List[tuple[str, str]]:
        try:
            from sqlalchemy import create_engine, text
            from sqlalchemy.orm import sessionmaker

            database_url = "postgresql://novanews:changeme@localhost:5432/novanews"
            engine = create_engine(database_url)
            SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=engine
            )

            db = SessionLocal()
            try:
                query = text(
                    "SELECT url, code FROM news_sites WHERE is_active = true ORDER BY name"
                )
                results = db.execute(query).fetchall()
                if results:
                    sites = [(row[0], row[1]) for row in results]
                    self._log_and_print(
                        f"📋 Loaded {len(sites)} active sites from database"
                    )
                    return sites
            finally:
                db.close()
        except Exception as exc:
            self._log_and_print(
                f"⚠️ Failed to load sites from database: {exc}", "WARNING"
            )
        self._log_and_print("📋 Using fallback hardcoded sites")
        return [("https://latent.space/", "latent_space"), ("https://www.forwardfuture.ai/", "forward_future")]

    def _scrape_sites_by_topic_parallel(
        self,
        topic: str,
        max_items_per_site: int = 3,
        sources: list[str] | None = None,
        available_sites: list[tuple[str, str]] | None = None,
    ) -> List[AINewsItem]:
        all_news_items: List[AINewsItem] = []

        def scrape_single(site_url: str, source_name: str) -> List[AINewsItem]:
            try:
                with self._nova_act_session(
                    starting_page=site_url,
                    headless=self.headless,
                ) as nova:
                    return self._scrape_site_for_topic(
                        nova,
                        site_url,
                        source_name,
                        topic,
                        max_items=max_items_per_site,
                    )
            except Exception as exc:
                self._log_and_print(
                    f"❌ Failed {source_name} for topic: {exc}", "ERROR"
                )
                return []

        all_sources = available_sites or self._get_available_sites()
        if sources:
            available_codes = {name for _, name in all_sources}
            selected = [s for s in sources if s in available_codes]
            source_mappings = [
                (url, name) for url, name in all_sources if name in selected
            ]
            if not source_mappings:
                self._log_and_print(
                    f"⚠️ No valid sources found in {sources}, using all available sites"
                )
                source_mappings = all_sources
        else:
            source_mappings = all_sources

        source_count = len(source_mappings)
        search_label = "Parallel topic search" if source_count > 1 else "Topic search"
        source_word = "source" if source_count == 1 else "sources"
        self._log_and_print(
            f"🚀 {search_label}: '{topic}' across {source_count} {source_word}"
        )

        with ThreadPoolExecutor(max_workers=max(1, source_count)) as executor:
            futures = {
                executor.submit(scrape_single, url, name): name
                for url, name in source_mappings
            }
            for future in as_completed(futures):
                name = futures[future]
                try:
                    items = future.result()
                    all_news_items.extend(items)
                    self._log_and_print(
                        f"✅ {name}: {len(items)} item(s) for topic '{topic}'"
                    )
                except Exception as exc:
                    self._log_and_print(
                        f"❌ {name} future failed: {exc}", "ERROR"
                    )

        return all_news_items

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
        return self._scrape_sites_by_topic_parallel(
            topic=topic,
            max_items_per_site=max_items_per_site,
            sources=sources,
            available_sites=available_sites,
        )

    def run_sample_search(
        self,
        topic: str = "nova act",
        max_items_per_site: int = 3,
        sources: list[str] | None = None,
        headless: bool | None = None,
    ) -> List[AINewsItem]:
        if headless is not None:
            self.headless = headless
        self._log_and_print(
            f"🔍 Running NovaNews sample search for topic: '{topic}'"
        )
        items = self.search_articles_by_topic(
            topic=topic,
            headless=self.headless,
            max_items_per_site=max_items_per_site,
            sources=sources,
            available_sites=None,
        )
        self._log_and_print(
            f"📰 Found {len(items)} article(s) for '{topic}'"
        )
        for index, item in enumerate(items, 1):
            try:
                line = (
                    f"{index}. [{item.source}] {self._safe_string(item.title)}\n   {item.url}"
                )
            except Exception:
                line = f"{index}. [{item.source}] {item.url}"
            if self.console_logging_enabled:
                self._maybe_console(line)
        return items

    @staticmethod
    def _safe_string(text: str) -> str:
        if not text:
            return ""
        try:
            if isinstance(text, str):
                import re

                text = re.sub(r"[\ud800-\udfff]", "", text)
                text = text.replace("\ud83d\ude02", "😄")
                text = text.replace("\ud83d\udca1", "💡")
                text = text.replace("\ud83d", "🤖")
                text = text.replace("\ude02", "")
                text = text.replace("\udca1", "")
                return text
            return str(text)
        except Exception:
            return "🤖"


def main() -> None:
    try:
        client = NovaNews(console_logging=True)
        client.run_sample_search(headless=True)
    except Exception as exc:
        print(f"❌ Error running NovaNews sample search: {exc}")
        print("Make sure you have NOVA_ACT_API_KEY set in your environment variables.")


if __name__ == "__main__":
    main()
