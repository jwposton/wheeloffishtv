import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { describe, expect, it, vi, beforeEach } from "vitest"

import type { PlaylistListItem } from "@/api/types"

vi.mock("@/api/playlists", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/playlists")>()
  return {
    ...actual,
    usePlaylists: vi.fn(),
    useAppendPlaylistRow: vi.fn(),
    createPlaylistWithSeries: vi.fn(),
  }
})

import {
  usePlaylists,
  useAppendPlaylistRow,
} from "@/api/playlists"
import { AddToPlaylistMenu } from "@/components/playlists/AddToPlaylistMenu"
import { QuickCreatePlaylistDialog } from "@/components/playlists/QuickCreatePlaylistDialog"

const mockUsePlaylists = vi.mocked(usePlaylists)
const mockUseAppendPlaylistRow = vi.mocked(useAppendPlaylistRow)

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

function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function renderMenu() {
  const queryClient = makeQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <AddToPlaylistMenu
          seriesId="series-abc"
          trigger={<button type="button">Open menu</button>}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function renderQuickCreate(open = true) {
  const queryClient = makeQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <QuickCreatePlaylistDialog
          seriesId="series-abc"
          open={open}
          onOpenChange={() => {}}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe("AddToPlaylistMenu", () => {
  beforeEach(() => {
    mockUsePlaylists.mockReturnValue({
      data: MOCK_PLAYLISTS,
      isLoading: false,
      isError: false,
    } as ReturnType<typeof usePlaylists>)
    mockUseAppendPlaylistRow.mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useAppendPlaylistRow>)
  })

  it("renders playlist names when menu is opened", async () => {
    renderMenu()

    fireEvent.click(screen.getByRole("button", { name: "Open menu" }))

    await waitFor(() => {
      expect(screen.getByText("Weeknight Mix")).toBeInTheDocument()
      expect(screen.getByText("Sci-Fi Marathon")).toBeInTheDocument()
    })
  })

  it('shows "Create new playlist…" action', async () => {
    renderMenu()

    fireEvent.click(screen.getByRole("button", { name: "Open menu" }))

    await waitFor(() => {
      expect(screen.getByText("Create new playlist…")).toBeInTheDocument()
    })
  })
})

describe("QuickCreatePlaylistDialog", () => {
  it("renders Create and add button", () => {
    renderQuickCreate()
    expect(screen.getByRole("button", { name: "Create and add" })).toBeInTheDocument()
  })

  it("Advanced link includes seriesId query param", () => {
    renderQuickCreate()
    const link = screen.getByRole("link", { name: /Advanced/i })
    expect(link.getAttribute("href")).toContain("seriesId=series-abc")
  })
})
