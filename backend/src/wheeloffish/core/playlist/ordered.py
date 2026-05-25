"""Ordered serial picker for playlist builder (PLT-05).

Semantics:
- D-07: one ordered slot emits a multipart-forward block via ``expand_multipart_forward``
- D-10: SCH-02 adjacency — multipart parts stay contiguous within a single slot
- D-17: serial from resume/on-deck cursor; ``restart=True`` forces index 0
- Phase 2 D-10: hybrid resume via ``ResumeService`` only (no forked on-deck logic)
- Phase 2 D-12: walk ``order_episodes`` list directly (specials after season finale)
"""

from dataclasses import dataclass

from wheeloffish.core.playlist.multipart import expand_multipart_forward
from wheeloffish.core.resume import ResumeService, order_episodes
from wheeloffish.domain.dto import Episode

__all__ = ["OrderedCursor", "start_index_for_row", "next_block", "make_cursor"]


@dataclass(frozen=True)
class OrderedCursor:
    series_id: str
    index: int


def start_index_for_row(
    series_id: str,
    episodes: list[Episode],
    on_deck: Episode | None,
    *,
    restart: bool = False,
) -> int:
    if restart:
        return 0

    cursor = ResumeService().compute(series_id, episodes, on_deck)
    ordered = order_episodes(episodes)

    if cursor.series_complete:
        return len(ordered)

    assert cursor.episode_id is not None
    return next(i for i, ep in enumerate(ordered) if ep.id == cursor.episode_id)


def next_block(
    ordered: list[Episode],
    episodes_by_id: dict[str, Episode],
    index: int,
) -> tuple[list[Episode], int]:
    if index >= len(ordered):
        return ([], index)

    anchor = ordered[index]
    block = expand_multipart_forward(anchor, episodes_by_id)
    assert block, "ordered.next_block must emit a non-empty block when index < len(ordered)"

    pos_of_id = {ep.id: i for i, ep in enumerate(ordered)}
    positions = [pos_of_id[ep.id] for ep in block if ep.id in pos_of_id]
    if positions:
        new_index = max(positions) + 1
    else:
        new_index = index + 1

    return (block, new_index)


def make_cursor(
    series_id: str,
    episodes: list[Episode],
    on_deck: Episode | None,
    *,
    restart: bool = False,
) -> OrderedCursor:
    return OrderedCursor(
        series_id=series_id,
        index=start_index_for_row(series_id, episodes, on_deck, restart=restart),
    )
