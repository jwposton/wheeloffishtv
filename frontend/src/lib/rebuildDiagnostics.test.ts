import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import type { DiagnosticAction, RebuildRunSummary } from "@/api/playlists"
import { seriesDetailRoute } from "@/lib/seriesId"

import { runDiagnosticAction, shouldShowDiagnostics } from "./rebuildDiagnostics"

function makeRun(overrides: Partial<RebuildRunSummary> = {}): RebuildRunSummary {
  return {
    id: "run-1",
    status: "succeeded",
    started_at: null,
    finished_at: "2026-06-01T12:00:00Z",
    error_message: null,
    slots_filled: null,
    slots_requested: null,
    ...overrides,
  }
}

describe("shouldShowDiagnostics", () => {
  it("returns false when last rebuild is null", () => {
    expect(shouldShowDiagnostics(null)).toBe(false)
  })

  it("returns true when rebuild status is partial or failed", () => {
    expect(shouldShowDiagnostics(makeRun({ status: "partial" }))).toBe(true)
    expect(shouldShowDiagnostics(makeRun({ status: "failed" }))).toBe(true)
  })

  it("returns false for succeeded, queued, and running without writeback warnings", () => {
    expect(shouldShowDiagnostics(makeRun({ status: "succeeded" }))).toBe(false)
    expect(shouldShowDiagnostics(makeRun({ status: "queued" }))).toBe(false)
    expect(shouldShowDiagnostics(makeRun({ status: "running" }))).toBe(false)
  })

  it("returns true when writeback is partial or failed even if rebuild succeeded", () => {
    expect(
      shouldShowDiagnostics(
        makeRun({ status: "succeeded", writeback_status: "partial" }),
      ),
    ).toBe(true)
    expect(
      shouldShowDiagnostics(
        makeRun({ status: "succeeded", writeback_status: "failed" }),
      ),
    ).toBe(true)
  })

  it("returns false when writeback succeeded and rebuild is clean", () => {
    expect(
      shouldShowDiagnostics(
        makeRun({ status: "succeeded", writeback_status: "succeeded" }),
      ),
    ).toBe(false)
  })
})

describe("runDiagnosticAction", () => {
  const seriesId = "conn:plex:show-1"
  let onRemoveRow: ReturnType<typeof vi.fn>
  let navigate: ReturnType<typeof vi.fn>
  let openSpy: ReturnType<typeof vi.spyOn>
  let assignSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    onRemoveRow = vi.fn()
    navigate = vi.fn()
    openSpy = vi.spyOn(window, "open").mockImplementation(() => null)
    assignSpy = vi.spyOn(window.location, "assign").mockImplementation(() => {})
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("calls onRemoveRow for remove_row when series_id is present", () => {
    const action: DiagnosticAction = {
      type: "remove_row",
      label: "Remove from playlist",
      series_id: seriesId,
    }

    runDiagnosticAction(action, { onRemoveRow, navigate })

    expect(onRemoveRow).toHaveBeenCalledWith(seriesId)
  })

  it("no-ops remove_row without series_id", () => {
    runDiagnosticAction(
      { type: "remove_row", label: "Remove from playlist" },
      { onRemoveRow, navigate },
    )

    expect(onRemoveRow).not.toHaveBeenCalled()
  })

  it("navigates to series detail for open_series when series_id is present", () => {
    runDiagnosticAction(
      { type: "open_series", label: "View series", series_id: seriesId },
      { onRemoveRow, navigate },
    )

    expect(navigate).toHaveBeenCalledWith(seriesDetailRoute(seriesId))
    expect(assignSpy).not.toHaveBeenCalled()
  })

  it("falls back to window.location.assign when navigate is omitted", () => {
    runDiagnosticAction(
      { type: "open_series", label: "View series", series_id: seriesId },
      { onRemoveRow },
    )

    expect(assignSpy).toHaveBeenCalledWith(seriesDetailRoute(seriesId))
  })

  it("no-ops open_series without series_id", () => {
    runDiagnosticAction(
      { type: "open_series", label: "View series" },
      { onRemoveRow, navigate },
    )

    expect(navigate).not.toHaveBeenCalled()
    expect(assignSpy).not.toHaveBeenCalled()
  })

  it("opens provider URL in a new tab with noopener,noreferrer", () => {
    const url = "https://app.plex.tv/desktop#!/playlists/abc"

    runDiagnosticAction(
      { type: "open_provider", label: "Open in Plex", url },
      { onRemoveRow, navigate },
    )

    expect(openSpy).toHaveBeenCalledWith(url, "_blank", "noopener,noreferrer")
  })

  it("no-ops open_provider without url", () => {
    runDiagnosticAction(
      { type: "open_provider", label: "Open in Plex" },
      { onRemoveRow, navigate },
    )

    expect(openSpy).not.toHaveBeenCalled()
  })
})
