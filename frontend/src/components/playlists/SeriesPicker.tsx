import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { XIcon } from "lucide-react"

import { fetchJson } from "@/api/client"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useAuth } from "@/hooks/useAuth"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import type { Series, SeriesBrowseResponse } from "@/api/types"

export interface SeriesRow {
  series_id: string
  series_title: string
  thumb_url: string | null
  mode: "ordered" | "disordered"
  completion_policy: "remove" | "restart" | "disordered"
}

interface SeriesPickerProps {
  rows: SeriesRow[]
  onAdd: (row: SeriesRow) => void
  onRemove: (seriesId: string) => void
  onUpdateRow?: (seriesId: string, updates: Partial<Pick<SeriesRow, "mode" | "completion_policy">>) => void
}

function useSeriesSearch(connectionId: string | undefined, q: string) {
  return useQuery({
    queryKey: ["series-picker", connectionId ?? "", q],
    queryFn: () => {
      const params = new URLSearchParams({ page: "1", limit: "20" })
      if (q) params.set("q", q)
      return fetchJson<SeriesBrowseResponse>(
        `/connections/${connectionId}/series?${params.toString()}`,
      )
    },
    enabled: Boolean(connectionId),
    staleTime: 30_000,
  })
}

function SeriesThumb({ thumbUrl, title }: { thumbUrl: string | null; title: string }) {
  if (!thumbUrl) {
    return (
      <div className="size-8 rounded bg-muted flex items-center justify-center shrink-0">
        <span className="text-xs text-muted-foreground">?</span>
      </div>
    )
  }
  return (
    <img
      src={thumbUrl}
      alt={title}
      className="size-8 rounded object-cover shrink-0"
      loading="lazy"
    />
  )
}

export function SeriesPicker({ rows, onAdd, onRemove, onUpdateRow }: SeriesPickerProps) {
  const { user } = useAuth()
  const connectionId = user?.connection?.id
  const [searchInput, setSearchInput] = useState("")
  const debouncedQ = useDebouncedValue(searchInput, 300)

  const { data, isLoading } = useSeriesSearch(connectionId, debouncedQ)
  const results: Series[] = data?.items ?? []

  const selectedIds = new Set(rows.map((r) => r.series_id))

  function handleAdd(series: Series) {
    if (selectedIds.has(series.id)) return
    onAdd({
      series_id: series.id,
      series_title: series.title,
      thumb_url: series.thumb_url,
      mode: "ordered",
      completion_policy: "remove",
    })
    setSearchInput("")
  }

  return (
    <div className="flex flex-col gap-3">
      {/* Selected rows */}
      {rows.length > 0 && (
        <ul className="flex flex-col gap-2">
          {rows.map((row) => (
            <li
              key={row.series_id}
              className="flex items-center gap-3 rounded-lg border bg-card px-3 py-2"
            >
              <SeriesThumb thumbUrl={row.thumb_url} title={row.series_title} />
              <span className="flex-1 truncate text-sm font-medium">
                {row.series_title}
              </span>

              {/* per-row ordered/disordered toggle */}
              {onUpdateRow && (
                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => onUpdateRow(row.series_id, { mode: "ordered" })}
                    className={`rounded px-2 py-0.5 text-xs transition-colors ${
                      row.mode === "ordered"
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-muted-foreground hover:bg-muted/80"
                    }`}
                  >
                    Ordered
                  </button>
                  <button
                    type="button"
                    onClick={() => onUpdateRow(row.series_id, { mode: "disordered" })}
                    className={`rounded px-2 py-0.5 text-xs transition-colors ${
                      row.mode === "disordered"
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-muted-foreground hover:bg-muted/80"
                    }`}
                  >
                    Random
                  </button>
                </div>
              )}

              {/* per-row completion policy override */}
              {onUpdateRow && (
                <select
                  aria-label="Completion policy"
                  value={row.completion_policy}
                  onChange={(e) =>
                    onUpdateRow(row.series_id, {
                      completion_policy: e.target.value as SeriesRow["completion_policy"],
                    })
                  }
                  className="h-7 rounded-lg border border-input bg-transparent px-2 py-0.5 text-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <option value="remove">Remove when done</option>
                  <option value="restart">Restart</option>
                  <option value="disordered">Switch to random</option>
                </select>
              )}

              <Button
                type="button"
                variant="ghost"
                size="icon-xs"
                onClick={() => onRemove(row.series_id)}
                aria-label={`Remove ${row.series_title}`}
              >
                <XIcon />
              </Button>
            </li>
          ))}
        </ul>
      )}

      {/* Search input */}
      <div className="relative">
        <Input
          type="text"
          placeholder="Search series…"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
        />
      </div>

      {/* Search results */}
      {searchInput.length > 0 && (
        <div className="flex flex-col gap-1 rounded-lg border bg-popover p-1 shadow-sm">
          {isLoading ? (
            <div className="flex flex-col gap-1 p-1">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-9 w-full" />
              ))}
            </div>
          ) : results.length === 0 ? (
            <p className="px-3 py-2 text-sm text-muted-foreground">No series found.</p>
          ) : (
            results.map((series) => {
              const alreadySelected = selectedIds.has(series.id)
              return (
                <button
                  key={series.id}
                  type="button"
                  disabled={alreadySelected}
                  onClick={() => handleAdd(series)}
                  className="flex items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <SeriesThumb thumbUrl={series.thumb_url} title={series.title} />
                  <span className="flex-1 truncate">{series.title}</span>
                  {alreadySelected && (
                    <span className="text-xs text-muted-foreground">Added</span>
                  )}
                </button>
              )
            })
          )}
        </div>
      )}
    </div>
  )
}
