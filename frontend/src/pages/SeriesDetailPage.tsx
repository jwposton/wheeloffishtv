import { useQueryClient } from "@tanstack/react-query"
import { ArrowLeftIcon } from "lucide-react"
import { useEffect, useMemo, useRef } from "react"
import { Link, useParams } from "react-router-dom"

import type { Series, SeriesBrowseResponse } from "@/api/types"
import { ResumePreview } from "@/components/browse/ResumePreview"
import { SeriesPoster } from "@/components/browse/SeriesPoster"
import { Skeleton } from "@/components/ui/skeleton"
import { useAuth } from "@/hooks/useAuth"
import { useSeriesEpisodes } from "@/hooks/useSeriesEpisodes"
import { useSeriesResume } from "@/hooks/useSeriesResume"

function findSeriesInBrowseCache(
  queryClient: ReturnType<typeof useQueryClient>,
  connectionId: string,
  seriesId: string,
): Series | undefined {
  const queries = queryClient.getQueriesData<{ pages: SeriesBrowseResponse[] }>(
    { queryKey: ["series", connectionId] },
  )

  for (const [, data] of queries) {
    const match = data?.pages
      .flatMap((page) => page.items)
      .find((series) => series.id === seriesId)
    if (match) {
      return match
    }
  }

  return undefined
}

export function SeriesDetailPage() {
  const { seriesId: encodedSeriesId } = useParams<{ seriesId: string }>()
  const seriesId = encodedSeriesId ? decodeURIComponent(encodedSeriesId) : undefined
  const headingRef = useRef<HTMLHeadingElement>(null)
  const { user } = useAuth()
  const connectionId = user?.connection?.id
  const queryClient = useQueryClient()

  const cachedSeries = useMemo(
    () =>
      connectionId && seriesId
        ? findSeriesInBrowseCache(queryClient, connectionId, seriesId)
        : undefined,
    [connectionId, queryClient, seriesId],
  )

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

  const title = cachedSeries?.title ?? "Series detail"

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
        <h2
          ref={headingRef}
          tabIndex={-1}
          className="text-xl font-semibold outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        >
          {title}
        </h2>
        {cachedSeries?.year ? (
          <p className="text-muted-foreground text-sm">{cachedSeries.year}</p>
        ) : resumeQuery.isLoading && !cachedSeries ? (
          <Skeleton className="mt-1 h-4 w-16" />
        ) : null}
      </div>

      <div className="aspect-[2/3] w-40 overflow-hidden rounded-md border bg-white">
        <SeriesPoster
          title={title}
          thumbUrl={cachedSeries?.thumb_url}
          compact
        />
      </div>

      <ResumePreview
        resume={resumeQuery.data}
        episode={matchedEpisode}
        isLoading={resumeQuery.isLoading}
        isError={resumeQuery.isError}
      />
    </div>
  )
}
