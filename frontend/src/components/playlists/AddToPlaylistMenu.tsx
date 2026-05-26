import { useState, type ReactElement } from "react"
import { Link } from "react-router-dom"
import { toast } from "sonner"

import { useAppendPlaylistRow, usePlaylists } from "@/api/playlists"
import { QuickCreatePlaylistDialog } from "@/components/playlists/QuickCreatePlaylistDialog"
import {
  ContextMenuItem,
  ContextMenuSeparator,
} from "@/components/ui/context-menu"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

interface AddToPlaylistMenuProps {
  seriesId: string
  trigger: ReactElement
}

function useAddToPlaylistHandlers(seriesId: string) {
  const { data: playlists, isLoading } = usePlaylists()
  const appendMutation = useAppendPlaylistRow()
  const [quickCreateOpen, setQuickCreateOpen] = useState(false)
  const advancedHref = `/playlists/new?seriesId=${encodeURIComponent(seriesId)}`

  async function handleAppend(playlistId: string, playlistName: string) {
    try {
      await appendMutation.mutateAsync({
        playlistId,
        payload: { series_id: seriesId },
      })
      toast.success(`Added to ${playlistName}`)
    } catch {
      toast.error("Failed to add to playlist")
    }
  }

  function openQuickCreate(event: React.MouseEvent | React.SyntheticEvent) {
    event.stopPropagation()
    setQuickCreateOpen(true)
  }

  return {
    playlists: playlists ?? [],
    isLoading,
    quickCreateOpen,
    setQuickCreateOpen,
    handleAppend,
    openQuickCreate,
    appendPending: appendMutation.isPending,
    advancedHref,
  }
}

export function AddToPlaylistContextMenuItems({ seriesId }: { seriesId: string }) {
  const {
    playlists,
    isLoading,
    quickCreateOpen,
    setQuickCreateOpen,
    handleAppend,
    openQuickCreate,
    appendPending,
    advancedHref,
  } = useAddToPlaylistHandlers(seriesId)

  return (
    <>
      {isLoading ? (
        <ContextMenuItem disabled>Loading playlists…</ContextMenuItem>
      ) : (
        playlists.map((playlist) => (
          <ContextMenuItem
            key={playlist.id}
            disabled={appendPending}
            onClick={(event) => {
              event.stopPropagation()
              void handleAppend(playlist.id, playlist.name)
            }}
          >
            {playlist.name}
          </ContextMenuItem>
        ))
      )}
      <ContextMenuSeparator />
      <ContextMenuItem onClick={openQuickCreate}>Create new playlist…</ContextMenuItem>
      <ContextMenuItem
        render={<Link to={advancedHref} />}
        onClick={(event) => event.stopPropagation()}
      >
        Advanced…
      </ContextMenuItem>
      <QuickCreatePlaylistDialog
        seriesId={seriesId}
        open={quickCreateOpen}
        onOpenChange={setQuickCreateOpen}
      />
    </>
  )
}

export function AddToPlaylistMenu({ seriesId, trigger }: AddToPlaylistMenuProps) {
  const {
    playlists,
    isLoading,
    quickCreateOpen,
    setQuickCreateOpen,
    handleAppend,
    openQuickCreate,
    appendPending,
    advancedHref,
  } = useAddToPlaylistHandlers(seriesId)

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger render={trigger} />
        <DropdownMenuContent align="end" onClick={(event) => event.stopPropagation()}>
          {isLoading ? (
            <DropdownMenuItem disabled>Loading playlists…</DropdownMenuItem>
          ) : (
            playlists.map((playlist) => (
              <DropdownMenuItem
                key={playlist.id}
                disabled={appendPending}
                onClick={(event) => {
                  event.stopPropagation()
                  void handleAppend(playlist.id, playlist.name)
                }}
              >
                {playlist.name}
              </DropdownMenuItem>
            ))
          )}
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={openQuickCreate}>
            Create new playlist…
          </DropdownMenuItem>
          <DropdownMenuItem
            render={<Link to={advancedHref} />}
            onClick={(event) => event.stopPropagation()}
          >
            Advanced…
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      <QuickCreatePlaylistDialog
        seriesId={seriesId}
        open={quickCreateOpen}
        onOpenChange={setQuickCreateOpen}
      />
    </>
  )
}
