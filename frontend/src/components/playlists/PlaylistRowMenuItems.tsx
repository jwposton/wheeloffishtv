import { useState } from "react"
import { AlertDialog } from "@base-ui/react/alert-dialog"

import type { CompletionPolicy, RowMode } from "@/api/playlists"
import type { SeriesRow } from "@/components/playlists/RowSettingsSheet"
import { Button } from "@/components/ui/button"
import {
  ContextMenuItem,
  ContextMenuSeparator,
  ContextMenuSub,
  ContextMenuSubContent,
  ContextMenuSubTrigger,
} from "@/components/ui/context-menu"
import {
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
} from "@/components/ui/dropdown-menu"
import { cn } from "@/lib/utils"

interface PlaylistRowMenuItemsProps {
  row: SeriesRow
  onModeChange: (mode: RowMode) => void
  onPolicyChange: (policy: CompletionPolicy) => void
  onRemove: () => void
  variant: "dropdown" | "context"
}

function RemoveConfirmDialog({
  open,
  onOpenChange,
  seriesTitle,
  onConfirm,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  seriesTitle: string
  onConfirm: () => void
}) {
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

export function PlaylistRowMenuItems({
  row,
  onModeChange,
  onPolicyChange,
  onRemove,
  variant,
}: PlaylistRowMenuItemsProps) {
  const [confirmRemoveOpen, setConfirmRemoveOpen] = useState(false)

  const modeItems = (
    <>
      <ModeItem
        variant={variant}
        label="Ordered"
        selected={row.mode === "ordered"}
        onSelect={() => onModeChange("ordered")}
      />
      <ModeItem
        variant={variant}
        label="Random"
        selected={row.mode === "disordered"}
        onSelect={() => onModeChange("disordered")}
      />
    </>
  )

  const policyItems = (
    <>
      <PolicyItem
        variant={variant}
        label="Remove when done"
        selected={row.completion_policy === "remove"}
        onSelect={() => onPolicyChange("remove")}
      />
      <PolicyItem
        variant={variant}
        label="Restart"
        selected={row.completion_policy === "restart"}
        onSelect={() => onPolicyChange("restart")}
      />
      <PolicyItem
        variant={variant}
        label="Switch to random"
        selected={row.completion_policy === "disordered"}
        onSelect={() => onPolicyChange("disordered")}
      />
    </>
  )

  const Separator = variant === "dropdown" ? DropdownMenuSeparator : ContextMenuSeparator

  if (variant === "dropdown") {
    return (
      <>
        <DropdownMenuSub>
          <DropdownMenuSubTrigger>Playback mode</DropdownMenuSubTrigger>
          <DropdownMenuSubContent>{modeItems}</DropdownMenuSubContent>
        </DropdownMenuSub>
        <DropdownMenuSub>
          <DropdownMenuSubTrigger>Completion policy</DropdownMenuSubTrigger>
          <DropdownMenuSubContent>{policyItems}</DropdownMenuSubContent>
        </DropdownMenuSub>
        <Separator />
        <DropdownMenuItem
          variant="destructive"
          onClick={(event) => {
            event.stopPropagation()
            setConfirmRemoveOpen(true)
          }}
        >
          Remove from playlist
        </DropdownMenuItem>
        <RemoveConfirmDialog
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

  return (
    <>
      <ContextMenuSub>
        <ContextMenuSubTrigger>Playback mode</ContextMenuSubTrigger>
        <ContextMenuSubContent>{modeItems}</ContextMenuSubContent>
      </ContextMenuSub>
      <ContextMenuSub>
        <ContextMenuSubTrigger>Completion policy</ContextMenuSubTrigger>
        <ContextMenuSubContent>{policyItems}</ContextMenuSubContent>
      </ContextMenuSub>
      <Separator />
      <ContextMenuItem
        variant="destructive"
        onClick={(event) => {
          event.stopPropagation()
          setConfirmRemoveOpen(true)
        }}
      >
        Remove from playlist
      </ContextMenuItem>
      <RemoveConfirmDialog
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

function ModeItem({
  variant,
  label,
  selected,
  onSelect,
}: {
  variant: "dropdown" | "context"
  label: string
  selected: boolean
  onSelect: () => void
}) {
  if (variant === "dropdown") {
    return (
      <DropdownMenuItem
        onClick={(event) => {
          event.stopPropagation()
          onSelect()
        }}
      >
        {selected ? `${label} ✓` : label}
      </DropdownMenuItem>
    )
  }

  return (
    <ContextMenuItem
      onClick={(event) => {
        event.stopPropagation()
        onSelect()
      }}
    >
      {selected ? `${label} ✓` : label}
    </ContextMenuItem>
  )
}

function PolicyItem({
  variant,
  label,
  selected,
  onSelect,
}: {
  variant: "dropdown" | "context"
  label: string
  selected: boolean
  onSelect: () => void
}) {
  return (
    <ModeItem variant={variant} label={label} selected={selected} onSelect={onSelect} />
  )
}
