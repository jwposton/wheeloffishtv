MEDIA_SERVER_NS = "media_server"


def media_server_token_key(connection_id: str) -> str:
    return f"media_server/{connection_id}/token"


def media_user_token_key(connection_id: str, app_user_id: str) -> str:
    return f"media_server/{connection_id}/users/{app_user_id}/token"


def media_user_client_identifier_key(connection_id: str, app_user_id: str) -> str:
    return f"media_server/{connection_id}/users/{app_user_id}/plex_client_identifier"


def plex_user_credentials_key(connection_id: str, app_user_id: str) -> str:
    return f"media_server/{connection_id}/users/{app_user_id}/plex_credentials"


def connection_secrets_prefix(connection_id: str) -> str:
    return f"media_server/{connection_id}/"
