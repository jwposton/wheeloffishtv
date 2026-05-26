import { useCallback, useEffect, useState } from "react"

export type FeedbackVariant = "success" | "info" | "error"

export interface TransientFeedback {
  variant: FeedbackVariant
  message: string
}

export function useTransientFeedback(durationMs = 2500) {
  const [feedback, setFeedback] = useState<TransientFeedback | null>(null)

  useEffect(() => {
    if (!feedback) {
      return
    }
    const timer = window.setTimeout(() => setFeedback(null), durationMs)
    return () => window.clearTimeout(timer)
  }, [durationMs, feedback])

  const showFeedback = useCallback((next: TransientFeedback) => {
    setFeedback(next)
  }, [])

  return { feedback, showFeedback }
}
