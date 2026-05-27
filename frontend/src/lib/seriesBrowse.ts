/** Library / playlist picker browse: maps to `GET .../series?sort=&order=`. */

export type SeriesBrowseMode = "title_asc" | "added_desc" | "added_asc"

export const SERIES_BROWSE_MODE_LABELS: Record<SeriesBrowseMode, string> = {
  title_asc: "Title (A-Z)",
  added_desc: "Date added (newest first)",
  added_asc: "Date added (oldest first)",
}

export function seriesBrowseModeToApiParams(mode: SeriesBrowseMode): {
  sort: "title" | "added_at"
  order: "asc" | "desc"
} {
  switch (mode) {
    case "title_asc":
      return { sort: "title", order: "asc" }
    case "added_desc":
      return { sort: "added_at", order: "desc" }
    case "added_asc":
      return { sort: "added_at", order: "asc" }
  }
}
