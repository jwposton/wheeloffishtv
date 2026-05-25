import { fireEvent, render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { describe, expect, it, vi, beforeEach } from "vitest"

import type { Series } from "@/api/types"

const mockNavigate = vi.fn()

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router-dom")>()
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

vi.mock("@/components/playlists/AddToPlaylistMenu", () => ({
  AddToPlaylistMenu: ({
    trigger,
  }: {
    seriesId: string
    trigger: React.ReactElement
  }) => <div data-testid="add-to-playlist-menu">{trigger}</div>,
  AddToPlaylistContextMenuItems: () => null,
}))

import { SeriesCard } from "@/components/browse/SeriesCard"

const MOCK_SERIES: Series = {
  id: "series-1",
  title: "Test Show",
  native_id: "native-1",
  library_native_id: "lib-1",
  connection_id: "conn-1",
  provider: "plex",
  year: 2020,
  thumb_url: null,
  provider_metadata: null,
}

function renderCard(variant: "grid" | "list" = "grid") {
  return render(
    <MemoryRouter>
      <SeriesCard series={MOCK_SERIES} variant={variant} />
    </MemoryRouter>,
  )
}

describe("SeriesCard", () => {
  beforeEach(() => {
    mockNavigate.mockClear()
  })

  it("navigates to series detail when tile body is clicked", () => {
    renderCard()
    fireEvent.click(screen.getByText("Test Show"))
    expect(mockNavigate).toHaveBeenCalledWith("/series?id=series-1")
  })

  it("does not navigate when the more menu button is clicked", () => {
    renderCard()
    fireEvent.click(screen.getByRole("button", { name: "Series actions" }))
    expect(mockNavigate).not.toHaveBeenCalled()
  })

  it("renders a context menu trigger for right-click", () => {
    renderCard()
    expect(document.querySelector('[data-slot="context-menu-trigger"]')).toBeTruthy()
  })

  it("renders more menu on list variant without navigating", () => {
    renderCard("list")
    fireEvent.click(screen.getByRole("button", { name: "Series actions" }))
    expect(mockNavigate).not.toHaveBeenCalled()
  })
})
