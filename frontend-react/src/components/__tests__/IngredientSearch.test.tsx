import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { IngredientSearch } from "../IngredientSearch";
import type { USDAFood } from "@/store/api/usdaApi";

const { mockSearch } = vi.hoisted(() => ({ mockSearch: vi.fn() }));

vi.mock("@/store/api/usdaApi", () => ({
  useSearchMutation: () => [mockSearch, { isLoading: false }],
}));

const makeFood = (fdcId: number, description: string, brandOwner?: string): USDAFood => ({
  fdcId,
  description,
  foodNutrients: [],
  ...(brandOwner ? { brandOwner } : {}),
});

describe("IngredientSearch", () => {
  const onSelect = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockSearch.mockReturnValue({ unwrap: vi.fn().mockResolvedValue([]) });
  });

  describe("rendering", () => {
    it("renders the default placeholder", () => {
      render(<IngredientSearch onSelect={onSelect} />);
      expect(screen.getByPlaceholderText("Search USDA database...")).toBeInTheDocument();
    });

    it("accepts a custom placeholder", () => {
      render(<IngredientSearch onSelect={onSelect} placeholder="Find food..." />);
      expect(screen.getByPlaceholderText("Find food...")).toBeInTheDocument();
    });

    it("renders the Search button", () => {
      render(<IngredientSearch onSelect={onSelect} />);
      expect(screen.getByRole("button", { name: /search/i })).toBeInTheDocument();
    });

    it("renders data type radio buttons", () => {
      render(<IngredientSearch onSelect={onSelect} />);
      expect(screen.getByRole("radio", { name: "Produce/Meat" })).toBeInTheDocument();
      expect(screen.getByRole("radio", { name: "Commercial Product" })).toBeInTheDocument();
      expect(screen.getByRole("radio", { name: "Meal" })).toBeInTheDocument();
      expect(screen.getByRole("radio", { name: "Any" })).toBeInTheDocument();
    });

    it("defaults to 'Any' radio selected (null dataType)", () => {
      render(<IngredientSearch onSelect={onSelect} />);
      expect(screen.getByRole("radio", { name: "Any" })).toBeChecked();
    });
  });

  describe("validation", () => {
    it("shows error when search is submitted with empty query", async () => {
      const user = userEvent.setup();
      render(<IngredientSearch onSelect={onSelect} />);
      await user.click(screen.getByRole("button", { name: /search/i }));
      expect(screen.getByText("Please enter a search term.")).toBeInTheDocument();
    });

    it("shows error when search is submitted with whitespace-only query", async () => {
      const user = userEvent.setup();
      render(<IngredientSearch onSelect={onSelect} />);
      await user.type(screen.getByPlaceholderText("Search USDA database..."), "   ");
      await user.click(screen.getByRole("button", { name: /search/i }));
      expect(screen.getByText("Please enter a search term.")).toBeInTheDocument();
    });

    it("clears the error when user starts typing", async () => {
      const user = userEvent.setup();
      render(<IngredientSearch onSelect={onSelect} />);
      await user.click(screen.getByRole("button", { name: /search/i }));
      expect(screen.getByText("Please enter a search term.")).toBeInTheDocument();
      await user.type(screen.getByPlaceholderText("Search USDA database..."), "c");
      expect(screen.queryByText("Please enter a search term.")).not.toBeInTheDocument();
    });
  });

  describe("search behavior", () => {
    it("calls the search mutation with the typed query", async () => {
      const user = userEvent.setup();
      render(<IngredientSearch onSelect={onSelect} />);
      await user.type(screen.getByPlaceholderText("Search USDA database..."), "chicken");
      await user.click(screen.getByRole("button", { name: /search/i }));
      expect(mockSearch).toHaveBeenCalledWith(expect.objectContaining({ query: "chicken" }));
    });

    it("includes all data types when 'Any' is selected", async () => {
      const user = userEvent.setup();
      render(<IngredientSearch onSelect={onSelect} />);
      await user.type(screen.getByPlaceholderText("Search USDA database..."), "beef");
      await user.click(screen.getByRole("button", { name: /search/i }));
      expect(mockSearch).toHaveBeenCalledWith(
        expect.objectContaining({
          dataType: expect.arrayContaining([
            "Foundation",
            "SR Legacy",
            "Branded",
            "Survey (FNDDS)",
          ]),
        })
      );
    });

    it("restricts data types when a specific type is selected", async () => {
      const user = userEvent.setup();
      render(<IngredientSearch onSelect={onSelect} />);
      await user.click(screen.getByRole("radio", { name: "Produce/Meat" }));
      await user.type(screen.getByPlaceholderText("Search USDA database..."), "beef");
      await user.click(screen.getByRole("button", { name: /search/i }));
      expect(mockSearch).toHaveBeenCalledWith(
        expect.objectContaining({ dataType: ["Foundation", "SR Legacy"] })
      );
    });

    it("triggers search on Enter key", async () => {
      const user = userEvent.setup();
      render(<IngredientSearch onSelect={onSelect} />);
      await user.type(screen.getByPlaceholderText("Search USDA database..."), "chicken{Enter}");
      expect(mockSearch).toHaveBeenCalled();
    });
  });

  describe("commercial product filter", () => {
    it("shows brand input when Commercial Product is selected", async () => {
      const user = userEvent.setup();
      render(<IngredientSearch onSelect={onSelect} />);
      await user.click(screen.getByRole("radio", { name: "Commercial Product" }));
      expect(screen.getByPlaceholderText("Brand (e.g. Frank's RedHot)")).toBeInTheDocument();
    });

    it("hides brand input for non-Commercial types", async () => {
      const user = userEvent.setup();
      render(<IngredientSearch onSelect={onSelect} />);
      await user.click(screen.getByRole("radio", { name: "Commercial Product" }));
      await user.click(screen.getByRole("radio", { name: "Produce/Meat" }));
      expect(screen.queryByPlaceholderText("Brand (e.g. Frank's RedHot)")).not.toBeInTheDocument();
    });

    it("includes brandOwner in search request when provided", async () => {
      const user = userEvent.setup();
      render(<IngredientSearch onSelect={onSelect} />);
      await user.click(screen.getByRole("radio", { name: "Commercial Product" }));
      await user.type(screen.getByPlaceholderText("Search USDA database..."), "sauce");
      await user.type(screen.getByPlaceholderText("Brand (e.g. Frank's RedHot)"), "Heinz");
      await user.click(screen.getByRole("button", { name: /search/i }));
      expect(mockSearch).toHaveBeenCalledWith(expect.objectContaining({ brandOwner: "Heinz" }));
    });
  });

  describe("results display", () => {
    it("renders returned food items", async () => {
      const user = userEvent.setup();
      mockSearch.mockReturnValue({
        unwrap: vi
          .fn()
          .mockResolvedValue([
            makeFood(1, "Chicken Breast, raw"),
            makeFood(2, "Chicken Thigh, raw"),
          ]),
      });
      render(<IngredientSearch onSelect={onSelect} />);
      await user.type(screen.getByPlaceholderText("Search USDA database..."), "chicken");
      await user.click(screen.getByRole("button", { name: /search/i }));
      expect(await screen.findByText("Chicken Breast, raw")).toBeInTheDocument();
      expect(screen.getByText("Chicken Thigh, raw")).toBeInTheDocument();
    });

    it("shows brandOwner for branded foods", async () => {
      const user = userEvent.setup();
      mockSearch.mockReturnValue({
        unwrap: vi.fn().mockResolvedValue([makeFood(1, "Hot Sauce", "Frank's RedHot")]),
      });
      render(<IngredientSearch onSelect={onSelect} />);
      await user.type(screen.getByPlaceholderText("Search USDA database..."), "hot sauce");
      await user.click(screen.getByRole("button", { name: /search/i }));
      expect(await screen.findByText(/Frank's RedHot/)).toBeInTheDocument();
    });

    it("renders no results section when search returns empty", async () => {
      const user = userEvent.setup();
      mockSearch.mockReturnValue({ unwrap: vi.fn().mockResolvedValue([]) });
      render(<IngredientSearch onSelect={onSelect} />);
      await user.type(screen.getByPlaceholderText("Search USDA database..."), "xyz123");
      await user.click(screen.getByRole("button", { name: /search/i }));
      // No results list should appear
      expect(screen.queryByRole("list")).not.toBeInTheDocument();
    });
  });

  describe("food selection", () => {
    it("calls onSelect with the chosen food", async () => {
      const user = userEvent.setup();
      const food = makeFood(42, "Broccoli, raw");
      mockSearch.mockReturnValue({ unwrap: vi.fn().mockResolvedValue([food]) });
      render(<IngredientSearch onSelect={onSelect} />);
      await user.type(screen.getByPlaceholderText("Search USDA database..."), "broccoli");
      await user.click(screen.getByRole("button", { name: /search/i }));
      await user.click(await screen.findByText("Broccoli, raw"));
      expect(onSelect).toHaveBeenCalledWith(food);
    });

    it("clears results after selection", async () => {
      const user = userEvent.setup();
      const food = makeFood(42, "Broccoli, raw");
      mockSearch.mockReturnValue({ unwrap: vi.fn().mockResolvedValue([food]) });
      render(<IngredientSearch onSelect={onSelect} />);
      await user.type(screen.getByPlaceholderText("Search USDA database..."), "broccoli");
      await user.click(screen.getByRole("button", { name: /search/i }));
      await user.click(await screen.findByText("Broccoli, raw"));
      expect(screen.queryByText("Broccoli, raw")).not.toBeInTheDocument();
    });

    it("clears query input after selection", async () => {
      const user = userEvent.setup();
      const food = makeFood(42, "Broccoli, raw");
      mockSearch.mockReturnValue({ unwrap: vi.fn().mockResolvedValue([food]) });
      render(<IngredientSearch onSelect={onSelect} />);
      const input = screen.getByPlaceholderText("Search USDA database...");
      await user.type(input, "broccoli");
      await user.click(screen.getByRole("button", { name: /search/i }));
      await user.click(await screen.findByText("Broccoli, raw"));
      expect(input).toHaveValue("");
    });
  });

  describe("error handling", () => {
    it("shows error message when search fails", async () => {
      const user = userEvent.setup();
      mockSearch.mockReturnValue({
        unwrap: vi.fn().mockRejectedValue(new Error("Network error")),
      });
      render(<IngredientSearch onSelect={onSelect} />);
      await user.type(screen.getByPlaceholderText("Search USDA database..."), "chicken");
      await user.click(screen.getByRole("button", { name: /search/i }));
      expect(await screen.findByText("Search failed. Please try again.")).toBeInTheDocument();
    });
  });

  describe("data type switching", () => {
    it("clears results when data type changes", async () => {
      const user = userEvent.setup();
      mockSearch.mockReturnValue({
        unwrap: vi.fn().mockResolvedValue([makeFood(1, "Chicken Breast, raw")]),
      });
      render(<IngredientSearch onSelect={onSelect} />);
      await user.type(screen.getByPlaceholderText("Search USDA database..."), "chicken");
      await user.click(screen.getByRole("button", { name: /search/i }));
      expect(await screen.findByText("Chicken Breast, raw")).toBeInTheDocument();

      // Switch data type — results and query should clear
      await user.click(screen.getByRole("radio", { name: "Produce/Meat" }));
      expect(screen.queryByText("Chicken Breast, raw")).not.toBeInTheDocument();
    });
  });
});
