import { useMemo } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { ArrowLeftIcon } from "lucide-react"

import { PlaylistForm } from "@/components/playlists/PlaylistForm"
import type { SeriesRow } from "@/components/playlists/TwoPanePicker"
import { Button } from "@/components/ui/button"

export function PlaylistFormPage() {
  const [searchParams] = useSearchParams()
  const seriesId = searchParams.get("seriesId")

  const initialRows = useMemo<SeriesRow[] | undefined>(() => {
    if (!seriesId) {
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
  }, [seriesId])

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-4">
      <Button
        size="sm"
        variant="ghost"
        className="-ml-2 w-fit gap-1.5 text-muted-foreground"
        render={<Link to="/playlists" />}
      >
        <ArrowLeftIcon className="size-4" aria-hidden />
        Playlists
      </Button>
      <h2 className="text-xl font-semibold">New playlist</h2>
      <PlaylistForm mode="create" initialRows={initialRows} />
    </div>
  )
}
