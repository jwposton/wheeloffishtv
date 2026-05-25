import type { KeyboardEvent, MouseEvent } from "react"
import { MoreVertical } from "lucide-react"
import { useNavigate } from "react-router-dom"

import type { Series } from "@/api/types"
import {
  AddToPlaylistContextMenuItems,
  AddToPlaylistMenu,
} from "@/components/playlists/AddToPlaylistMenu"
import { SeriesPoster } from "@/components/browse/SeriesPoster"
import { Button } from "@/components/ui/button"
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuTrigger,
} from "@/components/ui/context-menu"
import { seriesDetailRoute } from "@/lib/seriesId"
import { cn } from "@/lib/utils"

interface SeriesCardProps {
  series: Series
  variant: "grid" | "list"
}

function PosterThumb({
  series,
  compact,
}: {
  series: Series
  compact?: boolean
}) {
  return (
    <SeriesPoster
      title={series.title}
      thumbUrl={series.thumb_url}
      compact={compact}
    />
  )
}

function SeriesActionsMenu({ seriesId }: { seriesId: string }) {
  return (
    <AddToPlaylistMenu
      seriesId={seriesId}
      trigger={
        <Button
          type="button"
          variant="secondary"
          size="icon-xs"
          className="bg-background/90 shadow-sm backdrop-blur-sm"
          aria-label="Series actions"
          onClick={(event: MouseEvent) => event.stopPropagation()}
        >
          <MoreVertical />
        </Button>
      }
    />
  )
}

export function SeriesCard({ series, variant }: SeriesCardProps) {
  const navigate = useNavigate()

  const handleActivate = () => {
    navigate(seriesDetailRoute(series.id))
  }

  const handleKeyDown = (event: KeyboardEvent) => {
    if (event.key === "Enter") {
      event.preventDefault()
      handleActivate()
    }
  }

  const focusRing =
    "focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:outline-none"

  if (variant === "list") {
    return (
      <ContextMenu>
        <ContextMenuTrigger
          className="w-full"
          onClick={(event: MouseEvent) => {
            if (event.defaultPrevented) {
              return
            }
            handleActivate()
          }}
        >
          <div
            className={cn(
              "flex w-full items-center gap-3 rounded-md border bg-card p-2 text-left transition-colors hover:bg-accent/40",
              focusRing,
            )}
            role="button"
            tabIndex={0}
            onKeyDown={handleKeyDown}
          >
            <div className="aspect-[2/3] w-12 shrink-0 overflow-hidden rounded-sm border bg-white">
              <PosterThumb series={series} compact />
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate font-medium">{series.title}</p>
              {series.year ? (
                <p className="text-muted-foreground text-sm">{series.year}</p>
              ) : null}
            </div>
            <div
              className="shrink-0"
              onClick={(event) => event.stopPropagation()}
              onContextMenu={(event) => event.stopPropagation()}
            >
              <SeriesActionsMenu seriesId={series.id} />
            </div>
          </div>
        </ContextMenuTrigger>
        <ContextMenuContent onClick={(event) => event.stopPropagation()}>
          <AddToPlaylistContextMenuItems seriesId={series.id} />
        </ContextMenuContent>
      </ContextMenu>
    )
  }

  return (
    <ContextMenu>
      <ContextMenuTrigger className="block w-full">
        <div className="relative flex flex-col gap-2 rounded-md text-left">
          <button
            type="button"
            onClick={handleActivate}
            onKeyDown={handleKeyDown}
            className={cn(
              "flex flex-col gap-2 rounded-md text-left transition-colors hover:bg-accent/40",
              focusRing,
            )}
          >
            <div className="aspect-[2/3] w-full overflow-hidden rounded-md border bg-white">
              <PosterThumb series={series} />
            </div>
            <span className="line-clamp-2 text-sm font-medium">{series.title}</span>
          </button>
          <div
            className="absolute top-2 right-2"
            onClick={(event) => event.stopPropagation()}
            onContextMenu={(event) => event.stopPropagation()}
          >
            <SeriesActionsMenu seriesId={series.id} />
          </div>
        </div>
      </ContextMenuTrigger>
      <ContextMenuContent onClick={(event) => event.stopPropagation()}>
        <AddToPlaylistContextMenuItems seriesId={series.id} />
      </ContextMenuContent>
    </ContextMenu>
  )
}
