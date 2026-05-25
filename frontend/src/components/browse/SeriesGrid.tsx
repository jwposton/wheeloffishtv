import type { Series } from "@/api/types"

import { SeriesCard } from "./SeriesCard"

interface SeriesGridProps {
  items: Series[]
}

export function SeriesGrid({ items }: SeriesGridProps) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
      {items.map((series) => (
        <SeriesCard key={series.id} series={series} variant="grid" />
      ))}
    </div>
  )
}
