import type { RebuildStatus } from "@/api/types"

export function isRebuildInProgress(
  status: RebuildStatus | undefined | null,
): boolean {
  return status === "running" || status === "queued"
}
