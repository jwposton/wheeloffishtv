import type { Episode, ResumePreviewResponse } from "@/api/types"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

type WatchState = "unwatched" | "partial" | "complete"

function classifyWatch(
  percentWatched: number | null,
  providerMarkedPlayed: boolean,
): WatchState {
  if (providerMarkedPlayed || (percentWatched ?? 0) >= 95) {
    return "complete"
  }
  if ((percentWatched ?? 0) >= 5) {
    return "partial"
  }
  return "unwatched"
}

function watchStateLabel(state: WatchState): string {
  switch (state) {
    case "complete":
      return "Complete"
    case "partial":
      return "In progress"
    case "unwatched":
      return "Unwatched"
  }
}

function previewHeading(resume: ResumePreviewResponse): string {
  if (resume.series_complete) {
    return "Series complete"
  }
  if (resume.source === "on_deck") {
    return "Up next"
  }
  if ((resume.percent_watched ?? 0) >= 5) {
    return "Resume"
  }
  return "Up next"
}

function formatSeasonEpisode(
  seasonIndex: number | null,
  episodeIndex: number | null,
): string | null {
  if (seasonIndex == null || episodeIndex == null) {
    return null
  }
  return `S${seasonIndex} · E${episodeIndex}`
}

interface ResumePreviewProps {
  resume: ResumePreviewResponse | undefined
  episode: Episode | undefined
  isLoading: boolean
  isError: boolean
}

export function ResumePreview({
  resume,
  episode,
  isLoading,
  isError,
}: ResumePreviewProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-24" />
          <Skeleton className="h-4 w-48" />
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-32" />
        </CardContent>
      </Card>
    )
  }

  if (isError) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Resume preview</CardTitle>
          <CardDescription>
            Could not load resume data for this series.
          </CardDescription>
        </CardHeader>
      </Card>
    )
  }

  if (!resume) {
    return null
  }

  if (resume.series_complete) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{previewHeading(resume)}</CardTitle>
          <CardDescription>
            You have finished every episode in this series.
          </CardDescription>
        </CardHeader>
      </Card>
    )
  }

  const watchState = classifyWatch(
    episode?.percent_watched ?? resume.percent_watched,
    episode?.provider_marked_played ?? false,
  )
  const seasonEpisode = formatSeasonEpisode(
    resume.season_index,
    resume.episode_index,
  )

  return (
    <Card>
      <CardHeader>
        <CardTitle>{previewHeading(resume)}</CardTitle>
        <CardDescription>
          Read-only preview from your media server watch state.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="flex flex-col gap-1">
          <p className="font-medium">
            {episode?.title ?? "Episode details loading…"}
          </p>
          {seasonEpisode ? (
            <p className="text-muted-foreground text-sm">{seasonEpisode}</p>
          ) : null}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="secondary">{watchStateLabel(watchState)}</Badge>
          {resume.percent_watched != null && watchState === "partial" ? (
            <span className="text-muted-foreground text-sm">
              {Math.round(resume.percent_watched)}% watched
            </span>
          ) : null}
        </div>
      </CardContent>
    </Card>
  )
}
