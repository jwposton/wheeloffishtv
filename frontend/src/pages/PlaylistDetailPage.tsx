import { useState } from "react"
import { Link, useNavigate, useParams } from "react-router-dom"
import { AlertDialog } from "@base-ui/react/alert-dialog"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { RebuildButton } from "@/components/playlists/RebuildButton"
import { RebuildBanner } from "@/components/playlists/RebuildBanner"
import { OutputList } from "@/components/playlists/OutputList"
import { PlaylistMembersPanel } from "@/components/playlists/PlaylistMembersPanel"
import { usePlaylist, useDeletePlaylist, useRebuildPlaylist } from "@/api/playlists"
import { isRebuildInProgress } from "@/lib/rebuild"
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
      const run = await rebuildMutation.mutateAsync(id)
      if (run.status === "failed") {
        toast.error(run.error_message ?? "Rebuild failed")
        return
      }
      if (run.status === "partial") {
        toast.success("Rebuild complete with warnings")
        return
      }
      toast.success("Rebuild complete")
    } catch {
      toast.error("Failed to rebuild playlist")
    }
  }

  const isRebuildRunning = isRebuildInProgress(playlist?.last_rebuild?.status)

  if (isLoading) {
    return (
      <div className="mx-auto flex max-w-6xl flex-col gap-4">
        <Skeleton className="h-8 w-56" />
        <Skeleton className="h-20 w-full rounded-xl" />
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1.85fr)_minmax(240px,1fr)]">
          <Skeleton className="h-64 w-full rounded-xl" />
          <Skeleton className="h-64 w-full rounded-xl" />
        </div>
      </div>
    )
  }

  if (isError || !playlist) {
    return (
      <div className="mx-auto max-w-6xl">
        <p className="text-sm text-destructive">Failed to load playlist. Please try again.</p>
      </div>
    )
  }

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6">
      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-col gap-1 min-w-0">
          <h2 className="truncate text-2xl">{playlist.name}</h2>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <RebuildButton
            onClick={() => void handleRebuild()}
            spinning={rebuildMutation.isPending || isRebuildRunning}
          />
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

      <RebuildBanner
        lastRebuild={playlist.last_rebuild}
        snapshot={playlist.current_snapshot}
        providerKind={playlist.provider_kind}
        providerPlaylistOpenUrl={playlist.provider_playlist_open_url}
      />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.85fr)_minmax(240px,1fr)]">
        <section className="flex flex-col gap-3">
          <h3 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">
            Shows ({playlist.rows.length})
          </h3>
          <div className="wof-panel p-4">
            <PlaylistMembersPanel playlistId={playlist.id} rows={playlist.rows} />
          </div>
        </section>

        <section className="flex flex-col gap-3">
          <h3 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">
            Output — {playlist.episode_count} episodes
          </h3>
          <div className="wof-panel p-4">
            <OutputList episodes={playlist.current_snapshot} />
          </div>
        </section>
      </div>
    </div>
  )
}
