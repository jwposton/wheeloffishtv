import { describe, expect, it, vi, beforeEach } from "vitest"

vi.mock("@/api/client", () => ({
  fetchJson: vi.fn(),
}))

import { fetchJson } from "@/api/client"
import {
  patchPlaylistRow,
  removePlaylistRow,
} from "@/api/playlists"

const mockFetchJson = vi.mocked(fetchJson)

const CONNECTION = "5d176728-53f0-4ce5-bfb1-69f593a63209"
const GUID = "643cbf9ec1962a0897b7f6dd"
const PLEX_SERIES_ID = `${CONNECTION}:plex:plex%3A%2F%2Fshow%2F${GUID}`
const PLAYLIST_ID = "pl-test-123"
const PLAIN_SERIES_ID = "conn-aaaa::plex::show-alpha"

describe("playlist row mutations", () => {
  beforeEach(() => {
    mockFetchJson.mockResolvedValue({} as never)
  })

  it("removePlaylistRow encodes composite Plex series IDs in the URL path", async () => {
    await removePlaylistRow(PLAYLIST_ID, PLEX_SERIES_ID)

    expect(mockFetchJson).toHaveBeenCalledWith(
      `/playlists/${PLAYLIST_ID}/rows/${encodeURIComponent(PLEX_SERIES_ID)}`,
      { method: "DELETE" },
    )
  })

  it("patchPlaylistRow encodes composite Plex series IDs in the URL path", async () => {
    await patchPlaylistRow(PLAYLIST_ID, PLEX_SERIES_ID, { mode: "disordered" })

    expect(mockFetchJson).toHaveBeenCalledWith(
      `/playlists/${PLAYLIST_ID}/rows/${encodeURIComponent(PLEX_SERIES_ID)}`,
      {
        method: "PATCH",
        body: JSON.stringify({ mode: "disordered" }),
      },
    )
  })

  it("removePlaylistRow encodes plain series IDs without breaking the path", async () => {
    await removePlaylistRow(PLAYLIST_ID, PLAIN_SERIES_ID)

    expect(mockFetchJson).toHaveBeenCalledWith(
      `/playlists/${PLAYLIST_ID}/rows/${encodeURIComponent(PLAIN_SERIES_ID)}`,
      { method: "DELETE" },
    )
  })
})
