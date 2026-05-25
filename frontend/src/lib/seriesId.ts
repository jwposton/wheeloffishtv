/** Helpers for composite series IDs ({connection}:{provider}:{native}). */

export function connectionIdFromSeriesId(seriesId: string): string | null {
  const separator = seriesId.indexOf(":")
  if (separator <= 0) {
    return null
  }
  return seriesId.slice(0, separator)
}

/** Plex show ids end with a 24-char hex guid — stable across encoding variants. */
export function seriesIdFingerprint(seriesId: string): string {
  const match = seriesId.match(/([a-f0-9]{24})$/i)
  return match?.[1] ?? seriesId
}

export function seriesIdsEquivalent(a: string, b: string): boolean {
  if (a === b) {
    return true
  }
  return seriesIdFingerprint(a) === seriesIdFingerprint(b)
}

/** Build a client route — query param avoids path-encoding issues with plex:// guids. */
export function seriesDetailRoute(seriesId: string): string {
  return `/series?id=${encodeURIComponent(seriesId)}`
}

/** Single encoding for API path segments (do not decode before calling). */
export function seriesApiPath(
  connectionId: string,
  seriesId: string,
  suffix = "",
): string {
  return `/connections/${connectionId}/series/${encodeURIComponent(seriesId)}${suffix}`
}

/** Resolve series id from query string (preferred) or legacy path param. */
export function resolveSeriesId(
  searchParams: URLSearchParams,
  pathParam: string | undefined,
): string | undefined {
  const fromQuery = searchParams.get("id")
  if (fromQuery) {
    return fromQuery
  }
  if (pathParam) {
    return pathParam
  }
  return undefined
}
