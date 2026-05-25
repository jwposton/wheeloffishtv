import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { ThemeProvider } from "@/components/layout/ThemeProvider"
import App from "./App"

describe("App", () => {
  it("renders the operator shell heading", () => {
    render(
      <ThemeProvider>
        <App />
      </ThemeProvider>,
    )
    expect(
      screen.getByRole("heading", { name: "Wheel of Fish TV" }),
    ).toBeInTheDocument()
  })
})
