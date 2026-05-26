import { Link } from "react-router-dom"
import { toast } from "sonner"
import { useEffect } from "react"

import { WheelIcon } from "@/components/icons/WheelIcon"
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
        <div>
          <h2 className="text-2xl">Playlists</h2>
          <p className="text-sm text-muted-foreground">Your daily and weekly mixes</p>
        </div>
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
        <div className="wof-panel border-dashed p-8 text-center">
          <div className="mx-auto mb-4 flex justify-center">
            <div className="rounded-full bg-secondary/80 p-3 ring-1 ring-border/80">
              <WheelIcon className="size-10" />
            </div>
          </div>
          <p className="font-heading text-lg">No playlists yet</p>
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
