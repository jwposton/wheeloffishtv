import { AlertDialog } from "@base-ui/react/alert-dialog"

import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"

interface RemoveFromPlaylistDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  seriesTitle: string
  dontAskAgain: boolean
  onDontAskAgainChange: (checked: boolean) => void
  onConfirm: () => void
}

export function RemoveFromPlaylistDialog({
  open,
  onOpenChange,
  seriesTitle,
  dontAskAgain,
  onDontAskAgainChange,
  onConfirm,
}: RemoveFromPlaylistDialogProps) {
  return (
    <AlertDialog.Root open={open} onOpenChange={onOpenChange}>
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
              Remove from playlist
            </AlertDialog.Title>
            <AlertDialog.Description className="mt-2 text-sm text-muted-foreground">
              Remove {seriesTitle} from this playlist?
            </AlertDialog.Description>
            <div className="mt-4 flex items-center gap-2">
              <Checkbox
                id="remove-dont-ask-again"
                checked={dontAskAgain}
                onCheckedChange={(checked) => onDontAskAgainChange(checked === true)}
              />
              <Label htmlFor="remove-dont-ask-again" className="cursor-pointer font-normal">
                Don&apos;t ask again
              </Label>
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <AlertDialog.Close render={<Button variant="outline" size="sm" />}>
                Cancel
              </AlertDialog.Close>
              <AlertDialog.Close
                render={<Button variant="destructive" size="sm" />}
                onClick={onConfirm}
              >
                Remove
              </AlertDialog.Close>
            </div>
          </AlertDialog.Popup>
        </AlertDialog.Viewport>
      </AlertDialog.Portal>
    </AlertDialog.Root>
  )
}
