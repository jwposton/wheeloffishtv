import { useQuery } from "@tanstack/react-query"

import { fetchJson } from "@/api/client"
import type { PlaylistListItem, RefreshCadence } from "@/api/types"

const WEEKDAY_NAMES = [
  "Sunday",
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
] as const

export async function fetchPlaylists(): Promise<PlaylistListItem[]> {
  return fetchJson<PlaylistListItem[]>("/playlists")
}

export function usePlaylists() {
  return useQuery({
    queryKey: ["playlists", "list"],
    queryFn: fetchPlaylists,
    staleTime: 30_000,
  })
}

export function formatCadence(item: {
  refresh_cadence: RefreshCadence
  refresh_day_of_week: number | null
}): string {
  if (item.refresh_cadence === "daily") {
    return "Daily"
  }
  const dayName =
    item.refresh_day_of_week != null
      ? WEEKDAY_NAMES[item.refresh_day_of_week]
      : null
  return dayName ? `Weekly \u00b7 ${dayName}` : "Weekly"
}
