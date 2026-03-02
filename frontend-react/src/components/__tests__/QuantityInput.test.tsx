import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QuantityInput } from "../QuantityInput";
import { GRAMS_PER_UNIT } from "@/lib/units";

describe("QuantityInput", () => {
  describe("default (weight) mode", () => {
    it("renders a number input", () => {
      render(<QuantityInput value={100} onChange={vi.fn()} />);
      expect(screen.getByRole("spinbutton")).toBeInTheDocument();
    });

    it("displays the initial value in grams", () => {
      render(<QuantityInput value={100} onChange={vi.fn()} />);
      expect(screen.getByRole("spinbutton")).toHaveValue(100);
    });

    it("renders the unit selector", () => {
      render(<QuantityInput value={100} onChange={vi.fn()} />);
      expect(screen.getByRole("combobox")).toBeInTheDocument();
    });

    it("defaults unit selector to grams", () => {
      render(<QuantityInput value={100} onChange={vi.fn()} />);
      expect(screen.getByRole("combobox")).toHaveValue("g");
    });

    it("shows g, oz, and lbs options", () => {
      render(<QuantityInput value={100} onChange={vi.fn()} />);
      const select = screen.getByRole("combobox");
      const options = Array.from(select.querySelectorAll("option")).map((o) => o.value);
      expect(options).toContain("g");
      expect(options).toContain("oz");
      expect(options).toContain("lb");
    });

    it("calls onChange with grams when value is typed", async () => {
      const onChange = vi.fn();
      const user = userEvent.setup();
      render(<QuantityInput value={100} onChange={onChange} />);
      const input = screen.getByRole("spinbutton");
      await user.clear(input);
      await user.type(input, "200");
      expect(onChange).toHaveBeenLastCalledWith(200);
    });

    it("does not call onChange for non-numeric input", async () => {
      const onChange = vi.fn();
      const user = userEvent.setup();
      render(<QuantityInput value={100} onChange={onChange} />);
      await user.clear(screen.getByRole("spinbutton"));
      // Clearing gives NaN, which the component ignores
      expect(onChange).not.toHaveBeenCalled();
    });

    it("does not call onChange for zero or negative", async () => {
      const onChange = vi.fn();
      const user = userEvent.setup();
      render(<QuantityInput value={100} onChange={onChange} />);
      const input = screen.getByRole("spinbutton");
      await user.clear(input);
      await user.type(input, "0");
      expect(onChange).not.toHaveBeenCalled();
    });

    it("converts displayed value when switching to oz", async () => {
      const user = userEvent.setup();
      render(<QuantityInput value={100} onChange={vi.fn()} />);
      await user.selectOptions(screen.getByRole("combobox"), "oz");
      const input = screen.getByRole("spinbutton") as HTMLInputElement;
      expect(Number.parseFloat(input.value)).toBeCloseTo(100 / GRAMS_PER_UNIT.oz, 1);
    });

    it("converts displayed value when switching to lb", async () => {
      const user = userEvent.setup();
      render(<QuantityInput value={453.592} onChange={vi.fn()} />);
      await user.selectOptions(screen.getByRole("combobox"), "lb");
      const input = screen.getByRole("spinbutton") as HTMLInputElement;
      expect(Number.parseFloat(input.value)).toBeCloseTo(1, 2);
    });

    it("calls onChange in grams when value typed after switching to oz", async () => {
      const onChange = vi.fn();
      const user = userEvent.setup();
      render(<QuantityInput value={100} onChange={onChange} />);
      await user.selectOptions(screen.getByRole("combobox"), "oz");
      const input = screen.getByRole("spinbutton");
      await user.clear(input);
      await user.type(input, "1");
      // 1 oz → 28.3495g
      expect(onChange).toHaveBeenLastCalledWith(expect.closeTo(GRAMS_PER_UNIT.oz, 0));
    });

    it("accepts optional inputId and applies it to the input", () => {
      render(<QuantityInput value={100} onChange={vi.fn()} inputId="test-input" />);
      expect(screen.getByRole("spinbutton")).toHaveAttribute("id", "test-input");
    });

    it("applies custom inputClassName to the input", () => {
      render(<QuantityInput value={100} onChange={vi.fn()} inputClassName="custom-class" />);
      expect(screen.getByRole("spinbutton")).toHaveClass("custom-class");
    });
  });

  describe("serving mode (servingGrams provided)", () => {
    it("shows the serving label instead of unit selector", () => {
      render(
        <QuantityInput value={240} onChange={vi.fn()} servingGrams={240} servingLabel="1 cup" />
      );
      expect(screen.getByText("1 cup")).toBeInTheDocument();
      expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
    });

    it("defaults label to 'serving' when servingLabel is absent", () => {
      render(<QuantityInput value={240} onChange={vi.fn()} servingGrams={240} />);
      expect(screen.getByText("serving")).toBeInTheDocument();
    });

    it("displays value as count (value / servingGrams)", () => {
      // 240g / 240g per serving = 1 serving
      render(
        <QuantityInput value={240} onChange={vi.fn()} servingGrams={240} servingLabel="1 cup" />
      );
      expect(screen.getByRole("spinbutton")).toHaveValue(1);
    });

    it("displays 2 for two servings", () => {
      // 480g / 240g per serving = 2
      render(
        <QuantityInput value={480} onChange={vi.fn()} servingGrams={240} servingLabel="1 cup" />
      );
      expect(screen.getByRole("spinbutton")).toHaveValue(2);
    });

    it("calls onChange with grams (count × servingGrams)", async () => {
      const onChange = vi.fn();
      const user = userEvent.setup();
      render(
        <QuantityInput value={240} onChange={onChange} servingGrams={240} servingLabel="1 cup" />
      );
      const input = screen.getByRole("spinbutton");
      await user.clear(input);
      await user.type(input, "2");
      expect(onChange).toHaveBeenLastCalledWith(480); // 2 * 240
    });

    it("calls onChange correctly for fractional servings", async () => {
      const onChange = vi.fn();
      const user = userEvent.setup();
      render(
        <QuantityInput value={240} onChange={onChange} servingGrams={240} servingLabel="1 cup" />
      );
      const input = screen.getByRole("spinbutton");
      await user.clear(input);
      await user.type(input, "0.5");
      expect(onChange).toHaveBeenLastCalledWith(120); // 0.5 * 240
    });
  });
});
