import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { describe, expect, it, vi, beforeEach } from "vitest"

import { PlaylistDetailPage } from "./PlaylistDetailPage"
import type { PlaylistDetailResponse } from "@/api/playlists"

const navigateMock = vi.fn()

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router-dom")>()
  return {
    ...actual,
    useNavigate: () => navigateMock,
  }
})

vi.mock("@/components/playlists/PlaylistForm", () => ({
  PlaylistForm: () => <div data-testid="playlist-form" />,
}))

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
  rows: [
    {
      series_id: "s-1",
      mode: "ordered",
      completion_policy: "remove",
      completion_event: "series_complete",
      series_title: "Great Show",
      thumb_url: null,
    },
  ],
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
    writeback_status: "succeeded",
    writeback_error: null,
  },
  recent_runs: [],
  recent_prune_events: [],
  provider_playlist_id: "555",
  provider_kind: "plex",
  provider_playlist_open_url:
    "https://app.plex.tv/desktop#!/server/machine-abc/playlist?key=%2Fplaylists%2F555",
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
    navigateMock.mockReset()
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

  it('renders the rebuild control with a wheel icon', () => {
    renderDetailPage()
    const button = screen.getByRole("button", { name: "Rebuild" })
    expect(button).toBeInTheDocument()
    expect(button.querySelector('[data-testid="wheel-icon"]')).toBeInTheDocument()
  })

  it("shows a spinning rebuild button when a rebuild is running", () => {
    mockUsePlaylist.mockReturnValue({
      data: {
        ...MOCK_PLAYLIST,
        last_rebuild: {
          ...MOCK_PLAYLIST.last_rebuild!,
          status: "running",
          finished_at: null,
        },
      },
      isLoading: false,
      isError: false,
    } as ReturnType<typeof usePlaylist>)

    renderDetailPage()

    const button = screen.getByRole("button", { name: "Rebuilding…" })
    expect(button).toBeDisabled()
    expect(button.querySelector('[data-testid="wheel-icon"]')).toHaveAttribute(
      "data-spinning",
      "true",
    )
  })

  it("renders the output list with episode titles", () => {
    renderDetailPage()
    expect(screen.getByText("The Pilot")).toBeInTheDocument()
    expect(screen.getByText("Episode Two")).toBeInTheDocument()
  })

  it("renders the unified playlist editor", () => {
    renderDetailPage()
    expect(screen.getByTestId("playlist-form")).toBeInTheDocument()
  })

  it("shows writeback status and open link", () => {
    renderDetailPage()
    expect(screen.getByText("Synced")).toBeInTheDocument()
    expect(screen.getByRole("link", { name: /Open in Plex/i })).toBeInTheDocument()
  })

  it("shows writeback partial summary without inline warning lists", () => {
    mockUsePlaylist.mockReturnValue({
      data: {
        ...MOCK_PLAYLIST,
        last_rebuild: {
          ...MOCK_PLAYLIST.last_rebuild!,
          writeback_status: "partial",
          writeback_warnings: [
            {
              episode_id: "ep-1",
              reason: "No metadata found for guid: plex://episode/abc",
            },
          ],
        },
      },
      isLoading: false,
      isError: false,
    } as ReturnType<typeof usePlaylist>)

    renderDetailPage()

    expect(screen.getByText("Partial sync")).toBeInTheDocument()
    expect(
      screen.getByText("Some episodes could not be synced to your media server."),
    ).toBeInTheDocument()
    expect(screen.queryByRole("list", { name: "Sync warnings" })).not.toBeInTheDocument()
    expect(screen.getByRole("button", { name: "View details" })).toBeInTheDocument()
  })

  it("shows succeeded writeback without inline sync notes list", () => {
    mockUsePlaylist.mockReturnValue({
      data: {
        ...MOCK_PLAYLIST,
        last_rebuild: {
          ...MOCK_PLAYLIST.last_rebuild!,
          writeback_status: "succeeded",
          writeback_warnings: [
            {
              episode_id: null,
              reason: "The linked Plex playlist was missing; a new one was created.",
            },
          ],
        },
      },
      isLoading: false,
      isError: false,
    } as ReturnType<typeof usePlaylist>)

    renderDetailPage()

    expect(screen.getByText("Synced")).toBeInTheDocument()
    expect(screen.queryByText("Partial sync")).not.toBeInTheDocument()
    expect(
      screen.queryByText("Some episodes could not be synced to your media server."),
    ).not.toBeInTheDocument()
    expect(screen.queryByRole("list", { name: "Sync notes" })).not.toBeInTheDocument()
    expect(screen.queryByRole("button", { name: "View details" })).not.toBeInTheDocument()
  })

  it("renders Delete button to trigger confirmation", () => {
    renderDetailPage()
    expect(screen.getByRole("button", { name: "Delete playlist" })).toBeInTheDocument()
  })

  it("renders Settings and rebuild actions in the header row", () => {
    renderDetailPage()
    expect(screen.getByRole("button", { name: "Playlist settings" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Rebuild" })).toBeInTheDocument()
    expect(screen.getByText("Last rebuild")).toBeInTheDocument()
    expect(screen.getByText("Plex Sync Status")).toBeInTheDocument()
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
