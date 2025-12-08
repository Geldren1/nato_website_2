"use client";

import Link from "next/link";
import { Mail } from "lucide-react";

export default function Footer() {
  const currentYear = new Date().getFullYear();

  const footerLinks = {
    main: [
      { href: "/", label: "Opportunities" },
      { href: "/feedback", label: "Feedback" },
    ],
    legal: [
      { href: "/about", label: "About" },
      { href: "/privacy", label: "Privacy Policy" },
      { href: "/terms", label: "Terms of Service" },
    ],
  };

  return (
    <footer className="bg-slate-900 text-slate-300 border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Brand Section */}
          <div>
            <h3 className="text-white text-lg font-bold mb-4">NATO Opportunities</h3>
            <p className="text-sm text-slate-400 mb-4">
              Stay informed about procurement opportunities from NATO bodies.
            </p>
            <div className="flex items-center gap-2">
              <Mail className="w-4 h-4" />
              <a
                href="/#subscribe-section"
                className="text-sm text-teal-400 hover:text-teal-300 transition-colors"
              >
                Subscribe for updates
              </a>
            </div>
          </div>

          {/* Main Links */}
          <div>
            <h4 className="text-white text-sm font-semibold mb-4 uppercase tracking-wider">
              Navigation
            </h4>
            <ul className="space-y-2">
              {footerLinks.main.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-slate-400 hover:text-teal-400 transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal Links */}
          <div>
            <h4 className="text-white text-sm font-semibold mb-4 uppercase tracking-wider">
              Legal
            </h4>
            <ul className="space-y-2">
              {footerLinks.legal.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-slate-400 hover:text-teal-400 transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Copyright */}
        <div className="mt-8 pt-8 border-t border-slate-800 flex items-center justify-center">
          <p className="text-sm text-slate-500">
            © {currentYear} NATO Opportunities. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}

