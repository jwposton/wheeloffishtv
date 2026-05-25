export interface ConnectionSummary {
  id: string
  provider: string
  display_name: string
  base_url: string
}

export interface AuthMeResponse {
  app_user_id: string
  provider_user_id: string
  provider_username: string | null
  is_admin: boolean
  setup_mode: boolean
  connection: ConnectionSummary | null
  has_media_link: boolean
  libraries_scoped: boolean
}

export interface ProvidersMetaResponse {
  provider: string
  oauth_callback_base: string
}

export interface PlexOAuthStartResponse {
  pin_id: number
  auth_url: string
}

export interface JellyfinAuthResponse {
  status: string
  connection_id: string
  auth_token_present: boolean
}

export interface Library {
  id: string
  title: string
  native_id: string
  connection_id: string
  provider: string
  in_scope: boolean
}

export interface LibraryScopeUpdate {
  in_scope_library_native_ids: string[]
}

export interface LibraryScopeResponse {
  libraries: Library[]
}

export interface SyncStatusEmbed {
  status: string
  progress_pct: number | null
  library_native_id: string | null
  error_message: string | null
}

export interface Series {
  id: string
  title: string
  native_id: string
  library_native_id: string
  connection_id: string
  provider: string
  year: number | null
  thumb_url: string | null
  provider_metadata: Record<string, unknown> | null
}

export interface SeriesBrowseResponse {
  items: Series[]
  page: number
  limit: number
  total: number
  sync: SyncStatusEmbed
}

export type ResumeSource = "earliest_unfinished" | "on_deck"

export interface ResumePreviewResponse {
  series_id: string | null
  episode_id: string | null
  season_index: number | null
  episode_index: number | null
  percent_watched: number | null
  source: ResumeSource | null
  series_complete: boolean
}

export interface Episode {
  id: string
  title: string
  season_index: number
  episode_index: number
  duration_ms: number
  percent_watched: number
  provider_marked_played: boolean
  part_index: number | null
  multipart_group_id: string | null
  is_special: boolean
  special_for_season: number | null
}

export interface EpisodesListResponse {
  episodes: Episode[]
}
