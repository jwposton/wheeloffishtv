import { useEffect, useMemo, useRef, useState } from "react"
import { toast } from "sonner"
import { useNavigate } from "react-router-dom"

import type { Series } from "@/api/types"
import {
  type CompletionPolicy,
  type RowMode,
} from "@/api/playlists"
import { SeriesPoster } from "@/components/browse/SeriesPoster"
import { PlaylistMemberTile } from "@/components/playlists/PlaylistMemberTile"
import { type SeriesRow } from "@/components/playlists/RowSettingsSheet"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useAuth } from "@/hooks/useAuth"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { useSeriesInfiniteQuery } from "@/hooks/useSeriesInfiniteQuery"
import {
  SERIES_BROWSE_MODE_LABELS,
  type SeriesBrowseMode,
} from "@/lib/seriesBrowse"
import { cn } from "@/lib/utils"
import { seriesDetailRoute } from "@/lib/seriesId"

export type { SeriesRow }

interface TwoPanePickerProps {
  rows: SeriesRow[]
  onRowsChange: (rows: SeriesRow[]) => void
  playlistId?: string
  onRowMutationsPendingChange?: (pending: boolean) => void
  skipRemoveConfirm?: boolean
  onEnableSkipRemoveConfirm?: () => void
}

function InPlaylistPane({
  rows,
  newSeriesIds,
  onModeChange,
  onPolicyChange,
  onRemove,
  onViewSeries,
  skipRemoveConfirm,
  onEnableSkipRemoveConfirm,
}: {
  rows: SeriesRow[]
  newSeriesIds: Set<string>
  onModeChange: (row: SeriesRow, mode: RowMode) => void
  onPolicyChange: (row: SeriesRow, policy: CompletionPolicy) => void
  onRemove: (seriesId: string) => void
  onViewSeries: (seriesId: string) => void
  skipRemoveConfirm: boolean
  onEnableSkipRemoveConfirm: () => void
}) {
  if (rows.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No shows yet — pick from Available to add.
      </p>
    )
  }

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
      {rows.map((row) => (
        <PlaylistMemberTile
          key={row.series_id}
          row={row}
          onModeChange={(mode) => onModeChange(row, mode)}
          onPolicyChange={(policy) => onPolicyChange(row, policy)}
          onRemove={() => onRemove(row.series_id)}
          onViewSeries={onViewSeries}
          isNew={newSeriesIds.has(row.series_id)}
          skipRemoveConfirm={skipRemoveConfirm}
          onEnableSkipRemoveConfirm={onEnableSkipRemoveConfirm}
        />
      ))}
    </div>
  )
}

function AvailableTile({
  series,
  disabled,
  onAdd,
}: {
  series: Series
  disabled: boolean
  onAdd: (series: Series) => void
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={() => onAdd(series)}
      className={cn(
        "flex flex-col gap-2 rounded-md text-left transition-colors hover:bg-accent/40",
        "focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:outline-none",
        disabled && "cursor-not-allowed opacity-40 hover:bg-transparent",
      )}
    >
      <div className="aspect-[2/3] w-full overflow-hidden rounded-md border bg-white">
        <SeriesPoster title={series.title} thumbUrl={series.thumb_url} />
      </div>
      <span className="line-clamp-2 text-sm font-medium">{series.title}</span>
    </button>
  )
}

function TileGridSkeleton() {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
      {Array.from({ length: 6 }).map((_, index) => (
        <div key={index} className="flex flex-col gap-2">
          <Skeleton className="aspect-[2/3] w-full" />
          <Skeleton className="h-4 w-3/4" />
        </div>
      ))}
    </div>
  )
}

function AvailablePane({
  searchInput,
  onSearchInputChange,
  browseMode,
  onBrowseModeChange,
  catalogItems,
  selectedIds,
  isLoading,
  isFetchingNextPage,
  onAdd,
  sentinelRef,
}: {
  searchInput: string
  onSearchInputChange: (value: string) => void
  browseMode: SeriesBrowseMode
  onBrowseModeChange: (mode: SeriesBrowseMode) => void
  catalogItems: Series[]
  selectedIds: Set<string>
  isLoading: boolean
  isFetchingNextPage: boolean
  onAdd: (series: Series) => void
  sentinelRef: React.RefObject<HTMLDivElement | null>
}) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-col gap-1">
        <Label htmlFor="picker-library-sort">Sort</Label>
        <select
          id="picker-library-sort"
          value={browseMode}
          onChange={(event) =>
            onBrowseModeChange(event.target.value as SeriesBrowseMode)
          }
          className="h-10 w-full rounded-md border border-input bg-transparent px-2.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          aria-label="Sort available shows"
        >
          {(Object.keys(SERIES_BROWSE_MODE_LABELS) as SeriesBrowseMode[]).map(
            (key) => (
              <option key={key} value={key}>
                {SERIES_BROWSE_MODE_LABELS[key]}
              </option>
            ),
          )}
        </select>
      </div>
      <Input
        type="text"
        placeholder="Search series…"
        value={searchInput}
        onChange={(e) => onSearchInputChange(e.target.value)}
      />

      {isLoading && catalogItems.length === 0 ? (
        <TileGridSkeleton />
      ) : catalogItems.length === 0 ? (
        <p className="text-sm text-muted-foreground">No matching shows in your library.</p>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
            {catalogItems.map((series) => (
              <AvailableTile
                key={series.id}
                series={series}
                disabled={selectedIds.has(series.id)}
                onAdd={onAdd}
              />
            ))}
          </div>
          {isFetchingNextPage ? <TileGridSkeleton /> : null}
          <div ref={sentinelRef} aria-hidden className="h-1 w-full" />
        </>
      )}
    </div>
  )
}

export function TwoPanePicker({
  rows,
  onRowsChange,
  playlistId,
  onRowMutationsPendingChange,
  skipRemoveConfirm = false,
  onEnableSkipRemoveConfirm = () => {},
}: TwoPanePickerProps) {
  const navigate = useNavigate()
  const { user } = useAuth()
  const connectionId = user?.connection?.id
  const [searchInput, setSearchInput] = useState("")
  const [browseMode, setBrowseMode] = useState<SeriesBrowseMode>("title_asc")
  const [sessionNewSeriesIds, setSessionNewSeriesIds] = useState<Set<string>>(new Set())
  const [sessionNewSeriesOrder, setSessionNewSeriesOrder] = useState<string[]>([])
  const debouncedQ = useDebouncedValue(searchInput, 300)
  const sentinelRef = useRef<HTMLDivElement>(null)

  function preserveViewportAndFocus() {
    const scrollY = window.scrollY
    const active = document.activeElement as HTMLElement | null
    window.requestAnimationFrame(() => {
      window.scrollTo({ top: scrollY })
      active?.focus({ preventScroll: true })
    })
  }

  useEffect(() => {
    onRowMutationsPendingChange?.(false)
  }, [onRowMutationsPendingChange])

  const query = useSeriesInfiniteQuery(connectionId, debouncedQ, browseMode)
  const catalogItems = useMemo(
    () => query.data?.pages.flatMap((page) => page.items) ?? [],
    [query.data?.pages],
  )

  const selectedIds = useMemo(() => new Set(rows.map((row) => row.series_id)), [rows])

  const catalogById = useMemo(() => {
    const map = new Map<string, Series>()
    for (const item of catalogItems) {
      map.set(item.id, item)
    }
    return map
  }, [catalogItems])

  const displayRows = useMemo(
    () => {
      const mappedRows = rows.map((row) => {
        const catalog = catalogById.get(row.series_id)
        if (!catalog) {
          return row
        }
        return {
          ...row,
          series_title: catalog.title,
          thumb_url: row.thumb_url ?? catalog.thumb_url,
        }
      })
      return mappedRows.sort((a, b) => {
        const aIsNew = sessionNewSeriesIds.has(a.series_id)
        const bIsNew = sessionNewSeriesIds.has(b.series_id)
        if (aIsNew === bIsNew) {
          if (aIsNew) {
            return (
              sessionNewSeriesOrder.indexOf(a.series_id) -
              sessionNewSeriesOrder.indexOf(b.series_id)
            )
          }
          return a.series_title.localeCompare(b.series_title)
        }
        return aIsNew ? -1 : 1
      })
    },
    [rows, catalogById, sessionNewSeriesIds, sessionNewSeriesOrder],
  )

  useEffect(() => {
    const sentinel = sentinelRef.current
    if (!sentinel || !query.hasNextPage || query.isFetchingNextPage) {
      return
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          void query.fetchNextPage()
        }
      },
      { rootMargin: "240px" },
    )

    observer.observe(sentinel)
    return () => observer.disconnect()
  }, [query.fetchNextPage, query.hasNextPage, query.isFetchingNextPage])

  function handleAdd(series: Series) {
    if (selectedIds.has(series.id)) {
      return
    }

    const newRow: SeriesRow = {
      series_id: series.id,
      series_title: series.title,
      thumb_url: series.thumb_url,
      mode: "ordered",
      completion_policy: "remove",
    }

    onRowsChange([...rows, newRow])
    setSessionNewSeriesIds((previous) => new Set(previous).add(series.id))
    setSessionNewSeriesOrder((previous) =>
      previous.includes(series.id) ? previous : [...previous, series.id],
    )
    preserveViewportAndFocus()
    toast.success(`Added ${series.title}`)
  }

  function handleRemove(seriesId: string) {
    setSessionNewSeriesIds((previous) => {
      const next = new Set(previous)
      next.delete(seriesId)
      return next
    })
    setSessionNewSeriesOrder((previous) => previous.filter((id) => id !== seriesId))
    onRowsChange(rows.filter((row) => row.series_id !== seriesId))
    toast.success("Removed from playlist")
  }

  function handleSave(updatedRow: SeriesRow) {
    onRowsChange(
      rows.map((row) => (row.series_id === updatedRow.series_id ? updatedRow : row)),
    )
  }

  function handleModeChange(row: SeriesRow, mode: RowMode) {
    if (mode === row.mode) {
      return
    }
    void handleSave({ ...row, mode })
  }

  function handlePolicyChange(row: SeriesRow, policy: CompletionPolicy) {
    if (policy === row.completion_policy) {
      return
    }
    void handleSave({ ...row, completion_policy: policy })
  }

  function handleViewSeries(seriesId: string) {
    const returnTo = playlistId ? `/playlists/${playlistId}/edit` : "/playlists/create"
    navigate(
      `${seriesDetailRoute(seriesId)}&origin=playlist-edit&from=${encodeURIComponent(returnTo)}`,
    )
  }

  const inPane = (
    <div className="flex flex-col gap-3">
      <h4 className="text-sm font-medium">In playlist ({displayRows.length})</h4>
      <InPlaylistPane
        rows={displayRows}
        newSeriesIds={sessionNewSeriesIds}
        onModeChange={handleModeChange}
        onPolicyChange={handlePolicyChange}
        onRemove={(seriesId) => void handleRemove(seriesId)}
        onViewSeries={handleViewSeries}
        skipRemoveConfirm={skipRemoveConfirm}
        onEnableSkipRemoveConfirm={onEnableSkipRemoveConfirm}
      />
    </div>
  )

  const availablePane = (
    <div className="flex flex-col gap-3">
      <h4 className="text-sm font-medium">Available to add</h4>
      <AvailablePane
        searchInput={searchInput}
        onSearchInputChange={setSearchInput}
        browseMode={browseMode}
        onBrowseModeChange={setBrowseMode}
        catalogItems={catalogItems}
        selectedIds={selectedIds}
        isLoading={query.isLoading}
        isFetchingNextPage={query.isFetchingNextPage}
        onAdd={(series) => void handleAdd(series)}
        sentinelRef={sentinelRef}
      />
    </div>
  )

  return (
    <>
      <div className="md:hidden">
        <Tabs defaultValue="in">
          <TabsList>
            <TabsTrigger value="in">In playlist ({displayRows.length})</TabsTrigger>
            <TabsTrigger value="add">Add shows</TabsTrigger>
          </TabsList>
          <TabsContent value="in">{inPane}</TabsContent>
          <TabsContent value="add">{availablePane}</TabsContent>
        </Tabs>
      </div>

      <div
        data-testid="two-pane-desktop"
        className="hidden grid-cols-1 gap-8 md:grid md:grid-cols-2"
      >
        {inPane}
        {availablePane}
      </div>
    </>
  )
}
