import { act, renderHook } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { useRemoveConfirmSession } from "@/hooks/useRemoveConfirmSession"

describe("useRemoveConfirmSession", () => {
  it("resets skip flag on unmount", () => {
    const { result, unmount } = renderHook(() => useRemoveConfirmSession())

    act(() => result.current.enableSkipRemoveConfirm())
    expect(result.current.skipRemoveConfirm).toBe(true)

    unmount()

    const { result: next } = renderHook(() => useRemoveConfirmSession())
    expect(next.current.skipRemoveConfirm).toBe(false)
  })

  it("resetSkipRemoveConfirm clears the flag", () => {
    const { result } = renderHook(() => useRemoveConfirmSession())

    act(() => result.current.enableSkipRemoveConfirm())
    act(() => result.current.resetSkipRemoveConfirm())

    expect(result.current.skipRemoveConfirm).toBe(false)
  })
})
