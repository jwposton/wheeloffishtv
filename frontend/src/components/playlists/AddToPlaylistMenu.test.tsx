import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { describe, expect, it, vi, beforeEach } from "vitest"

import { ApiError } from "@/api/client"
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

vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    info: vi.fn(),
    error: vi.fn(),
  },
}))

import { toast } from "sonner"

import {
  usePlaylists,
  useAppendPlaylistRow,
} from "@/api/playlists"
import {
  AddToPlaylistContextMenuItems,
  AddToPlaylistMenu,
} from "@/components/playlists/AddToPlaylistMenu"
import { QuickCreatePlaylistDialog } from "@/components/playlists/QuickCreatePlaylistDialog"
import { Button } from "@/components/ui/button"
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuTrigger,
} from "@/components/ui/context-menu"

const mockUsePlaylists = vi.mocked(usePlaylists)
const mockUseAppendPlaylistRow = vi.mocked(useAppendPlaylistRow)
const mockMutateAsync = vi.fn()

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
          trigger={<Button type="button">Open menu</Button>}
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
    vi.clearAllMocks()
    mockUsePlaylists.mockReturnValue({
      data: MOCK_PLAYLISTS,
      isLoading: false,
      isError: false,
    } as ReturnType<typeof usePlaylists>)
    mockMutateAsync.mockResolvedValue({})
    mockUseAppendPlaylistRow.mockReturnValue({
      mutateAsync: mockMutateAsync,
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

  it("shows Advanced… link in dropdown when enabled", async () => {
    const queryClient = makeQueryClient()
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AddToPlaylistMenu
            seriesId="series-abc"
            showAdvancedLink
            trigger={<Button type="button">Open menu</Button>}
          />
        </MemoryRouter>
      </QueryClientProvider>,
    )

    fireEvent.click(screen.getByRole("button", { name: "Open menu" }))

    await waitFor(() => {
      expect(screen.getByText("Advanced…")).toBeInTheDocument()
    })
    const advanced = screen.getByText("Advanced…").closest("a")
    expect(advanced?.getAttribute("href")).toContain("seriesId=series-abc")
  })

  it("hides Advanced… on library menus by default", async () => {
    renderMenu()

    fireEvent.click(screen.getByRole("button", { name: "Open menu" }))

    await waitFor(() => {
      expect(screen.getByText("Weeknight Mix")).toBeInTheDocument()
    })
    expect(screen.queryByText("Advanced…")).not.toBeInTheDocument()
  })

  it("shows Advanced… in context menu variant when enabled", async () => {
    const queryClient = makeQueryClient()
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ContextMenu open>
            <ContextMenuTrigger render={<Button type="button">Tile</Button>} />
            <ContextMenuContent>
              <AddToPlaylistContextMenuItems seriesId="series-abc" showAdvancedLink />
            </ContextMenuContent>
          </ContextMenu>
        </MemoryRouter>
      </QueryClientProvider>,
    )

    await waitFor(() => {
      expect(screen.getByText("Advanced…")).toBeInTheDocument()
    })
    const advanced = screen.getByText("Advanced…").closest("a")
    expect(advanced?.getAttribute("href")).toContain("seriesId=series-abc")
  })

  it("reports duplicate append as info feedback instead of error toast", async () => {
    mockMutateAsync.mockRejectedValue(new ApiError("conflict", 409, { detail: "Row already exists" }))
    const onAppendFeedback = vi.fn()

    const queryClient = makeQueryClient()
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AddToPlaylistMenu
            seriesId="series-abc"
            onAppendFeedback={onAppendFeedback}
            trigger={<Button type="button">Open menu</Button>}
          />
        </MemoryRouter>
      </QueryClientProvider>,
    )

    fireEvent.click(screen.getByRole("button", { name: "Open menu" }))
    fireEvent.click(await screen.findByText("Weeknight Mix"))

    await waitFor(() => {
      expect(onAppendFeedback).toHaveBeenCalledWith({
        variant: "info",
        message: "Already in Weeknight Mix",
      })
    })
    expect(toast.error).not.toHaveBeenCalled()
  })

  it("falls back to corner toast when no poster feedback handler is provided", async () => {
    mockMutateAsync.mockRejectedValue(new ApiError("conflict", 409, { detail: "Row already exists" }))
    renderMenu()

    fireEvent.click(screen.getByRole("button", { name: "Open menu" }))
    fireEvent.click(await screen.findByText("Weeknight Mix"))

    await waitFor(() => {
      expect(toast.info).toHaveBeenCalledWith("Already in Weeknight Mix")
    })
    expect(toast.error).not.toHaveBeenCalled()
  })
})

describe("QuickCreatePlaylistDialog", () => {
  it("renders Create and add button", () => {
    renderQuickCreate()
    expect(screen.getByRole("button", { name: "Create and add" })).toBeInTheDocument()
  })

  it("Advanced link includes seriesId query param when enabled", () => {
    const queryClient = makeQueryClient()
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <QuickCreatePlaylistDialog
            seriesId="series-abc"
            open
            onOpenChange={() => {}}
            showAdvancedLink
          />
        </MemoryRouter>
      </QueryClientProvider>,
    )
    const link = screen.getByRole("link", { name: /Advanced/i })
    expect(link.getAttribute("href")).toContain("seriesId=series-abc")
  })

  it("hides Advanced link in quick create by default", () => {
    renderQuickCreate()
    expect(screen.queryByRole("link", { name: /Advanced/i })).not.toBeInTheDocument()
  })
})
