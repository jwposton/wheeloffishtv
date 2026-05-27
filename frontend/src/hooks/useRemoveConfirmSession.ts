import { useCallback, useEffect, useState } from "react"

/** Session-scoped skip for remove-from-playlist confirmation (BL-01). */
export function useRemoveConfirmSession() {
  const [skipRemoveConfirm, setSkipRemoveConfirm] = useState(false)

  const enableSkipRemoveConfirm = useCallback(() => {
    setSkipRemoveConfirm(true)
  }, [])

  const resetSkipRemoveConfirm = useCallback(() => {
    setSkipRemoveConfirm(false)
  }, [])

  useEffect(() => () => resetSkipRemoveConfirm(), [resetSkipRemoveConfirm])

  return { skipRemoveConfirm, enableSkipRemoveConfirm, resetSkipRemoveConfirm }
}
