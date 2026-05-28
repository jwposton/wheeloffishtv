import type { ReactElement } from "react"
import { AlertDialog } from "@base-ui/react/alert-dialog"

import deleteWheelIcon from "@/assets/playlists/delete-wheel.png"
import {
  playlistActionButtonClass,
  playlistActionIconFrameClass,
  playlistActionLabelClass,
} from "@/components/playlists/playlistActionButton"
import { buttonVariants } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export function PlaylistDeleteTrigger({
  disabled,
  className,
  onClick,
}: {
  disabled?: boolean
  className?: string
  onClick?: () => void
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      aria-label="Delete playlist"
      className={cn(buttonVariants({ variant: "outline" }), playlistActionButtonClass(className))}
    >
      <span className={playlistActionIconFrameClass}>
        <img
          src={deleteWheelIcon}
          alt=""
          className="size-full rounded-full object-contain"
        />
      </span>
      <span className={playlistActionLabelClass}>Delete</span>
    </button>
  )
}

export function PlaylistDeleteDialog({
  playlistName,
  onConfirm,
  isPending,
  trigger,
  open,
  onOpenChange,
}: {
  playlistName: string
  onConfirm: () => void
  isPending: boolean
  trigger?: ReactElement
  open?: boolean
  onOpenChange?: (open: boolean) => void
}) {
  const triggerNode = trigger ?? <PlaylistDeleteTrigger disabled={isPending} />

  return (
    <AlertDialog.Root open={open} onOpenChange={onOpenChange}>
      <AlertDialog.Trigger render={triggerNode} />
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
            <p className="mt-1 truncate text-sm font-medium">{playlistName}</p>
            <div className="mt-4 flex justify-end gap-2">
              <AlertDialog.Close
                render={
                  <button
                    type="button"
                    className={buttonVariants({ variant: "outline", size: "sm" })}
                  />
                }
              >
                Cancel
              </AlertDialog.Close>
              <button
                type="button"
                className={buttonVariants({ variant: "destructive", size: "sm" })}
                disabled={isPending}
                aria-busy={isPending}
                onClick={onConfirm}
              >
                {isPending ? "Deleting…" : "Delete playlist"}
              </button>
            </div>
          </AlertDialog.Popup>
        </AlertDialog.Viewport>
      </AlertDialog.Portal>
    </AlertDialog.Root>
  )
}
