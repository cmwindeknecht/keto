import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { Header } from "../Header";

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    className,
  }: {
    href: string;
    children: React.ReactNode;
    className?: string;
  }) => (
    <a href={href} className={className}>
      {children}
    </a>
  ),
}));

describe("Header", () => {
  it("renders the brand name", () => {
    render(<Header />);
    expect(screen.getByText("Keto Validator")).toBeInTheDocument();
  });

  it("brand link points to home", () => {
    render(<Header />);
    expect(screen.getByRole("link", { name: "Keto Validator" })).toHaveAttribute("href", "/");
  });

  it("renders the Home navigation link", () => {
    render(<Header />);
    expect(screen.getByRole("link", { name: "Home" })).toHaveAttribute("href", "/");
  });

  it("renders the Recipes navigation link", () => {
    render(<Header />);
    expect(screen.getByRole("link", { name: "Recipes" })).toHaveAttribute("href", "/recipes");
  });

  it("renders the Quick Lookup navigation link", () => {
    render(<Header />);
    expect(screen.getByRole("link", { name: "Quick Lookup" })).toHaveAttribute("href", "/lookup");
  });

  it("renders a nav element inside a header", () => {
    const { container } = render(<Header />);
    expect(container.querySelector("header")).toBeInTheDocument();
    expect(container.querySelector("nav")).toBeInTheDocument();
  });

  it("renders exactly three nav links", () => {
    render(<Header />);
    // Home, Recipes, Quick Lookup (brand link is separate)
    const navLinks = screen
      .getAllByRole("link")
      .filter((l) => ["Home", "Recipes", "Quick Lookup"].includes(l.textContent ?? ""));
    expect(navLinks).toHaveLength(3);
  });
});
