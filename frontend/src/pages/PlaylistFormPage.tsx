import { useParams } from "react-router-dom"

import { PlaylistForm } from "@/components/playlists/PlaylistForm"
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
  const isNew = id === "new" || !id

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <h2 className="text-xl font-semibold">
        {isNew ? "New playlist" : "Edit playlist"}
      </h2>

      {isNew ? (
        <PlaylistForm mode="create" />
      ) : (
        <EditPlaylistForm id={id} />
      )}
    </div>
  )
}
