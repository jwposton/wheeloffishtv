import { StatusBadge } from "@/components/playlists/StatusBadge"
import { WritebackStatus } from "@/components/playlists/WritebackStatus"
import type { RebuildRunSummary, SnapshotEpisode } from "@/api/playlists"
import type { RebuildStatus, WritebackStatus as WritebackStatusValue } from "@/api/types"

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

interface RebuildBannerProps {
  lastRebuild: RebuildRunSummary | null
  snapshot?: SnapshotEpisode[]
  providerKind?: string | null
  providerPlaylistOpenUrl?: string | null
}

function episodeTitlesById(snapshot: SnapshotEpisode[] | undefined): Record<string, string> {
  if (!snapshot?.length) return {}
  return Object.fromEntries(snapshot.map((ep) => [ep.episode_id, ep.title]))
}

export function RebuildBanner({
  lastRebuild,
  snapshot,
  providerKind,
  providerPlaylistOpenUrl,
}: RebuildBannerProps) {
  const status = (lastRebuild?.status ?? null) as RebuildStatus
  const writebackStatus = (lastRebuild?.writeback_status ?? null) as WritebackStatusValue

  return (
    <div className="flex flex-col gap-3 rounded-xl border bg-card p-4">
      <div className="flex items-center gap-3">
        <StatusBadge status={status} />
        {lastRebuild?.finished_at && (
          <span className="text-xs text-muted-foreground">
            {formatRelativeTime(lastRebuild.finished_at)}
          </span>
        )}
      </div>

      {status === "failed" && lastRebuild?.error_message && (
        <p className="text-sm text-destructive">
          Last rebuild failed: {lastRebuild.error_message}. Your previous playlist output
          is still available below.
        </p>
      )}

      {status === "partial" && (
        <p className="text-sm text-amber-600">
          Last rebuild completed with warnings — some series were skipped.
        </p>
      )}

      <WritebackStatus
        status={writebackStatus}
        error={lastRebuild?.writeback_error}
        warnings={lastRebuild?.writeback_warnings}
        episodeTitlesById={episodeTitlesById(snapshot)}
        providerKind={providerKind}
        openUrl={providerPlaylistOpenUrl}
      />
    </div>
  )
}
