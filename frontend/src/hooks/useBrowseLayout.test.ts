import { act, renderHook } from "@testing-library/react"
import { beforeEach, describe, expect, it } from "vitest"

import { useBrowseLayout } from "./useBrowseLayout"

const STORAGE_KEY = "wof.browse.layout"

describe("useBrowseLayout", () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it("persists grid|list to localStorage key wof.browse.layout", () => {
    const { result } = renderHook(() => useBrowseLayout())

    expect(result.current.layout).toBe("grid")
    expect(localStorage.getItem(STORAGE_KEY)).toBe("grid")

    act(() => {
      result.current.setLayout("list")
    })

    expect(result.current.layout).toBe("list")
    expect(localStorage.getItem(STORAGE_KEY)).toBe("list")
  })
})
