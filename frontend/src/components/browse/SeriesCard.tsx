import { useNavigate } from "react-router-dom"

import type { Series } from "@/api/types"
import { cn } from "@/lib/utils"

interface SeriesCardProps {
  series: Series
  variant: "grid" | "list"
}

function PosterThumb({ series }: { series: Series }) {
  if (series.thumb_url) {
    return (
      <img
        src={series.thumb_url}
        alt=""
        className="size-full object-cover"
        loading="lazy"
      />
    )
  }

  return (
    <div
      aria-hidden
      className="flex size-full items-center justify-center bg-muted text-muted-foreground text-xs"
    >
      No image
    </div>
  )
}

export function SeriesCard({ series, variant }: SeriesCardProps) {
  const navigate = useNavigate()

  const handleClick = () => {
    navigate(`/series/${encodeURIComponent(series.id)}`)
  }

  const focusRing =
    "focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:outline-none"

  if (variant === "list") {
    return (
      <button
        type="button"
        onClick={handleClick}
        className={cn(
          "flex w-full items-center gap-3 rounded-md border bg-card p-2 text-left transition-colors hover:bg-accent/40",
          focusRing,
        )}
      >
        <div className="aspect-[2/3] w-12 shrink-0 overflow-hidden rounded-sm bg-muted">
          <PosterThumb series={series} />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate font-medium">{series.title}</p>
          {series.year ? (
            <p className="text-muted-foreground text-sm">{series.year}</p>
          ) : null}
        </div>
      </button>
    )
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      className={cn(
        "flex flex-col gap-2 rounded-md text-left transition-colors hover:bg-accent/40",
        focusRing,
      )}
    >
      <div className="aspect-[2/3] w-full overflow-hidden rounded-md border bg-muted">
        <PosterThumb series={series} />
      </div>
      <span className="line-clamp-2 text-sm font-medium">{series.title}</span>
    </button>
  )
}
