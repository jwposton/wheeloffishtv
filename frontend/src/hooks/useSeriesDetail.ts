import { useQuery, useQueryClient } from "@tanstack/react-query"

import { ApiError, fetchJson } from "@/api/client"
import type { Series, SeriesBrowseResponse } from "@/api/types"
import { seriesApiPath, seriesIdsEquivalent } from "@/lib/seriesId"

export function seriesDetailQueryKey(connectionId: string, seriesId: string) {
  return ["series-detail", connectionId, seriesId] as const
}

function findSeriesInBrowseCache(
  queryClient: ReturnType<typeof useQueryClient>,
  connectionId: string,
  seriesId: string,
): Series | undefined {
  const queries = queryClient.getQueriesData<{ pages: SeriesBrowseResponse[] }>({
    queryKey: ["series", connectionId],
  })

  for (const [, data] of queries) {
    const match = data?.pages
      .flatMap((page) => page.items)
      .find((series) => seriesIdsEquivalent(series.id, seriesId))
    if (match) {
      return match
    }
  }

  return undefined
}

function fetchSeriesDetail(
  connectionId: string,
  seriesId: string,
): Promise<Series> {
  return fetchJson<Series>(seriesApiPath(connectionId, seriesId))
}

export function useSeriesDetail(
  connectionId: string | undefined,
  seriesId: string | undefined,
  options?: { enabled?: boolean },
) {
  const queryClient = useQueryClient()
  const cached =
    connectionId && seriesId
      ? findSeriesInBrowseCache(queryClient, connectionId, seriesId)
      : undefined

  const ready = options?.enabled ?? true

  return useQuery({
    queryKey: seriesDetailQueryKey(connectionId ?? "", seriesId ?? ""),
    queryFn: () => fetchSeriesDetail(connectionId!, seriesId!),
    enabled: ready && Boolean(connectionId && seriesId),
    placeholderData: (previous) => previous ?? cached,
    staleTime: 60_000,
    retry: (failureCount, error) => {
      if (error instanceof ApiError && (error.status === 404 || error.status === 422)) {
        return false
      }
      return failureCount < 2
    },
  })
}
