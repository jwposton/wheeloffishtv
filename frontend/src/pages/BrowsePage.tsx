import { useEffect, useMemo, useRef, useState } from "react"
import { useQueryClient } from "@tanstack/react-query"

import { BrowseToolbar } from "@/components/browse/BrowseToolbar"
import { SeriesGrid } from "@/components/browse/SeriesGrid"
import { SeriesList } from "@/components/browse/SeriesList"
import { SyncBanner } from "@/components/layout/SyncBanner"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { fetchJson } from "@/api/client"
import { useAuth } from "@/hooks/useAuth"
import { useBrowseLayout } from "@/hooks/useBrowseLayout"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { useSeriesInfiniteQuery } from "@/hooks/useSeriesInfiniteQuery"
import { useSyncSeriesRefresh } from "@/hooks/useSyncSeriesRefresh"
import type { SeriesBrowseMode } from "@/lib/seriesBrowse"

function BrowseSkeleton({ layout }: { layout: "grid" | "list" }) {
  if (layout === "list") {
    return (
      <div className="flex flex-col gap-2">
        {Array.from({ length: 6 }).map((_, index) => (
          <Skeleton key={index} className="h-16 w-full" />
        ))}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
      {Array.from({ length: 10 }).map((_, index) => (
        <div key={index} className="flex flex-col gap-2">
          <Skeleton className="aspect-[2/3] w-full" />
          <Skeleton className="h-4 w-3/4" />
        </div>
      ))}
    </div>
  )
}

export function BrowsePage() {
  const { user } = useAuth()
  const connectionId = user?.connection?.id
  const queryClient = useQueryClient()
  const [searchInput, setSearchInput] = useState("")
  const [browseMode, setBrowseMode] = useState<SeriesBrowseMode>("title_asc")
  const debouncedQ = useDebouncedValue(searchInput, 300)
  const { layout, setLayout } = useBrowseLayout()
  const query = useSeriesInfiniteQuery(connectionId, debouncedQ, browseMode)
  const sentinelRef = useRef<HTMLDivElement>(null)

  const items = useMemo(
    () => query.data?.pages.flatMap((page) => page.items) ?? [],
    [query.data?.pages],
  )
  const firstPage = query.data?.pages[0]
  const total = firstPage?.total ?? 0
  const sync = firstPage?.sync
  const isSyncing = sync?.status === "running"

  useEffect(() => {
    if (!connectionId) {
      return
    }
    queryClient.removeQueries({
      predicate: (query) => {
        const key = query.queryKey
        if (key[0] === "series" && typeof key[1] === "string" && key[1] !== connectionId) {
          return true
        }
        if (
          (key[0] === "series-detail" ||
            key[0] === "series-resume" ||
            key[0] === "series-episodes") &&
          typeof key[1] === "string" &&
          key[1] !== connectionId
        ) {
          return true
        }
        return false
      },
    })
  }, [connectionId, queryClient])
  const syncFailed = sync?.status === "failed"

  useSyncSeriesRefresh(connectionId, debouncedQ, sync, browseMode)

  const { fetchNextPage, hasNextPage, isFetchingNextPage, refetch } = query
  const syncKickRef = useRef(false)

  useEffect(() => {
    if (!connectionId || syncKickRef.current || query.isLoading) {
      return
    }
    if (total > 0 || isSyncing) {
      return
    }
    syncKickRef.current = true
    void fetchJson(`/connections/${connectionId}/sync`, { method: "POST" }).then(
      () => refetch(),
    )
  }, [
    connectionId,
    query.isLoading,
    total,
    isSyncing,
    syncFailed,
    refetch,
  ])

  useEffect(() => {
    const sentinel = sentinelRef.current
    if (!sentinel || !hasNextPage || isFetchingNextPage) {
      return
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          void fetchNextPage()
        }
      },
      { rootMargin: "240px" },
    )

    observer.observe(sentinel)
    return () => observer.disconnect()
  }, [fetchNextPage, hasNextPage, isFetchingNextPage])

  const showInitialSkeleton = query.isLoading && items.length === 0
  const showSyncingEmpty = isSyncing && items.length === 0 && !syncFailed
  const showEmpty =
    !query.isLoading && total === 0 && !isSyncing

  const retrySync = async () => {
    if (!connectionId) {
      return
    }
    await fetchJson(`/connections/${connectionId}/sync`, { method: "POST" })
    await query.refetch()
  }

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-4">
      <div className="flex flex-col gap-1">
        <h2 className="text-2xl">Library</h2>
        <p className="text-sm text-muted-foreground">
          Search and scroll through in-scope TV series.
        </p>
      </div>

      <SyncBanner sync={sync} />

      <BrowseToolbar
        searchValue={searchInput}
        onSearchValueChange={setSearchInput}
        layout={layout}
        onLayoutChange={setLayout}
        browseMode={browseMode}
        onBrowseModeChange={setBrowseMode}
      />

      {showInitialSkeleton ? (
        <BrowseSkeleton layout={layout} />
      ) : showSyncingEmpty ? (
        <div className="wof-panel border-dashed p-8 text-center">
          <p className="font-heading text-lg">Importing shows from Plex</p>
          <p className="text-muted-foreground mt-1 text-sm">
            Titles appear here as they sync. If this takes more than a few
            minutes, use Retry sync below.
          </p>
          {connectionId ? (
            <Button type="button" className="mt-4" variant="outline" onClick={() => void retrySync()}>
              Retry sync
            </Button>
          ) : null}
        </div>
      ) : showEmpty ? (
        <div className="wof-panel border-dashed p-8 text-center">
          <p className="font-heading text-lg">No series found</p>
          <p className="text-muted-foreground mt-1 text-sm">
            {debouncedQ
              ? "Try a different search term."
              : syncFailed
                ? (sync?.error_message ??
                  "Library sync failed. Log out and reconnect your Plex account.")
                : "Your library has not synced yet. Refresh the page or use Retry sync."}
          </p>
          {!debouncedQ && connectionId && (syncFailed || showEmpty) ? (
            <Button type="button" className="mt-4" onClick={() => void retrySync()}>
              {syncFailed ? "Retry sync" : "Sync library"}
            </Button>
          ) : null}
        </div>
      ) : layout === "list" ? (
        <SeriesList items={items} />
      ) : (
        <SeriesGrid items={items} />
      )}

      {query.isFetchingNextPage ? (
        <div className="py-4">
          <BrowseSkeleton layout={layout} />
        </div>
      ) : null}

      <div ref={sentinelRef} aria-hidden className="h-1 w-full" />
    </div>
  )
}
