import { useQuery } from "@tanstack/react-query"

import { ApiError, fetchJson } from "@/api/client"
import type { AuthMeResponse } from "@/api/types"

export function useAuth() {
  const query = useQuery({
    queryKey: ["auth", "me"],
    queryFn: () => fetchJson<AuthMeResponse>("/auth/me"),
    refetchOnMount: "always",
    staleTime: 0,
    retry: (failureCount, error) => {
      if (error instanceof ApiError && error.status === 401) {
        return false
      }
      return failureCount < 3
    },
  })

  return {
    user: query.data ?? null,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  }
}

export const authQueryKey = ["auth", "me"] as const
