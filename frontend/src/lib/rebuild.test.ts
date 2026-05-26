import { describe, expect, it } from "vitest"

import { isRebuildInProgress } from "./rebuild"

describe("isRebuildInProgress", () => {
  it("returns true for running and queued statuses", () => {
    expect(isRebuildInProgress("running")).toBe(true)
    expect(isRebuildInProgress("queued")).toBe(true)
  })

  it("returns false for terminal and empty statuses", () => {
    expect(isRebuildInProgress("succeeded")).toBe(false)
    expect(isRebuildInProgress("partial")).toBe(false)
    expect(isRebuildInProgress("failed")).toBe(false)
    expect(isRebuildInProgress(null)).toBe(false)
    expect(isRebuildInProgress(undefined)).toBe(false)
  })
})
