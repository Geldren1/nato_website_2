"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X, Mail } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

export default function Header() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { href: "/", label: "Opportunities" },
    { href: "/feedback", label: "Feedback" },
  ];

  const isActive = (href: string) => {
    if (href === "/") {
      return pathname === "/";
    }
    return pathname?.startsWith(href);
  };

  return (
    <header className="sticky top-0 z-50 bg-white border-b border-slate-200 shadow-sm">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo / Home */}
          <div className="flex items-center">
            <Link
              href="/"
              className="text-xl font-bold text-slate-900 hover:text-teal-600 transition-colors"
            >
              NATO Opportunities
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "text-sm font-medium transition-colors",
                  isActive(link.href)
                    ? "text-teal-600"
                    : "text-slate-700 hover:text-teal-600"
                )}
              >
                {link.label}
              </Link>
            ))}
            <Link
              href="/#subscribe-section"
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-slate-700 to-teal-600 text-white text-sm font-semibold rounded-lg hover:from-slate-800 hover:to-teal-700 transition-all"
            >
              <Mail className="w-4 h-4" />
              Subscribe
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 text-slate-700 hover:text-teal-600 transition-colors"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? (
              <X className="w-6 h-6" />
            ) : (
              <Menu className="w-6 h-6" />
            )}
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden py-4 border-t border-slate-200">
            <div className="flex flex-col gap-4">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={cn(
                    "text-base font-medium transition-colors",
                    isActive(link.href)
                      ? "text-teal-600"
                      : "text-slate-700 hover:text-teal-600"
                  )}
                >
                  {link.label}
                </Link>
              ))}
              <Link
                href="/#subscribe-section"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center justify-center gap-2 px-4 py-2 bg-gradient-to-r from-slate-700 to-teal-600 text-white text-sm font-semibold rounded-lg hover:from-slate-800 hover:to-teal-700 transition-all"
              >
                <Mail className="w-4 h-4" />
                Subscribe
              </Link>
            </div>
          </div>
        )}
      </nav>
    </header>
  );
}

