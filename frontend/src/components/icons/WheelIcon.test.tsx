import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { WheelIcon } from "./WheelIcon"

describe("WheelIcon", () => {
  it("renders the wheel svg", () => {
    render(<WheelIcon />)
    expect(screen.getByTestId("wheel-icon")).toBeInTheDocument()
  })

  it("marks spinning state for styling", () => {
    render(<WheelIcon spinning />)
    expect(screen.getByTestId("wheel-icon")).toHaveAttribute("data-spinning", "true")
    expect(
      screen.getByTestId("wheel-disc").querySelector("animateTransform"),
    ).toBeInTheDocument()
  })

  it("does not spin when idle", () => {
    render(<WheelIcon />)
    expect(screen.getByTestId("wheel-icon")).toHaveAttribute("data-spinning", "false")
    expect(
      screen.getByTestId("wheel-disc").querySelector("animateTransform"),
    ).not.toBeInTheDocument()
  })
})
