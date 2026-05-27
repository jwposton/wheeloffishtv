import { useEffect, useRef } from "react"
import { useQueryClient } from "@tanstack/react-query"

import { fetchJson } from "@/api/client"
import { authQueryKey, useAuth } from "@/hooks/useAuth"

/** Trigger background catalog sync once when a linked user has no scoped libraries yet. */
export function useSessionCatalogRefresh() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const kickedRef = useRef(false)

  useEffect(() => {
    if (kickedRef.current || !user?.has_media_link) {
      return
    }
    if (user.libraries_scoped) {
      return
    }

    kickedRef.current = true
    void fetchJson("/session/catalog-refresh", { method: "POST" }).then(() =>
      queryClient.invalidateQueries({ queryKey: authQueryKey }),
    )
  }, [queryClient, user])
}
