import type { CompletionPolicy, RowMode } from "@/api/playlists"
import type { SeriesRow } from "@/components/playlists/RowSettingsSheet"
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

interface PlaylistRowMenuItemsProps {
  row: SeriesRow
  onModeChange: (mode: RowMode) => void
  onPolicyChange: (policy: CompletionPolicy) => void
  onRemoveRequest: () => void
  variant: "dropdown" | "context"
}

export function PlaylistRowMenuItems({
  row,
  onModeChange,
  onPolicyChange,
  onRemoveRequest,
  variant,
}: PlaylistRowMenuItemsProps) {
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
            onRemoveRequest()
          }}
        >
          Remove from playlist
        </DropdownMenuItem>
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
          onRemoveRequest()
        }}
      >
        Remove from playlist
      </ContextMenuItem>
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
