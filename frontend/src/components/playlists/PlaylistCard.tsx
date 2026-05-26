import { Link } from "react-router-dom"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { StatusBadge } from "@/components/playlists/StatusBadge"
import { WritebackStatus } from "@/components/playlists/WritebackStatus"
import { formatCadence } from "@/api/playlists"
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
  return (
    <Link to={`/playlists/${item.id}`} className="block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-xl">
      <Card className="hover:ring-foreground/20 transition-shadow h-full">
        <CardHeader>
          <CardTitle className="truncate">{item.name}</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          <p className="text-xs text-muted-foreground">{formatCadence(item)}</p>
          <div className="flex items-center justify-between gap-2">
            <StatusBadge status={item.last_rebuild_status} />
            <span className="text-xs text-muted-foreground shrink-0">
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
