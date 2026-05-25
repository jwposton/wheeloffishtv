import { useState } from "react"
import { Link, useNavigate, useParams } from "react-router-dom"
import { AlertDialog } from "@base-ui/react/alert-dialog"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { RebuildBanner } from "@/components/playlists/RebuildBanner"
import { OutputList } from "@/components/playlists/OutputList"
import { usePlaylist, useDeletePlaylist, useRebuildPlaylist } from "@/api/playlists"
import { cn } from "@/lib/utils"

function DeleteConfirmDialog({
  playlistName,
  onConfirm,
  isPending,
}: {
  playlistName: string
  onConfirm: () => void
  isPending: boolean
}) {
  return (
    <AlertDialog.Root>
      <AlertDialog.Trigger
        render={
          <Button variant="destructive" size="sm" disabled={isPending}>
            Delete
          </Button>
        }
      />
      <AlertDialog.Portal>
        <AlertDialog.Backdrop
          className={cn(
            "fixed inset-0 z-50 bg-black/40 transition-opacity duration-150",
            "data-ending-style:opacity-0 data-starting-style:opacity-0",
          )}
        />
        <AlertDialog.Viewport className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <AlertDialog.Popup
            className={cn(
              "w-full max-w-sm rounded-xl border bg-popover p-6 shadow-lg",
              "transition-all duration-150",
              "data-ending-style:opacity-0 data-ending-style:scale-95",
              "data-starting-style:opacity-0 data-starting-style:scale-95",
            )}
          >
            <AlertDialog.Title className="text-base font-semibold">
              Delete playlist
            </AlertDialog.Title>
            <AlertDialog.Description className="mt-2 text-sm text-muted-foreground">
              This removes the playlist and its rebuild history. This cannot be undone.
            </AlertDialog.Description>
            <p className="mt-1 text-sm font-medium truncate">{playlistName}</p>
            <div className="mt-4 flex justify-end gap-2">
              <AlertDialog.Close
                render={<Button variant="outline" size="sm" />}
              >
                Cancel
              </AlertDialog.Close>
              <AlertDialog.Close
                render={
                  <Button variant="destructive" size="sm" disabled={isPending} />
                }
                onClick={onConfirm}
              >
                {isPending ? "Deleting…" : "Delete playlist"}
              </AlertDialog.Close>
            </div>
          </AlertDialog.Popup>
        </AlertDialog.Viewport>
      </AlertDialog.Portal>
    </AlertDialog.Root>
  )
}

export function PlaylistDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: playlist, isLoading, isError } = usePlaylist(id!)
  const deleteMutation = useDeletePlaylist()
  const rebuildMutation = useRebuildPlaylist()
  const [isDeleting, setIsDeleting] = useState(false)

  async function handleDelete() {
    if (!id) return
    setIsDeleting(true)
    try {
      await deleteMutation.mutateAsync(id)
      toast.success("Playlist deleted")
      navigate("/playlists")
    } catch {
      toast.error("Failed to delete playlist")
      setIsDeleting(false)
    }
  }

  async function handleRebuild() {
    if (!id) return
    try {
      await rebuildMutation.mutateAsync(id)
      toast.success("Rebuild queued")
    } catch {
      toast.error("Failed to queue rebuild")
    }
  }

  const isRebuildRunning =
    playlist?.last_rebuild?.status === "running" ||
    playlist?.last_rebuild?.status === "queued"

  if (isLoading) {
    return (
      <div className="mx-auto flex max-w-3xl flex-col gap-4">
        <Skeleton className="h-8 w-56" />
        <Skeleton className="h-20 w-full rounded-xl" />
        <Skeleton className="h-64 w-full rounded-xl" />
      </div>
    )
  }

  if (isError || !playlist) {
    return (
      <div className="mx-auto max-w-3xl">
        <p className="text-sm text-destructive">Failed to load playlist. Please try again.</p>
      </div>
    )
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-col gap-1 min-w-0">
          <h2 className="text-xl font-semibold truncate">{playlist.name}</h2>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Button
            size="sm"
            onClick={() => void handleRebuild()}
            disabled={isRebuildRunning || rebuildMutation.isPending}
          >
            {rebuildMutation.isPending || isRebuildRunning ? "Rebuilding…" : "Rebuild now"}
          </Button>
          <Button
            size="sm"
            variant="outline"
            render={<Link to={`/playlists/${playlist.id}/edit`} />}
          >
            Edit
          </Button>
          <DeleteConfirmDialog
            playlistName={playlist.name}
            onConfirm={() => void handleDelete()}
            isPending={isDeleting}
          />
        </div>
      </div>

      {/* Rebuild status banner */}
      <RebuildBanner lastRebuild={playlist.last_rebuild} />

      {/* Output list */}
      <section>
        <h3 className="mb-3 font-medium text-sm text-muted-foreground uppercase tracking-wide">
          Output — {playlist.episode_count} episodes
        </h3>
        <div className="rounded-xl border bg-card p-4">
          <OutputList episodes={playlist.current_snapshot} />
        </div>
      </section>
    </div>
  )
}
