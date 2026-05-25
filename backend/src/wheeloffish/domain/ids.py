from urllib.parse import quote, unquote

_COMPOSITE_PARTS = 3


def format_composite_id(connection_id: str, provider: str, native_id: str) -> str:
    """Format a stable composite ID: {connection_id}:{provider}:{native_id}."""
    encoded_native_id = quote(native_id, safe="")
    return f"{connection_id}:{provider}:{encoded_native_id}"


def parse_composite_id(value: str) -> tuple[str, str, str]:
    """Parse a composite ID into (connection_id, provider, native_id)."""
    parts = value.split(":", _COMPOSITE_PARTS - 1)
    if len(parts) != _COMPOSITE_PARTS:
        raise ValueError(f"Invalid composite ID format: {value!r}")
    connection_id, provider, encoded_native_id = parts
    if not connection_id or not provider or not encoded_native_id:
        raise ValueError(f"Invalid composite ID format: {value!r}")
    return connection_id, provider, unquote(encoded_native_id)
