import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import Filters from "./Filters";

test("clicking a color swatch calls onColorChange with that hex", () => {
  const onColorChange = jest.fn();
  render(
    <Filters
      colors={["#dc143c", "#00ff00"]}
      tags={["Shoe"]}
      selectedColor=""
      selectedTag=""
      onColorChange={onColorChange}
      onTagChange={jest.fn()}
    />
  );

  fireEvent.click(screen.getByLabelText("Filter by #dc143c"));
  expect(onColorChange).toHaveBeenCalledWith("#dc143c");
});

test("selecting a tag calls onTagChange with the selected value", () => {
  const onTagChange = jest.fn();
  render(
    <Filters
      colors={[]}
      tags={["Shoe", "Bag"]}
      selectedColor=""
      selectedTag=""
      onColorChange={jest.fn()}
      onTagChange={onTagChange}
    />
  );

  fireEvent.change(screen.getByLabelText("Filter by tag"), { target: { value: "Bag" } });
  expect(onTagChange).toHaveBeenCalledWith("Bag");
});

test("'All colors' button is marked active when no color is selected", () => {
  render(
    <Filters
      colors={["#dc143c"]}
      tags={[]}
      selectedColor=""
      selectedTag=""
      onColorChange={jest.fn()}
      onTagChange={jest.fn()}
    />
  );
  expect(screen.getByText("All colors")).toHaveClass("active");
});
