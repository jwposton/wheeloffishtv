MEDIA_SERVER_NS = "media_server"


def media_server_token_key(connection_id: str) -> str:
    return f"media_server/{connection_id}/token"


def media_user_token_key(connection_id: str, app_user_id: str) -> str:
    return f"media_server/{connection_id}/users/{app_user_id}/token"


def connection_secrets_prefix(connection_id: str) -> str:
    return f"media_server/{connection_id}/"
