import { useEffect, useState } from "react"

import { cn } from "@/lib/utils"

interface SeriesPosterProps {
  title: string
  thumbUrl: string | null | undefined
  compact?: boolean
  className?: string
}

export function SeriesPoster({
  title,
  thumbUrl,
  compact = false,
  className,
}: SeriesPosterProps) {
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    setFailed(false)
  }, [thumbUrl])

  const showPlaceholder = !thumbUrl || failed

  if (showPlaceholder) {
    return (
      <div
        className={cn(
          "flex size-full items-center justify-center bg-white p-2 text-center text-neutral-900",
          compact
            ? "text-[0.5625rem] leading-tight"
            : "text-xs leading-snug sm:text-sm md:text-base",
          className,
        )}
        aria-label={title}
      >
        <span className={cn("font-medium", compact ? "line-clamp-3" : "line-clamp-4")}>
          {title}
        </span>
      </div>
    )
  }

  return (
    <img
      src={thumbUrl}
      alt=""
      className={cn("size-full object-cover", className)}
      loading="lazy"
      onError={() => setFailed(true)}
    />
  )
}
