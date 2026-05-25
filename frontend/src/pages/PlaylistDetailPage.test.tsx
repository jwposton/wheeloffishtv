import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { describe, expect, it, vi, beforeEach } from "vitest"

import { PlaylistDetailPage } from "./PlaylistDetailPage"
import type { PlaylistDetailResponse } from "@/api/playlists"

vi.mock("@/api/playlists", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/playlists")>()
  return {
    ...actual,
    usePlaylist: vi.fn(),
    useDeletePlaylist: vi.fn(),
    useRebuildPlaylist: vi.fn(),
  }
})

import { usePlaylist, useDeletePlaylist, useRebuildPlaylist } from "@/api/playlists"

const mockUsePlaylist = vi.mocked(usePlaylist)
const mockUseDeletePlaylist = vi.mocked(useDeletePlaylist)
const mockUseRebuildPlaylist = vi.mocked(useRebuildPlaylist)

const MOCK_PLAYLIST: PlaylistDetailResponse = {
  id: "pl-001",
  name: "Test Playlist",
  episode_count: 5,
  slot_allocation: "wild",
  default_completion_policy: "remove",
  refresh_cadence: "daily",
  refresh_day_of_week: null,
  rows: [],
  current_snapshot: [
    {
      episode_id: "ep-1",
      title: "The Pilot",
      series_id: "s-1",
      series_title: "Great Show",
      slot_index: 0,
      row_mode: "ordered",
    },
    {
      episode_id: "ep-2",
      title: "Episode Two",
      series_id: "s-1",
      series_title: "Great Show",
      slot_index: 1,
      row_mode: "ordered",
    },
  ],
  last_rebuild: {
    id: "run-1",
    status: "succeeded",
    started_at: "2026-05-25T10:00:00Z",
    finished_at: "2026-05-25T10:01:00Z",
    error_message: null,
    slots_filled: 5,
    slots_requested: 5,
  },
  recent_runs: [],
}

function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function renderDetailPage(playlistId = "pl-001") {
  const queryClient = makeQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/playlists/${playlistId}`]}>
        <Routes>
          <Route path="/playlists/:id" element={<PlaylistDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe("PlaylistDetailPage", () => {
  beforeEach(() => {
    mockUsePlaylist.mockReturnValue({
      data: MOCK_PLAYLIST,
      isLoading: false,
      isError: false,
    } as ReturnType<typeof usePlaylist>)

    mockUseDeletePlaylist.mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useDeletePlaylist>)

    mockUseRebuildPlaylist.mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useRebuildPlaylist>)
  })

  it('renders the "Rebuild now" button', () => {
    renderDetailPage()
    expect(screen.getByRole("button", { name: "Rebuild now" })).toBeInTheDocument()
  })

  it("renders the output list with episode titles", () => {
    renderDetailPage()
    expect(screen.getByText("The Pilot")).toBeInTheDocument()
    expect(screen.getByText("Episode Two")).toBeInTheDocument()
  })

  it("shows playlist name in the header", () => {
    renderDetailPage()
    expect(screen.getByRole("heading", { name: "Test Playlist" })).toBeInTheDocument()
  })

  it("renders Delete button to trigger confirmation", () => {
    renderDetailPage()
    expect(screen.getByRole("button", { name: "Delete" })).toBeInTheDocument()
  })

  it("shows loading skeletons when playlist is loading", () => {
    mockUsePlaylist.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    } as ReturnType<typeof usePlaylist>)
    const { container } = renderDetailPage()
    expect(container.querySelectorAll("[class*='animate-pulse']").length).toBeGreaterThan(0)
  })
})
