import { Loader2 } from "lucide-react"

import { useWatchMutationProgress } from "@/hooks/useSeriesEpisodes"

function actionLabel(action: "watched" | "unwatched" | null): string {
  if (action === "watched") {
    return "mark watched"
  }
  if (action === "unwatched") {
    return "mark unwatched"
  }
  return "update"
}

export function WatchStateProgressBanner() {
  const progress = useWatchMutationProgress()
  if (!progress.visible) {
    return null
  }

  const runningText = `Running ${actionLabel(progress.action)} for ${progress.targetLabel ?? "selection"}...`
  const resultText = progress.message ?? "Watch state update complete."

  return (
    <div className="pointer-events-none fixed right-4 bottom-4 z-50">
      <div className="bg-background/95 text-foreground flex items-center gap-2 rounded-md border px-3 py-2 text-sm shadow-md">
        {progress.status === "running" ? (
          <Loader2 className="text-muted-foreground size-4 animate-spin" aria-hidden />
        ) : null}
        <span>{progress.status === "running" ? runningText : resultText}</span>
      </div>
    </div>
  )
}
