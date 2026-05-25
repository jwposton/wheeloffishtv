from wheeloffish.core.secrets import SecretsVault


def test_store_and_get_plex_user_credentials(vault: SecretsVault) -> None:
    vault.store_plex_user_credentials(
        "conn-1",
        "user-1",
        "token-abc",
        "client-xyz",
    )

    creds = vault.get_plex_user_credentials("conn-1", "user-1")
    assert creds is not None
    assert creds.token == "token-abc"
    assert creds.client_identifier == "client-xyz"


def test_get_plex_user_credentials_legacy_keys(vault: SecretsVault) -> None:
    vault.store_media_user_token("conn-1", "user-1", "legacy-token")
    vault.store_media_user_client_identifier("conn-1", "user-1", "legacy-client")

    creds = vault.get_plex_user_credentials("conn-1", "user-1")
    assert creds is not None
    assert creds.token == "legacy-token"
    assert creds.client_identifier == "legacy-client"


def test_clear_plex_user_credentials(vault: SecretsVault) -> None:
    vault.store_plex_user_credentials("conn-1", "user-1", "token", "client")
    vault.clear_plex_user_credentials("conn-1", "user-1")

    assert vault.get_plex_user_credentials("conn-1", "user-1") is None
    assert vault.get_media_user_token("conn-1", "user-1") is None
    assert vault.get_media_user_client_identifier("conn-1", "user-1") is None
