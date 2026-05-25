from pathlib import Path

from fastapi import HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException


class SPAStaticFiles(StaticFiles):
    """Serve a Vite build with index.html fallback for client-side routes."""

    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except (HTTPException, StarletteHTTPException) as exc:
            if exc.status_code == 404:
                return await super().get_response("index.html", scope)
            raise exc


def spa_dist_exists(directory: str | Path) -> bool:
    dist = Path(directory)
    return dist.is_dir() and (dist / "index.html").is_file()
