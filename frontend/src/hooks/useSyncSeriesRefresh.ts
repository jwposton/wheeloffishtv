import { useQueryClient, type InfiniteData } from "@tanstack/react-query"
import { useEffect, useRef } from "react"

import {
  fetchSeriesPage,
  seriesQueryKey,
} from "@/hooks/useSeriesInfiniteQuery"
import type { SeriesBrowseResponse, SyncStatusEmbed } from "@/api/types"

const SYNC_POLL_MS = 5000

/** While sync is running, refresh page 1 periodically (includes sync status + new titles). */
export function useSyncSeriesRefresh(
  connectionId: string | undefined,
  debouncedQ: string,
  sync: SyncStatusEmbed | undefined,
) {
  const queryClient = useQueryClient()
  const prevSyncStatusRef = useRef<string | undefined>(undefined)

  useEffect(() => {
    if (!connectionId || sync?.status !== "running") {
      return
    }

    let cancelled = false

    const refreshPage1 = async () => {
      const page1 = await fetchSeriesPage(connectionId, 1, debouncedQ)
      if (cancelled) {
        return
      }
      queryClient.setQueryData<InfiniteData<SeriesBrowseResponse>>(
        seriesQueryKey(connectionId, debouncedQ),
        (current) => {
          if (!current) {
            return { pages: [page1], pageParams: [1] }
          }
          return {
            pages: [page1, ...current.pages.slice(1)],
            pageParams:
              current.pageParams.length > 0
                ? [1, ...current.pageParams.slice(1)]
                : [1],
          }
        },
      )
    }

    void refreshPage1()
    const timer = window.setInterval(() => {
      void refreshPage1()
    }, SYNC_POLL_MS)

    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [connectionId, debouncedQ, queryClient, sync?.status])

  useEffect(() => {
    if (!connectionId || !sync) {
      return
    }

    const previousStatus = prevSyncStatusRef.current
    prevSyncStatusRef.current = sync.status

    if (
      (sync.status === "complete" || sync.status === "failed") &&
      previousStatus === "running"
    ) {
      void queryClient.invalidateQueries({
        queryKey: seriesQueryKey(connectionId, debouncedQ),
      })
    }
  }, [connectionId, debouncedQ, queryClient, sync?.status])
}
