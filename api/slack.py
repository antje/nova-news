from __future__ import annotations

import json
from typing import Callable, Sequence
from urllib import error as urllib_error, request as urllib_request

from sqlalchemy.orm import Session

from .schemas import ArticleDTO
from .settings import get_settings

LogCallback = Callable[[Session, str, str], None]


def _post_slack_webhook(webhook_url: str, payload: dict, timeout: int = 8) -> bool:
    data = json.dumps(payload).encode("utf-8")
    req = urllib_request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "NovaNews/1.0"},
        method="POST",
    )
    with urllib_request.urlopen(req, timeout=timeout) as response:
        status = getattr(response, "status", None) or response.getcode()
        return 200 <= int(status) < 300


def _truncate(text: str, limit: int = 200) -> str:
    clean = (text or "").strip()
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1].rstrip() + "…"


def send_slack_summary(
    db: Session,
    job_id: str,
    topic: str,
    results: Sequence[ArticleDTO],
    log: LogCallback,
) -> None:
    settings = get_settings()
    if not settings.enable_slack_notifications or not settings.slack_configured:
        return

    preview_items = list(results[: settings.slack_preview_limit])
    total_results = len(results)

    header_text = f"Topic: {topic}"
    summary_lines = [
        "*Status*: completed",
        f"*Results*: {total_results} article{'s' if total_results != 1 else ''}",
        f"*Job ID*: `{job_id}`",
    ]

    blocks: list[dict] = [
        {"type": "header", "text": {"type": "plain_text", "text": header_text[:150]}},
        {"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(summary_lines)}},
    ]

    if preview_items:
        article_lines: list[str] = []
        for item in preview_items:
            title = item.title or "Untitled article"
            link = item.url or ""
            summary = _truncate(getattr(item, "summary", "") or getattr(item, "content", ""))
            source = item.source or "unknown"
            if link:
                headline = f"• <{link}|{title}> — {source}"
            else:
                headline = f"• *{title}* — {source}"
            if summary:
                article_lines.append(f"{headline}\n>{summary}")
            else:
                article_lines.append(headline)

        if total_results > settings.slack_preview_limit:
            remaining = total_results - settings.slack_preview_limit
            article_lines.append(
                f"• …and {remaining} more article{'s' if remaining != 1 else ''} in the dashboard"
            )

        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(article_lines)}})

    payload: dict = {
        "text": f"NovaNews job '{topic}' completed with {total_results} result(s).",
        "username": settings.slack_username,
        "blocks": blocks,
    }
    if settings.slack_icon_emoji:
        payload["icon_emoji"] = settings.slack_icon_emoji

    try:
        if _post_slack_webhook(settings.slack_webhook_url, payload):
            log(db, job_id, "Slack notification has been sent")
    except urllib_error.URLError:
        return
    except Exception:  # pragma: no cover - best effort
        return
