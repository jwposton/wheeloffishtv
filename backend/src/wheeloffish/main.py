import time
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import structlog
from fastapi import FastAPI, Request
from starlette.middleware.sessions import SessionMiddleware

from wheeloffish.api.routes import (
    auth,
    catalog,
    connections,
    health,
    meta,
    oauth_jellyfin,
    oauth_plex,
)
from wheeloffish.api.spa import SPAStaticFiles, spa_dist_exists
from wheeloffish.core.boot import sync_connection_from_env
from wheeloffish.core.config import Settings, get_settings
from wheeloffish.core.logging import configure_logging, get_logger
from wheeloffish.core.orchestrator import run_nightly_rebuilds
from wheeloffish.core.scheduler import create_scheduler
from wheeloffish.db.session import get_session_factory


def recover_interrupted_rebuilds(db) -> None:
    """Mark any rebuild_runs stuck in 'running' status as failed on startup."""
    from wheeloffish.db.models.rebuild_run import RebuildRun

    interrupted = db.query(RebuildRun).filter(RebuildRun.status == "running").all()
    for run in interrupted:
        run.status = "failed"
        run.error_message = "Interrupted by restart"
        run.finished_at = datetime.now(UTC)
    if interrupted:
        db.commit()
        structlog.get_logger("wheeloffish").warning(
            "interrupted_rebuilds_recovered", count=len(interrupted)
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings)
    session_factory = get_session_factory(settings)
    db = session_factory()
    try:
        sync_connection_from_env(db, settings)
        recover_interrupted_rebuilds(db)
    finally:
        db.close()

    scheduler = create_scheduler(settings, job_callable=run_nightly_rebuilds)
    scheduler.start()
    get_logger("wheeloffish").info(
        "application_startup",
        environment=settings.ENVIRONMENT,
        scheduler_cron=settings.WOF_REBUILD_CRON,
        scheduler_tz=settings.WOF_INSTALL_TIMEZONE,
    )
    try:
        yield
    finally:
        scheduler.shutdown(wait=True)


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    app = FastAPI(title="Wheel of Fish TV", lifespan=lifespan)
    app.add_middleware(
        SessionMiddleware,
        secret_key=resolved.WOF_SECRET_KEY,
        max_age=resolved.session_max_age_seconds,
        same_site="lax",
        https_only=(resolved.ENVIRONMENT == "production"),
    )
    logger = get_logger("wheeloffish.http")

    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        request_id = str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            request_id=request_id,
        )
        response.headers["X-Request-ID"] = request_id
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    app.include_router(health.router)
    app.include_router(meta.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(connections.router, prefix="/api/v1")
    app.include_router(catalog.router, prefix="/api/v1")
    app.include_router(catalog.admin_router, prefix="/api/v1")
    app.include_router(catalog.session_router, prefix="/api/v1")
    app.include_router(oauth_plex.router, prefix="/api/v1")
    app.include_router(oauth_jellyfin.router, prefix="/api/v1")

    if spa_dist_exists(resolved.SPA_DIST_DIR):
        app.mount(
            "/",
            SPAStaticFiles(directory=resolved.SPA_DIST_DIR, html=True),
            name="spa",
        )

    return app


app = create_app()
