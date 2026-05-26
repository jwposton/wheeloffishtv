import { useState, type MouseEvent } from "react"
import { MoreVertical } from "lucide-react"

import { SeriesPoster } from "@/components/browse/SeriesPoster"
import { PlaylistRowMenuItems } from "@/components/playlists/PlaylistRowMenuItems"
import { RemoveFromPlaylistDialog } from "@/components/playlists/RemoveFromPlaylistDialog"
import type { SeriesRow } from "@/components/playlists/RowSettingsSheet"
import type { CompletionPolicy, RowMode } from "@/api/playlists"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuTrigger,
} from "@/components/ui/context-menu"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { cn } from "@/lib/utils"

interface PlaylistMemberTileProps {
  row: SeriesRow
  onModeChange: (mode: RowMode) => void
  onPolicyChange: (policy: CompletionPolicy) => void
  onRemove: () => void
}

export function PlaylistMemberTile({
  row,
  onModeChange,
  onPolicyChange,
  onRemove,
}: PlaylistMemberTileProps) {
  const [confirmRemoveOpen, setConfirmRemoveOpen] = useState(false)

  return (
    <>
      <ContextMenu>
        <ContextMenuTrigger className="block w-full">
          <div className="relative flex flex-col gap-1.5 rounded-md text-left">
            <div
              className={cn(
                "relative flex flex-col gap-1.5 rounded-md text-left",
                "focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:outline-none",
              )}
            >
              <div className="aspect-[2/3] w-full overflow-hidden rounded-md border bg-white">
                <SeriesPoster title={row.series_title} thumbUrl={row.thumb_url} />
              </div>
              <span className="line-clamp-2 text-xs font-medium leading-tight">
                {row.series_title}
              </span>
              {row.mode === "disordered" ? (
                <Badge variant="secondary" className="absolute top-1.5 left-1.5 px-1.5 py-0 text-[0.65rem]">
                  Random
                </Badge>
              ) : null}
            </div>
            <div
              className="absolute top-1.5 right-1.5"
              onClick={(event: MouseEvent) => event.stopPropagation()}
              onContextMenu={(event: MouseEvent) => event.stopPropagation()}
            >
              <DropdownMenu>
                <DropdownMenuTrigger
                  render={
                    <Button
                      type="button"
                      variant="secondary"
                      size="icon-xs"
                      className="bg-background/90 shadow-sm backdrop-blur-sm"
                      aria-label="Series actions"
                      onClick={(event: MouseEvent) => event.stopPropagation()}
                    >
                      <MoreVertical />
                    </Button>
                  }
                />
                <DropdownMenuContent align="end" onClick={(event) => event.stopPropagation()}>
                  <PlaylistRowMenuItems
                    row={row}
                    variant="dropdown"
                    onModeChange={onModeChange}
                    onPolicyChange={onPolicyChange}
                    onRemoveRequest={() => setConfirmRemoveOpen(true)}
                  />
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </ContextMenuTrigger>
        <ContextMenuContent onClick={(event) => event.stopPropagation()}>
          <PlaylistRowMenuItems
            row={row}
            variant="context"
            onModeChange={onModeChange}
            onPolicyChange={onPolicyChange}
            onRemoveRequest={() => setConfirmRemoveOpen(true)}
          />
        </ContextMenuContent>
      </ContextMenu>

      <RemoveFromPlaylistDialog
        open={confirmRemoveOpen}
        onOpenChange={setConfirmRemoveOpen}
        seriesTitle={row.series_title}
        onConfirm={() => {
          onRemove()
          setConfirmRemoveOpen(false)
        }}
      />
    </>
  )
}
