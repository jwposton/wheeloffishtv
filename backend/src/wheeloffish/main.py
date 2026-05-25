import time
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request

from wheeloffish.api.routes import connections, health, meta, oauth_jellyfin, oauth_plex
from wheeloffish.core.config import get_settings
from wheeloffish.core.logging import configure_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings)
    get_logger("wheeloffish").info("application_startup", environment=settings.ENVIRONMENT)
    yield


app = FastAPI(title="Wheel of Fish TV", lifespan=lifespan)
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
    return response


app.include_router(health.router)
app.include_router(meta.router, prefix="/api/v1")
app.include_router(connections.router, prefix="/api/v1")
app.include_router(oauth_plex.router, prefix="/api/v1")
app.include_router(oauth_jellyfin.router, prefix="/api/v1")


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "wheeloffish", "status": "ok"}
