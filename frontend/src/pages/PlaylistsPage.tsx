import { Link } from "react-router-dom"
import { toast } from "sonner"
import { useEffect } from "react"

import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { PlaylistCard } from "@/components/playlists/PlaylistCard"
import { usePlaylists } from "@/api/playlists"

function PlaylistsSkeletons() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="flex flex-col gap-2">
          <Skeleton className="h-28 w-full rounded-xl" />
        </div>
      ))}
    </div>
  )
}

export function PlaylistsPage() {
  const { data: playlists, isLoading, isError, error } = usePlaylists()

  useEffect(() => {
    if (isError && error) {
      toast.error("Failed to load playlists")
    }
  }, [isError, error])

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-4">
      <div className="flex items-center justify-between gap-4">
        <h2 className="text-xl font-semibold">Playlists</h2>
        <Button size="sm" render={<Link to="/playlists/new" />}>
          New playlist
        </Button>
      </div>

      {isLoading ? (
        <PlaylistsSkeletons />
      ) : playlists && playlists.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
          {playlists.map((item) => (
            <PlaylistCard key={item.id} item={item} />
          ))}
        </div>
      ) : (
        <div className="rounded-md border border-dashed p-8 text-center">
          <p className="font-medium">No playlists yet</p>
          <p className="text-muted-foreground mt-1 text-sm">
            Create a playlist to mix episodes from your favorite shows on a
            daily or weekly schedule.
          </p>
          <Button size="sm" className="mt-4" render={<Link to="/playlists/new" />}>
            New playlist
          </Button>
        </div>
      )}
    </div>
  )
}
