import { useQuery } from "@tanstack/react-query"

import { ApiError, fetchJson } from "@/api/client"
import type { ResumePreviewResponse } from "@/api/types"
import { seriesApiPath } from "@/lib/seriesId"

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
    seriesApiPath(connectionId, seriesId, "/resume"),
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
    retry: (failureCount, error) => {
      if (error instanceof ApiError && (error.status === 404 || error.status === 422)) {
        return false
      }
      return failureCount < 2
    },
  })
}
