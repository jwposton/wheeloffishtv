import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useSyncExternalStore } from "react"

import { ApiError, fetchJson } from "@/api/client"
import type {
  EpisodesListResponse,
  WatchStateMutationResponse,
} from "@/api/types"
import { seriesApiPath } from "@/lib/seriesId"
import { seriesDetailQueryKey } from "@/hooks/useSeriesDetail"
import { seriesResumeQueryKey } from "@/hooks/useSeriesResume"

export function seriesEpisodesQueryKey(
  connectionId: string,
  seriesId: string,
) {
  return ["series-episodes", connectionId, seriesId] as const
}

function fetchSeriesEpisodes(
  connectionId: string,
  seriesId: string,
): Promise<EpisodesListResponse> {
  return fetchJson<EpisodesListResponse>(
    seriesApiPath(connectionId, seriesId, "/episodes"),
  )
}

function mutationPath(connectionId: string): string {
  return `/connections/${connectionId}/watch-state`
}

interface WatchMutationPayload {
  target_id?: string
  target_ids?: string[]
  scope: "episode" | "season" | "series"
  action: "watched" | "unwatched"
}

export interface WatchMutationProgressState {
  visible: boolean
  status: "running" | "succeeded" | "partial" | "failed"
  scope: "episode" | "season" | "series" | null
  action: "watched" | "unwatched" | null
  targetLabel: string | null
  message: string | null
}

const defaultProgressState: WatchMutationProgressState = {
  visible: false,
  status: "running",
  scope: null,
  action: null,
  targetLabel: null,
  message: null,
}

let watchMutationProgressState: WatchMutationProgressState = defaultProgressState
const watchMutationProgressListeners = new Set<() => void>()

function emitWatchMutationProgress() {
  for (const listener of watchMutationProgressListeners) {
    listener()
  }
}

function setWatchMutationProgressState(next: WatchMutationProgressState) {
  watchMutationProgressState = next
  emitWatchMutationProgress()
}

export function setWatchMutationProgressRunning(
  scope: "episode" | "season" | "series",
  action: "watched" | "unwatched",
  targetLabel: string,
) {
  setWatchMutationProgressState({
    visible: true,
    status: "running",
    scope,
    action,
    targetLabel,
    message: null,
  })
}

export function setWatchMutationProgressResult(
  result: WatchStateMutationResponse,
  fallbackLabel: string,
) {
  setWatchMutationProgressState({
    visible: true,
    status: result.status,
    scope: result.scope,
    action: null,
    targetLabel: fallbackLabel,
    message: result.message,
  })
  window.setTimeout(() => {
    setWatchMutationProgressState(defaultProgressState)
  }, 3000)
}

export function clearWatchMutationProgress() {
  setWatchMutationProgressState(defaultProgressState)
}

export function useWatchMutationProgress() {
  return useSyncExternalStore(
    (listener) => {
      watchMutationProgressListeners.add(listener)
      return () => watchMutationProgressListeners.delete(listener)
    },
    () => watchMutationProgressState,
    () => watchMutationProgressState,
  )
}

function postWatchMutation(
  connectionId: string,
  payload: WatchMutationPayload,
): Promise<WatchStateMutationResponse> {
  return fetchJson<WatchStateMutationResponse>(mutationPath(connectionId), {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export function useSeriesEpisodes(
  connectionId: string | undefined,
  seriesId: string | undefined,
  enabled = true,
) {
  const queryClient = useQueryClient()
  const episodesQuery = useQuery({
    queryKey: seriesEpisodesQueryKey(connectionId ?? "", seriesId ?? ""),
    queryFn: () => fetchSeriesEpisodes(connectionId!, seriesId!),
    enabled: Boolean(connectionId && seriesId && enabled),
    staleTime: 60_000,
    retry: (failureCount, error) => {
      if (error instanceof ApiError && (error.status === 404 || error.status === 422)) {
        return false
      }
      return failureCount < 2
    },
  })

  async function reconcileAfterMutation() {
    if (!connectionId || !seriesId) {
      return
    }
    await Promise.all([
      queryClient.invalidateQueries({
        queryKey: seriesEpisodesQueryKey(connectionId, seriesId),
      }),
      queryClient.invalidateQueries({
        queryKey: seriesResumeQueryKey(connectionId, seriesId),
      }),
      queryClient.invalidateQueries({
        queryKey: seriesDetailQueryKey(connectionId, seriesId),
      }),
    ])
  }

  const episodeMutation = useMutation({
    mutationFn: async ({
      episodeId,
      watched,
    }: {
      episodeId: string
      watched: boolean
    }) => {
      setWatchMutationProgressRunning(
        "episode",
        watched ? "watched" : "unwatched",
        "episode",
      )
      const prior = queryClient.getQueryData<EpisodesListResponse>(
        seriesEpisodesQueryKey(connectionId ?? "", seriesId ?? ""),
      )
      queryClient.setQueryData<EpisodesListResponse>(
        seriesEpisodesQueryKey(connectionId ?? "", seriesId ?? ""),
        (current) => {
          if (!current) {
            return current
          }
          return {
            episodes: current.episodes.map((episode) =>
              episode.id === episodeId
                ? {
                    ...episode,
                    provider_marked_played: watched,
                    percent_watched: watched ? 100 : 0,
                  }
                : episode,
            ),
          }
        },
      )
      try {
        const result = await postWatchMutation(connectionId!, {
          target_id: episodeId,
          scope: "episode",
          action: watched ? "watched" : "unwatched",
        })
        if (result.status !== "succeeded") {
          queryClient.setQueryData(
            seriesEpisodesQueryKey(connectionId ?? "", seriesId ?? ""),
            prior,
          )
        }
        setWatchMutationProgressResult(result, "episode")
        await reconcileAfterMutation()
        return result
      } catch (error) {
        queryClient.setQueryData(
          seriesEpisodesQueryKey(connectionId ?? "", seriesId ?? ""),
          prior,
        )
        await reconcileAfterMutation()
        clearWatchMutationProgress()
        throw error
      }
    },
  })

  const seasonMutation = useMutation({
    mutationFn: async ({
      seasonIndex,
      watched,
    }: {
      seasonIndex: number
      watched: boolean
    }) => {
      setWatchMutationProgressRunning(
        "season",
        watched ? "watched" : "unwatched",
        `season ${seasonIndex}`,
      )
      const seasonEpisodeIds =
        episodesQuery.data?.episodes
          .filter((episode) => episode.season_index === seasonIndex)
          .map((episode) => episode.id) ?? []
      const result = await postWatchMutation(connectionId!, {
        target_ids: seasonEpisodeIds,
        scope: "season",
        action: watched ? "watched" : "unwatched",
      })
      setWatchMutationProgressResult(result, `season ${seasonIndex}`)
      return result
    },
    onSettled: async () => {
      await reconcileAfterMutation()
    },
    onError: () => {
      clearWatchMutationProgress()
    },
  })

  const seriesMutation = useMutation({
    mutationFn: async ({ watched }: { watched: boolean }) => {
      setWatchMutationProgressRunning(
        "series",
        watched ? "watched" : "unwatched",
        "series",
      )
      const allEpisodeIds = episodesQuery.data?.episodes.map((episode) => episode.id) ?? []
      const result = await postWatchMutation(connectionId!, {
        target_ids: allEpisodeIds,
        scope: "series",
        action: watched ? "watched" : "unwatched",
      })
      setWatchMutationProgressResult(result, "series")
      return result
    },
    onSettled: async () => {
      await reconcileAfterMutation()
    },
    onError: () => {
      clearWatchMutationProgress()
    },
  })

  return {
    ...episodesQuery,
    updateEpisodeWatchState: episodeMutation.mutateAsync,
    updateSeasonWatchState: seasonMutation.mutateAsync,
    updateSeriesWatchState: seriesMutation.mutateAsync,
    isUpdating:
      episodeMutation.isPending ||
      seasonMutation.isPending ||
      seriesMutation.isPending,
  }
}
