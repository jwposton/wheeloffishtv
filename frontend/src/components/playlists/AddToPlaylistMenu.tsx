import { useState, type ReactElement } from "react"
import { Link } from "react-router-dom"
import { toast } from "sonner"

import { getApiErrorStatus, isAlreadyInPlaylistError } from "@/api/client"
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
import type { TransientFeedback } from "@/hooks/useTransientFeedback"

export type AppendFeedback = TransientFeedback

interface AddToPlaylistHandlersOptions {
  onAppendFeedback?: (feedback: AppendFeedback) => void
  showAdvancedLink?: boolean
}

interface AddToPlaylistMenuProps extends AddToPlaylistHandlersOptions {
  seriesId: string
  trigger: ReactElement
}

function notifyAppendFeedback(
  feedback: AppendFeedback,
  onAppendFeedback?: (feedback: AppendFeedback) => void,
) {
  if (onAppendFeedback) {
    onAppendFeedback(feedback)
    return
  }

  if (feedback.variant === "success") {
    toast.success(feedback.message)
  } else if (feedback.variant === "info") {
    toast.info(feedback.message)
  } else {
    toast.error(feedback.message)
  }
}

function useAddToPlaylistHandlers(
  seriesId: string,
  { onAppendFeedback, showAdvancedLink = false }: AddToPlaylistHandlersOptions = {},
) {
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
      notifyAppendFeedback(
        { variant: "success", message: `Added to ${playlistName}` },
        onAppendFeedback,
      )
    } catch (error) {
      if (isAlreadyInPlaylistError(error)) {
        notifyAppendFeedback(
          { variant: "info", message: `Already in ${playlistName}` },
          onAppendFeedback,
        )
        return
      }
      notifyAppendFeedback(
        {
          variant: "error",
          message:
            getApiErrorStatus(error) === 422
              ? "Show not in your library"
              : "Could not add to playlist",
        },
        onAppendFeedback,
      )
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
    showAdvancedLink,
  }
}

export function AddToPlaylistContextMenuItems({
  seriesId,
  onAppendFeedback,
  showAdvancedLink = false,
}: {
  seriesId: string
  onAppendFeedback?: (feedback: AppendFeedback) => void
  showAdvancedLink?: boolean
}) {
  const {
    playlists,
    isLoading,
    quickCreateOpen,
    setQuickCreateOpen,
    handleAppend,
    openQuickCreate,
    appendPending,
    advancedHref,
    showAdvancedLink: showAdvanced,
  } = useAddToPlaylistHandlers(seriesId, { onAppendFeedback, showAdvancedLink })

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
      {showAdvanced ? (
        <ContextMenuItem
          render={<Link to={advancedHref} />}
          onClick={(event) => event.stopPropagation()}
        >
          Advanced…
        </ContextMenuItem>
      ) : null}
      <QuickCreatePlaylistDialog
        seriesId={seriesId}
        open={quickCreateOpen}
        onOpenChange={setQuickCreateOpen}
        showAdvancedLink={showAdvanced}
      />
    </>
  )
}

export function AddToPlaylistMenu({
  seriesId,
  trigger,
  onAppendFeedback,
  showAdvancedLink = false,
}: AddToPlaylistMenuProps) {
  const {
    playlists,
    isLoading,
    quickCreateOpen,
    setQuickCreateOpen,
    handleAppend,
    openQuickCreate,
    appendPending,
    advancedHref,
    showAdvancedLink: showAdvanced,
  } = useAddToPlaylistHandlers(seriesId, { onAppendFeedback, showAdvancedLink })

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
          {showAdvanced ? (
            <DropdownMenuItem
              render={<Link to={advancedHref} />}
              onClick={(event) => event.stopPropagation()}
            >
              Advanced…
            </DropdownMenuItem>
          ) : null}
        </DropdownMenuContent>
      </DropdownMenu>
      <QuickCreatePlaylistDialog
        seriesId={seriesId}
        open={quickCreateOpen}
        onOpenChange={setQuickCreateOpen}
        showAdvancedLink={showAdvanced}
      />
    </>
  )
}
