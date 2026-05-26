import { useMemo } from "react"
import { toast } from "sonner"

import type { PlaylistSeriesRowResponse } from "@/api/playlists"
import {
  usePatchPlaylistRow,
  useRemovePlaylistRow,
  type CompletionPolicy,
  type RowMode,
} from "@/api/playlists"
import { PlaylistMemberTile } from "@/components/playlists/PlaylistMemberTile"
import type { SeriesRow } from "@/components/playlists/RowSettingsSheet"

function toSeriesRow(row: PlaylistSeriesRowResponse): SeriesRow {
  return {
    series_id: row.series_id,
    series_title: row.series_title ?? row.series_id,
    thumb_url: row.thumb_url,
    mode: row.mode,
    completion_policy: row.completion_policy,
  }
}

interface PlaylistMembersPanelProps {
  playlistId: string
  rows: PlaylistSeriesRowResponse[]
}

export function PlaylistMembersPanel({ playlistId, rows }: PlaylistMembersPanelProps) {
  const removeMutation = useRemovePlaylistRow()
  const patchMutation = usePatchPlaylistRow()

  const displayRows = useMemo(() => rows.map(toSeriesRow), [rows])

  async function handleRemove(seriesId: string, seriesTitle: string) {
    try {
      await removeMutation.mutateAsync({ playlistId, seriesId })
      toast.success(`Removed ${seriesTitle}`)
    } catch {
      toast.error("Failed to remove show")
    }
  }

  async function handlePatch(updatedRow: SeriesRow) {
    try {
      await patchMutation.mutateAsync({
        playlistId,
        seriesId: updatedRow.series_id,
        payload: {
          mode: updatedRow.mode,
          completion_policy: updatedRow.completion_policy,
        },
      })
    } catch {
      toast.error("Failed to save row settings")
    }
  }

  function handleModeChange(row: SeriesRow, mode: RowMode) {
    if (mode === row.mode) {
      return
    }
    void handlePatch({ ...row, mode })
  }

  function handlePolicyChange(row: SeriesRow, policy: CompletionPolicy) {
    if (policy === row.completion_policy) {
      return
    }
    void handlePatch({ ...row, completion_policy: policy })
  }

  if (displayRows.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No shows in this playlist yet. Use Edit to add series.
      </p>
    )
  }

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-2">
      {displayRows.map((row) => (
        <PlaylistMemberTile
          key={row.series_id}
          row={row}
          onModeChange={(mode) => handleModeChange(row, mode)}
          onPolicyChange={(policy) => handlePolicyChange(row, policy)}
          onRemove={() => void handleRemove(row.series_id, row.series_title)}
        />
      ))}
    </div>
  )
}
