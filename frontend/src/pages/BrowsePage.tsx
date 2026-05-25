import { useEffect, useMemo, useRef, useState } from "react"

import { BrowseToolbar } from "@/components/browse/BrowseToolbar"
import { SeriesGrid } from "@/components/browse/SeriesGrid"
import { SeriesList } from "@/components/browse/SeriesList"
import { SyncBanner } from "@/components/layout/SyncBanner"
import { Skeleton } from "@/components/ui/skeleton"
import { useAuth } from "@/hooks/useAuth"
import { useBrowseLayout } from "@/hooks/useBrowseLayout"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { useSeriesInfiniteQuery } from "@/hooks/useSeriesInfiniteQuery"

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
  const [searchInput, setSearchInput] = useState("")
  const debouncedQ = useDebouncedValue(searchInput, 300)
  const { layout, setLayout } = useBrowseLayout()
  const query = useSeriesInfiniteQuery(connectionId, debouncedQ)
  const sentinelRef = useRef<HTMLDivElement>(null)

  const items = useMemo(
    () => query.data?.pages.flatMap((page) => page.items) ?? [],
    [query.data?.pages],
  )
  const firstPage = query.data?.pages[0]
  const total = firstPage?.total ?? 0
  const sync = firstPage?.sync

  const { fetchNextPage, hasNextPage, isFetchingNextPage } = query

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

  const showInitialSkeleton = query.isLoading
  const showEmpty = !query.isLoading && total === 0

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-4">
      <div className="flex flex-col gap-1">
        <h2 className="text-xl font-semibold">Browse</h2>
        <p className="text-muted-foreground text-sm">
          Search and scroll through in-scope TV series.
        </p>
      </div>

      <SyncBanner sync={sync} />

      <BrowseToolbar
        searchValue={searchInput}
        onSearchValueChange={setSearchInput}
        layout={layout}
        onLayoutChange={setLayout}
      />

      {showInitialSkeleton ? (
        <BrowseSkeleton layout={layout} />
      ) : showEmpty ? (
        <div className="rounded-md border border-dashed p-8 text-center">
          <p className="font-medium">No series found</p>
          <p className="text-muted-foreground mt-1 text-sm">
            {debouncedQ
              ? "Try a different search term."
              : "Your in-scope libraries have no cached series yet."}
          </p>
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
