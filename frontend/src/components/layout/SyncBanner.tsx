import type { SyncStatusEmbed } from "@/api/types"

interface SyncBannerProps {
  sync: SyncStatusEmbed | undefined
}

export function SyncBanner({ sync }: SyncBannerProps) {
  if (sync?.status !== "running") {
    return null
  }

  return (
    <div
      role="status"
      className="border-b bg-muted/80 px-4 py-2 text-center text-sm text-muted-foreground"
    >
      Updating library…
    </div>
  )
}
