import type { Series } from "@/api/types"

import { SeriesCard } from "./SeriesCard"

interface SeriesListProps {
  items: Series[]
}

export function SeriesList({ items }: SeriesListProps) {
  return (
    <ul className="flex flex-col gap-2">
      {items.map((series) => (
        <li key={series.id}>
          <SeriesCard series={series} variant="list" />
        </li>
      ))}
    </ul>
  )
}
