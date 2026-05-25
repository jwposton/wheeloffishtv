"""Playlist rebuild orchestrator — stub until Phase 05 Plan 03."""
from __future__ import annotations

import structlog

logger = structlog.get_logger("wheeloffish.orchestrator")


async def run_nightly_rebuilds() -> None:
    """Trigger nightly playlist rebuild for all due playlists. Stub — implemented in 05-03."""
    logger.info("run_nightly_rebuilds_called_stub")
