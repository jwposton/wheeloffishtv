import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { describe, expect, it, vi, beforeEach } from "vitest"

import type { Series } from "@/api/types"

vi.mock("@/hooks/useAuth", () => ({
  useAuth: vi.fn(),
}))

vi.mock("@/hooks/useSeriesDetail", () => ({
  useSeriesDetail: vi.fn(),
}))

vi.mock("@/hooks/useSeriesResume", () => ({
  useSeriesResume: vi.fn(),
}))

vi.mock("@/hooks/useSeriesEpisodes", () => ({
  useSeriesEpisodes: vi.fn(),
}))

vi.mock("@/components/playlists/AddToPlaylistMenu", () => ({
  AddToPlaylistMenu: ({
    trigger,
  }: {
    seriesId: string
    trigger: React.ReactElement
  }) => <div data-testid="add-to-playlist-menu">{trigger}</div>,
  AddToPlaylistContextMenuItems: () => null,
}))

vi.mock("@/components/series/SeriesPlaylistsSection", () => ({
  SeriesPlaylistsSection: () => <div data-testid="series-playlists-section" />,
}))

import { useAuth } from "@/hooks/useAuth"
import { useSeriesDetail } from "@/hooks/useSeriesDetail"
import { useSeriesEpisodes } from "@/hooks/useSeriesEpisodes"
import { useSeriesResume } from "@/hooks/useSeriesResume"

import { SeriesDetailPage } from "./SeriesDetailPage"

const mockUseAuth = vi.mocked(useAuth)
const mockUseSeriesDetail = vi.mocked(useSeriesDetail)
const mockUseSeriesResume = vi.mocked(useSeriesResume)
const mockUseSeriesEpisodes = vi.mocked(useSeriesEpisodes)

const MOCK_SERIES: Series = {
  id: "series-spy",
  title: "Spy Show",
  native_id: "native-spy",
  library_native_id: "lib-1",
  connection_id: "conn-1",
  provider: "plex",
  year: 2011,
  thumb_url: null,
  provider_metadata: {
    summary: "A spy show",
    genres: ["Action"],
    contentRating: "TV-MA",
    studio: "HBO",
  },
}

function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function renderDetailPage(seriesId = "series-spy") {
  const queryClient = makeQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/series?id=${seriesId}`]}>
        <Routes>
          <Route path="/series" element={<SeriesDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe("SeriesDetailPage", () => {
  beforeEach(() => {
    mockUseAuth.mockReturnValue({
      user: {
        connection: { id: "conn-1" },
      },
      isLoading: false,
    } as ReturnType<typeof useAuth>)

    mockUseSeriesDetail.mockReturnValue({
      data: MOCK_SERIES,
      isLoading: false,
      isError: false,
      isFetching: false,
      isFetched: true,
    } as ReturnType<typeof useSeriesDetail>)

    mockUseSeriesResume.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useSeriesResume>)

    mockUseSeriesEpisodes.mockReturnValue({
      data: undefined,
      isLoading: false,
    } as ReturnType<typeof useSeriesEpisodes>)
  })

  it("test_renders_metadata", () => {
    renderDetailPage()
    expect(screen.getByText("A spy show")).toBeInTheDocument()
    expect(screen.getByText("Action")).toBeInTheDocument()
  })

  it("renders Add to playlist button", () => {
    renderDetailPage()
    expect(
      screen.getByRole("button", { name: "Add to playlist" }),
    ).toBeInTheDocument()
  })

  it('renders "Back to Library" link', () => {
    renderDetailPage()
    expect(screen.getByRole("link", { name: /Back to Library/i })).toBeInTheDocument()
  })
})
