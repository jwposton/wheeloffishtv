import { render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import { PlaylistRowMenuItems } from "@/components/playlists/PlaylistRowMenuItems"
import type { SeriesRow } from "@/components/playlists/RowSettingsSheet"
import { DropdownMenu, DropdownMenuContent, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"

const ROW: SeriesRow = {
  series_id: "series-1",
  series_title: "Test Show",
  thumb_url: null,
  mode: "ordered",
  completion_policy: "remove",
}

function renderDropdownMenu() {
  return render(
    <DropdownMenu defaultOpen>
      <DropdownMenuTrigger render={<Button type="button">Open</Button>} />
      <DropdownMenuContent>
        <PlaylistRowMenuItems
          row={ROW}
          variant="dropdown"
          onModeChange={vi.fn()}
          onPolicyChange={vi.fn()}
          onRemove={vi.fn()}
        />
      </DropdownMenuContent>
    </DropdownMenu>,
  )
}

describe("PlaylistRowMenuItems", () => {
  it("renders playback mode, completion policy, and remove items", async () => {
    renderDropdownMenu()

    expect(await screen.findByText("Playback mode")).toBeInTheDocument()
    expect(screen.getByText("Completion policy")).toBeInTheDocument()
    expect(screen.getByText("Remove from playlist")).toBeInTheDocument()
  })
})
