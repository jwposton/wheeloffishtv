MEDIA_SERVER_NS = "media_server"


def media_server_token_key(connection_id: str) -> str:
    return f"media_server/{connection_id}/token"
