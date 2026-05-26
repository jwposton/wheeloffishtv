import type { TransientFeedback } from "@/hooks/useTransientFeedback"
import { cn } from "@/lib/utils"

interface PosterFeedbackOverlayProps {
  feedback: TransientFeedback | null
}

export function PosterFeedbackOverlay({ feedback }: PosterFeedbackOverlayProps) {
  if (!feedback) {
    return null
  }

  return (
    <div
      role="status"
      aria-live="polite"
      className={cn(
        "absolute inset-0 z-10 flex items-center justify-center rounded-[inherit] p-2 text-center text-xs leading-snug font-medium backdrop-blur-sm",
        feedback.variant === "error"
          ? "bg-destructive/90 text-destructive-foreground"
          : "bg-background/90 text-foreground",
      )}
    >
      {feedback.message}
    </div>
  )
}
