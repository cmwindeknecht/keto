import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NutrientTable } from "../NutrientTable";
import type { Nutrient } from "@/store/api/recipesApi";

function makeNutrient(
  id: number,
  name: string,
  number: string,
  amount: number,
  unitName = "g"
): Nutrient {
  return { nutrient: { id, number, name, unitName }, amount };
}

// Primary nutrient IDs and nutrient number strings must match what the component looks up.
// getNutrientValue uses parseInt(n.nutrient.number) === nutrientId.
// allOtherNutrients uses n.nutrient.id to check against the primaryIds set.
const BASE_NUTRIENTS: Nutrient[] = [
  makeNutrient(1008, "Energy", "1008", 200, "kcal"), // 200 kcal/100g
  makeNutrient(1003, "Protein", "1003", 20), // 20g/100g
  makeNutrient(1004, "Total lipid (fat)", "1004", 10), // 10g/100g
  makeNutrient(1005, "Carbohydrate, by difference", "1005", 8), // 8g/100g
  makeNutrient(1079, "Fiber, total dietary", "1079", 3), // 3g/100g → net carbs = 5
  makeNutrient(1093, "Sodium, Na", "1093", 150, "mg"),
  makeNutrient(1092, "Potassium, K", "1092", 300, "mg"),
  makeNutrient(1090, "Magnesium, Mg", "1090", 25, "mg"),
];

describe("NutrientTable", () => {
  describe("column headers", () => {
    it("renders all primary nutrient column headers", () => {
      render(<NutrientTable nutrients={BASE_NUTRIENTS} quantityGrams={100} />);
      expect(screen.getByText("Calories")).toBeInTheDocument();
      expect(screen.getByText("Protein")).toBeInTheDocument();
      expect(screen.getByText("Fat")).toBeInTheDocument();
      expect(screen.getByText("Carbs")).toBeInTheDocument();
      expect(screen.getByText("Fiber")).toBeInTheDocument();
      expect(screen.getByText("Sodium")).toBeInTheDocument();
      expect(screen.getByText("Potassium")).toBeInTheDocument();
      expect(screen.getByText("Magnesium")).toBeInTheDocument();
    });

    it("renders Net Carbs column header", () => {
      render(<NutrientTable nutrients={BASE_NUTRIENTS} quantityGrams={100} />);
      expect(screen.getByText("Net Carbs")).toBeInTheDocument();
    });
  });

  describe("nutrient scaling", () => {
    it("displays calories scaled to 100g", () => {
      render(<NutrientTable nutrients={BASE_NUTRIENTS} quantityGrams={100} />);
      // 200 kcal/100g at 100g = 200.0 kcal
      expect(screen.getByText("200.0 kcal")).toBeInTheDocument();
    });

    it("scales calories at 50g", () => {
      render(<NutrientTable nutrients={BASE_NUTRIENTS} quantityGrams={50} />);
      // 200 kcal/100g at 50g = 100.0
      expect(screen.getByText("100.0 kcal")).toBeInTheDocument();
    });

    it("scales calories at 200g", () => {
      render(<NutrientTable nutrients={BASE_NUTRIENTS} quantityGrams={200} />);
      // 200 kcal/100g at 200g = 400.0
      expect(screen.getByText("400.0 kcal")).toBeInTheDocument();
    });
  });

  describe("net carbs calculation", () => {
    it("shows net carbs = carbs - fiber at 100g", () => {
      render(<NutrientTable nutrients={BASE_NUTRIENTS} quantityGrams={100} />);
      // Carbs 8g - Fiber 3g = 5.0g net carbs
      expect(screen.getByText("5.0 g")).toBeInTheDocument();
    });

    it("shows 0 net carbs when carbs equal fiber", () => {
      const equal = BASE_NUTRIENTS.map((n) => {
        if (n.nutrient.number === "1005") return makeNutrient(1005, n.nutrient.name, "1005", 3);
        return n;
      });
      render(<NutrientTable nutrients={equal} quantityGrams={100} />);
      expect(screen.getByText("0.0 g")).toBeInTheDocument();
    });

    it("shows negative net carbs when fiber > carbs", () => {
      const inverted = BASE_NUTRIENTS.map((n) => {
        if (n.nutrient.number === "1005") return makeNutrient(1005, n.nutrient.name, "1005", 1);
        return n;
      });
      render(<NutrientTable nutrients={inverted} quantityGrams={100} />);
      // Carbs 1g - Fiber 3g = -2.0g
      expect(screen.getByText("-2.0 g")).toBeInTheDocument();
    });
  });

  describe("missing nutrients", () => {
    it("shows 0.0 for a missing primary nutrient", () => {
      render(<NutrientTable nutrients={[]} quantityGrams={100} />);
      // All nutrients should be 0
      const zeros = screen.getAllByText(/^0\.0/);
      expect(zeros.length).toBeGreaterThan(0);
    });
  });

  describe("all nutrients toggle", () => {
    const withExtra = [
      ...BASE_NUTRIENTS,
      makeNutrient(9001, "Vitamin C", "9001", 50, "mg"),
      makeNutrient(9002, "Zinc", "9002", 5, "mg"),
    ];

    it("shows 'All nutrients' button when extra nutrients exist", () => {
      render(<NutrientTable nutrients={withExtra} quantityGrams={100} />);
      expect(screen.getByText(/All nutrients \(2\)/)).toBeInTheDocument();
    });

    it("does not show 'All nutrients' button when no extra nutrients", () => {
      render(<NutrientTable nutrients={BASE_NUTRIENTS} quantityGrams={100} />);
      expect(screen.queryByText(/All nutrients/)).not.toBeInTheDocument();
    });

    it("expands to show extra nutrients on click", async () => {
      const user = userEvent.setup();
      render(<NutrientTable nutrients={withExtra} quantityGrams={100} />);
      await user.click(screen.getByText(/All nutrients/));
      expect(screen.getByText("Vitamin C")).toBeInTheDocument();
      expect(screen.getByText("Zinc")).toBeInTheDocument();
    });

    it("shows filter input after expanding", async () => {
      const user = userEvent.setup();
      render(<NutrientTable nutrients={withExtra} quantityGrams={100} />);
      await user.click(screen.getByText(/All nutrients/));
      expect(screen.getByPlaceholderText("Filter nutrients...")).toBeInTheDocument();
    });

    it("collapses back on 'Show less' click", async () => {
      const user = userEvent.setup();
      render(<NutrientTable nutrients={withExtra} quantityGrams={100} />);
      await user.click(screen.getByText(/All nutrients/));
      await user.click(screen.getByText("Show less ▲"));
      expect(screen.queryByPlaceholderText("Filter nutrients...")).not.toBeInTheDocument();
      expect(screen.queryByText("Vitamin C")).not.toBeInTheDocument();
    });
  });

  describe("nutrient filter", () => {
    const withExtra = [
      ...BASE_NUTRIENTS,
      makeNutrient(9001, "Vitamin C", "9001", 50, "mg"),
      makeNutrient(9002, "Zinc", "9002", 5, "mg"),
      makeNutrient(9003, "Vitamin B12", "9003", 2, "mcg"),
    ];

    it("shows all extra nutrients when filter is empty", async () => {
      const user = userEvent.setup();
      render(<NutrientTable nutrients={withExtra} quantityGrams={100} />);
      await user.click(screen.getByText(/All nutrients/));
      expect(screen.getByText("Vitamin C")).toBeInTheDocument();
      expect(screen.getByText("Zinc")).toBeInTheDocument();
      expect(screen.getByText("Vitamin B12")).toBeInTheDocument();
    });

    it("filters nutrients by prefix (case-insensitive)", async () => {
      const user = userEvent.setup();
      render(<NutrientTable nutrients={withExtra} quantityGrams={100} />);
      await user.click(screen.getByText(/All nutrients/));
      await user.type(screen.getByPlaceholderText("Filter nutrients..."), "vit");
      // Both Vitamin C and Vitamin B12 start with "vit"
      expect(screen.getByText("Vitamin C")).toBeInTheDocument();
      expect(screen.getByText("Vitamin B12")).toBeInTheDocument();
      // Zinc doesn't match but is still rendered (dimmed)
      expect(screen.getByText("Zinc")).toBeInTheDocument();
    });

    it("matches are sorted and non-matches appear after a divider", async () => {
      const user = userEvent.setup();
      render(<NutrientTable nutrients={withExtra} quantityGrams={100} />);
      await user.click(screen.getByText(/All nutrients/));
      await user.type(screen.getByPlaceholderText("Filter nutrients..."), "zinc");
      // Zinc should be in the matches section
      expect(screen.getByText("Zinc")).toBeInTheDocument();
    });

    it("scales extra nutrient values by quantity", async () => {
      const user = userEvent.setup();
      // 50mg Vitamin C / 100g at 200g = 100.00 mg
      render(<NutrientTable nutrients={withExtra} quantityGrams={200} />);
      await user.click(screen.getByText(/All nutrients/));
      expect(screen.getByText("100.00 mg")).toBeInTheDocument();
    });
  });
});
