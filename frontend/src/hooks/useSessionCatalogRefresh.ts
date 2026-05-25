import { useEffect, useRef } from "react"

import { fetchJson } from "@/api/client"
import { useAuth } from "@/hooks/useAuth"

/** Trigger background catalog sync once when a linked user has no cached library yet. */
export function useSessionCatalogRefresh() {
  const { user } = useAuth()
  const kickedRef = useRef(false)

  useEffect(() => {
    if (kickedRef.current || !user?.has_media_link) {
      return
    }
    if (!user.install_libraries_configured) {
      return
    }
    if (user.libraries_scoped) {
      return
    }

    kickedRef.current = true
    void fetchJson("/session/catalog-refresh", { method: "POST" })
  }, [user])
}
