"""Phase 2 — Plex API client stub."""


class PlexClient:
    def connect(self) -> None:
        raise NotImplementedError("Plex connectivity is implemented in Phase 2")

    def list_libraries(self) -> list[dict]:
        raise NotImplementedError("Plex library listing is implemented in Phase 2")

    def list_shows(self, library_id: str) -> list[dict]:
        raise NotImplementedError("Plex show listing is implemented in Phase 2")
