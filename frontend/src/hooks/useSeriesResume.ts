import { useQuery } from "@tanstack/react-query"

import { fetchJson } from "@/api/client"
import type { ResumePreviewResponse } from "@/api/types"

export function seriesResumeQueryKey(
  connectionId: string,
  seriesId: string,
) {
  return ["series-resume", connectionId, seriesId] as const
}

function fetchSeriesResume(
  connectionId: string,
  seriesId: string,
): Promise<ResumePreviewResponse> {
  return fetchJson<ResumePreviewResponse>(
    `/connections/${connectionId}/series/${encodeURIComponent(seriesId)}/resume`,
  )
}

export function useSeriesResume(
  connectionId: string | undefined,
  seriesId: string | undefined,
) {
  return useQuery({
    queryKey: seriesResumeQueryKey(connectionId ?? "", seriesId ?? ""),
    queryFn: () => fetchSeriesResume(connectionId!, seriesId!),
    enabled: Boolean(connectionId && seriesId),
    staleTime: 60_000,
  })
}
