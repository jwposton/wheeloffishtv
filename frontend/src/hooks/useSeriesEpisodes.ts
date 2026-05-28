import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

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
        await reconcileAfterMutation()
        return result
      } catch (error) {
        queryClient.setQueryData(
          seriesEpisodesQueryKey(connectionId ?? "", seriesId ?? ""),
          prior,
        )
        await reconcileAfterMutation()
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
      const seasonEpisodeIds =
        episodesQuery.data?.episodes
          .filter((episode) => episode.season_index === seasonIndex)
          .map((episode) => episode.id) ?? []
      return postWatchMutation(connectionId!, {
        target_ids: seasonEpisodeIds,
        scope: "season",
        action: watched ? "watched" : "unwatched",
      })
    },
    onSettled: async () => {
      await reconcileAfterMutation()
    },
  })

  const seriesMutation = useMutation({
    mutationFn: async ({ watched }: { watched: boolean }) => {
      const allEpisodeIds = episodesQuery.data?.episodes.map((episode) => episode.id) ?? []
      return postWatchMutation(connectionId!, {
        target_ids: allEpisodeIds,
        scope: "series",
        action: watched ? "watched" : "unwatched",
      })
    },
    onSettled: async () => {
      await reconcileAfterMutation()
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
