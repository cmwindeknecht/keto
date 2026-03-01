import Link from "next/link";

export function Header() {
  return (
    <header className="bg-gray-800 text-white shadow-md">
      <nav className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
        <Link href="/" className="text-2xl font-bold">
          Keto Validator
        </Link>
        <div className="flex gap-6">
          <Link href="/" className="hover:text-gray-300 transition">
            Home
          </Link>
          <Link href="/recipes" className="hover:text-gray-300 transition">
            Recipes
          </Link>
          <Link href="/lookup" className="hover:text-gray-300 transition">
            Quick Lookup
          </Link>
        </div>
      </nav>
    </header>
  );
}
