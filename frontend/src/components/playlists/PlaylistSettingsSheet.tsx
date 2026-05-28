import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { PlaylistForm } from "@/components/playlists/PlaylistForm"
import type { PlaylistDetailResponse } from "@/api/playlists"

interface PlaylistSettingsSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  playlist: PlaylistDetailResponse
}

export function PlaylistSettingsSheet({
  open,
  onOpenChange,
  playlist,
}: PlaylistSettingsSheetProps) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full overflow-y-auto sm:max-w-lg">
        <SheetHeader className="border-b pb-4">
          <SheetTitle>Playlist settings</SheetTitle>
          <SheetDescription>
            Name, episode count, slot allocation, completion policy, and refresh schedule.
          </SheetDescription>
        </SheetHeader>
        <div className="px-4 pb-6">
          <PlaylistForm
            mode="edit"
            playlist={playlist}
            sections="settings"
            onSettingsSaved={() => onOpenChange(false)}
            onSettingsCancel={() => onOpenChange(false)}
          />
        </div>
      </SheetContent>
    </Sheet>
  )
}
