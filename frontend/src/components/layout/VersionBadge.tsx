import { useQuery } from "@tanstack/react-query"

import { fetchJson } from "@/api/client"
import type { VersionMetaResponse } from "@/api/types"
import { cn } from "@/lib/utils"

const VERSION_QUERY_KEY = ["meta", "version"] as const

export function VersionBadge({ className }: { className?: string }) {
  const { data } = useQuery({
    queryKey: VERSION_QUERY_KEY,
    queryFn: () => fetchJson<VersionMetaResponse>("/meta/version"),
    staleTime: 60 * 60 * 1000,
    retry: 1,
  })

  if (!data) {
    return null
  }

  const label = `v${data.version}`
  const title = data.update_available
    ? `Update available: v${data.latest_version}`
    : `Wheel of Fish TV ${label}`

  if (data.update_available && data.release_url) {
    return (
      <a
        href={data.release_url}
        target="_blank"
        rel="noopener noreferrer"
        title={title}
        className={cn(
          "inline-flex items-center gap-1.5 rounded-md px-1.5 py-0.5 text-[10px] font-medium tabular-nums tracking-wide text-wof-orange/90 transition-colors hover:text-wof-orange focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          className,
        )}
      >
        <span
          className="size-1.5 shrink-0 rounded-full bg-wof-orange motion-safe:animate-pulse"
          aria-hidden
        />
        <span>{label}</span>
        <span className="sr-only"> — update available</span>
      </a>
    )
  }

  return (
    <span
      title={title}
      className={cn(
        "select-none px-1.5 py-0.5 text-[10px] tabular-nums tracking-wide text-muted-foreground/55",
        className,
      )}
    >
      {label}
    </span>
  )
}
