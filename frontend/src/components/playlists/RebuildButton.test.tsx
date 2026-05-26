import { fireEvent, render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import { RebuildButton } from "./RebuildButton"

describe("RebuildButton", () => {
  it('renders a wheel icon with "Rebuild" label when idle', () => {
    render(<RebuildButton onClick={vi.fn()} />)

    expect(screen.getByRole("button", { name: "Rebuild" })).toBeEnabled()
    expect(screen.getByTestId("wheel-icon")).toHaveAttribute("data-spinning", "false")
    expect(screen.getByText("Rebuild")).toBeInTheDocument()
  })

  it("shows a spinning wheel and disables the button while rebuilding", () => {
    render(<RebuildButton onClick={vi.fn()} spinning />)

    const button = screen.getByRole("button", { name: "Rebuilding…" })
    expect(button).toBeDisabled()
    expect(button).toHaveAttribute("aria-busy", "true")
    expect(screen.getByTestId("wheel-icon")).toHaveAttribute("data-spinning", "true")
  })

  it("calls onClick when idle", () => {
    const onClick = vi.fn()

    render(<RebuildButton onClick={onClick} />)
    fireEvent.click(screen.getByRole("button", { name: "Rebuild" }))

    expect(onClick).toHaveBeenCalledOnce()
  })
})
