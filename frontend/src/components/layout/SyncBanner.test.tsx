import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import type { SyncStatusEmbed } from "@/api/types"

import { SyncBanner } from "./SyncBanner"

describe("SyncBanner", () => {
  it("is visible when sync.status is running", () => {
    const sync: SyncStatusEmbed = {
      status: "running",
      progress_pct: 42,
      library_native_id: null,
      error_message: null,
    }

    render(<SyncBanner sync={sync} />)

    expect(screen.getByText(/Updating library/i)).toBeInTheDocument()
  })

  it("is hidden when sync is idle", () => {
    const sync: SyncStatusEmbed = {
      status: "idle",
      progress_pct: null,
      library_native_id: null,
      error_message: null,
    }

    render(<SyncBanner sync={sync} />)

    expect(screen.queryByText(/Updating library/i)).not.toBeInTheDocument()
  })
})
