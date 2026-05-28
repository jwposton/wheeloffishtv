import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { beforeEach, describe, expect, it, vi } from "vitest"

import type { Episode, ResumePreviewResponse, Series } from "@/api/types"

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
  AddToPlaylistMenu: ({ trigger }: { trigger: React.ReactElement }) => (
    <div data-testid="add-to-playlist-menu">{trigger}</div>
  ),
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
  id: "conn-1:plex:series-spy",
  title: "Spy Show",
  native_id: "series-spy",
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

const EPISODES: Episode[] = [
  {
    id: "conn-1:plex:episode-101",
    title: "Pilot",
    season_index: 1,
    episode_index: 1,
    duration_ms: 1800000,
    percent_watched: 100,
    provider_marked_played: true,
    part_index: null,
    multipart_group_id: null,
    is_special: false,
    special_for_season: null,
  },
  {
    id: "conn-1:plex:episode-102",
    title: "Second Contact",
    season_index: 1,
    episode_index: 2,
    duration_ms: 1800000,
    percent_watched: 20,
    provider_marked_played: false,
    part_index: null,
    multipart_group_id: null,
    is_special: false,
    special_for_season: null,
  },
  {
    id: "conn-1:plex:episode-special",
    title: "Holiday Special",
    season_index: 0,
    episode_index: 1,
    duration_ms: 1800000,
    percent_watched: 0,
    provider_marked_played: false,
    part_index: null,
    multipart_group_id: null,
    is_special: true,
    special_for_season: null,
  },
]

function makeResume(): ResumePreviewResponse {
  return {
    series_id: MOCK_SERIES.id,
    episode_id: "conn-1:plex:episode-102",
    season_index: 1,
    episode_index: 2,
    percent_watched: 20,
    source: "on_deck",
    series_complete: false,
  }
}

function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function renderPage(search = "/series?id=conn-1%3Aplex%3Aseries-spy") {
  const queryClient = makeQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[search]}>
        <Routes>
          <Route path="/series" element={<SeriesDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe("SeriesDetailPage watch-state", () => {
  beforeEach(() => {
    mockUseAuth.mockReturnValue({
      user: { connection: { id: "conn-1" } },
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
      data: makeResume(),
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useSeriesResume>)

    mockUseSeriesEpisodes.mockReturnValue({
      data: { episodes: EPISODES },
      isLoading: false,
      isError: false,
      isFetching: false,
      isFetched: true,
    } as ReturnType<typeof useSeriesEpisodes>)
  })

  it("groups episodes by season and renders specials after numbered seasons", () => {
    renderPage()
    const headings = screen
      .getAllByRole("heading", { level: 3 })
      .map((element) => element.textContent)
    expect(headings).toEqual(["Season 1", "Specials"])
  })

  it("renders watched, on-deck, and unwatched status affordances", () => {
    renderPage()
    expect(screen.getByText("Watched")).toBeInTheDocument()
    expect(screen.getByText("On deck")).toBeInTheDocument()
    expect(screen.getByText("Unwatched")).toBeInTheDocument()
  })

  it("keeps one shared layout across library and playlist entry contexts", () => {
    const libraryRender = renderPage("/series?id=conn-1%3Aplex%3Aseries-spy")
    expect(screen.getByRole("link", { name: "Back to Library" })).toBeInTheDocument()
    libraryRender.unmount()

    const playlistViewRender = renderPage(
      "/series?id=conn-1%3Aplex%3Aseries-spy&origin=playlist-view&from=%2Fplaylists%2Fabc",
    )
    expect(screen.getByRole("link", { name: "Back to Library" })).toBeInTheDocument()
    playlistViewRender.unmount()

    renderPage(
      "/series?id=conn-1%3Aplex%3Aseries-spy&origin=playlist-edit&from=%2Fplaylists%2Fabc%2Fedit",
    )
    expect(screen.getByRole("link", { name: "Back to Playlist" })).toBeInTheDocument()

    expect(screen.getAllByText("Spy Show").length).toBeGreaterThanOrEqual(1)
  })
})
