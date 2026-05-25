import { useMemo } from "react"
import { useParams, useSearchParams } from "react-router-dom"

import { PlaylistForm } from "@/components/playlists/PlaylistForm"
import type { SeriesRow } from "@/components/playlists/TwoPanePicker"
import { Skeleton } from "@/components/ui/skeleton"
import { usePlaylist } from "@/api/playlists"

function EditPlaylistForm({ id }: { id: string }) {
  const { data: playlist, isLoading, isError } = usePlaylist(id)

  if (isLoading) {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-40 w-full rounded-xl" />
        <Skeleton className="h-28 w-full rounded-xl" />
        <Skeleton className="h-32 w-full rounded-xl" />
      </div>
    )
  }

  if (isError || !playlist) {
    return (
      <p className="text-sm text-destructive">Failed to load playlist. Please try again.</p>
    )
  }

  return <PlaylistForm mode="edit" playlist={playlist} />
}

export function PlaylistFormPage() {
  const { id } = useParams<{ id: string }>()
  const [searchParams] = useSearchParams()
  const isNew = id === "new" || !id

  const seriesId = searchParams.get("seriesId")

  const initialRows = useMemo<SeriesRow[] | undefined>(() => {
    if (!isNew || !seriesId) {
      return undefined
    }
    return [
      {
        series_id: seriesId,
        series_title: seriesId,
        thumb_url: null,
        mode: "ordered",
        completion_policy: "remove",
      },
    ]
  }, [isNew, seriesId])

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-4">
      <h2 className="text-xl font-semibold">
        {isNew ? "New playlist" : "Edit playlist"}
      </h2>

      {isNew ? (
        <PlaylistForm mode="create" initialRows={initialRows} />
      ) : (
        <EditPlaylistForm id={id} />
      )}
    </div>
  )
}
