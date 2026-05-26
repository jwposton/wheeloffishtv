import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { describe, expect, it, vi, beforeEach } from "vitest"

import type { PlaylistListItem } from "@/api/types"

vi.mock("@/api/playlists", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/playlists")>()
  return {
    ...actual,
    usePlaylistsContainingSeries: vi.fn(),
  }
})

import { usePlaylistsContainingSeries } from "@/api/playlists"
import { SeriesPlaylistsSection } from "@/components/series/SeriesPlaylistsSection"

const mockUsePlaylistsContainingSeries = vi.mocked(usePlaylistsContainingSeries)

const MOCK_PLAYLISTS: PlaylistListItem[] = [
  {
    id: "pl-1",
    name: "Weeknight Mix",
    refresh_cadence: "daily",
    refresh_day_of_week: null,
    last_rebuild_status: "succeeded",
    last_rebuild_at: "2026-05-25T10:00:00Z",
  },
  {
    id: "pl-2",
    name: "Sci-Fi Marathon",
    refresh_cadence: "weekly",
    refresh_day_of_week: 0,
    last_rebuild_status: null,
    last_rebuild_at: null,
  },
]

function renderSection() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <SeriesPlaylistsSection seriesId="series-abc" />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe("SeriesPlaylistsSection", () => {
  beforeEach(() => {
    mockUsePlaylistsContainingSeries.mockReturnValue({
      data: MOCK_PLAYLISTS,
      isLoading: false,
      isError: false,
    } as unknown as ReturnType<typeof usePlaylistsContainingSeries>)
  })

  it("lists playlists containing the series", () => {
    renderSection()
    expect(screen.getByText("Weeknight Mix")).toBeInTheDocument()
    expect(screen.getByText("Sci-Fi Marathon")).toBeInTheDocument()
    expect(screen.getByRole("link", { name: "Weeknight Mix" })).toHaveAttribute(
      "href",
      "/playlists/pl-1",
    )
  })

  it("shows empty state when not in any playlists", () => {
    mockUsePlaylistsContainingSeries.mockReturnValue({
      data: [] as PlaylistListItem[],
      isLoading: false,
      isError: false,
    } as unknown as ReturnType<typeof usePlaylistsContainingSeries>)
    renderSection()
    expect(screen.getByText("Not in any playlists yet.")).toBeInTheDocument()
  })
})
