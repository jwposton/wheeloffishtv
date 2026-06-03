import type { DiagnosticAction, RebuildRunSummary } from "@/api/playlists"
import { seriesDetailRoute } from "@/lib/seriesId"

export interface DiagnosticActionContext {
  onRemoveRow: (seriesId: string) => void
  navigate?: (to: string) => void
}

function hasStructuredDiagnosticRows(last: RebuildRunSummary): boolean {
  const diagnostics = last.diagnostics
  if (!diagnostics) {
    return false
  }
  return (
    diagnostics.rebuild_error != null ||
    diagnostics.show_issues.length > 0 ||
    diagnostics.episode_issues.length > 0
  )
}

export function shouldShowDiagnostics(last: RebuildRunSummary | null): boolean {
  if (!last) {
    return false
  }

  const rebuildWarn = last.status === "partial" || last.status === "failed"
  const writebackWarn =
    last.writeback_status === "partial" || last.writeback_status === "failed"
  const underfilled =
    last.slots_filled != null &&
    last.slots_requested != null &&
    last.slots_filled < last.slots_requested

  return (
    rebuildWarn || writebackWarn || underfilled || hasStructuredDiagnosticRows(last)
  )
}

export function runDiagnosticAction(
  action: DiagnosticAction,
  ctx: DiagnosticActionContext,
): void {
  switch (action.type) {
    case "remove_row":
      if (action.series_id) {
        ctx.onRemoveRow(action.series_id)
      }
      break
    case "open_provider":
      if (action.url) {
        window.open(action.url, "_blank", "noopener,noreferrer")
      }
      break
    case "open_series":
      if (action.series_id) {
        const route = seriesDetailRoute(action.series_id)
        if (ctx.navigate) {
          ctx.navigate(route)
        } else {
          window.location.assign(route)
        }
      }
      break
    default:
      break
  }
}
