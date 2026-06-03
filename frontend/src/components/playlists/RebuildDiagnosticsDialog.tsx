import type { ReactNode } from "react"

import type {
  DiagnosticIssueRow,
  PruneEvent,
  RebuildRunSummary,
} from "@/api/playlists"
import { StatusBadge } from "@/components/playlists/StatusBadge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  runDiagnosticAction,
  type DiagnosticActionContext,
} from "@/lib/rebuildDiagnostics"
import type { RebuildStatus } from "@/api/types"

const UNKNOWN_SHOW_LABEL = "Unknown show"
const UNKNOWN_EPISODE_LABEL = "Unknown episode"

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

function hasDiagnosticRows(
  lastRebuild: RebuildRunSummary | null,
  pruneEvents: PruneEvent[],
): boolean {
  const diagnostics = lastRebuild?.diagnostics
  if (!diagnostics) {
    return pruneEvents.length > 0
  }

  return (
    diagnostics.rebuild_error != null ||
    diagnostics.show_issues.length > 0 ||
    diagnostics.episode_issues.length > 0 ||
    pruneEvents.length > 0
  )
}

function pruneEventLabel(event: PruneEvent): string {
  switch (event.event_type) {
    case "auto_pruned":
      return "Auto pruned"
    case "catalog_sync":
      return "Catalog sync"
    case "operator":
      return "Operator removal"
    default:
      return event.event_type.replace(/_/g, " ")
  }
}

interface IssueRowProps {
  row: DiagnosticIssueRow
  actionContext: DiagnosticActionContext
}

function DiagnosticIssueRowView({ row, actionContext }: IssueRowProps) {
  const showSeriesIdFallback =
    row.label === UNKNOWN_SHOW_LABEL && Boolean(row.series_id)
  const showEpisodeIdFallback =
    row.label === UNKNOWN_EPISODE_LABEL && Boolean(row.episode_id)

  return (
    <div className="flex flex-col gap-1 border-b border-border/60 pb-3 last:border-b-0 last:pb-0">
      <p className="text-sm font-medium">{row.label}</p>
      <p className="text-sm text-muted-foreground">{row.reason_text}</p>
      {row.remediation_hint ? (
        <p className="text-xs text-muted-foreground">{row.remediation_hint}</p>
      ) : null}
      {showSeriesIdFallback ? (
        <p className="font-mono text-xs text-muted-foreground">{row.series_id}</p>
      ) : null}
      {showEpisodeIdFallback ? (
        <p className="font-mono text-xs text-muted-foreground">{row.episode_id}</p>
      ) : null}
      {row.actions.length > 0 ? (
        <div className="flex flex-wrap gap-2 pt-1">
          {row.actions.map((action, index) => (
            <Button
              key={`${action.type}-${action.label}-${index}`}
              type="button"
              variant="link"
              className="h-auto px-0"
              onClick={() => runDiagnosticAction(action, actionContext)}
            >
              {action.label}
            </Button>
          ))}
        </div>
      ) : null}
    </div>
  )
}

interface PruneEventRowProps {
  event: PruneEvent
  actionContext: DiagnosticActionContext
}

function PruneEventRowView({ event, actionContext }: PruneEventRowProps) {
  return (
    <div className="flex flex-col gap-1 border-b border-border/60 pb-3 last:border-b-0 last:pb-0">
      <p className="text-sm font-medium">{pruneEventLabel(event)}</p>
      <p className="text-sm text-muted-foreground">{event.reason}</p>
      <p className="font-mono text-xs text-muted-foreground">{event.series_id}</p>
      <div className="pt-1">
        <Button
          type="button"
          variant="link"
          className="h-auto px-0"
          onClick={() =>
            runDiagnosticAction(
              {
                type: "open_series",
                label: "View series",
                series_id: event.series_id,
              },
              actionContext,
            )
          }
        >
          View series
        </Button>
      </div>
    </div>
  )
}

interface DiagnosticsSectionProps {
  title: string
  children: ReactNode
}

function DiagnosticsSection({ title, children }: DiagnosticsSectionProps) {
  return (
    <section className="flex flex-col gap-3">
      <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </h3>
      <div className="flex flex-col gap-3">{children}</div>
    </section>
  )
}

export interface RebuildDiagnosticsDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  lastRebuild: RebuildRunSummary | null
  pruneEvents: PruneEvent[]
  actionContext: DiagnosticActionContext
}

export function RebuildDiagnosticsDialog({
  open,
  onOpenChange,
  lastRebuild,
  pruneEvents,
  actionContext,
}: RebuildDiagnosticsDialogProps) {
  const status = (lastRebuild?.status ?? null) as RebuildStatus
  const diagnostics = lastRebuild?.diagnostics
  const finishedLabel = formatRelativeTime(lastRebuild?.finished_at ?? null)
  const showEmptyState = !hasDiagnosticRows(lastRebuild, pruneEvents)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent showCloseButton className="max-w-xl sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>Rebuild diagnostics</DialogTitle>
          <div className="flex flex-wrap items-center gap-3">
            <StatusBadge status={status} />
            {lastRebuild?.finished_at ? (
              <span className="text-xs text-muted-foreground">
                Finished {finishedLabel}
              </span>
            ) : null}
          </div>
        </DialogHeader>

        <div className="max-h-[70vh] overflow-y-auto pr-1">
          {showEmptyState ? (
            <div className="flex flex-col gap-2 py-2">
              <p className="text-sm font-medium">
                No detailed diagnostics available for this run
              </p>
              <p className="text-sm text-muted-foreground">
                Finished {finishedLabel} — nothing else was recorded for this run.
              </p>
            </div>
          ) : (
            <div className="flex flex-col gap-6 py-1">
              {diagnostics?.rebuild_error ? (
                <DiagnosticsSection title="Rebuild">
                  <DiagnosticIssueRowView
                    row={diagnostics.rebuild_error}
                    actionContext={actionContext}
                  />
                </DiagnosticsSection>
              ) : null}

              {diagnostics?.show_issues.length ? (
                <DiagnosticsSection title="Shows skipped">
                  {diagnostics.show_issues.map((row, index) => (
                    <DiagnosticIssueRowView
                      key={`show-${row.reason_code}-${row.series_id ?? index}`}
                      row={row}
                      actionContext={actionContext}
                    />
                  ))}
                </DiagnosticsSection>
              ) : null}

              {diagnostics?.episode_issues.length ? (
                <DiagnosticsSection title="Episode sync">
                  {diagnostics.episode_issues.map((row, index) => (
                    <DiagnosticIssueRowView
                      key={`episode-${row.reason_code}-${row.episode_id ?? index}`}
                      row={row}
                      actionContext={actionContext}
                    />
                  ))}
                </DiagnosticsSection>
              ) : null}

              {pruneEvents.length > 0 ? (
                <DiagnosticsSection title="Prune history">
                  {pruneEvents.map((event) => (
                    <PruneEventRowView
                      key={event.id}
                      event={event}
                      actionContext={actionContext}
                    />
                  ))}
                </DiagnosticsSection>
              ) : null}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
