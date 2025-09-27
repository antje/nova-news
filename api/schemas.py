from __future__ import annotations

import datetime
from typing import List, Optional

from pydantic import BaseModel


class ArticleDTO(BaseModel):
    title: str
    summary: str
    url: str
    source: str


class SearchJobRequest(BaseModel):
    topic: str
    max_items_per_site: int = 3
    sites: Optional[str] = None  # comma-separated list


class SearchJobResponse(BaseModel):
    job_id: str
    status: str


class SearchJobStatus(BaseModel):
    job_id: str
    status: str
    total_logs: int
    error: Optional[str] = None


class SearchJobLogs(BaseModel):
    job_id: str
    from_index: int = 0
    logs: List[str]
    total: int


class SearchJobResults(BaseModel):
    job_id: str
    status: str
    results: List[ArticleDTO]
    error: Optional[str] = None


class AdminSearchJobDTO(BaseModel):
    job_id: str
    topic: str
    sites: Optional[str]
    max_items_per_site: int
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    error: Optional[str]
    result_count: int


class NewsSiteDTO(BaseModel):
    id: int
    name: str
    code: str
    url: str
    is_active: bool
    is_default: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime


class CreateNewsSiteRequest(BaseModel):
    name: str
    code: str
    url: str
    is_active: bool = True


class UpdateNewsSiteRequest(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    url: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
