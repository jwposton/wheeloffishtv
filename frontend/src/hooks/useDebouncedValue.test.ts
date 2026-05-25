import { act, renderHook } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { useDebouncedValue } from "./useDebouncedValue"

describe("useDebouncedValue", () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it("delays value update by 300ms", () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebouncedValue(value, 300),
      { initialProps: { value: "alpha" } },
    )

    expect(result.current).toBe("alpha")

    rerender({ value: "beta" })
    expect(result.current).toBe("alpha")

    act(() => {
      vi.advanceTimersByTime(299)
    })
    expect(result.current).toBe("alpha")

    act(() => {
      vi.advanceTimersByTime(1)
    })
    expect(result.current).toBe("beta")
  })
})
