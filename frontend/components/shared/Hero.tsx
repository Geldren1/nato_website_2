"use client";

import Link from "next/link";
import { Badge } from "@/components/ui";

interface HeroProps {
  title?: string;
  subtitle?: string;
  hideBadge?: boolean;
}

export default function Hero({ title, subtitle, hideBadge = false }: HeroProps = {}) {
  const displayTitle = title || "NATO Contracting Opportunities";
  const displaySubtitle = subtitle || "Stay informed about procurement opportunities from NATO ACT";

  return (
    <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-4">
      <div className="text-center">
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mb-4">
          <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold text-slate-900 leading-tight">
            {displayTitle}
          </h1>
          {!hideBadge && (
            <Link href="/feedback">
              <Badge variant="warning" className="text-xs px-2 py-1 cursor-pointer hover:opacity-80 transition-opacity whitespace-nowrap">
                Beta
              </Badge>
            </Link>
          )}
        </div>
        <p className="text-lg sm:text-xl md:text-2xl lg:text-3xl text-slate-600 max-w-3xl mx-auto px-4">
          {displaySubtitle}
        </p>
      </div>
    </section>
  );
}

