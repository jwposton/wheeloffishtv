import { keepPreviousData, useInfiniteQuery } from "@tanstack/react-query"

import { fetchJson } from "@/api/client"
import type { SeriesBrowseResponse } from "@/api/types"
import {
  seriesBrowseModeToApiParams,
  type SeriesBrowseMode,
} from "@/lib/seriesBrowse"

export const SERIES_PAGE_LIMIT = 50

export function seriesQueryKey(
  connectionId: string,
  q: string,
  browseMode: SeriesBrowseMode,
) {
  return ["series", connectionId, q, browseMode] as const
}

export function getNextSeriesPageParam(
  lastPage: SeriesBrowseResponse,
): number | undefined {
  return lastPage.page * lastPage.limit < lastPage.total
    ? lastPage.page + 1
    : undefined
}

export function fetchSeriesPage(
  connectionId: string,
  page: number,
  q: string,
  browseMode: SeriesBrowseMode,
): Promise<SeriesBrowseResponse> {
  const { sort, order } = seriesBrowseModeToApiParams(browseMode)
  const params = new URLSearchParams({
    page: String(page),
    limit: String(SERIES_PAGE_LIMIT),
    sort,
    order,
  })
  if (q) {
    params.set("q", q)
  }
  return fetchJson<SeriesBrowseResponse>(
    `/connections/${connectionId}/series?${params.toString()}`,
  )
}

export function useSeriesInfiniteQuery(
  connectionId: string | undefined,
  debouncedQ: string,
  browseMode: SeriesBrowseMode = "title_asc",
) {
  return useInfiniteQuery({
    queryKey: seriesQueryKey(connectionId ?? "", debouncedQ, browseMode),
    queryFn: ({ pageParam }) =>
      fetchSeriesPage(connectionId!, pageParam as number, debouncedQ, browseMode),
    initialPageParam: 1,
    getNextPageParam: getNextSeriesPageParam,
    enabled: Boolean(connectionId),
    staleTime: 30_000,
    placeholderData: keepPreviousData,
  })
}
