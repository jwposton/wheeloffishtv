import { Badge } from "@/components/ui/badge"
import { WheelIcon } from "@/components/icons/WheelIcon"
import { cn } from "@/lib/utils"
import { isRebuildInProgress } from "@/lib/rebuild"
import type { RebuildStatus } from "@/api/types"

interface StatusBadgeProps {
  status: RebuildStatus
}

export function StatusBadge({ status }: StatusBadgeProps) {
  if (status === null) {
    return (
      <Badge variant="outline" className="text-muted-foreground">
        Never rebuilt
      </Badge>
    )
  }

  if (status === "succeeded") {
    return (
      <Badge variant="outline" className={cn("text-green-600 border-green-600/40")}>
        Succeeded
      </Badge>
    )
  }

  if (status === "partial") {
    return (
      <Badge variant="secondary" className="text-amber-600">
        Partial
      </Badge>
    )
  }

  if (status === "failed") {
    return <Badge variant="destructive">Failed</Badge>
  }

  if (isRebuildInProgress(status)) {
    return (
      <Badge variant="secondary">
        <WheelIcon spinning />
        Rebuilding&hellip;
      </Badge>
    )
  }

  return null
}
