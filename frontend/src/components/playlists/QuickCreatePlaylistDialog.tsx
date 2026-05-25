import { useState } from "react"
import { Link } from "react-router-dom"
import { toast } from "sonner"

import {
  createPlaylistWithSeries,
} from "@/api/playlists"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

interface QuickCreatePlaylistDialogProps {
  seriesId: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function QuickCreatePlaylistDialog({
  seriesId,
  open,
  onOpenChange,
}: QuickCreatePlaylistDialogProps) {
  const [name, setName] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    const trimmed = name.trim()
    if (!trimmed) {
      return
    }

    setIsSubmitting(true)
    try {
      const result = await createPlaylistWithSeries(trimmed, seriesId)
      toast.success(`Added to ${result.name}`)
      setName("")
      onOpenChange(false)
    } catch {
      toast.error("Failed to create playlist")
    } finally {
      setIsSubmitting(false)
    }
  }

  const advancedHref = `/playlists/new?seriesId=${encodeURIComponent(seriesId)}`

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent showCloseButton>
        <form onSubmit={(event) => void handleSubmit(event)}>
          <DialogHeader>
            <DialogTitle>Create new playlist</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-2 py-2">
            <Label htmlFor="quick-create-name">Name</Label>
            <Input
              id="quick-create-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              autoFocus
              placeholder="My playlist"
            />
          </div>
          <DialogFooter className="mt-2 border-t-0 bg-transparent p-0">
            <Link
              to={advancedHref}
              className="text-muted-foreground hover:text-foreground mr-auto text-sm underline-offset-4 hover:underline"
              onClick={() => onOpenChange(false)}
            >
              Advanced…
            </Link>
            <Button
              type="submit"
              disabled={!name.trim() || isSubmitting}
            >
              Create and add
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
