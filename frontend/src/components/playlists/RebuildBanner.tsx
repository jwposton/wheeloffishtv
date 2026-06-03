import { useState } from "react"

import { StatusBadge } from "@/components/playlists/StatusBadge"
import { RebuildDiagnosticsDialog } from "@/components/playlists/RebuildDiagnosticsDialog"
import { WritebackStatus } from "@/components/playlists/WritebackStatus"
import { Button } from "@/components/ui/button"
import { shouldShowDiagnostics } from "@/lib/rebuildDiagnostics"
import type { PruneEvent, RebuildRunSummary } from "@/api/playlists"
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
  providerKind?: string | null
  providerPlaylistOpenUrl?: string | null
  pruneEvents?: PruneEvent[]
  onRemoveRow?: (seriesId: string) => void
  navigate?: (to: string) => void
}

export function RebuildBanner({
  lastRebuild,
  providerKind,
  providerPlaylistOpenUrl,
  pruneEvents = [],
  onRemoveRow,
  navigate,
}: RebuildBannerProps) {
  const [diagnosticsOpen, setDiagnosticsOpen] = useState(false)
  const status = (lastRebuild?.status ?? null) as RebuildStatus
  const writebackStatus = (lastRebuild?.writeback_status ?? null) as WritebackStatusValue
  const provider = providerLabel(providerKind)
  const slotsFilled = lastRebuild?.slots_filled
  const slotsRequested = lastRebuild?.slots_requested
  const showDetails = shouldShowDiagnostics(lastRebuild)

  return (
    <div className="wof-panel flex flex-col gap-4 p-4">
      <section className="flex flex-col gap-2">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Last rebuild
        </h3>
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
        <WritebackStatus
          status={writebackStatus}
          error={lastRebuild?.writeback_error}
          warnings={lastRebuild?.writeback_warnings}
          providerKind={providerKind}
          openUrl={providerPlaylistOpenUrl}
        />
      </section>

      {showDetails ? (
        <Button
          type="button"
          variant="link"
          className="h-auto px-0 self-start"
          onClick={() => setDiagnosticsOpen(true)}
        >
          View details
        </Button>
      ) : null}

      <RebuildDiagnosticsDialog
        open={diagnosticsOpen}
        onOpenChange={setDiagnosticsOpen}
        lastRebuild={lastRebuild}
        pruneEvents={pruneEvents}
        actionContext={{
          onRemoveRow: onRemoveRow ?? (() => {}),
          navigate,
        }}
      />
    </div>
  )
}
