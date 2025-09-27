from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Tuple


def _bool_env(name: str, *, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, *, default: int, min_value: int | None = None, max_value: int | None = None) -> int:
    raw = os.getenv(name)
    if raw is None:
        value = default
    else:
        try:
            value = int(raw)
        except ValueError:
            value = default
    if min_value is not None:
        value = max(min_value, value)
    if max_value is not None:
        value = min(max_value, value)
    return value


def _split_env(name: str, *, default: Tuple[str, ...]) -> Tuple[str, ...]:
    raw = os.getenv(name)
    if not raw:
        return default
    parts = [segment.strip() for segment in raw.split(",") if segment.strip()]
    return tuple(parts) if parts else default


@dataclass(frozen=True)
class Settings:
    database_url: str
    nova_act_api_key: str | None
    cors_origins: Tuple[str, ...]
    enable_slack_notifications: bool
    slack_webhook_url: str
    slack_preview_limit: int
    slack_username: str
    slack_icon_emoji: str | None

    @property
    def slack_configured(self) -> bool:
        return bool(self.slack_webhook_url)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv(
            "DATABASE_URL", "postgresql://novanews:changeme@localhost:5432/novanews"
        ),
        nova_act_api_key=os.getenv("NOVA_ACT_API_KEY"),
        cors_origins=_split_env(
            "NOVANEWS_ALLOWED_ORIGINS",
            default=("http://localhost:8001", "http://127.0.0.1:8001"),
        ),
        enable_slack_notifications=_bool_env(
            "NOVANEWS_ENABLE_SLACK_NOTIFICATIONS", default=True
        ),
        slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL", "").strip(),
        slack_preview_limit=_int_env(
            "SLACK_WEBHOOK_PREVIEW_LIMIT", default=5, min_value=1, max_value=10
        ),
        slack_username=os.getenv("SLACK_WEBHOOK_USERNAME", "NovaNews Bot").strip()
        or "NovaNews Bot",
        slack_icon_emoji=(os.getenv("SLACK_WEBHOOK_ICON_EMOJI") or "").strip() or None,
    )
