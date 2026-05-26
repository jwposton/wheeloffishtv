"""Push rebuild snapshots to native Plex/Jellyfin playlists (Phase 07, EXP-01)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

import structlog
from sqlalchemy.orm import Session

from wheeloffish.db.models.playlist import Playlist as PlaylistOrm
from wheeloffish.db.models.rebuild_run import RebuildRun
from wheeloffish.integrations.base import MediaProvider
from wheeloffish.integrations.errors import ProviderNotFound
from wheeloffish.integrations.jellyfin import playlists as jellyfin_playlists
from wheeloffish.integrations.jellyfin.client import JellyfinProvider
from wheeloffish.integrations.playlist_names import provider_playlist_display_name
from wheeloffish.integrations.plex import playlists as plex_playlists
from wheeloffish.integrations.plex.client import PlexProvider

logger = structlog.get_logger("wheeloffish.provider_writeback")

WritebackStatus = Literal["succeeded", "partial", "failed", "skipped"]

ORPHAN_RECREATED_WARNING = {
    "episode_id": None,
    "reason": "The linked Plex playlist was missing; a new one was created.",
}


@dataclass
class WritebackResult:
    status: WritebackStatus
    error: str | None = None
    warnings: list[dict] = field(default_factory=list)


def _episode_warnings(warnings: list[dict]) -> list[dict]:
    return [w for w in warnings if w.get("episode_id")]


def _finalize_writeback_result(warnings: list[dict]) -> WritebackResult:
    if _episode_warnings(warnings):
        return WritebackResult(status="partial", warnings=warnings)
    if warnings:
        return WritebackResult(status="succeeded", warnings=warnings)
    return WritebackResult(status="succeeded")


def apply_writeback_result(run: RebuildRun, result: WritebackResult) -> None:
    run.writeback_status = result.status
    run.writeback_error = result.error
    run.writeback_warnings = result.warnings or None
    run.writeback_at = datetime.now(UTC)


def clear_provider_link(playlist: PlaylistOrm) -> None:
    """Drop stale provider_playlist_id when the remote playlist no longer exists."""
    playlist.provider_playlist_id = None
    playlist.provider_kind = None


def _is_not_found(exc: Exception) -> bool:
    if isinstance(exc, ProviderNotFound):
        return True
    return "404" in str(exc)


async def _resolve_plex_keys(
    provider: PlexProvider,
    snapshot: list[dict],
) -> tuple[list[str], list[dict]]:
    keys: list[str] = []
    warnings: list[dict] = []
    for entry in snapshot:
        episode_id = entry.get("episode_id")
        if not episode_id:
            warnings.append({"episode_id": None, "reason": "missing_episode_id"})
            continue
        try:
            keys.append(await plex_playlists.resolve_episode_rating_key(provider, episode_id))
        except Exception as exc:
            warnings.append({"episode_id": episode_id, "reason": str(exc)})
    return keys, warnings


def _resolve_jellyfin_ids(snapshot: list[dict]) -> tuple[list[str], list[dict]]:
    ids: list[str] = []
    warnings: list[dict] = []
    for entry in snapshot:
        episode_id = entry.get("episode_id")
        if not episode_id:
            warnings.append({"episode_id": None, "reason": "missing_episode_id"})
            continue
        try:
            ids.append(jellyfin_playlists.episode_native_id(episode_id))
        except Exception as exc:
            warnings.append({"episode_id": episode_id, "reason": str(exc)})
    return ids, warnings


async def _create_plex_playlist(
    db: Session,
    playlist: PlaylistOrm,
    provider: PlexProvider,
    title: str,
    keys: list[str],
) -> str:
    playlist_key = await plex_playlists.create_video_playlist(provider, title, keys)
    playlist.provider_playlist_id = playlist_key
    playlist.provider_kind = "plex"
    db.flush()
    return playlist_key


async def _sync_plex_playlist(
    db: Session,
    playlist: PlaylistOrm,
    provider: PlexProvider,
    title: str,
    keys: list[str],
) -> tuple[str, bool]:
    """Create or replace Plex playlist. Returns (playlist_key, recreated_after_orphan)."""
    if playlist.provider_playlist_id is None:
        playlist_key = await _create_plex_playlist(db, playlist, provider, title, keys)
        return playlist_key, False

    playlist_key = playlist.provider_playlist_id
    try:
        await plex_playlists.replace_playlist_items(provider, playlist_key, keys)
        return playlist_key, False
    except Exception as exc:
        if not _is_not_found(exc):
            raise
        if await plex_playlists.playlist_exists(provider, playlist_key):
            raise
        logger.info(
            "plex_playlist_orphaned",
            playlist_id=playlist.id,
            provider_playlist_id=playlist_key,
        )
        clear_provider_link(playlist)
        db.flush()
        playlist_key = await _create_plex_playlist(db, playlist, provider, title, keys)
        return playlist_key, True


async def _create_jellyfin_playlist(
    db: Session,
    playlist: PlaylistOrm,
    provider: JellyfinProvider,
    title: str,
    media_ids: list[str],
) -> str:
    playlist_id = await jellyfin_playlists.create_playlist(provider, title, media_ids)
    playlist.provider_playlist_id = playlist_id
    playlist.provider_kind = "jellyfin"
    db.flush()
    return playlist_id


async def _sync_jellyfin_playlist(
    db: Session,
    playlist: PlaylistOrm,
    provider: JellyfinProvider,
    title: str,
    media_ids: list[str],
) -> bool:
    """Create or replace Jellyfin playlist. Returns recreated_after_orphan."""
    if playlist.provider_playlist_id is None:
        await _create_jellyfin_playlist(db, playlist, provider, title, media_ids)
        return False

    try:
        await jellyfin_playlists.replace_playlist_items(
            provider,
            playlist.provider_playlist_id,
            media_ids,
        )
        return False
    except Exception as exc:
        if not _is_not_found(exc):
            raise
        logger.info(
            "jellyfin_playlist_orphaned",
            playlist_id=playlist.id,
            provider_playlist_id=playlist.provider_playlist_id,
        )
        clear_provider_link(playlist)
        db.flush()
        await _create_jellyfin_playlist(db, playlist, provider, title, media_ids)
        return True


async def push_snapshot(
    db: Session,
    playlist: PlaylistOrm,
    run: RebuildRun,
    snapshot: list[dict],
    provider: MediaProvider,
) -> WritebackResult:
    """Create or replace provider playlist from rebuild snapshot."""
    if isinstance(provider, PlexProvider):
        return await _push_plex_snapshot(db, playlist, snapshot, provider)
    if isinstance(provider, JellyfinProvider):
        return await _push_jellyfin_snapshot(db, playlist, snapshot, provider)
    return WritebackResult(
        status="skipped",
        error=f"Writeback not supported for provider type {type(provider).__name__}",
    )


async def _push_plex_snapshot(
    db: Session,
    playlist: PlaylistOrm,
    snapshot: list[dict],
    provider: PlexProvider,
) -> WritebackResult:
    keys, warnings = await _resolve_plex_keys(provider, snapshot)
    if not keys:
        return WritebackResult(
            status="failed",
            error="No episodes could be mapped to Plex rating keys",
            warnings=warnings,
        )

    title = provider_playlist_display_name(playlist.name)
    recreated = False
    try:
        playlist_key, recreated = await _sync_plex_playlist(
            db, playlist, provider, title, keys
        )
        synced_keys = await plex_playlists.list_playlist_item_keys(provider, playlist_key)
        if not synced_keys:
            return WritebackResult(
                status="failed",
                error="Plex playlist has no items after writeback",
                warnings=warnings,
            )
    except Exception as exc:
        logger.warning("plex_writeback_failed", playlist_id=playlist.id, error=str(exc))
        return WritebackResult(status="failed", error=str(exc), warnings=warnings)

    if recreated:
        warnings = [*warnings, ORPHAN_RECREATED_WARNING.copy()]
    return _finalize_writeback_result(warnings)


async def _push_jellyfin_snapshot(
    db: Session,
    playlist: PlaylistOrm,
    snapshot: list[dict],
    provider: JellyfinProvider,
) -> WritebackResult:
    media_ids, warnings = _resolve_jellyfin_ids(snapshot)
    if not media_ids:
        return WritebackResult(
            status="failed",
            error="No episodes could be mapped to Jellyfin item ids",
            warnings=warnings,
        )

    title = provider_playlist_display_name(playlist.name)
    try:
        recreated = await _sync_jellyfin_playlist(
            db, playlist, provider, title, media_ids
        )
    except Exception as exc:
        logger.warning("jellyfin_writeback_failed", playlist_id=playlist.id, error=str(exc))
        return WritebackResult(status="failed", error=str(exc), warnings=warnings)

    if recreated:
        warnings = [*warnings, ORPHAN_RECREATED_WARNING.copy()]
    return _finalize_writeback_result(warnings)


async def rename_linked(
    playlist: PlaylistOrm,
    provider: MediaProvider,
    db: Session,
) -> None:
    if not playlist.provider_playlist_id:
        return
    title = provider_playlist_display_name(playlist.name)
    try:
        if isinstance(provider, PlexProvider):
            await plex_playlists.rename_playlist(
                provider,
                playlist.provider_playlist_id,
                title,
            )
        elif isinstance(provider, JellyfinProvider):
            await jellyfin_playlists.rename_playlist(
                provider,
                playlist.provider_playlist_id,
                title,
            )
    except Exception as exc:
        if _is_not_found(exc):
            logger.info(
                "provider_playlist_rename_orphaned",
                playlist_id=playlist.id,
                provider_playlist_id=playlist.provider_playlist_id,
            )
            clear_provider_link(playlist)
            db.flush()
            return
        logger.warning(
            "provider_playlist_rename_failed",
            playlist_id=playlist.id,
            error=str(exc),
        )


async def delete_linked(
    playlist: PlaylistOrm,
    provider: MediaProvider,
) -> None:
    if not playlist.provider_playlist_id:
        return
    try:
        if isinstance(provider, PlexProvider):
            await plex_playlists.delete_playlist(provider, playlist.provider_playlist_id)
        elif isinstance(provider, JellyfinProvider):
            await jellyfin_playlists.delete_playlist(provider, playlist.provider_playlist_id)
    except Exception as exc:
        if _is_not_found(exc):
            logger.info(
                "provider_playlist_delete_already_gone",
                playlist_id=playlist.id,
                provider_playlist_id=playlist.provider_playlist_id,
            )
            return
        logger.warning(
            "provider_playlist_delete_failed",
            playlist_id=playlist.id,
            error=str(exc),
        )
