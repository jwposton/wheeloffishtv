import { useQuery } from "@tanstack/react-query"

import { ApiError, fetchJson } from "@/api/client"
import type { EpisodesListResponse } from "@/api/types"
import { seriesApiPath } from "@/lib/seriesId"

export function seriesEpisodesQueryKey(
  connectionId: string,
  seriesId: string,
) {
  return ["series-episodes", connectionId, seriesId] as const
}

function fetchSeriesEpisodes(
  connectionId: string,
  seriesId: string,
): Promise<EpisodesListResponse> {
  return fetchJson<EpisodesListResponse>(
    seriesApiPath(connectionId, seriesId, "/episodes"),
  )
}

export function useSeriesEpisodes(
  connectionId: string | undefined,
  seriesId: string | undefined,
  enabled = true,
) {
  return useQuery({
    queryKey: seriesEpisodesQueryKey(connectionId ?? "", seriesId ?? ""),
    queryFn: () => fetchSeriesEpisodes(connectionId!, seriesId!),
    enabled: Boolean(connectionId && seriesId && enabled),
    staleTime: 60_000,
    retry: (failureCount, error) => {
      if (error instanceof ApiError && (error.status === 404 || error.status === 422)) {
        return false
      }
      return failureCount < 2
    },
  })
}
