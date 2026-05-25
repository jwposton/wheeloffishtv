import { GridIcon, ListIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import type { BrowseLayout } from "@/hooks/useBrowseLayout"

interface BrowseToolbarProps {
  searchValue: string
  onSearchValueChange: (value: string) => void
  layout: BrowseLayout
  onLayoutChange: (layout: BrowseLayout) => void
}

export function BrowseToolbar({
  searchValue,
  onSearchValueChange,
  layout,
  onLayoutChange,
}: BrowseToolbarProps) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <Input
        type="search"
        placeholder="Search series…"
        value={searchValue}
        onChange={(event) => onSearchValueChange(event.target.value)}
        className="max-w-md"
        aria-label="Search series"
      />
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
