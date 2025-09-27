#!/usr/bin/env python3
"""
MCP server exposing tools to launch and monitor NovaNews search jobs using
HTTP requests (polling). No WebSocket streaming is used.

The `search_news` tool starts an async job, then clients poll with
`get_search_status` until completed and fetch results with `get_search_results`.

Usage:
  1) Start the NovaNews backend in ../ (project root):
       python -m uvicorn api.main:app --reload --port 8000
  2) Start this MCP server:
       NOVA_NEWS_API_BASE_URL=http://localhost:8000 \
       python mcp/novanews_mcp_server.py

Environment variables:
  - NOVA_NEWS_API_BASE_URL (default: http://localhost:8000)
  - NOVA_NEWS_HTTP_TIMEOUT (seconds, default: 300)
"""

from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Optional, Sequence, Literal

import httpx
from mcp.server.fastmcp import FastMCP


MCP_SERVER_NAME = "novanews-mcp-server"
MCP_SERVER_VERSION = "1.0.0"
DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_TIMEOUT_SECONDS = 300.0
ALLOWED_SITES: Sequence[str] = ("latent_space", "forward_future")
MAX_ITEMS_PER_SITE_CAP = 10


def get_base_url() -> str:
    base_url = os.getenv("NOVA_NEWS_API_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    return base_url


def get_timeout() -> float:
    raw = os.getenv("NOVA_NEWS_HTTP_TIMEOUT")
    if not raw:
        return DEFAULT_TIMEOUT_SECONDS
    try:
        return max(1.0, float(raw))
    except Exception:
        return DEFAULT_TIMEOUT_SECONDS




mcp = FastMCP(
    name=MCP_SERVER_NAME,
    dependencies=[
        "httpx>=0.27.0,<1",
    ],
)


@mcp.tool()
async def search_news(
    topic: str,
    sites: Optional[List[Literal["latent_space", "forward_future"]]] = None,
    max_items_per_site: Optional[int] = 3,
) -> Dict[str, Any]:
    """Launch a news search job and return immediately with job_id.
    
    This now starts an async job on the NovaNews API and returns:
      { job_id: string, status: "queued"|"running" }
    
    Use companion tools to monitor and retrieve results:
      - get_search_status(job_id)
      - get_search_results(job_id)
    """
    if topic is None or len(topic.strip()) == 0:
        raise ValueError("'topic' must be a non-empty string")

    filtered_sites: List[str]
    if sites and len(sites) > 0:
        filtered_sites = [s for s in (s.strip() for s in sites) if s in ALLOWED_SITES]
        if len(filtered_sites) == 0:
            filtered_sites = list(ALLOWED_SITES)
    else:
        filtered_sites = list(ALLOWED_SITES)

    per_site = 3 if max_items_per_site is None else int(max_items_per_site)
    if per_site < 1:
        per_site = 1
    if per_site > MAX_ITEMS_PER_SITE_CAP:
        per_site = MAX_ITEMS_PER_SITE_CAP

    base_url = get_base_url()
    timeout = get_timeout()

    payload = {
        "topic": topic,
        "max_items_per_site": per_site,
        "sites": ",".join(filtered_sites),
    }

    url = f"{base_url}/api/search_jobs"

    # Start the search job
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(url, json=payload)
        except httpx.RequestError as exc:
            raise RuntimeError(f"Failed to reach NovaNews API at {url}: {exc}")

    if response.status_code != 200:
        try:
            data = response.json()
            if isinstance(data, dict) and data.get("detail"):
                raise RuntimeError(f"NovaNews API error HTTP {response.status_code}: {data['detail']}")
        except Exception:
            pass
        raise RuntimeError(f"NovaNews API error HTTP {response.status_code}")

    data = response.json()
    if not isinstance(data, dict) or "job_id" not in data:
        raise RuntimeError("Unexpected API response: expected {job_id, status}")
    
    return {
        "job_id": data["job_id"], 
        "status": data.get("status", "queued")
    }


@mcp.tool()
async def get_search_status(job_id: str) -> Dict[str, Any]:
    """Get status for a search job: {job_id, status, total_logs, error?}."""
    base_url = get_base_url()
    timeout = get_timeout()
    
    url = f"{base_url}/api/search_jobs/{job_id}/status"
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(url)
        except httpx.RequestError as exc:
            raise RuntimeError(f"Failed to reach NovaNews API at {url}: {exc}")
    
    if response.status_code == 404:
        raise RuntimeError(f"Job {job_id} not found")
    elif response.status_code != 200:
        try:
            data = response.json()
            if isinstance(data, dict) and data.get("detail"):
                raise RuntimeError(f"NovaNews API error HTTP {response.status_code}: {data['detail']}")
        except Exception:
            pass
        raise RuntimeError(f"NovaNews API error HTTP {response.status_code}")
    
    return response.json()


    


@mcp.tool()
async def get_search_results(job_id: str) -> List[Dict[str, Any]]:
    """Get final results for a completed job. Returns list of articles."""
    base_url = get_base_url()
    timeout = get_timeout()
    
    url = f"{base_url}/api/search_jobs/{job_id}/results"
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(url)
        except httpx.RequestError as exc:
            raise RuntimeError(f"Failed to reach NovaNews API at {url}: {exc}")
    
    if response.status_code == 404:
        raise RuntimeError(f"Job {job_id} not found")
    elif response.status_code != 200:
        try:
            data = response.json()
            if isinstance(data, dict) and data.get("detail"):
                raise RuntimeError(f"NovaNews API error HTTP {response.status_code}: {data['detail']}")
        except Exception:
            pass
        raise RuntimeError(f"NovaNews API error HTTP {response.status_code}")
    
    data = response.json()
    
    # Handle both possible response formats
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "results" in data:
        return data["results"]
    else:
        return []



if __name__ == "__main__":
    mcp.run()


