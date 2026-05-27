"""Playlist builder orchestrator (D-01, D-02, D-23, D-24).

Pure playlist mathematics — no DB, HTTP, or scheduler coupling.
Phase 5 calls ``PlaylistBuilder.build()`` with live episode snapshots.
"""

from __future__ import annotations

import hashlib
import random

import structlog

from wheeloffish.core.playlist.completion import apply_policy, evaluate_completion
from wheeloffish.core.playlist.disordered import compute_eligible_pool, pick_disordered_block
from wheeloffish.core.playlist.ordered import OrderedCursor, make_cursor, next_block
from wheeloffish.core.resume import order_episodes
from wheeloffish.domain.playlist import (
    BuiltEpisode,
    CompletionPolicy,
    Playlist,
    PlaylistBuildResult,
    RowMode,
    SeriesRebuildInput,
    SlotAllocation,
)

logger = structlog.get_logger("wheeloffish.playlist_builder")

__all__ = ["make_build_rng", "allocate_slots", "PlaylistBuilder"]


def make_build_rng(playlist_id: str, rebuild_seed: str) -> random.Random:
    seed = int.from_bytes(
        hashlib.sha256(f"{playlist_id}:{rebuild_seed}".encode()).digest()[:8],
        "big",
    )
    return random.Random(seed)


def allocate_slots(
    active_series_ids: list[str],
    n: int,
    mode: SlotAllocation,
    rng: random.Random,
) -> list[str]:
    if not active_series_ids or n <= 0:
        return []

    if mode == SlotAllocation.ROUND_ROBIN:
        ordered = sorted(active_series_ids)
        return [ordered[i % len(ordered)] for i in range(n)]

    if mode == SlotAllocation.BALANCED:
        counts: dict[str, int] = {sid: 0 for sid in active_series_ids}
        assignments: list[str] = []
        for _ in range(n):
            min_count = min(counts.values())
            candidates = sorted(
                sid for sid, count in counts.items() if count == min_count
            )
            pick = rng.choice(candidates)
            assignments.append(pick)
            counts[pick] += 1
        return assignments

    # WILD (default)
    return [rng.choice(active_series_ids) for _ in range(n)]


class PlaylistBuilder:
    @staticmethod
    def build(
        playlist: Playlist,
        inputs: list[SeriesRebuildInput],
        rebuild_seed: str,
    ) -> PlaylistBuildResult:
        inputs_by_series = {inp.series_id: inp for inp in inputs}

        row_outcomes = []
        for row in playlist.rows:
            inp = inputs_by_series.get(row.series_id)
            episodes = inp.episodes if inp is not None else []
            on_deck = inp.on_deck if inp is not None else None
            completion_event = evaluate_completion(row, episodes, on_deck)
            row_outcomes.append(apply_policy(row, completion_event))

        active_series_ids = [
            outcome.series_id
            for outcome in row_outcomes
            if not outcome.excluded
        ]

        if not active_series_ids:
            return PlaylistBuildResult(
                episodes=[],
                row_outcomes=row_outcomes,
                day_key=rebuild_seed,
                slots_requested=playlist.episode_count,
                slots_filled=0,
            )

        rng = make_build_rng(playlist.id, rebuild_seed)
        slot_assignments = allocate_slots(
            active_series_ids,
            playlist.episode_count,
            playlist.slot_allocation,
            rng,
        )

        outcome_by_series = {o.series_id: o for o in row_outcomes}

        ordered_cursors: dict[str, OrderedCursor] = {}
        emitted_ids: dict[str, set[str]] = {}

        for outcome in row_outcomes:
            if outcome.excluded:
                continue
            inp = inputs_by_series.get(outcome.series_id)
            episodes = inp.episodes if inp is not None else []
            on_deck = inp.on_deck if inp is not None else None
            restart = outcome.policy_applied == CompletionPolicy.RESTART
            if outcome.effective_mode == RowMode.ORDERED:
                ordered_cursors[outcome.series_id] = make_cursor(
                    outcome.series_id,
                    episodes,
                    on_deck,
                    restart=restart,
                )
            else:
                emitted_ids[outcome.series_id] = set()

        built: list[BuiltEpisode] = []
        slots_filled = 0

        for slot_index, series_id in enumerate(slot_assignments):
            outcome = outcome_by_series[series_id]
            inp = inputs_by_series.get(series_id)
            episodes = inp.episodes if inp is not None else []
            by_id = {ep.id: ep for ep in episodes}

            if outcome.effective_mode == RowMode.ORDERED:
                ordered = order_episodes(episodes)
                cursor = ordered_cursors[series_id]
                cursor_before = cursor.index
                ordered_len = len(ordered)
                block, new_index = next_block(ordered, by_id, cursor.index)
                ordered_cursors[series_id] = OrderedCursor(series_id, new_index)
                if not block:
                    logger.info(
                        "playlist_slot_empty",
                        playlist_id=playlist.id,
                        slot_index=slot_index,
                        series_id=series_id,
                        row_mode=RowMode.ORDERED.value,
                        reason="ordered_exhausted",
                        ordered_episode_count=ordered_len,
                        cursor_index=cursor_before,
                    )
                    continue
            else:
                pool = compute_eligible_pool(episodes)
                emitted = emitted_ids.setdefault(series_id, set())
                block = pick_disordered_block(pool, by_id, emitted, rng)
                if block:
                    emitted.update(ep.id for ep in block)
                if not block:
                    logger.info(
                        "playlist_slot_empty",
                        playlist_id=playlist.id,
                        slot_index=slot_index,
                        series_id=series_id,
                        row_mode=RowMode.DISORDERED.value,
                        reason="disordered_fully_emitted",
                        eligible_pool_size=len(pool),
                        emitted_episode_count=len(emitted),
                        series_episode_count=len(by_id),
                    )
                    continue

            for ep in block:
                built.append(
                    BuiltEpisode(
                        episode=ep,
                        series_id=series_id,
                        row_mode=outcome.effective_mode,
                        slot_index=slot_index,
                    )
                )
            slots_filled += 1

        return PlaylistBuildResult(
            episodes=built,
            row_outcomes=row_outcomes,
            day_key=rebuild_seed,
            slots_requested=playlist.episode_count,
            slots_filled=slots_filled,
        )
