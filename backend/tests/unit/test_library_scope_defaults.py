from wheeloffish.core.catalog_sync import _resolve_library_in_scope
from wheeloffish.core.config import Settings
from wheeloffish.db.models.cached_library import CachedLibrary
from wheeloffish.db.models.connection import Connection


def test_resolve_library_in_scope_defaults_all_when_user_unscoped() -> None:
    connection = Connection(
        id="conn-1",
        provider_type="plex",
        base_url="http://plex",
        display_name="Plex",
    )
    settings = Settings(WOF_SECRET_KEY="a" * 64)

    assert (
        _resolve_library_in_scope(
            "lib-1",
            connection,
            settings,
            existing_row=None,
            user_has_scoped_libraries=False,
        )
        is True
    )


def test_resolve_library_in_scope_preserves_existing_when_user_scoped() -> None:
    connection = Connection(
        id="conn-1",
        provider_type="plex",
        base_url="http://plex",
        display_name="Plex",
    )
    settings = Settings(WOF_SECRET_KEY="a" * 64)
    existing = CachedLibrary(
        id="cached-1",
        app_user_id="user-1",
        connection_id="conn-1",
        native_id="lib-1",
        title="TV",
        in_scope=False,
    )

    assert (
        _resolve_library_in_scope(
            "lib-1",
            connection,
            settings,
            existing_row=existing,
            user_has_scoped_libraries=True,
        )
        is False
    )
