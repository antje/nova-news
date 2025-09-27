from __future__ import annotations

from typing import Iterable, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from .notifier import websocket_notifier
from .schemas import AdminSearchJobDTO, ArticleDTO, NewsSiteDTO


# Search job helpers -----------------------------------------------------------------

def create_job(
    db: Session,
    job_id: str,
    topic: str,
    sites: Optional[str] = None,
    max_items_per_site: int = 3,
) -> None:
    query = text(
        """
        INSERT INTO search_jobs (id, topic, sites, max_items_per_site, status, created_at, updated_at)
        VALUES (:job_id, :topic, :sites, :max_items_per_site, 'queued', NOW(), NOW())
        """
    )
    db.execute(
        query,
        {
            "job_id": job_id,
            "topic": topic,
            "sites": sites,
            "max_items_per_site": max_items_per_site,
        },
    )
    db.commit()


def get_job(db: Session, job_id: str):
    query = text("SELECT * FROM search_jobs WHERE id = :job_id")
    return db.execute(query, {"job_id": job_id}).fetchone()


def update_job_status(db: Session, job_id: str, status: str, error: Optional[str] = None) -> None:
    if error:
        query = text(
            "UPDATE search_jobs SET status = :status, error = :error, updated_at = NOW() WHERE id = :job_id"
        )
        db.execute(query, {"job_id": job_id, "status": status, "error": error})
    else:
        query = text(
            "UPDATE search_jobs SET status = :status, updated_at = NOW() WHERE id = :job_id"
        )
        db.execute(query, {"job_id": job_id, "status": status})
    db.commit()
    websocket_notifier.notify_job_update_sync(job_id, "status", {"status": status, "error": error})


def append_job_log(db: Session, job_id: str, message: str) -> None:
    count_query = text(
        "SELECT COALESCE(MAX(line_number), 0) + 1 FROM job_logs WHERE job_id = :job_id"
    )
    line_number = db.execute(count_query, {"job_id": job_id}).scalar()

    insert_query = text(
        """
        INSERT INTO job_logs (job_id, line_number, message, created_at)
        VALUES (:job_id, :line_number, :message, NOW())
        """
    )
    db.execute(
        insert_query,
        {"job_id": job_id, "line_number": line_number, "message": message},
    )
    db.commit()
    websocket_notifier.notify_job_update_sync(job_id, "log", message)


def get_job_logs(db: Session, job_id: str, from_index: int = 0) -> List[str]:
    query = text(
        """
        SELECT message FROM job_logs
        WHERE job_id = :job_id AND line_number > :from_index
        ORDER BY line_number
        """
    )
    result = db.execute(query, {"job_id": job_id, "from_index": from_index}).fetchall()
    return [row[0] for row in result]


def get_job_logs_count(db: Session, job_id: str) -> int:
    query = text("SELECT COUNT(*) FROM job_logs WHERE job_id = :job_id")
    return db.execute(query, {"job_id": job_id}).scalar()


def save_job_results(db: Session, job_id: str, results: Iterable[ArticleDTO]) -> None:
    stored = list(results)
    insert_query = text(
        """
        INSERT INTO job_results (job_id, title, summary, url, source)
        VALUES (:job_id, :title, :summary, :url, :source)
        """
    )
    for result in stored:
        db.execute(
            insert_query,
            {
                "job_id": job_id,
                "title": result.title,
                "summary": result.summary,
                "url": result.url,
                "source": result.source,
            },
        )
    db.commit()
    websocket_notifier.notify_job_update_sync(
        job_id,
        "results",
        [
            {
                "title": r.title,
                "summary": r.summary,
                "url": r.url,
                "source": r.source,
            }
            for r in stored
        ],
    )


def get_job_results(db: Session, job_id: str) -> List[ArticleDTO]:
    query = text(
        """
        SELECT title, summary, url, source FROM job_results
        WHERE job_id = :job_id
        ORDER BY id
        """
    )
    rows = db.execute(query, {"job_id": job_id}).fetchall()
    return [ArticleDTO(title=row[0], summary=row[1], url=row[2], source=row[3]) for row in rows]


def get_all_search_jobs(db: Session) -> List[AdminSearchJobDTO]:
    query = text(
        """
        SELECT \
            sj.id,\
            sj.topic,\
            sj.sites,\
            sj.max_items_per_site,\
            sj.status,\
            sj.created_at,\
            sj.updated_at,\
            sj.error,\
            COALESCE(jr.result_count, 0) as result_count\
        FROM search_jobs sj\
        LEFT JOIN (\
            SELECT job_id, COUNT(*) as result_count\
            FROM job_results\
            GROUP BY job_id\
        ) jr ON sj.id = jr.job_id\
        ORDER BY sj.created_at DESC
        """
    )
    rows = db.execute(query).fetchall()
    return [
        AdminSearchJobDTO(
            job_id=str(row[0]),
            topic=row[1],
            sites=row[2],
            max_items_per_site=row[3],
            status=row[4],
            created_at=row[5],
            updated_at=row[6],
            error=row[7],
            result_count=row[8],
        )
        for row in rows
    ]


# News site management --------------------------------------------------------------

def get_all_news_sites(db: Session, *, active_only: bool = False) -> List[NewsSiteDTO]:
    if active_only:
        query = text("SELECT * FROM news_sites WHERE is_active = true ORDER BY name")
    else:
        query = text("SELECT * FROM news_sites ORDER BY name")
    rows = db.execute(query).fetchall()
    return [
        NewsSiteDTO(
            id=row[0],
            name=row[1],
            code=row[2],
            url=row[3],
            is_active=row[4],
            is_default=row[5],
            created_at=row[6],
            updated_at=row[7],
        )
        for row in rows
    ]


def get_news_site_by_id(db: Session, site_id: int) -> Optional[NewsSiteDTO]:
    query = text("SELECT * FROM news_sites WHERE id = :site_id")
    row = db.execute(query, {"site_id": site_id}).fetchone()
    if not row:
        return None
    return NewsSiteDTO(
        id=row[0],
        name=row[1],
        code=row[2],
        url=row[3],
        is_active=row[4],
        is_default=row[5],
        created_at=row[6],
        updated_at=row[7],
    )


def create_news_site(db: Session, request) -> NewsSiteDTO:
    query = text(
        """
        INSERT INTO news_sites (name, code, url, is_active, is_default)
        VALUES (:name, :code, :url, :is_active, false)
        RETURNING *
        """
    )
    row = db.execute(
        query,
        {
            "name": request.name,
            "code": request.code,
            "url": request.url,
            "is_active": request.is_active,
        },
    ).fetchone()
    db.commit()
    return NewsSiteDTO(
        id=row[0],
        name=row[1],
        code=row[2],
        url=row[3],
        is_active=row[4],
        is_default=row[5],
        created_at=row[6],
        updated_at=row[7],
    )


def update_news_site(db: Session, site_id: int, request) -> Optional[NewsSiteDTO]:
    current = get_news_site_by_id(db, site_id)
    if not current:
        return None

    updated_fields = {
        "name": request.name if request.name is not None else current.name,
        "code": request.code if request.code is not None else current.code,
        "url": request.url if request.url is not None else current.url,
        "is_active": request.is_active if request.is_active is not None else current.is_active,
        "is_default": request.is_default if request.is_default is not None else current.is_default,
    }

    query = text(
        """
        UPDATE news_sites
        SET name = :name,
            code = :code,
            url = :url,
            is_active = :is_active,
            is_default = :is_default,
            updated_at = NOW()
        WHERE id = :site_id
        RETURNING *
        """
    )
    row = db.execute(query, {"site_id": site_id, **updated_fields}).fetchone()
    db.commit()
    return NewsSiteDTO(
        id=row[0],
        name=row[1],
        code=row[2],
        url=row[3],
        is_active=row[4],
        is_default=row[5],
        created_at=row[6],
        updated_at=row[7],
    )


def delete_news_site(db: Session, site_id: int) -> bool:
    site = get_news_site_by_id(db, site_id)
    if not site:
        return False
    if site.is_default:
        raise ValueError("Cannot delete default site")
    query = text("DELETE FROM news_sites WHERE id = :site_id")
    db.execute(query, {"site_id": site_id})
    db.commit()
    return True


def delete_search_job(db: Session, job_id: str) -> bool:
    job = get_job(db, job_id)
    if not job:
        return False
    if job.status == "running":
        raise ValueError("Cannot delete a running job")
    query = text("DELETE FROM search_jobs WHERE id = :job_id")
    db.execute(query, {"job_id": job_id})
    db.commit()
    return True
