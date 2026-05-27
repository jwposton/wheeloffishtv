import { GridIcon, ListIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import type { BrowseLayout } from "@/hooks/useBrowseLayout"
import {
  SERIES_BROWSE_MODE_LABELS,
  type SeriesBrowseMode,
} from "@/lib/seriesBrowse"

interface BrowseToolbarProps {
  searchValue: string
  onSearchValueChange: (value: string) => void
  layout: BrowseLayout
  onLayoutChange: (layout: BrowseLayout) => void
  browseMode: SeriesBrowseMode
  onBrowseModeChange: (mode: SeriesBrowseMode) => void
}

export function BrowseToolbar({
  searchValue,
  onSearchValueChange,
  layout,
  onLayoutChange,
  browseMode,
  onBrowseModeChange,
}: BrowseToolbarProps) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end sm:justify-between">
      <div className="flex max-w-full flex-col gap-3 sm:flex-row sm:items-end sm:gap-4">
        <Input
          type="search"
          placeholder="Search series…"
          value={searchValue}
          onChange={(event) => onSearchValueChange(event.target.value)}
          className="max-w-md"
          aria-label="Search series"
        />
        <div className="flex min-w-0 flex-col gap-1 sm:w-56">
          <Label htmlFor="library-sort">Sort</Label>
          <select
            id="library-sort"
            value={browseMode}
            onChange={(event) =>
              onBrowseModeChange(event.target.value as SeriesBrowseMode)
            }
            className="h-10 w-full rounded-md border border-input bg-transparent px-2.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            aria-label="Sort series list"
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
      </div>
      <div className="flex items-center gap-1" role="group" aria-label="Layout">
        <Button
          type="button"
          variant={layout === "grid" ? "default" : "outline"}
          size="icon-sm"
          aria-pressed={layout === "grid"}
          aria-label="Grid layout"
          onClick={() => onLayoutChange("grid")}
        >
          <GridIcon />
        </Button>
        <Button
          type="button"
          variant={layout === "list" ? "default" : "outline"}
          size="icon-sm"
          aria-pressed={layout === "list"}
          aria-label="List layout"
          onClick={() => onLayoutChange("list")}
        >
          <ListIcon />
        </Button>
      </div>
    </div>
  )
}
