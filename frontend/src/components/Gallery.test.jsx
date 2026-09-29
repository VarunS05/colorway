import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import Gallery from "./Gallery";

const sampleItems = [
  {
    id: "1",
    url: "https://example.com/shoe.png",
    sourceKey: "shoe.png",
    colorway: { hex: "#dc143c" },
    tags: [{ name: "Shoe" }, { name: "Footwear" }],
  },
];

test("renders empty state when there are no items", () => {
  render(<Gallery items={[]} />);
  expect(screen.getByText(/no images yet/i)).toBeInTheDocument();
});

test("renders an image with its color swatch and tags", () => {
  render(<Gallery items={sampleItems} />);
  expect(screen.getByAltText("shoe.png")).toHaveAttribute("src", sampleItems[0].url);
  expect(screen.getByTestId("swatch")).toHaveStyle({ backgroundColor: "rgb(220, 20, 60)" });
  expect(screen.getByText("Shoe")).toBeInTheDocument();
  expect(screen.getByText("Footwear")).toBeInTheDocument();
});

test("calls onDelete with the item id when delete is clicked", () => {
  const onDelete = jest.fn();
  render(<Gallery items={sampleItems} onDelete={onDelete} />);
  fireEvent.click(screen.getByRole("button", { name: /delete 1/i }));
  expect(onDelete).toHaveBeenCalledWith("1");
});
