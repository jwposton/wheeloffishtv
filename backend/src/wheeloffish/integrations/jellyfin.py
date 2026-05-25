"""Phase 2 — Jellyfin API client stub."""


class JellyfinClient:
    def connect(self) -> None:
        raise NotImplementedError("Jellyfin connectivity is implemented in Phase 2")

    def list_libraries(self) -> list[dict]:
        raise NotImplementedError("Jellyfin library listing is implemented in Phase 2")

    def list_shows(self, library_id: str) -> list[dict]:
        raise NotImplementedError("Jellyfin show listing is implemented in Phase 2")
