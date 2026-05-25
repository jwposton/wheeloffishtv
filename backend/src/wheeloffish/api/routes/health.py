from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from wheeloffish import __version__
from wheeloffish.core.config import Settings, get_settings
from wheeloffish.db.models.app_metadata import AppMetadata
from wheeloffish.db.session import check_database, get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    checks: dict[str, str] = {"api": "ok"}
    schema_version: str | None = None

    try:
        check_database(db)
        checks["database"] = "ok"
        meta = db.query(AppMetadata).order_by(AppMetadata.id.asc()).first()
        if meta is not None:
            schema_version = meta.schema_version
    except Exception:
        checks["database"] = "error"
        payload = {
            "status": "degraded",
            "service": "wheeloffish",
            "version": __version__,
            "environment": settings.ENVIRONMENT,
            "checks": checks,
        }
        if schema_version is not None:
            payload["schema_version"] = schema_version
        return JSONResponse(status_code=503, content=payload)

    payload = {
        "status": "ok",
        "service": "wheeloffish",
        "version": __version__,
        "environment": settings.ENVIRONMENT,
        "checks": checks,
    }
    if schema_version is not None:
        payload["schema_version"] = schema_version
    return JSONResponse(status_code=200, content=payload)
