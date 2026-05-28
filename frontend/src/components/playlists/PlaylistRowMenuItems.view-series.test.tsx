import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { useState } from "react"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { PlaylistRowMenuItems } from "@/components/playlists/PlaylistRowMenuItems"
import type { SeriesRow } from "@/components/playlists/RowSettingsSheet"
import { TwoPanePicker } from "@/components/playlists/TwoPanePicker"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

const navigateMock = vi.fn()

const INITIAL_ROWS: SeriesRow[] = [
  {
    series_id: "series-existing",
    series_title: "Existing Show",
    thumb_url: null,
    mode: "ordered",
    completion_policy: "remove",
  },
]

const appendMutateAsyncMock = vi.fn().mockImplementation(async () => ({
  rows: [
    ...INITIAL_ROWS.map((row) => ({
      series_id: row.series_id,
      mode: row.mode,
      completion_policy: row.completion_policy,
      completion_event: "series_complete" as const,
      series_title: row.series_title,
      thumb_url: row.thumb_url,
    })),
    {
      series_id: "series-new",
      mode: "ordered" as const,
      completion_policy: "remove" as const,
      completion_event: "series_complete" as const,
      series_title: "Brand New Show",
      thumb_url: null,
    },
  ],
}))

const queryItems = [
  {
    id: "series-new",
    title: "Brand New Show",
    thumb_url: null,
  },
]

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router-dom")>()
  return {
    ...actual,
    useNavigate: () => navigateMock,
  }
})

vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => ({
    user: { connection: { id: "conn-1" } },
    isLoading: false,
    isError: false,
  }),
}))

vi.mock("@/hooks/useSeriesInfiniteQuery", () => ({
  useSeriesInfiniteQuery: () => ({
    data: { pages: [{ items: queryItems, total: 1, page: 1, limit: 50 }] },
    isLoading: false,
    isFetchingNextPage: false,
    hasNextPage: false,
    fetchNextPage: vi.fn(),
  }),
}))

vi.mock("@/api/playlists", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/playlists")>()
  return {
    ...actual,
    useAppendPlaylistRow: () => ({ mutateAsync: appendMutateAsyncMock, isPending: false }),
    useRemovePlaylistRow: () => ({ mutateAsync: vi.fn(), isPending: false }),
    usePatchPlaylistRow: () => ({ mutateAsync: vi.fn(), isPending: false }),
  }
})

const MENU_ROW: SeriesRow = {
  series_id: "series-1",
  series_title: "Existing Show",
  thumb_url: null,
  mode: "ordered",
  completion_policy: "remove",
}

function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function MenuHarness({ onViewSeries }: { onViewSeries: (seriesId: string) => void }) {
  return (
    <DropdownMenu defaultOpen>
      <DropdownMenuTrigger render={<Button type="button">Open</Button>} />
      <DropdownMenuContent>
        <PlaylistRowMenuItems
          row={MENU_ROW}
          variant="dropdown"
          onModeChange={vi.fn()}
          onPolicyChange={vi.fn()}
          onRemoveRequest={vi.fn()}
          onViewSeries={onViewSeries}
        />
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

function TwoPaneHarness() {
  const [rows, setRows] = useState<SeriesRow[]>(INITIAL_ROWS)
  return <TwoPanePicker rows={rows} onRowsChange={setRows} playlistId="playlist-123" />
}

describe("Playlist row view-series parity", () => {
  beforeEach(() => {
    navigateMock.mockReset()
    appendMutateAsyncMock.mockClear()
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
    vi.stubGlobal("scrollTo", vi.fn())
  })

  it("renders view series action and forwards series id", async () => {
    const onViewSeries = vi.fn()

    render(<MenuHarness onViewSeries={onViewSeries} />)

    const viewSeries = await screen.findByText("View series")
    fireEvent.click(viewSeries)

    expect(onViewSeries).toHaveBeenCalledWith("series-1")
  })

  it("keeps click-to-add and surfaces new rows first with marker", async () => {
    const queryClient = makeQueryClient()

    render(
      <QueryClientProvider client={queryClient}>
        <TwoPaneHarness />
      </QueryClientProvider>,
    )

    fireEvent.click(screen.getByRole("tab", { name: "Add shows" }))
    fireEvent.click((await screen.findAllByText("Brand New Show"))[0]!)

    await waitFor(() =>
      expect(appendMutateAsyncMock).toHaveBeenCalledWith({
        playlistId: "playlist-123",
        payload: { series_id: "series-new" },
      }),
    )
    expect(await screen.findByText("New")).toBeInTheDocument()
    await waitFor(() => expect(window.scrollTo).toHaveBeenCalled())

    const posterLabels = screen.getAllByLabelText(/Show/)
    expect(posterLabels[0]?.getAttribute("aria-label")).toContain("Brand New Show")
  })

  it("navigates view series with playlist-edit origin metadata", async () => {
    const queryClient = makeQueryClient()

    render(
      <QueryClientProvider client={queryClient}>
        <TwoPaneHarness />
      </QueryClientProvider>,
    )

    fireEvent.click((await screen.findAllByRole("button", { name: "Series actions" }))[0]!)
    fireEvent.click(await screen.findByText("View series"))

    expect(navigateMock).toHaveBeenCalledWith(
      "/series?id=series-existing&origin=playlist-edit&from=%2Fplaylists%2Fplaylist-123",
    )
  })
})
