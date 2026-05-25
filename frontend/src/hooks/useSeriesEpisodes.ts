import { useQuery } from "@tanstack/react-query"

import { fetchJson } from "@/api/client"
import type { EpisodesListResponse } from "@/api/types"

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
    `/connections/${connectionId}/series/${encodeURIComponent(seriesId)}/episodes`,
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
  })
}
