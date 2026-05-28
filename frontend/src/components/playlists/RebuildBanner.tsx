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

function providerLabel(providerKind: string | null | undefined): string {
  if (providerKind === "jellyfin") return "Jellyfin"
  return "Plex"
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
  const provider = providerLabel(providerKind)
  const slotsFilled = lastRebuild?.slots_filled
  const slotsRequested = lastRebuild?.slots_requested

  return (
    <div className="wof-panel flex flex-col gap-4 p-4">
      <section className="flex flex-col gap-2">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Last rebuild
        </h3>
        <p className="text-sm text-muted-foreground">
        </p>
        <div className="flex flex-wrap items-center gap-3">
          <StatusBadge status={status} />
          {lastRebuild?.finished_at ? (
            <span className="text-xs text-muted-foreground">
              Finished {formatRelativeTime(lastRebuild.finished_at)}
            </span>
          ) : status === null ? (
            <span className="text-xs text-muted-foreground">No rebuild has run yet</span>
          ) : null}
        </div>
        {slotsFilled != null && slotsRequested != null ? (
          <p className="text-xs text-muted-foreground">
            Filled {slotsFilled} of {slotsRequested} requested slots
          </p>
        ) : null}
        {status === "failed" && lastRebuild?.error_message ? (
          <p className="text-sm text-destructive">
            {lastRebuild.error_message}. Your previous output list below is unchanged.
          </p>
        ) : null}
        {status === "partial" ? (
          <p className="text-sm text-amber-600">
            Completed with warnings — some shows were skipped during the rebuild.
          </p>
        ) : null}
      </section>

      <section className="flex flex-col gap-2 border-t border-border/60 pt-4">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          {provider} Sync Status
        </h3>
        <p className="text-sm text-muted-foreground">
        </p>
        <WritebackStatus
          status={writebackStatus}
          error={lastRebuild?.writeback_error}
          warnings={lastRebuild?.writeback_warnings}
          episodeTitlesById={episodeTitlesById(snapshot)}
          providerKind={providerKind}
          openUrl={providerPlaylistOpenUrl}
        />
      </section>
    </div>
  )
}
