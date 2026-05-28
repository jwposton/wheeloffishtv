import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { fireEvent, render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { describe, expect, it, vi, beforeEach } from "vitest"

const mockUseSeriesInfiniteQuery = vi.fn()
const appendMutateAsync = vi.fn()
const removeMutateAsync = vi.fn()
const patchMutateAsync = vi.fn()

vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => ({
    user: { connection: { id: "conn-1" } },
    isLoading: false,
    isError: false,
  }),
}))

vi.mock("@/hooks/useSeriesInfiniteQuery", () => ({
  useSeriesInfiniteQuery: (...args: unknown[]) => mockUseSeriesInfiniteQuery(...args),
}))

vi.mock("@/api/playlists", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/playlists")>()
  return {
    ...actual,
    useAppendPlaylistRow: () => ({ mutateAsync: appendMutateAsync, isPending: false }),
    useRemovePlaylistRow: () => ({ mutateAsync: removeMutateAsync, isPending: false }),
    usePatchPlaylistRow: () => ({ mutateAsync: patchMutateAsync, isPending: false }),
  }
})

import { TwoPanePicker, type SeriesRow } from "@/components/playlists/TwoPanePicker"

const SAMPLE_ROW: SeriesRow = {
  series_id: "series-in-1",
  series_title: "In Playlist Show",
  thumb_url: null,
  mode: "ordered",
  completion_policy: "remove",
}

function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function renderPicker(rows: SeriesRow[] = []) {
  const queryClient = makeQueryClient()
  return render(
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>
        <TwoPanePicker rows={rows} onRowsChange={() => {}} />
      </QueryClientProvider>
    </MemoryRouter>,
  )
}

function renderPickerWithPlaylist(rows: SeriesRow[], onRowsChange: (rows: SeriesRow[]) => void) {
  const queryClient = makeQueryClient()
  return render(
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>
        <TwoPanePicker rows={rows} onRowsChange={onRowsChange} playlistId="playlist-123" />
      </QueryClientProvider>
    </MemoryRouter>,
  )
}

function renderPickerWithRows() {
  return renderPicker([SAMPLE_ROW])
}

describe("TwoPanePicker", () => {
  beforeEach(() => {
    appendMutateAsync.mockReset()
    removeMutateAsync.mockReset()
    patchMutateAsync.mockReset()
    mockUseSeriesInfiniteQuery.mockReturnValue({
      data: { pages: [{ items: [], total: 0, page: 1, limit: 50 }] },
      isLoading: false,
      isFetchingNextPage: false,
      hasNextPage: false,
      fetchNextPage: vi.fn(),
    })
    vi.stubGlobal(
      "matchMedia",
      vi.fn().mockImplementation(() => ({
        matches: false,
        media: "",
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    )
  })

  it("renders mobile tabs with In playlist and Add shows labels", () => {
    renderPicker()

    expect(screen.getAllByText(/In playlist \(0\)/).length).toBeGreaterThan(0)
    expect(screen.getByRole("tab", { name: "Add shows" })).toBeInTheDocument()
  })

  it("renders desktop layout wrapper with md:grid-cols-2", () => {
    renderPicker()

    const desktop = screen.getByTestId("two-pane-desktop")
    expect(desktop.className).toContain("md:grid-cols-2")
  })

  it("renders Available to add heading", () => {
    renderPicker()

    expect(screen.getAllByText("Available to add").length).toBeGreaterThan(0)
  })

  it("renders Series actions button on In-pane tiles", () => {
    renderPickerWithRows()

    expect(screen.getAllByRole("button", { name: "Series actions" }).length).toBeGreaterThan(0)
  })

  it("persists add/remove immediately when playlistId is set", async () => {
    const availableSeries = {
      id: "series-2",
      title: "Added Show",
      provider: "plex",
      provider_id: "plex://series/2",
      thumb_url: null,
      leaf_count: 12,
      viewed_leaf_count: 0,
      added_at: null,
      year: null,
    }
    mockUseSeriesInfiniteQuery.mockReturnValue({
      data: { pages: [{ items: [availableSeries], total: 1, page: 1, limit: 50 }] },
      isLoading: false,
      isFetchingNextPage: false,
      hasNextPage: false,
      fetchNextPage: vi.fn(),
    })

    appendMutateAsync.mockResolvedValue({
      rows: [
        {
          series_id: "series-in-1",
          mode: "ordered",
          completion_policy: "remove",
          completion_event: "series_complete",
          series_title: "In Playlist Show",
          thumb_url: null,
        },
        {
          series_id: "series-2",
          mode: "ordered",
          completion_policy: "remove",
          completion_event: "series_complete",
          series_title: "Added Show",
          thumb_url: null,
        },
      ],
    })

    const onRowsChange = vi.fn()
    renderPickerWithPlaylist([SAMPLE_ROW], onRowsChange)

    fireEvent.click(screen.getByRole("tab", { name: "Add shows" }))
    fireEvent.click(screen.getAllByRole("button", { name: /Added Show/ })[0]!)

    await vi.waitFor(() => {
      expect(appendMutateAsync).toHaveBeenCalledWith({
        playlistId: "playlist-123",
        payload: { series_id: "series-2" },
      })
    })
    expect(onRowsChange).toHaveBeenCalled()
  })

  it("stages add/remove locally when creating a playlist without playlistId", () => {
    const availableSeries = {
      id: "series-2",
      title: "Added Show",
      provider: "plex",
      provider_id: "plex://series/2",
      thumb_url: null,
      leaf_count: 12,
      viewed_leaf_count: 0,
      added_at: null,
      year: null,
    }
    mockUseSeriesInfiniteQuery.mockReturnValue({
      data: { pages: [{ items: [availableSeries], total: 1, page: 1, limit: 50 }] },
      isLoading: false,
      isFetchingNextPage: false,
      hasNextPage: false,
      fetchNextPage: vi.fn(),
    })

    const onRowsChange = vi.fn()
    const queryClient = makeQueryClient()
    render(
      <MemoryRouter>
        <QueryClientProvider client={queryClient}>
          <TwoPanePicker rows={[SAMPLE_ROW]} onRowsChange={onRowsChange} />
        </QueryClientProvider>
      </MemoryRouter>,
    )

    fireEvent.click(screen.getAllByRole("button", { name: /Added Show/ })[0]!)
    expect(onRowsChange).toHaveBeenCalledWith([
      SAMPLE_ROW,
      expect.objectContaining({ series_id: "series-2" }),
    ])
    expect(appendMutateAsync).not.toHaveBeenCalled()

    fireEvent.click(screen.getAllByRole("button", { name: "Series actions" })[0]!)
    fireEvent.click(screen.getAllByText("Remove from playlist")[0]!)
    expect(removeMutateAsync).not.toHaveBeenCalled()
    expect(patchMutateAsync).not.toHaveBeenCalled()
  })
})
