import { fireEvent, render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { SeriesPoster } from "./SeriesPoster"

describe("SeriesPoster", () => {
  it("renders centered title placeholder when thumb is missing", () => {
    render(<SeriesPoster title="The Office" thumbUrl={null} />)

    expect(screen.getByLabelText("The Office")).toBeInTheDocument()
    expect(screen.getByText("The Office")).toHaveClass("font-medium")
    expect(screen.queryByRole("img")).not.toBeInTheDocument()
  })

  it("renders placeholder after image load error", () => {
    const { container } = render(
      <SeriesPoster title="Parks and Rec" thumbUrl="/broken.jpg" />,
    )

    const image = container.querySelector("img")
    expect(image).not.toBeNull()
    fireEvent.error(image!)

    expect(screen.getByLabelText("Parks and Rec")).toBeInTheDocument()
    expect(container.querySelector("img")).toBeNull()
  })
})
