from __future__ import annotations

import json
import logging
import os
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from novanews import AINewsItem, NovaNews

from .db import SessionLocal, get_db
from .jobs import (
    append_job_log,
    create_job,
    create_news_site,
    update_news_site,
    delete_news_site,
    delete_search_job,
    get_all_news_sites,
    get_all_search_jobs,
    get_job,
    get_job_logs,
    get_job_logs_count,
    get_job_results,
    get_news_site_by_id,
    save_job_results,
    update_job_status,
)
from .notifier import websocket_notifier
from .schemas import (
    AdminSearchJobDTO,
    ArticleDTO,
    CreateNewsSiteRequest,
    NewsSiteDTO,
    SearchJobRequest,
    SearchJobResponse,
    SearchJobResults,
    SearchJobStatus,
    UpdateNewsSiteRequest,
)
from .settings import get_settings
from .slack import send_slack_summary

router = APIRouter()
settings = get_settings()
logger = logging.getLogger("NovaNews")


@router.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/api/search", response_model=List[ArticleDTO])
def search(
    topic: str,
    max_items_per_site: int = 3,
    sites: Optional[str] = None,
    db: Session = Depends(get_db),
) -> List[ArticleDTO] | JSONResponse:
    try:
        api_key = settings.nova_act_api_key
        if not api_key:
            return []

        news = NovaNews(
            api_key=api_key,
            logs_directory=os.path.join(os.getcwd(), "api_logs"),
            headless=False,
        )

        allowed_sites = get_all_news_sites(db, active_only=True)
        available_sites = [(site.url, site.code) for site in allowed_sites]

        selected_sources: Optional[List[str]] = None
        if sites:
            parts = [segment.strip() for segment in sites.split(",") if segment.strip()]
            allowed = {site.code for site in allowed_sites}
            selected_sources = [p for p in parts if p in allowed] or None

        articles: List[AINewsItem] = news.search_articles_by_topic(
            topic=topic,
            max_items_per_site=max_items_per_site,
            sources=selected_sources,
            available_sites=available_sites,
        )

        return [
            ArticleDTO(
                title=item.title,
                summary=item.content,
                url=item.url,
                source=item.source,
            )
            for item in articles
        ]
    except Exception as exc:
        return JSONResponse(status_code=500, content={"detail": str(exc)})


@router.post("/api/search_jobs", response_model=SearchJobResponse)
def create_search_job(
    payload: SearchJobRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> SearchJobResponse | JSONResponse:
    if not payload.topic or len(payload.topic.strip()) == 0:
        return JSONResponse(status_code=400, content={"detail": "'topic' must be non-empty"})

    import uuid

    job_id = str(uuid.uuid4())
    create_job(db, job_id, payload.topic, payload.sites, payload.max_items_per_site)
    background_tasks.add_task(_start_search_job, job_id, payload)
    return SearchJobResponse(job_id=job_id, status="queued")


@router.get("/api/search_jobs/{job_id}/status", response_model=SearchJobStatus)
def get_search_job_status(job_id: str, db: Session = Depends(get_db)) -> SearchJobStatus | JSONResponse:
    job = get_job(db, job_id)
    if not job:
        return JSONResponse(status_code=404, content={"detail": "job not found"})
    total_logs = get_job_logs_count(db, job_id)
    return SearchJobStatus(job_id=job_id, status=job.status, total_logs=total_logs, error=job.error)


@router.get("/api/search_jobs/{job_id}/results", response_model=SearchJobResults)
def get_search_job_results(job_id: str, db: Session = Depends(get_db)) -> SearchJobResults | JSONResponse:
    job = get_job(db, job_id)
    if not job:
        return JSONResponse(status_code=404, content={"detail": "job not found"})

    results = get_job_results(db, job_id)
    return SearchJobResults(job_id=job_id, status=job.status, results=results, error=job.error)


@router.get("/api/search_jobs/{job_id}/logs", response_model=List[str])
def get_search_job_logs(job_id: str, from_index: int = 0, db: Session = Depends(get_db)) -> List[str] | JSONResponse:
    job = get_job(db, job_id)
    if not job:
        return JSONResponse(status_code=404, content={"detail": "job not found"})
    return get_job_logs(db, job_id, from_index)


@router.get("/api/admin/search_jobs", response_model=List[AdminSearchJobDTO])
def get_admin_search_jobs(db: Session = Depends(get_db)) -> List[AdminSearchJobDTO]:
    return get_all_search_jobs(db)


@router.delete("/api/admin/search_jobs/{job_id}")
def delete_job(job_id: str, db: Session = Depends(get_db)) -> dict:
    try:
        success = delete_search_job(db, job_id)
        if not success:
            return JSONResponse(status_code=404, content={"detail": "Job not found"})
        return {"message": "Job deleted successfully"}
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"detail": str(exc)})
    except Exception as exc:
        return JSONResponse(status_code=500, content={"detail": str(exc)})


@router.get("/api/sites", response_model=List[NewsSiteDTO])
def get_news_sites(active_only: bool = False, db: Session = Depends(get_db)) -> List[NewsSiteDTO]:
    return get_all_news_sites(db, active_only=active_only)


@router.get("/api/admin/sites", response_model=List[NewsSiteDTO])
def get_admin_news_sites(db: Session = Depends(get_db)) -> List[NewsSiteDTO]:
    return get_all_news_sites(db, active_only=False)


@router.get("/api/admin/sites/{site_id}", response_model=NewsSiteDTO)
def get_news_site(site_id: int, db: Session = Depends(get_db)) -> NewsSiteDTO | JSONResponse:
    site = get_news_site_by_id(db, site_id)
    if not site:
        return JSONResponse(status_code=404, content={"detail": "Site not found"})
    return site


@router.post("/api/admin/sites", response_model=NewsSiteDTO)
def create_site(req: CreateNewsSiteRequest, db: Session = Depends(get_db)) -> NewsSiteDTO | JSONResponse:
    try:
        return create_news_site(db, req)
    except Exception as exc:
        lowered = str(exc).lower()
        if "duplicate key" in lowered or "unique constraint" in lowered:
            if "name" in lowered:
                return JSONResponse(status_code=400, content={"detail": "Site name already exists"})
            if "code" in lowered:
                return JSONResponse(status_code=400, content={"detail": "Site code already exists"})
        return JSONResponse(status_code=400, content={"detail": str(exc)})


@router.put("/api/admin/sites/{site_id}", response_model=NewsSiteDTO)
def update_site(site_id: int, req: UpdateNewsSiteRequest, db: Session = Depends(get_db)) -> NewsSiteDTO | JSONResponse:
    try:
        site = update_news_site(db, site_id, req)
        if not site:
            return JSONResponse(status_code=404, content={"detail": "Site not found"})
        return site
    except Exception as exc:
        lowered = str(exc).lower()
        if "duplicate key" in lowered or "unique constraint" in lowered:
            if "name" in lowered:
                return JSONResponse(status_code=400, content={"detail": "Site name already exists"})
            if "code" in lowered:
                return JSONResponse(status_code=400, content={"detail": "Site code already exists"})
        return JSONResponse(status_code=400, content={"detail": str(exc)})


@router.delete("/api/admin/sites/{site_id}")
def delete_site(site_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        success = delete_news_site(db, site_id)
        if not success:
            return JSONResponse(status_code=404, content={"detail": "Site not found"})
        return {"message": "Site deleted successfully"}
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"detail": str(exc)})
    except Exception as exc:
        return JSONResponse(status_code=500, content={"detail": str(exc)})


@router.websocket("/ws/logs/{job_id}")
async def websocket_logs(websocket: WebSocket, job_id: str) -> None:
    await websocket.accept()
    db = SessionLocal()
    try:
        job = get_job(db, job_id)
        if not job:
            await websocket.send_text('{"type": "error", "data": "job not found"}')
            await websocket.close()
            return

        await websocket_notifier.add_connection(job_id, websocket)

        await websocket.send_text(
            json.dumps({"type": "status", "data": {"status": job.status, "error": job.error}})
        )

        for log in get_job_logs(db, job_id, 0):
            await websocket.send_text(json.dumps({"type": "log", "data": log}))

        if job.status == "completed":
            try:
                results = [result.dict() for result in get_job_results(db, job_id)]
                await websocket.send_text(json.dumps({"type": "results", "data": results}))
                await websocket.send_text(
                    json.dumps({"type": "complete", "data": {"final_status": "completed"}})
                )
            except Exception as exc:
                await websocket.send_text(
                    json.dumps({"type": "error", "data": f"Error fetching results: {exc}"})
                )
        elif job.status == "failed":
            await websocket.send_text(
                json.dumps({"type": "complete", "data": {"final_status": "failed"}})
            )

        while True:
            try:
                message = await websocket.receive_text()
                if message == "ping":
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                break
            except Exception:
                break
    finally:
        await websocket_notifier.remove_connection(job_id, websocket)
        db.close()


def _start_search_job(job_id: str, req: SearchJobRequest) -> None:
    db = SessionLocal()
    try:
        update_job_status(db, job_id, "running")

        api_key = settings.nova_act_api_key
        if not api_key:
            raise RuntimeError("NOVA_ACT_API_KEY not configured")

        news = NovaNews(
            api_key=api_key,
            logs_directory=os.path.join(os.getcwd(), "api_logs"),
            headless=False,
        )

        class DatabaseLogHandler(logging.Handler):
            def __init__(self, session: Session, job: str) -> None:
                super().__init__()
                self.db = session
                self.job_id = job

            def emit(self, record: logging.LogRecord) -> None:  # type: ignore[override]
                try:
                    message = self.format(record)
                except Exception:
                    message = record.getMessage()
                message = message or ""
                append_job_log(self.db, self.job_id, message)

        handler = DatabaseLogHandler(db, job_id)
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(handler)

        allowed_sites = get_all_news_sites(db, active_only=True)
        available_sites = [(site.url, site.code) for site in allowed_sites]
        allowed_codes = {site.code for site in allowed_sites}
        default_sources = [site.code for site in allowed_sites]

        selected_sources: Optional[List[str]] = None
        if req.sites:
            parts = [segment.strip() for segment in req.sites.split(",") if segment.strip()]
            selected_sources = [p for p in parts if p in allowed_codes] or None

        append_job_log(
            db,
            job_id,
            f"Launching search for topic='{req.topic}' sources={selected_sources or default_sources}",
        )

        items: List[AINewsItem] = news.search_articles_by_topic(
            topic=req.topic,
            max_items_per_site=req.max_items_per_site,
            sources=selected_sources,
            available_sites=available_sites,
        )

        logger.removeHandler(handler)

        results = [
            ArticleDTO(
                title=item.title,
                summary=item.content,
                url=item.url,
                source=item.source,
            )
            for item in items
        ]

        save_job_results(db, job_id, results)
        update_job_status(db, job_id, "completed")
        append_job_log(db, job_id, f"Job completed with {len(results)} result(s)")

        send_slack_summary(db, job_id, req.topic, results, append_job_log)
        websocket_notifier.notify_job_update_sync(job_id, "complete", {"final_status": "completed"})

    except Exception as exc:
        update_job_status(db, job_id, "failed", str(exc))
        append_job_log(db, job_id, f"Job failed: {exc}")
        websocket_notifier.notify_job_update_sync(job_id, "complete", {"final_status": "failed"})
    finally:
        db.close()
