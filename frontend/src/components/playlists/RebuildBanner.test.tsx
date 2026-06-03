import { fireEvent, render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import type { RebuildRunSummary } from "@/api/playlists"

import { RebuildBanner } from "./RebuildBanner"

function makeRun(overrides: Partial<RebuildRunSummary> = {}): RebuildRunSummary {
  return {
    id: "run-1",
    status: "succeeded",
    started_at: null,
    finished_at: new Date(Date.now() - 3_600_000).toISOString(),
    error_message: null,
    slots_filled: 5,
    slots_requested: 5,
    writeback_status: "succeeded",
    writeback_error: null,
    ...overrides,
  }
}

describe("RebuildBanner", () => {
  it("hides View details when rebuild and writeback succeeded", () => {
    render(<RebuildBanner lastRebuild={makeRun()} />)

    expect(screen.queryByRole("button", { name: "View details" })).not.toBeInTheDocument()
  })

  it("shows View details and opens diagnostics modal on partial rebuild", () => {
    render(
      <RebuildBanner
        lastRebuild={makeRun({
          status: "partial",
          diagnostics: {
            rebuild_error: null,
            show_issues: [
              {
                label: "Show A",
                reason_code: "skip",
                reason_text: "Skipped",
                remediation_hint: "",
                series_id: "s-1",
                actions: [],
              },
            ],
            episode_issues: [],
          },
        })}
      />,
    )

    expect(screen.getByRole("button", { name: "View details" })).toBeInTheDocument()
    fireEvent.click(screen.getByRole("button", { name: "View details" }))
    expect(screen.getByRole("dialog", { name: "Rebuild diagnostics" })).toBeInTheDocument()
    expect(screen.getByText("Show A")).toBeInTheDocument()
  })

  it("shows View details on failed rebuild without inline error_message", () => {
    const errorText = "Provider connection timed out"
    render(
      <RebuildBanner
        lastRebuild={makeRun({
          status: "failed",
          error_message: errorText,
          diagnostics: {
            rebuild_error: {
              label: "Rebuild failed",
              reason_code: "failed",
              reason_text: errorText,
              remediation_hint: "Try again later.",
              actions: [],
            },
            show_issues: [],
            episode_issues: [],
          },
        })}
      />,
    )

    expect(screen.getByRole("button", { name: "View details" })).toBeInTheDocument()
    expect(screen.queryByText(errorText)).not.toBeInTheDocument()
    expect(
      screen.queryByText(/Your previous output list below is unchanged/i),
    ).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole("button", { name: "View details" }))
    expect(screen.getByRole("dialog", { name: "Rebuild diagnostics" })).toBeInTheDocument()
    expect(screen.getByText(errorText)).toBeInTheDocument()
  })

  it("shows View details when writeback is partial", () => {
    render(
      <RebuildBanner
        lastRebuild={makeRun({
          status: "succeeded",
          writeback_status: "partial",
          writeback_warnings: [{ episode_id: "ep-1", reason: "Missing guid" }],
        })}
      />,
    )

    expect(screen.getByRole("button", { name: "View details" })).toBeInTheDocument()
  })

  it("passes onRemoveRow to the diagnostics modal", () => {
    const onRemoveRow = vi.fn()
    render(
      <RebuildBanner
        lastRebuild={makeRun({
          status: "partial",
          diagnostics: {
            rebuild_error: null,
            show_issues: [
              {
                label: "Show A",
                reason_code: "skip",
                reason_text: "Skipped",
                remediation_hint: "",
                series_id: "s-1",
                actions: [
                  {
                    type: "remove_row",
                    label: "Remove from playlist",
                    series_id: "s-1",
                  },
                ],
              },
            ],
            episode_issues: [],
          },
        })}
        onRemoveRow={onRemoveRow}
      />,
    )

    fireEvent.click(screen.getByRole("button", { name: "View details" }))
    fireEvent.click(screen.getByRole("button", { name: "Remove from playlist" }))
    expect(onRemoveRow).toHaveBeenCalledWith("s-1")
  })
})
