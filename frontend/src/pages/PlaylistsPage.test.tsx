import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import type { RebuildStatus } from "@/api/types"

import { StatusBadge } from "@/components/playlists/StatusBadge"

describe("StatusBadge", () => {
  it('renders "Never rebuilt" when status is null', () => {
    render(<StatusBadge status={null} />)
    expect(screen.getByText("Never rebuilt")).toBeInTheDocument()
  })

  it('renders "Succeeded" label when status is succeeded', () => {
    render(<StatusBadge status="succeeded" />)
    expect(screen.getByText("Succeeded")).toBeInTheDocument()
  })

  it('renders "Failed" label when status is failed', () => {
    render(<StatusBadge status="failed" />)
    expect(screen.getByText("Failed")).toBeInTheDocument()
  })

  it('renders "Partial" label when status is partial', () => {
    render(<StatusBadge status="partial" />)
    expect(screen.getByText("Partial")).toBeInTheDocument()
  })

  it('renders "Rebuilding\u2026" with a spinning wheel when status is running', () => {
    render(<StatusBadge status="running" />)
    expect(screen.getByText("Rebuilding\u2026")).toBeInTheDocument()
    expect(screen.getByTestId("wheel-icon")).toHaveAttribute("data-spinning", "true")
  })

  it('renders "Rebuilding\u2026" with a spinning wheel when status is queued', () => {
    render(<StatusBadge status="queued" />)
    expect(screen.getByText("Rebuilding\u2026")).toBeInTheDocument()
    expect(screen.getByTestId("wheel-icon")).toHaveAttribute("data-spinning", "true")
  })

  it("accepts all RebuildStatus values without TypeScript errors", () => {
    const statuses: Array<RebuildStatus> = [
      "succeeded",
      "partial",
      "failed",
      "running",
      "queued",
      null,
    ]
    for (const status of statuses) {
      const { unmount } = render(<StatusBadge status={status} />)
      unmount()
    }
  })
})
