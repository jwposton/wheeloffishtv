import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
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

  return (
    <Badge variant="secondary">
      Rebuilding&hellip;
    </Badge>
  )
}
