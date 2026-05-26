const API_BASE = "/api/v1"

export class ApiError extends Error {
  status: number
  body?: unknown

  constructor(message: string, status: number, body?: unknown) {
    super(message)
    this.name = "ApiError"
    this.status = status
    this.body = body
  }
}

export function getApiErrorStatus(error: unknown): number | undefined {
  if (error instanceof ApiError) {
    return error.status
  }
  if (typeof error === "object" && error !== null && "status" in error) {
    const status = (error as { status: unknown }).status
    if (typeof status === "number") {
      return status
    }
  }
  return undefined
}

export function getApiErrorDetail(error: unknown): string | undefined {
  if (!(error instanceof ApiError) || error.body == null || typeof error.body !== "object") {
    return undefined
  }
  const detail = (error.body as { detail?: unknown }).detail
  return typeof detail === "string" ? detail : undefined
}

/** True when append failed because the series is already on the playlist. */
export function isAlreadyInPlaylistError(error: unknown): boolean {
  if (getApiErrorStatus(error) === 409) {
    return true
  }
  const detail = getApiErrorDetail(error)
  return detail !== undefined && /already/i.test(detail)
}

export async function fetchJson<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const url = path.startsWith("/") ? `${API_BASE}${path}` : `${API_BASE}/${path}`
  const response = await fetch(url, {
    ...init,
    credentials: "include",
    cache: "no-store",
    headers: {
      Accept: "application/json",
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  })

  if (!response.ok) {
    let body: unknown
    try {
      body = await response.json()
    } catch {
      body = undefined
    }
    throw new ApiError(
      `Request failed: ${response.status} ${response.statusText}`,
      response.status,
      body,
    )
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}
