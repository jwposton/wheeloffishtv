import { ExternalLink } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export type WritebackStatusValue =
  | "succeeded"
  | "partial"
  | "failed"
  | "skipped"
  | null

export interface WritebackWarning {
  episode_id?: string | null
  reason?: string
}

interface WritebackStatusProps {
  status: WritebackStatusValue
  error?: string | null
  warnings?: WritebackWarning[] | null
  episodeTitlesById?: Record<string, string>
  providerKind?: string | null
  openUrl?: string | null
  compact?: boolean
}

function warningLabel(
  warning: WritebackWarning,
  episodeTitlesById: Record<string, string>,
): string {
  const episodeId = warning.episode_id
  if (episodeId && episodeTitlesById[episodeId]) {
    return episodeTitlesById[episodeId]
  }
  if (episodeId) {
    return episodeId
  }
  return "Note"
}

function statusLabel(status: WritebackStatusValue): string {
  if (status === null) return "Not synced"
  if (status === "succeeded") return "Synced"
  if (status === "partial") return "Partial sync"
  if (status === "failed") return "Sync failed"
  return "Sync skipped"
}

function providerLabel(providerKind: string | null | undefined): string {
  if (providerKind === "jellyfin") return "Jellyfin"
  return "Plex"
}

export function WritebackStatus({
  status,
  error,
  warnings,
  episodeTitlesById = {},
  providerKind,
  openUrl,
  compact = false,
}: WritebackStatusProps) {
  const warningItems = warnings?.filter((w) => w.reason) ?? []
  const episodeWarnings = warningItems.filter((w) => w.episode_id)
  const infoNotices = warningItems.filter((w) => !w.episode_id)

  if (status === null && !openUrl) {
    return null
  }

  const badgeClass =
    status === "succeeded"
      ? "text-green-600 border-green-600/40"
      : status === "partial"
        ? "text-amber-600"
        : status === "failed"
          ? "text-destructive border-destructive/40"
          : "text-muted-foreground"

  return (
    <div className={cn("flex flex-col gap-2", compact && "gap-1")}>
      <div className="flex flex-wrap items-center gap-2">
        {status !== null && (
          <Badge variant="outline" className={cn(badgeClass)}>
            {statusLabel(status)}
          </Badge>
        )}
        {openUrl ? (
          <Button
            variant="link"
            size="sm"
            className="h-auto px-0"
            render={
              <a href={openUrl} target="_blank" rel="noopener noreferrer">
                Open in {providerLabel(providerKind)}
                <ExternalLink className="ml-1 size-3" />
              </a>
            }
          />
        ) : null}
      </div>
      {status === "failed" && error ? (
        <p className={cn("text-destructive", compact ? "text-xs" : "text-sm")}>
          Sync failed: {error}
        </p>
      ) : null}
      {status === "partial" && episodeWarnings.length > 0 && !compact ? (
        <p className="text-sm text-amber-600">
          Some episodes could not be synced to your media server.
        </p>
      ) : null}
      {episodeWarnings.length > 0 && !compact ? (
        <ul
          aria-label="Sync warnings"
          className="list-disc space-y-1 pl-5 text-sm text-amber-700"
        >
          {episodeWarnings.map((warning, index) => (
            <li key={`${warning.episode_id}-${index}`}>
              <span className="font-medium">{warningLabel(warning, episodeTitlesById)}</span>
              {": "}
              {warning.reason}
            </li>
          ))}
        </ul>
      ) : null}
      {infoNotices.length > 0 && !compact ? (
        <ul
          aria-label="Sync notes"
          className="list-disc space-y-1 pl-5 text-sm text-muted-foreground"
        >
          {infoNotices.map((notice, index) => (
            <li key={`info-${index}`}>{notice.reason}</li>
          ))}
        </ul>
      ) : null}
    </div>
  )
}
