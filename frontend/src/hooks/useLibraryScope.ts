import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { ApiError, fetchJson } from "@/api/client"
import type { Library, LibraryScopeResponse, LibraryScopeUpdate } from "@/api/types"
import { authQueryKey } from "@/hooks/useAuth"

export function libraryScopeQueryKey(connectionId: string) {
  return ["libraries", "scope", connectionId] as const
}

export function useLibraryScope(connectionId: string | undefined) {
  const queryClient = useQueryClient()

  const librariesQuery = useQuery({
    queryKey: libraryScopeQueryKey(connectionId ?? ""),
    queryFn: () =>
      fetchJson<Library[]>(`/connections/${connectionId}/libraries`),
    enabled: Boolean(connectionId),
  })

  const saveScope = useMutation({
    mutationFn: (body: LibraryScopeUpdate) =>
      fetchJson<LibraryScopeResponse>(
        `/connections/${connectionId}/library-scope`,
        {
          method: "PUT",
          body: JSON.stringify(body),
        },
      ),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: authQueryKey }),
        queryClient.invalidateQueries({
          queryKey: libraryScopeQueryKey(connectionId ?? ""),
        }),
      ])
    },
  })

  return {
    libraries: librariesQuery.data ?? [],
    isLoading: librariesQuery.isLoading,
    isError: librariesQuery.isError,
    error: librariesQuery.error,
    saveScope,
    formatSaveError(error: unknown): string {
      if (error instanceof ApiError && error.status === 422) {
        return "Could not save library scope. Check your selections and try again."
      }
      return "Failed to save library scope. Try again."
    },
  }
}
