import { Link } from "react-router-dom"

import { WheelIcon } from "@/components/icons/WheelIcon"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { StatusBadge } from "@/components/playlists/StatusBadge"
import { WritebackStatus } from "@/components/playlists/WritebackStatus"
import { formatCadence } from "@/api/playlists"
import { isRebuildInProgress } from "@/lib/rebuild"
import type { PlaylistListItem } from "@/api/types"
import type { WritebackStatus as WritebackStatusValue } from "@/api/types"

function formatRelativeTime(isoString: string | null): string {
  if (!isoString) return "Never"
  const diffMs = Date.now() - new Date(isoString).getTime()
  const diffMins = Math.floor(diffMs / 60_000)
  if (diffMins < 1) return "Just now"
  if (diffMins < 60) return `${diffMins}m ago`
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}d ago`
}

interface PlaylistCardProps {
  item: PlaylistListItem
}

export function PlaylistCard({ item }: PlaylistCardProps) {
  const rebuilding = isRebuildInProgress(item.last_rebuild_status)

  return (
    <Link
      to={`/playlists/${item.id}`}
      className="block rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      <Card className="h-full border-border/80 bg-card/85 transition-all hover:border-accent/40 hover:shadow-lg hover:shadow-black/10">
        <CardHeader className="grid-cols-1 gap-3">
          <div className="flex items-start gap-3">
            <div className="rounded-full bg-secondary/80 p-2 ring-1 ring-border/80">
              <WheelIcon spinning={rebuilding} className="size-8" />
            </div>
            <div className="min-w-0 flex-1">
              <CardTitle className="truncate text-base">{item.name}</CardTitle>
              <p className="mt-1 text-xs text-muted-foreground">{formatCadence(item)}</p>
            </div>
          </div>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          <div className="flex items-center justify-between gap-2">
            <StatusBadge status={item.last_rebuild_status} />
            <span className="shrink-0 text-xs text-muted-foreground">
              {formatRelativeTime(item.last_rebuild_at)}
            </span>
          </div>
          <WritebackStatus
            status={(item.last_writeback_status ?? null) as WritebackStatusValue}
            providerKind={item.provider_kind}
            openUrl={item.provider_playlist_open_url}
            compact
          />
        </CardContent>
      </Card>
    </Link>
  )
}
