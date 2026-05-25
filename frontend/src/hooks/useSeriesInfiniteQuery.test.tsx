import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { renderHook, waitFor } from "@testing-library/react"
import type { ReactNode } from "react"
import { beforeEach, describe, expect, it, vi } from "vitest"

import type { SeriesBrowseResponse } from "@/api/types"

import {
  getNextSeriesPageParam,
  useSeriesInfiniteQuery,
} from "./useSeriesInfiniteQuery"

vi.mock("@/api/client", () => ({
  fetchJson: vi.fn(),
}))

import { fetchJson } from "@/api/client"

const mockFetchJson = vi.mocked(fetchJson)

const idleSync: SeriesBrowseResponse["sync"] = {
  status: "idle",
  progress_pct: null,
  library_native_id: null,
  error_message: null,
}

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })

  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )
  }
}

describe("getNextSeriesPageParam", () => {
  it("returns page+1 while page*limit less than total", () => {
    const page: SeriesBrowseResponse = {
      items: [],
      page: 1,
      limit: 50,
      total: 120,
      sync: idleSync,
    }

    expect(getNextSeriesPageParam(page)).toBe(2)
  })

  it("returns undefined when all pages fetched", () => {
    const page: SeriesBrowseResponse = {
      items: [],
      page: 2,
      limit: 50,
      total: 100,
      sync: idleSync,
    }

    expect(getNextSeriesPageParam(page)).toBeUndefined()
  })
})

describe("useSeriesInfiniteQuery", () => {
  beforeEach(() => {
    mockFetchJson.mockReset()
  })

  it("changing debounced q resets to page 1 via queryKey change", async () => {
    mockFetchJson.mockImplementation(async (path: string) => {
      if (path.includes("q=bat")) {
        return {
          items: [
            {
              id: "conn-1:plex:bat",
              title: "Batman",
              native_id: "bat",
              library_native_id: "lib-1",
              connection_id: "conn-1",
              provider: "plex",
              year: null,
              thumb_url: null,
              provider_metadata: null,
            },
          ],
          page: 1,
          limit: 50,
          total: 1,
          sync: idleSync,
        } satisfies SeriesBrowseResponse
      }

      return {
        items: [
          {
            id: "conn-1:plex:alpha",
            title: "Alpha",
            native_id: "alpha",
            library_native_id: "lib-1",
            connection_id: "conn-1",
            provider: "plex",
            year: null,
            thumb_url: null,
            provider_metadata: null,
          },
        ],
        page: 1,
        limit: 50,
        total: 1,
        sync: idleSync,
      } satisfies SeriesBrowseResponse
    })

    const wrapper = createWrapper()
    const { result, rerender } = renderHook(
      ({ q }) => useSeriesInfiniteQuery("conn-1", q),
      { wrapper, initialProps: { q: "" } },
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.pages[0]?.items[0]?.title).toBe("Alpha")

    rerender({ q: "bat" })

    await waitFor(() =>
      expect(result.current.data?.pages[0]?.items[0]?.title).toBe("Batman"),
    )

    const pageOneCalls = mockFetchJson.mock.calls.filter(([path]) =>
      String(path).includes("page=1"),
    )
    expect(pageOneCalls.length).toBeGreaterThanOrEqual(2)
  })
})
