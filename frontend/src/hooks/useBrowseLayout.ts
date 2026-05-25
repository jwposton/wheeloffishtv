import { useCallback, useState } from "react"

export type BrowseLayout = "grid" | "list"

const STORAGE_KEY = "wof.browse.layout"

function readStoredLayout(): BrowseLayout {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored === "list") {
    return "list"
  }
  if (stored !== "grid") {
    localStorage.setItem(STORAGE_KEY, "grid")
  }
  return "grid"
}

export function useBrowseLayout() {
  const [layout, setLayoutState] = useState<BrowseLayout>(() => readStoredLayout())

  const setLayout = useCallback((next: BrowseLayout) => {
    localStorage.setItem(STORAGE_KEY, next)
    setLayoutState(next)
  }, [])

  const toggleLayout = useCallback(() => {
    setLayout(layout === "grid" ? "list" : "grid")
  }, [layout, setLayout])

  return { layout, setLayout, toggleLayout }
}
