from wheeloffish.core.namespaces import MEDIA_SERVER_NS, media_server_token_key
from wheeloffish.core.secrets import SecretsVault
from wheeloffish.db.models.secret import Secret


def test_set_get_delete_round_trip(db_session, settings) -> None:
    vault = SecretsVault(db_session, settings)
    vault.set_secret("test-ns", "test-key", "secret-value")
    assert vault.get_secret("test-ns", "test-key") == "secret-value"
    assert vault.delete_secret("test-ns", "test-key") is True
    assert vault.get_secret("test-ns", "test-key") is None


def test_ciphertext_not_plaintext(db_session, settings) -> None:
    vault = SecretsVault(db_session, settings)
    plaintext = "plex-token-xyz"
    vault.set_secret(MEDIA_SERVER_NS, "conn/token", plaintext)

    row = db_session.query(Secret).filter_by(namespace=MEDIA_SERVER_NS, key="conn/token").one()
    assert plaintext not in row.ciphertext


def test_store_media_token_helper(db_session, settings) -> None:
    vault = SecretsVault(db_session, settings)
    vault.store_media_token("test-conn-1", "plex-token-xyz")
    assert vault.get_media_token("test-conn-1") == "plex-token-xyz"
    assert media_server_token_key("test-conn-1") == "media_server/test-conn-1/token"


def test_wrong_key_returns_none(db_session, settings) -> None:
    vault = SecretsVault(db_session, settings)
    assert vault.get_secret("missing", "key") is None
