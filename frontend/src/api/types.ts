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
