import { cn } from "@/lib/utils"

/** Shared vertical icon action control (Rebuild, Settings, Delete). */
export function playlistActionButtonClass(className?: string) {
  return cn(
    "h-auto min-w-[4.25rem] flex-col gap-1 px-2 py-2",
    className,
  )
}

/** Icon dominates the button; label sits below in small caps. */
export const playlistActionIconFrameClass =
  "relative inline-flex size-[4.5rem] shrink-0 items-center justify-center"

export const playlistActionIconClass = "size-14 shrink-0 object-contain"

/** Image inside the action icon frame — contain avoids cropping detailed art. */
export const playlistActionIconImgClass = "size-full object-contain"

export const playlistActionLabelClass =
  "max-w-[4.25rem] truncate text-[0.58rem] font-semibold uppercase leading-tight tracking-[0.08em] text-muted-foreground"
