import { fireEvent, render, screen, within } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import type {
  DiagnosticIssueRow,
  PruneEvent,
  RebuildRunSummary,
} from "@/api/playlists"

import { RebuildDiagnosticsDialog } from "./RebuildDiagnosticsDialog"

function makeRun(overrides: Partial<RebuildRunSummary> = {}): RebuildRunSummary {
  return {
    id: "run-1",
    status: "partial",
    started_at: null,
    finished_at: new Date(Date.now() - 3_600_000).toISOString(),
    error_message: null,
    slots_filled: 10,
    slots_requested: 10,
    ...overrides,
  }
}

const showIssue: DiagnosticIssueRow = {
  label: "Breaking Bad",
  reason_code: "fetch_failure",
  reason_text: "Could not fetch episodes from the provider.",
  remediation_hint: "Check your connection and try rebuilding again.",
  series_id: "conn:plex:show-1",
  actions: [
    {
      type: "remove_row",
      label: "Remove from playlist",
      series_id: "conn:plex:show-1",
    },
  ],
}

const episodeIssue: DiagnosticIssueRow = {
  label: "Unknown episode",
  reason_code: "episode_not_found",
  reason_text: "Episode was not found on the provider.",
  remediation_hint: "Verify the episode exists in your library.",
  series_id: "conn:plex:show-1",
  episode_id: "conn:plex:ep-1",
  actions: [],
}

const runWithIssues = makeRun({
  diagnostics: {
    rebuild_error: null,
    show_issues: [showIssue],
    episode_issues: [episodeIssue],
  },
})

const emptyRun = makeRun({
  status: "partial",
  diagnostics: {
    rebuild_error: null,
    show_issues: [],
    episode_issues: [],
  },
})

describe("RebuildDiagnosticsDialog", () => {
  it("renders show and episode rows with labels and remediation hints", () => {
    render(
      <RebuildDiagnosticsDialog
        open
        onOpenChange={vi.fn()}
        lastRebuild={runWithIssues}
        pruneEvents={[]}
        actionContext={{ onRemoveRow: vi.fn() }}
      />,
    )

    expect(screen.getByText("Shows skipped")).toBeInTheDocument()
    expect(screen.getByText("Episode sync")).toBeInTheDocument()
    expect(screen.getByText("Breaking Bad")).toBeInTheDocument()
    expect(
      screen.getByText("Could not fetch episodes from the provider."),
    ).toBeInTheDocument()
    expect(
      screen.getByText("Check your connection and try rebuilding again."),
    ).toBeInTheDocument()
    expect(screen.getByText("Unknown episode")).toBeInTheDocument()
    expect(
      screen.getByText("Verify the episode exists in your library."),
    ).toBeInTheDocument()
  })

  it("hides empty sections", () => {
    render(
      <RebuildDiagnosticsDialog
        open
        onOpenChange={vi.fn()}
        lastRebuild={makeRun({
          diagnostics: {
            rebuild_error: null,
            show_issues: [showIssue],
            episode_issues: [],
          },
        })}
        pruneEvents={[]}
        actionContext={{ onRemoveRow: vi.fn() }}
      />,
    )

    expect(screen.getByText("Shows skipped")).toBeInTheDocument()
    expect(screen.queryByText("Episode sync")).not.toBeInTheDocument()
    expect(screen.queryByText("Prune history")).not.toBeInTheDocument()
    expect(screen.queryByText("Rebuild")).not.toBeInTheDocument()
  })

  it("renders action buttons from actions metadata and calls onRemoveRow", () => {
    const onRemoveRow = vi.fn()

    render(
      <RebuildDiagnosticsDialog
        open
        onOpenChange={vi.fn()}
        lastRebuild={runWithIssues}
        pruneEvents={[]}
        actionContext={{ onRemoveRow }}
      />,
    )

    fireEvent.click(screen.getByRole("button", { name: "Remove from playlist" }))

    expect(onRemoveRow).toHaveBeenCalledWith("conn:plex:show-1")
  })

  it("shows id fallback for unknown labels", () => {
    render(
      <RebuildDiagnosticsDialog
        open
        onOpenChange={vi.fn()}
        lastRebuild={runWithIssues}
        pruneEvents={[]}
        actionContext={{ onRemoveRow: vi.fn() }}
      />,
    )

    const episodeSection = screen.getByText("Episode sync").closest("section")
    expect(episodeSection).not.toBeNull()
    expect(
      within(episodeSection!).getByText("conn:plex:ep-1"),
    ).toBeInTheDocument()
  })

  it("shows the empty state when no diagnostic rows exist", () => {
    render(
      <RebuildDiagnosticsDialog
        open
        onOpenChange={vi.fn()}
        lastRebuild={emptyRun}
        pruneEvents={[]}
        actionContext={{ onRemoveRow: vi.fn() }}
      />,
    )

    expect(
      screen.getByText("No detailed diagnostics available for this run"),
    ).toBeInTheDocument()
    expect(
      screen.getByText(/nothing else was recorded for this run/i),
    ).toBeInTheDocument()
    expect(screen.queryByText("Shows skipped")).not.toBeInTheDocument()
  })

  it("renders prune history with open series affordance", () => {
    const pruneEvents: PruneEvent[] = [
      {
        id: "pe-1",
        series_id: "conn:plex:show-2",
        event_type: "auto_pruned",
        reason: "catalog_sync",
        timestamp: "2026-06-01T10:00:00Z",
      },
    ]

    render(
      <RebuildDiagnosticsDialog
        open
        onOpenChange={vi.fn()}
        lastRebuild={emptyRun}
        pruneEvents={pruneEvents}
        actionContext={{ onRemoveRow: vi.fn() }}
      />,
    )

    expect(screen.getByText("Prune history")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "View series" })).toBeInTheDocument()
  })
})
