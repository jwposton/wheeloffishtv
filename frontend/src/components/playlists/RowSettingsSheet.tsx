import { useEffect, useState } from "react"
import { AlertDialog } from "@base-ui/react/alert-dialog"

import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import {
  Sheet,
  SheetContent,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { cn } from "@/lib/utils"

export interface SeriesRow {
  series_id: string
  series_title: string
  thumb_url: string | null
  mode: "ordered" | "disordered"
  completion_policy: "remove" | "restart" | "disordered"
}

interface RowSettingsSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  row: SeriesRow
  seriesTitle: string
  onSave: (updatedRow: SeriesRow) => void
  onRemove: () => void
}

export function RowSettingsSheet({
  open,
  onOpenChange,
  row,
  seriesTitle,
  onSave,
  onRemove,
}: RowSettingsSheetProps) {
  const [mode, setMode] = useState(row.mode)
  const [completionPolicy, setCompletionPolicy] = useState(row.completion_policy)
  const [confirmRemoveOpen, setConfirmRemoveOpen] = useState(false)

  useEffect(() => {
    if (open) {
      setMode(row.mode)
      setCompletionPolicy(row.completion_policy)
    }
  }, [open, row.mode, row.completion_policy])

  function handleSave() {
    onSave({
      ...row,
      mode,
      completion_policy: completionPolicy,
    })
    onOpenChange(false)
  }

  return (
    <>
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent side="bottom" className="max-h-[85vh]">
          <SheetHeader>
            <SheetTitle>{seriesTitle} — row settings</SheetTitle>
          </SheetHeader>

          <div className="flex flex-col gap-4 px-4">
            <div className="flex flex-col gap-2">
              <Label>Playback mode</Label>
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => setMode("ordered")}
                  className={cn(
                    "rounded px-3 py-1 text-sm transition-colors",
                    mode === "ordered"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground hover:bg-muted/80",
                  )}
                >
                  Ordered
                </button>
                <button
                  type="button"
                  onClick={() => setMode("disordered")}
                  className={cn(
                    "rounded px-3 py-1 text-sm transition-colors",
                    mode === "disordered"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground hover:bg-muted/80",
                  )}
                >
                  Random
                </button>
              </div>
            </div>

            <div className="flex flex-col gap-2">
              <Label htmlFor="row-completion-policy">Completion policy</Label>
              <select
                id="row-completion-policy"
                aria-label="Completion policy"
                value={completionPolicy}
                onChange={(e) =>
                  setCompletionPolicy(
                    e.target.value as SeriesRow["completion_policy"],
                  )
                }
                className="h-8 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="remove">Remove when done</option>
                <option value="restart">Restart</option>
                <option value="disordered">Switch to random</option>
              </select>
            </div>
          </div>

          <SheetFooter className="flex-row justify-between gap-2 sm:justify-between">
            <Button
              type="button"
              variant="destructive"
              onClick={() => setConfirmRemoveOpen(true)}
            >
              Remove from playlist
            </Button>
            <Button type="button" onClick={handleSave}>
              Save
            </Button>
          </SheetFooter>
        </SheetContent>
      </Sheet>

      <AlertDialog.Root open={confirmRemoveOpen} onOpenChange={setConfirmRemoveOpen}>
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
              <div className="mt-4 flex justify-end gap-2">
                <AlertDialog.Close render={<Button variant="outline" size="sm" />}>
                  Cancel
                </AlertDialog.Close>
                <AlertDialog.Close
                  render={<Button variant="destructive" size="sm" />}
                  onClick={() => {
                    onRemove()
                    onOpenChange(false)
                  }}
                >
                  Remove
                </AlertDialog.Close>
              </div>
            </AlertDialog.Popup>
          </AlertDialog.Viewport>
        </AlertDialog.Portal>
      </AlertDialog.Root>
    </>
  )
}
