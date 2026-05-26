import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { fetchJson } from "@/api/client"
import type { PlaylistListItem, RebuildStatus, RefreshCadence, WritebackStatus } from "@/api/types"

const WEEKDAY_NAMES = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
] as const

// ── Extra domain types ─────────────────────────────────────────────────────

export type RowMode = "ordered" | "disordered"
export type CompletionPolicy = "remove" | "restart" | "disordered"
export type SlotAllocation = "wild" | "balanced" | "round_robin"

export const SLOT_ALLOCATION_LABELS: Record<SlotAllocation, string> = {
  wild: "Wild",
  balanced: "Balanced",
  round_robin: "Round-robin",
}

export interface SnapshotEpisode {
  episode_id: string
  title: string
  series_id: string
  series_title: string | null
  slot_index: number
  row_mode: string
}

export interface PlaylistSeriesRowResponse {
  series_id: string
  mode: RowMode
  completion_policy: CompletionPolicy
  completion_event: string
  series_title: string | null
  thumb_url: string | null
}

export interface RebuildRunSummary {
  id: string
  status: string
  started_at: string | null
  finished_at: string | null
  error_message: string | null
  slots_filled: number | null
  slots_requested: number | null
  writeback_status?: WritebackStatus
  writeback_error?: string | null
  writeback_warnings?: Array<{ episode_id?: string | null; reason?: string }> | null
  writeback_at?: string | null
}

export interface PlaylistDetailResponse {
  id: string
  name: string
  episode_count: number
  slot_allocation: SlotAllocation
  default_completion_policy: CompletionPolicy
  refresh_cadence: RefreshCadence
  refresh_day_of_week: number | null
  rows: PlaylistSeriesRowResponse[]
  current_snapshot: SnapshotEpisode[]
  last_rebuild: RebuildRunSummary | null
  recent_runs: RebuildRunSummary[]
  provider_playlist_id?: string | null
  provider_kind?: string | null
  provider_playlist_open_url?: string | null
}

export interface PlaylistSeriesRowPayload {
  series_id: string
  mode: RowMode
  completion_policy: CompletionPolicy
}

export interface PlaylistCreatePayload {
  name: string
  episode_count: number
  slot_allocation: SlotAllocation
  default_completion_policy: CompletionPolicy
  refresh_cadence: RefreshCadence
  refresh_day_of_week: number | null
  rows: PlaylistSeriesRowPayload[]
}

export type PlaylistUpdatePayload = Partial<PlaylistCreatePayload>

// ── Fetch functions ────────────────────────────────────────────────────────

export async function fetchPlaylists(seriesId?: string): Promise<PlaylistListItem[]> {
  const query = seriesId
    ? `?series_id=${encodeURIComponent(seriesId)}`
    : ""
  return fetchJson<PlaylistListItem[]>(`/playlists${query}`)
}

export async function fetchPlaylist(id: string): Promise<PlaylistDetailResponse> {
  return fetchJson<PlaylistDetailResponse>(`/playlists/${id}`)
}

export async function createPlaylist(payload: PlaylistCreatePayload): Promise<PlaylistDetailResponse> {
  return fetchJson<PlaylistDetailResponse>("/playlists", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export async function updatePlaylist(id: string, payload: PlaylistUpdatePayload): Promise<PlaylistDetailResponse> {
  return fetchJson<PlaylistDetailResponse>(`/playlists/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  })
}

export async function deletePlaylist(id: string): Promise<void> {
  await fetchJson<void>(`/playlists/${id}`, { method: "DELETE" })
}

export async function triggerRebuild(id: string): Promise<RebuildRunSummary> {
  return fetchJson<RebuildRunSummary>(`/playlists/${id}/rebuild`, { method: "POST" })
}

export interface AppendPlaylistRowPayload {
  series_id: string
  mode?: RowMode
  completion_policy?: CompletionPolicy
}

export async function appendPlaylistRow(
  playlistId: string,
  payload: AppendPlaylistRowPayload,
): Promise<PlaylistDetailResponse> {
  return fetchJson<PlaylistDetailResponse>(`/playlists/${playlistId}/rows`, {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export interface PatchPlaylistRowPayload {
  mode?: RowMode
  completion_policy?: CompletionPolicy
}

export async function removePlaylistRow(
  playlistId: string,
  seriesId: string,
): Promise<void> {
  await fetchJson<void>(
    `/playlists/${playlistId}/rows/${encodeURIComponent(seriesId)}`,
    { method: "DELETE" },
  )
}

export async function patchPlaylistRow(
  playlistId: string,
  seriesId: string,
  payload: PatchPlaylistRowPayload,
): Promise<PlaylistDetailResponse> {
  return fetchJson<PlaylistDetailResponse>(
    `/playlists/${playlistId}/rows/${encodeURIComponent(seriesId)}`,
    { method: "PATCH", body: JSON.stringify(payload) },
  )
}

export async function createPlaylistWithSeries(
  name: string,
  seriesId: string,
): Promise<PlaylistDetailResponse> {
  return createPlaylist({
    name: name.trim(),
    episode_count: 20,
    slot_allocation: "wild",
    default_completion_policy: "remove",
    refresh_cadence: "daily",
    refresh_day_of_week: null,
    rows: [
      {
        series_id: seriesId,
        mode: "ordered",
        completion_policy: "remove",
      },
    ],
  })
}

// ── Query hooks ────────────────────────────────────────────────────────────

export function usePlaylists() {
  return useQuery({
    queryKey: ["playlists", "list"],
    queryFn: () => fetchPlaylists(),
    staleTime: 30_000,
  })
}

export function usePlaylistsContainingSeries(seriesId: string | undefined) {
  return useQuery({
    queryKey: ["playlists", "containing", seriesId],
    queryFn: () => fetchPlaylists(seriesId!),
    enabled: Boolean(seriesId),
    staleTime: 30_000,
  })
}

const POLLING_STATUSES: RebuildStatus[] = ["running", "queued"]

export function usePlaylist(id: string) {
  return useQuery({
    queryKey: ["playlists", id],
    queryFn: () => fetchPlaylist(id),
    staleTime: 5_000,
    refetchInterval: (query) => {
      const status = query.state.data?.last_rebuild?.status as RebuildStatus | undefined
      return status && POLLING_STATUSES.includes(status) ? 5_000 : false
    },
  })
}

// ── Mutation hooks ─────────────────────────────────────────────────────────

export function useCreatePlaylist() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createPlaylist,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["playlists"] })
    },
  })
}

export function useUpdatePlaylist() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: PlaylistUpdatePayload }) =>
      updatePlaylist(id, payload),
    onSuccess: (_data, { id }) => {
      void queryClient.invalidateQueries({ queryKey: ["playlists"] })
      void queryClient.invalidateQueries({ queryKey: ["playlists", id] })
    },
  })
}

export function useDeletePlaylist() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deletePlaylist,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["playlists"] })
    },
  })
}

export function useRebuildPlaylist() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: triggerRebuild,
    onSuccess: (_data, id) => {
      void queryClient.invalidateQueries({ queryKey: ["playlists", id] })
    },
  })
}

export function useAppendPlaylistRow() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      playlistId,
      payload,
    }: {
      playlistId: string
      payload: AppendPlaylistRowPayload
    }) => appendPlaylistRow(playlistId, payload),
    onSuccess: (_data, { playlistId }) => {
      void queryClient.invalidateQueries({ queryKey: ["playlists", playlistId] })
      void queryClient.invalidateQueries({ queryKey: ["playlists"] })
    },
  })
}

export function useRemovePlaylistRow() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      playlistId,
      seriesId,
    }: {
      playlistId: string
      seriesId: string
    }) => removePlaylistRow(playlistId, seriesId),
    onSuccess: (_data, { playlistId }) => {
      void queryClient.invalidateQueries({ queryKey: ["playlists", playlistId] })
      void queryClient.invalidateQueries({ queryKey: ["playlists"] })
    },
  })
}

export function usePatchPlaylistRow() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      playlistId,
      seriesId,
      payload,
    }: {
      playlistId: string
      seriesId: string
      payload: PatchPlaylistRowPayload
    }) => patchPlaylistRow(playlistId, seriesId, payload),
    onSuccess: (_data, { playlistId }) => {
      void queryClient.invalidateQueries({ queryKey: ["playlists", playlistId] })
      void queryClient.invalidateQueries({ queryKey: ["playlists"] })
    },
  })
}

// ── Formatters ─────────────────────────────────────────────────────────────

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
