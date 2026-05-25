import { ArrowLeftIcon } from "lucide-react"
import { useEffect, useMemo, useRef } from "react"
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom"

import { ResumePreview } from "@/components/browse/ResumePreview"
import { SeriesPoster } from "@/components/browse/SeriesPoster"
import { Skeleton } from "@/components/ui/skeleton"
import { useAuth } from "@/hooks/useAuth"
import { useSeriesDetail } from "@/hooks/useSeriesDetail"
import { useSeriesEpisodes } from "@/hooks/useSeriesEpisodes"
import { useSeriesResume } from "@/hooks/useSeriesResume"
import {
  connectionIdFromSeriesId,
  resolveSeriesId,
  seriesDetailRoute,
} from "@/lib/seriesId"

export function SeriesDetailPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { seriesId: pathSeriesId } = useParams<{ seriesId?: string }>()
  const seriesId = resolveSeriesId(searchParams, pathSeriesId)
  const headingRef = useRef<HTMLHeadingElement>(null)
  const { user, isLoading: authLoading } = useAuth()

  // Canonicalize legacy /series/:path bookmarks to /series?id=...
  useEffect(() => {
    if (!seriesId || searchParams.get("id")) {
      return
    }
    navigate(seriesDetailRoute(seriesId), { replace: true })
  }, [navigate, searchParams, seriesId])

  const connectionId = user?.connection?.id

  const connectionMismatch = Boolean(
    seriesId &&
      connectionId &&
      connectionIdFromSeriesId(seriesId) &&
      connectionIdFromSeriesId(seriesId) !== connectionId,
  )

  const authReady = !authLoading && Boolean(connectionId)
  const seriesQuery = useSeriesDetail(connectionId, seriesId, { enabled: authReady })
  const series = seriesQuery.data

  const resumeQuery = useSeriesResume(connectionId, seriesId)
  const needsEpisodeTitle = Boolean(
    resumeQuery.data?.episode_id && !resumeQuery.data.series_complete,
  )
  const episodesQuery = useSeriesEpisodes(
    connectionId,
    seriesId,
    needsEpisodeTitle,
  )

  const matchedEpisode = useMemo(() => {
    const episodeId = resumeQuery.data?.episode_id
    if (!episodeId) {
      return undefined
    }
    return episodesQuery.data?.episodes.find((episode) => episode.id === episodeId)
  }, [episodesQuery.data?.episodes, resumeQuery.data?.episode_id])

  useEffect(() => {
    headingRef.current?.focus()
  }, [seriesId])

  if (!seriesId) {
    return (
      <div className="mx-auto max-w-3xl">
        <p className="text-muted-foreground text-sm">Series not found.</p>
        <Link
          to="/browse"
          className="text-primary mt-4 inline-flex items-center gap-1 text-sm font-medium hover:underline"
        >
          <ArrowLeftIcon className="size-4" />
          Back to browse
        </Link>
      </div>
    )
  }

  if (connectionMismatch) {
    return (
      <div className="mx-auto max-w-3xl">
        <Link
          to="/browse"
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1 text-sm"
        >
          <ArrowLeftIcon className="size-4" />
          Back to browse
        </Link>
        <p className="text-muted-foreground text-sm">
          This link is from a previous server session. Open the show again from
          browse to refresh your catalog.
        </p>
      </div>
    )
  }

  const hasSeries = Boolean(series?.title)
  const detailFailed =
    authReady &&
    seriesQuery.isError &&
    !hasSeries &&
    !seriesQuery.isFetching &&
    seriesQuery.isFetched

  const title = series?.title ?? "Series detail"

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <div>
        <Link
          to="/browse"
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1 text-sm"
        >
          <ArrowLeftIcon className="size-4" />
          Back to browse
        </Link>
        {(authLoading || seriesQuery.isLoading) && !hasSeries ? (
          <>
            <Skeleton className="h-7 w-64" />
            <Skeleton className="mt-1 h-4 w-16" />
          </>
        ) : (
          <>
            <h2
              ref={headingRef}
              tabIndex={-1}
              className="text-xl font-semibold outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            >
              {title}
            </h2>
            {series?.year ? (
              <p className="text-muted-foreground text-sm">{series.year}</p>
            ) : null}
          </>
        )}
      </div>

      {detailFailed ? (
        <p className="text-muted-foreground text-sm">
          This series is not available. It may have been removed from your library
          scope or catalog sync may still be running.
        </p>
      ) : null}

      <div className="aspect-[2/3] w-40 overflow-hidden rounded-md border bg-white">
        {(authLoading || seriesQuery.isLoading) && !hasSeries ? (
          <Skeleton className="size-full" />
        ) : (
          <SeriesPoster
            title={title}
            thumbUrl={series?.thumb_url}
            compact
          />
        )}
      </div>

      <ResumePreview
        resume={resumeQuery.data}
        episode={matchedEpisode}
        isLoading={resumeQuery.isLoading}
        isError={resumeQuery.isError && !resumeQuery.data}
      />
    </div>
  )
}
