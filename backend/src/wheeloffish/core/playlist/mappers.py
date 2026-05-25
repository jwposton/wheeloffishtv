"""ORM ↔ domain Playlist conversion."""

from wheeloffish.db.models.playlist import Playlist as PlaylistOrm
from wheeloffish.domain.playlist import (
    CompletionEvent,
    CompletionPolicy,
    Playlist,
    PlaylistSeriesRow,
    RowMode,
    SlotAllocation,
)


def orm_to_playlist(orm: PlaylistOrm) -> Playlist:
    """Convert a Playlist ORM row (with rows loaded) to the domain Playlist model."""
    sorted_rows = sorted(orm.rows, key=lambda r: r.sort_order)
    domain_rows = [
        PlaylistSeriesRow(
            series_id=row.series_id,
            mode=RowMode(row.mode),
            completion_policy=CompletionPolicy(row.completion_policy),
            completion_event=CompletionEvent(row.completion_event),
        )
        for row in sorted_rows
    ]
    return Playlist(
        id=orm.id,
        name=orm.name,
        episode_count=orm.episode_count,
        slot_allocation=SlotAllocation(orm.slot_allocation),
        default_completion_policy=CompletionPolicy(orm.default_completion_policy),
        rows=domain_rows,
    )
