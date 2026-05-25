import { describe, expect, it } from "vitest"

import {
  connectionIdFromSeriesId,
  resolveSeriesId,
  seriesApiPath,
  seriesDetailRoute,
  seriesIdsEquivalent,
} from "@/lib/seriesId"

const CONNECTION = "5d176728-53f0-4ce5-bfb1-69f593a63209"
const GUID = "643cbf9ec1962a0897b7f6dd"
const SERIES_ID = `${CONNECTION}:plex:plex%3A%2F%2Fshow%2F${GUID}`

describe("seriesId", () => {
  it("extracts connection id from composite series id", () => {
    expect(connectionIdFromSeriesId(SERIES_ID)).toBe(CONNECTION)
  })

  it("builds query-param detail route", () => {
    expect(seriesDetailRoute(SERIES_ID)).toBe(
      `/series?id=${encodeURIComponent(SERIES_ID)}`,
    )
  })

  it("builds API path with single encoding", () => {
    expect(seriesApiPath(CONNECTION, SERIES_ID)).toBe(
      `/connections/${CONNECTION}/series/${encodeURIComponent(SERIES_ID)}`,
    )
    expect(seriesApiPath(CONNECTION, SERIES_ID, "/resume")).toBe(
      `/connections/${CONNECTION}/series/${encodeURIComponent(SERIES_ID)}/resume`,
    )
  })

  it("prefers query param over legacy path param", () => {
    const params = new URLSearchParams({ id: SERIES_ID })
    expect(resolveSeriesId(params, "legacy-id")).toBe(SERIES_ID)
    expect(resolveSeriesId(new URLSearchParams(), SERIES_ID)).toBe(SERIES_ID)
  })

  it("treats encoding variants as equivalent", () => {
    const decoded = `${CONNECTION}:plex:plex://show/${GUID}`
    expect(seriesIdsEquivalent(SERIES_ID, decoded)).toBe(true)
  })
})
