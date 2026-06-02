import { ArrowLeftIcon } from "lucide-react"
import { useEffect, useMemo, useRef, useState } from "react"
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom"
import { toast } from "sonner"

import type { Episode } from "@/api/types"
import { ResumePreview } from "@/components/browse/ResumePreview"
import { AddToPlaylistMenu } from "@/components/playlists/AddToPlaylistMenu"
import { SeriesMetadataHero } from "@/components/series/SeriesMetadataHero"
import { SeriesPlaylistsSection } from "@/components/series/SeriesPlaylistsSection"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
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

type EpisodeWatchLabel = "Watched" | "On deck" | "Unwatched"

function watchLabelForEpisode(
  percentWatched: number,
  providerMarkedPlayed: boolean,
  isOnDeck: boolean,
): EpisodeWatchLabel {
  if (providerMarkedPlayed || percentWatched >= 95) {
    return "Watched"
  }
  if (isOnDeck || percentWatched >= 5) {
    return "On deck"
  }
  return "Unwatched"
}

function seasonSortValue(seasonIndex: number): number {
  if (seasonIndex === 0) {
    return Number.MAX_SAFE_INTEGER
  }
  return seasonIndex
}

function seasonLabel(seasonIndex: number): string {
  return seasonIndex === 0 ? "Specials" : `Season ${seasonIndex}`
}

const UNSUPPORTED_BULK_SCOPE_MESSAGE =
  "This provider does not support this bulk update scope."

type BulkWatchScope = "season" | "series"

type UnsupportedBulkScope =
  | { scope: "series" }
  | { scope: "season"; seasonIndex: number }
  | null

function mutationErrorMessage(
  errorCode: string | null | undefined,
  scope?: "episode" | BulkWatchScope,
): string {
  if (errorCode === "auth") {
    return "Could not update watch status. Please reconnect your provider and try again."
  }
  if (errorCode === "provider_error" && (scope === "season" || scope === "series")) {
    return UNSUPPORTED_BULK_SCOPE_MESSAGE
  }
  if (errorCode === "provider_error") {
    return "Could not update watch status. Provider rejected this update."
  }
  return "Could not update watch status. Please try again."
}

export function SeriesDetailPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { seriesId: pathSeriesId } = useParams<{ seriesId?: string }>()
  const seriesId = resolveSeriesId(searchParams, pathSeriesId)
  const origin = searchParams.get("origin")
  const from = searchParams.get("from")
  const headingRef = useRef<HTMLHeadingElement>(null)
  const [unsupportedBulkScope, setUnsupportedBulkScope] =
    useState<UnsupportedBulkScope>(null)
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
  const isPlaylistOrigin = origin === "playlist-edit" || origin === "playlist-view"
  const playlistBackPath =
    from && from.startsWith("/") && !from.startsWith("//") ? from : null
  const backHref = isPlaylistOrigin && playlistBackPath ? playlistBackPath : "/browse"
  const backLabel = isPlaylistOrigin ? "Back to Playlist" : "Back to Library"

  const seriesQuery = useSeriesDetail(connectionId, seriesId, { enabled: authReady })
  const series = seriesQuery.data

  const resumeQuery = useSeriesResume(connectionId, seriesId)
  const episodesQuery = useSeriesEpisodes(connectionId, seriesId, authReady)

  const matchedEpisode = useMemo(() => {
    const episodeId = resumeQuery.data?.episode_id
    if (!episodeId) {
      return undefined
    }
    return episodesQuery.data?.episodes.find((episode) => episode.id === episodeId)
  }, [episodesQuery.data?.episodes, resumeQuery.data?.episode_id])

  const groupedEpisodes = useMemo(() => {
    const grouped = new Map<number, Episode[]>()
    for (const episode of episodesQuery.data?.episodes ?? []) {
      const bucket = grouped.get(episode.season_index)
      if (bucket) {
        bucket.push(episode)
      } else {
        grouped.set(episode.season_index, [episode])
      }
    }
    return Array.from(grouped.entries())
      .sort((a, b) => seasonSortValue(a[0]) - seasonSortValue(b[0]))
      .map(([seasonIndex, episodes]) => ({
        seasonIndex,
        episodes: [...episodes].sort((a, b) => a.episode_index - b.episode_index),
      }))
  }, [episodesQuery.data?.episodes])

  async function handleEpisodeMutation(episodeId: string, watched: boolean) {
    setUnsupportedBulkScope(null)
    try {
      const result = await episodesQuery.updateEpisodeWatchState({ episodeId, watched })
      if (result.status === "failed") {
        toast.error(mutationErrorMessage(result.error_code, "episode"))
        return
      }
      if (result.status === "partial") {
        toast.error("Some episode updates failed. Refresh and try again.")
        return
      }
      toast.success("Watch status updated")
    } catch {
      toast.error("Could not update watch status. Please try again.")
    }
  }

  async function handleSeasonMutation(seasonIndex: number, watched: boolean) {
    setUnsupportedBulkScope(null)
    try {
      const result = await episodesQuery.updateSeasonWatchState({ seasonIndex, watched })
      if (result.status === "failed") {
        if (result.error_code === "provider_error") {
          setUnsupportedBulkScope({ scope: "season", seasonIndex })
        }
        toast.error(mutationErrorMessage(result.error_code, "season"))
        return
      }
      if (result.status === "partial") {
        toast.error("Season update partially failed.")
        return
      }
      setUnsupportedBulkScope(null)
      toast.success("Season updated")
    } catch {
      toast.error("Could not update watch status. Please try again.")
    }
  }

  async function handleSeriesMutation(watched: boolean) {
    setUnsupportedBulkScope(null)
    try {
      const result = await episodesQuery.updateSeriesWatchState({ watched })
      if (result.status === "failed") {
        if (result.error_code === "provider_error") {
          setUnsupportedBulkScope({ scope: "series" })
        }
        toast.error(mutationErrorMessage(result.error_code, "series"))
        return
      }
      if (result.status === "partial") {
        toast.error("Series update partially failed.")
        return
      }
      setUnsupportedBulkScope(null)
      toast.success("Series updated")
    } catch {
      toast.error("Could not update watch status. Please try again.")
    }
  }

  useEffect(() => {
    headingRef.current?.focus()
  }, [seriesId])

  if (!seriesId) {
    return (
      <div className="mx-auto max-w-3xl">
        <p className="text-muted-foreground text-sm">Series not found.</p>
        <Link
          to={backHref}
          className="text-primary mt-4 inline-flex items-center gap-1 text-sm font-medium hover:underline"
        >
          <ArrowLeftIcon className="size-4" />
          {backLabel}
        </Link>
      </div>
    )
  }

  if (connectionMismatch) {
    return (
      <div className="mx-auto max-w-3xl">
        <Link
          to={backHref}
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1 text-sm"
        >
          <ArrowLeftIcon className="size-4" />
          {backLabel}
        </Link>
        <p className="text-muted-foreground text-sm">
          This link is from a previous server session. Open the show again from
          the library to refresh your catalog.
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

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <div>
        <Link
          to={backHref}
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1 text-sm"
        >
          <ArrowLeftIcon className="size-4" />
          {backLabel}
        </Link>
      </div>

      {(authLoading || seriesQuery.isLoading) && !hasSeries ? (
        <div className="flex flex-col gap-4 md:flex-row md:gap-6">
          <Skeleton className="aspect-[2/3] w-40 shrink-0" />
          <div className="flex flex-1 flex-col gap-2">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-4 w-full max-w-md" />
          </div>
        </div>
      ) : series ? (
        <>
          <SeriesMetadataHero series={series} headingRef={headingRef} />
          <div className="flex flex-col gap-4">
            <AddToPlaylistMenu
              seriesId={series.id}
              showAdvancedLink
              trigger={<Button>Add to playlist</Button>}
            />
            <SeriesPlaylistsSection seriesId={series.id} />
          </div>
        </>
      ) : null}

      {detailFailed ? (
        <p className="text-muted-foreground text-sm">
          This series is not available. It may have been removed from your library
          scope or catalog sync may still be running.
        </p>
      ) : null}

      <ResumePreview
        resume={resumeQuery.data}
        episode={matchedEpisode}
        isLoading={resumeQuery.isLoading}
        isError={resumeQuery.isError && !resumeQuery.data}
      />
      {episodesQuery.data?.episodes?.length ? (
        <section className="flex flex-col gap-4" aria-label="Episodes by season">
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="outline"
                disabled={episodesQuery.isUpdating}
                aria-describedby={
                  unsupportedBulkScope?.scope === "series"
                    ? "bulk-scope-unsupported-note-series"
                    : undefined
                }
                onClick={() => void handleSeriesMutation(true)}
              >
                Mark series watched
              </Button>
              <Button
                size="sm"
                variant="outline"
                disabled={episodesQuery.isUpdating}
                aria-describedby={
                  unsupportedBulkScope?.scope === "series"
                    ? "bulk-scope-unsupported-note-series"
                    : undefined
                }
                onClick={() => void handleSeriesMutation(false)}
              >
                Mark series unwatched
              </Button>
            </div>
            {unsupportedBulkScope?.scope === "series" ? (
              <p
                id="bulk-scope-unsupported-note-series"
                className="text-muted-foreground text-xs"
                role="status"
              >
                {UNSUPPORTED_BULK_SCOPE_MESSAGE}
              </p>
            ) : null}
          </div>
          {groupedEpisodes.map(({ seasonIndex, episodes }) => (
            <div key={seasonIndex} className="rounded-lg border p-4">
              <div className="mb-3 flex items-center justify-between gap-2">
                <h3 className="font-semibold">{seasonLabel(seasonIndex)}</h3>
                <div className="flex flex-col items-end gap-1">
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={episodesQuery.isUpdating}
                      aria-describedby={
                        unsupportedBulkScope?.scope === "season" &&
                        unsupportedBulkScope.seasonIndex === seasonIndex
                          ? `bulk-scope-unsupported-note-season-${seasonIndex}`
                          : undefined
                      }
                      onClick={() => void handleSeasonMutation(seasonIndex, true)}
                    >
                      Mark season watched
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={episodesQuery.isUpdating}
                      aria-describedby={
                        unsupportedBulkScope?.scope === "season" &&
                        unsupportedBulkScope.seasonIndex === seasonIndex
                          ? `bulk-scope-unsupported-note-season-${seasonIndex}`
                          : undefined
                      }
                      onClick={() => void handleSeasonMutation(seasonIndex, false)}
                    >
                      Mark season unwatched
                    </Button>
                  </div>
                  {unsupportedBulkScope?.scope === "season" &&
                  unsupportedBulkScope.seasonIndex === seasonIndex ? (
                    <p
                      id={`bulk-scope-unsupported-note-season-${seasonIndex}`}
                      className="text-muted-foreground max-w-xs text-right text-xs"
                      role="status"
                    >
                      {UNSUPPORTED_BULK_SCOPE_MESSAGE}
                    </p>
                  ) : null}
                </div>
              </div>
              <ul className="flex flex-col gap-2">
                {episodes.map((episode) => (
                  <li
                    key={episode.id}
                    className="flex items-center justify-between gap-3 rounded-md border px-3 py-2"
                  >
                    <div className="flex min-w-0 flex-col">
                      <span className="truncate text-sm font-medium">{episode.title}</span>
                      <span className="text-muted-foreground text-xs">
                        E{episode.episode_index}
                      </span>
                    </div>
                    <Badge variant="secondary">
                      {watchLabelForEpisode(
                        episode.percent_watched,
                        episode.provider_marked_played,
                        episode.id === resumeQuery.data?.episode_id,
                      )}
                    </Badge>
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={episodesQuery.isUpdating}
                      onClick={() =>
                        void handleEpisodeMutation(
                          episode.id,
                          !episode.provider_marked_played && episode.percent_watched < 95,
                        )
                      }
                    >
                      {episode.provider_marked_played || episode.percent_watched >= 95
                        ? "Mark episode unwatched"
                        : "Mark episode watched"}
                    </Button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </section>
      ) : null}
    </div>
  )
}
