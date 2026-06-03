import { useState } from "react"
import { Link, useNavigate, useParams } from "react-router-dom"
import { ArrowLeftIcon } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { PlaylistDeleteTrigger } from "@/components/playlists/PlaylistDeleteDialog"
import { PlaylistForm } from "@/components/playlists/PlaylistForm"
import { PlaylistSettingsButton } from "@/components/playlists/PlaylistSettingsButton"
import { PlaylistSettingsSheet } from "@/components/playlists/PlaylistSettingsSheet"
import { RebuildButton } from "@/components/playlists/RebuildButton"
import { RebuildBanner } from "@/components/playlists/RebuildBanner"
import { OutputList } from "@/components/playlists/OutputList"
import {
  usePlaylist,
  useDeletePlaylist,
  useRebuildPlaylist,
  useRemovePlaylistRow,
} from "@/api/playlists"
import { isRebuildInProgress } from "@/lib/rebuild"

export function PlaylistDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: playlist, isLoading, isError } = usePlaylist(id!)
  const deleteMutation = useDeletePlaylist()
  const rebuildMutation = useRebuildPlaylist()
  const removeRowMutation = useRemovePlaylistRow()
  const [isDeleting, setIsDeleting] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)

  async function handleDelete() {
    if (!id) return
    const confirmed = window.confirm(
      `Delete playlist \"${playlist?.name ?? "this playlist"}\"? This cannot be undone.`,
    )
    if (!confirmed) return
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

  async function handleRemoveRow(seriesId: string) {
    if (!id) return
    try {
      await removeRowMutation.mutateAsync({ playlistId: id, seriesId })
      toast.success("Show removed from playlist")
    } catch {
      toast.error("Failed to remove show — it may have already been removed")
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
        <Skeleton className="h-8 w-32" />
        <div className="flex justify-between gap-4">
          <Skeleton className="h-9 w-48" />
          <Skeleton className="h-16 w-40" />
        </div>
        <Skeleton className="h-28 w-full rounded-xl" />
        <Skeleton className="h-64 w-full rounded-xl" />
        <Skeleton className="h-48 w-full rounded-xl" />
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
      <Button
        size="sm"
        variant="ghost"
        className="-ml-2 w-fit gap-1.5 text-muted-foreground"
        render={<Link to="/playlists" />}
      >
        <ArrowLeftIcon className="size-4" aria-hidden />
        Playlists
      </Button>

      <div className="flex flex-wrap items-start justify-between gap-3">
        <h1 className="min-w-0 flex-1 truncate text-2xl font-semibold">{playlist.name}</h1>
        <div className="flex shrink-0 items-start gap-2">
          <RebuildButton
            onClick={() => void handleRebuild()}
            spinning={rebuildMutation.isPending || isRebuildRunning}
          />
          <PlaylistSettingsButton onClick={() => setSettingsOpen(true)} />
          <PlaylistDeleteTrigger
            disabled={isDeleting}
            className="cursor-pointer"
            onClick={() => void handleDelete()}
          />
        </div>
      </div>

      <RebuildBanner
        lastRebuild={playlist.last_rebuild}
        providerKind={playlist.provider_kind}
        providerPlaylistOpenUrl={playlist.provider_playlist_open_url}
        pruneEvents={playlist.recent_prune_events}
        onRemoveRow={(seriesId) => void handleRemoveRow(seriesId)}
      />

      <PlaylistForm mode="edit" playlist={playlist} sections="series" />

      <PlaylistSettingsSheet
        open={settingsOpen}
        onOpenChange={setSettingsOpen}
        playlist={playlist}
      />

      <section className="flex flex-col gap-3">
        <h2 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">
          Current output — {playlist.episode_count} episodes
        </h2>
        <p className="text-sm text-muted-foreground">
          Episodes from the last successful rebuild. Rebuild again to refresh this list.
        </p>
        <div className="wof-panel p-4">
          <OutputList episodes={playlist.current_snapshot} />
        </div>
      </section>
    </div>
  )
}
