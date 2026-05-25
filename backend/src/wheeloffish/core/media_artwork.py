from urllib.parse import quote


def public_artwork_url(connection_id: str, artwork_path: str | None) -> str | None:
    """Map provider-relative artwork paths to same-origin API proxy URLs."""
    if not artwork_path:
        return None
    if artwork_path.startswith(("http://", "https://")):
        return artwork_path
    return f"/api/v1/connections/{connection_id}/artwork?path={quote(artwork_path, safe='/')}"
