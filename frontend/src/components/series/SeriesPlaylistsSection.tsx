import { Link } from "react-router-dom"

import { usePlaylistsContainingSeries } from "@/api/playlists"
import { Skeleton } from "@/components/ui/skeleton"

interface SeriesPlaylistsSectionProps {
  seriesId: string
}

export function SeriesPlaylistsSection({ seriesId }: SeriesPlaylistsSectionProps) {
  const { data: playlists, isLoading, isError } = usePlaylistsContainingSeries(seriesId)

  if (isLoading) {
    return (
      <section className="flex flex-col gap-2">
        <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
          In playlists
        </h3>
        <Skeleton className="h-10 w-full max-w-sm" />
        <Skeleton className="h-10 w-full max-w-sm" />
      </section>
    )
  }

  if (isError) {
    return (
      <section className="flex flex-col gap-2">
        <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
          In playlists
        </h3>
        <p className="text-sm text-muted-foreground">Could not load playlists.</p>
      </section>
    )
  }

  const items = playlists ?? []

  return (
    <section className="flex flex-col gap-2">
      <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
        In playlists
      </h3>
      {items.length === 0 ? (
        <p className="text-sm text-muted-foreground">Not in any playlists yet.</p>
      ) : (
        <ul className="flex flex-col gap-1">
          {items.map((playlist) => (
            <li key={playlist.id}>
              <Link
                to={`/playlists/${playlist.id}`}
                className="text-sm font-medium text-primary hover:underline underline-offset-4"
              >
                {playlist.name}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
