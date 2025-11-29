"use client";

import { useState, useEffect } from "react";
import Hero from "@/components/shared/Hero";
import { OpportunityFilters, OpportunityList } from "@/components/features/opportunities";
import { getOpportunities, type Opportunity } from "@/lib/api";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

export default function HomePage() {
  const [isLoading, setIsLoading] = useState(true);
  const [filters, setFilters] = useState({
    opportunity_type: [] as string[],
    nato_body: [] as string[],
    search: "",
  });
  const [quickFilters, setQuickFilters] = useState({
    closing_in_7_days: false,
    new_this_week: false,
    updated_this_week: false,
  });
  const [sortBy, setSortBy] = useState("closing_date_asc");
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 24;

  // Load opportunities when filters, quick filters, sort, or page change
  useEffect(() => {
    setIsLoading(true);
    getOpportunities({
      is_active: true,
      page,
      page_size: pageSize,
      opportunity_type: filters.opportunity_type.length > 0 ? filters.opportunity_type : undefined,
      nato_body: filters.nato_body.length > 0 ? filters.nato_body : undefined,
      search: filters.search || undefined,
      closing_in_7_days: quickFilters.closing_in_7_days ? true : undefined,
      new_this_week: quickFilters.new_this_week ? true : undefined,
      updated_this_week: quickFilters.updated_this_week ? true : undefined,
      sort_by: sortBy,
    })
      .then((data) => {
        setOpportunities(data.opportunities);
        setTotal(data.total);
        setIsLoading(false);
      })
      .catch((error) => {
        console.error("Error loading opportunities:", error);
        setIsLoading(false);
      });
  }, [filters, quickFilters, sortBy, page]);
  
  // Reset to page 1 when filters, quick filters, or sort change
  useEffect(() => {
    setPage(1);
  }, [filters, quickFilters, sortBy]);
  
  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      {/* Landing Sections */}
      <Hero />

      {/* Opportunities Section */}
      <div id="opportunities-section" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-4 pb-12">
        {/* Filters and Sort */}
        <div className="mb-6 space-y-4">
          <OpportunityFilters
            filters={filters}
            onFiltersChange={(newFilters) => {
              setFilters(newFilters);
              setPage(1);
            }}
          />
          
          {/* Quick Filters */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-medium text-slate-700 mr-2">Quick filters:</span>
            <button
              onClick={() => {
                setQuickFilters(prev => ({ ...prev, closing_in_7_days: !prev.closing_in_7_days }));
                setPage(1);
              }}
              className={cn(
                "px-4 py-2 rounded-lg text-sm font-medium transition",
                quickFilters.closing_in_7_days
                  ? "bg-teal-600 text-white hover:bg-teal-700"
                  : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              )}
            >
              Closing in next 7 days
            </button>
            <button
              onClick={() => {
                setQuickFilters(prev => ({ ...prev, new_this_week: !prev.new_this_week }));
                setPage(1);
              }}
              className={cn(
                "px-4 py-2 rounded-lg text-sm font-medium transition",
                quickFilters.new_this_week
                  ? "bg-teal-600 text-white hover:bg-teal-700"
                  : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              )}
            >
              New this week
            </button>
            <button
              onClick={() => {
                setQuickFilters(prev => ({ ...prev, updated_this_week: !prev.updated_this_week }));
                setPage(1);
              }}
              className={cn(
                "px-4 py-2 rounded-lg text-sm font-medium transition",
                quickFilters.updated_this_week
                  ? "bg-teal-600 text-white hover:bg-teal-700"
                  : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              )}
            >
              Amended this week
            </button>
            {(quickFilters.closing_in_7_days || quickFilters.new_this_week || quickFilters.updated_this_week) && (
              <button
                onClick={() => {
                  setQuickFilters({
                    closing_in_7_days: false,
                    new_this_week: false,
                    updated_this_week: false,
                  });
                  setPage(1);
                }}
                className="px-4 py-2 rounded-lg text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition"
              >
                Clear quick filters
              </button>
            )}
          </div>
          
          {/* Sort Selector */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <label htmlFor="sort-select" className="text-sm font-medium text-slate-700">
                Sort by:
              </label>
              <select
                id="sort-select"
                value={sortBy}
                onChange={(e) => {
                  setSortBy(e.target.value);
                  setPage(1);
                }}
                className="px-4 py-2 border border-slate-300 rounded-lg text-sm text-slate-700 bg-white hover:border-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition"
              >
                <option value="closing_date_asc">Closing Date (Soonest First)</option>
                <option value="closing_date_desc">Closing Date (Furthest First)</option>
                <option value="recently_updated">Recently Amended</option>
                <option value="recently_added">Recently Added</option>
                <option value="name_asc">Name (A-Z)</option>
              </select>
            </div>
            <div className="text-sm text-slate-600">
              {total > 0 && (
                <span>
                  Showing {((page - 1) * pageSize) + 1}-{Math.min(page * pageSize, total)} of {total} opportunities
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Content Grid */}
        <div>
          <OpportunityList
            opportunities={opportunities}
            isLoading={isLoading}
            total={total}
          />

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-8 flex items-center justify-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className={cn(
                  "px-4 py-2 rounded-lg text-sm font-medium transition",
                  page === 1
                    ? "bg-slate-100 text-slate-400 cursor-not-allowed"
                    : "bg-white text-slate-700 hover:bg-slate-50 border border-slate-300 hover:border-slate-400"
                )}
                aria-label="Previous page"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              
              {/* Page Numbers */}
              <div className="flex items-center gap-1">
                {(() => {
                  const pages: (number | string)[] = [];
                  
                  if (totalPages <= 7) {
                    for (let i = 1; i <= totalPages; i++) {
                      pages.push(i);
                    }
                  } else {
                    pages.push(1);
                    
                    if (page <= 4) {
                      for (let i = 2; i <= 5; i++) {
                        pages.push(i);
                      }
                      pages.push('ellipsis');
                      pages.push(totalPages);
                    } else if (page >= totalPages - 3) {
                      pages.push('ellipsis');
                      for (let i = totalPages - 4; i <= totalPages; i++) {
                        pages.push(i);
                      }
                    } else {
                      pages.push('ellipsis');
                      pages.push(page - 1);
                      pages.push(page);
                      pages.push(page + 1);
                      pages.push('ellipsis');
                      pages.push(totalPages);
                    }
                  }
                  
                  return pages.map((pageNum, idx) => {
                    if (pageNum === 'ellipsis') {
                      return (
                        <span key={`ellipsis-${idx}`} className="px-2 text-slate-400">
                          ...
                        </span>
                      );
                    }
                    
                    return (
                      <button
                        key={pageNum}
                        onClick={() => setPage(pageNum as number)}
                        className={cn(
                          "px-4 py-2 rounded-lg text-sm font-medium transition min-w-[40px]",
                          page === pageNum
                            ? "bg-teal-600 text-white shadow-sm"
                            : "bg-white text-slate-700 hover:bg-slate-50 border border-slate-300 hover:border-slate-400"
                        )}
                      >
                        {pageNum}
                      </button>
                    );
                  });
                })()}
              </div>
              
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className={cn(
                  "px-4 py-2 rounded-lg text-sm font-medium transition",
                  page === totalPages
                    ? "bg-slate-100 text-slate-400 cursor-not-allowed"
                    : "bg-white text-slate-700 hover:bg-slate-50 border border-slate-300 hover:border-slate-400"
                )}
                aria-label="Next page"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
