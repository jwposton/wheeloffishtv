import settingsMopBucketIcon from "@/assets/playlists/settings-mop-bucket.png"
import {
  playlistActionButtonClass,
  playlistActionIconFrameClass,
  playlistActionLabelClass,
} from "@/components/playlists/playlistActionButton"
import { Button } from "@/components/ui/button"

interface PlaylistSettingsButtonProps {
  onClick: () => void
  className?: string
}

export function PlaylistSettingsButton({ onClick, className }: PlaylistSettingsButtonProps) {
  return (
    <Button
      type="button"
      variant="outline"
      onClick={onClick}
      aria-label="Playlist settings"
      className={playlistActionButtonClass(className)}
    >
      <span className={playlistActionIconFrameClass}>
        <img
          src={settingsMopBucketIcon}
          alt=""
          className="size-full rounded-full object-cover"
        />
      </span>
      <span className={playlistActionLabelClass}>Settings</span>
    </Button>
  )
}
