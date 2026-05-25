import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen } from "@testing-library/react"
import { describe, expect, it, vi, beforeEach } from "vitest"

vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => ({
    user: { connection: { id: "conn-1" } },
    isLoading: false,
    isError: false,
  }),
}))

vi.mock("@/hooks/useSeriesInfiniteQuery", () => ({
  useSeriesInfiniteQuery: () => ({
    data: { pages: [{ items: [], total: 0, page: 1, limit: 50 }] },
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
    useAppendPlaylistRow: () => ({ mutateAsync: vi.fn(), isPending: false }),
    useRemovePlaylistRow: () => ({ mutateAsync: vi.fn(), isPending: false }),
    usePatchPlaylistRow: () => ({ mutateAsync: vi.fn(), isPending: false }),
  }
})

import { TwoPanePicker } from "@/components/playlists/TwoPanePicker"

function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function renderPicker() {
  const queryClient = makeQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      <TwoPanePicker rows={[]} onRowsChange={() => {}} />
    </QueryClientProvider>,
  )
}

describe("TwoPanePicker", () => {
  beforeEach(() => {
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
})
