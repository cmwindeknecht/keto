import type { Metadata } from "next";
import { Header } from "@/components/Header";
import { Providers } from "./provider";
import "./globals.css";

export const metadata: Metadata = {
  title: "Keto Validator",
  description: "Recipe and nutrition tracking for keto diets",
};

export default function RootLayout({ children }: { readonly children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-50">
        <Providers>
          <Header />
          <main className="max-w-7xl mx-auto px-4 py-8">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
