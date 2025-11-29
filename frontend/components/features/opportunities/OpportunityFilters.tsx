"use client";

import { useState, useEffect } from "react";
import { Search, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface OpportunityFiltersProps {
  filters: {
    opportunity_type: string[];
    nato_body: string[];
    search: string;
  };
  onFiltersChange: (filters: {
    opportunity_type: string[];
    nato_body: string[];
    search: string;
  }) => void;
}

export default function OpportunityFilters({
  filters,
  onFiltersChange,
}: OpportunityFiltersProps) {
  const [searchValue, setSearchValue] = useState(filters.search);

  useEffect(() => {
    const timer = setTimeout(() => {
      onFiltersChange({ ...filters, search: searchValue });
    }, 300);

    return () => clearTimeout(timer);
  }, [searchValue]);

  const clearFilters = () => {
    setSearchValue("");
    onFiltersChange({
      opportunity_type: [],
      nato_body: [],
      search: "",
    });
  };

  const hasActiveFilters = filters.opportunity_type.length > 0 || filters.nato_body.length > 0 || filters.search;

  // Common opportunity types for filtering
  const commonTypes = ["RFP", "RFI", "IFIB", "NOI"];

  const handleTypeClick = (type: string) => {
    const currentTypes = filters.opportunity_type || [];
    const newTypes = currentTypes.includes(type)
      ? currentTypes.filter(t => t !== type)
      : [...currentTypes, type];
    
    onFiltersChange({
      ...filters,
      opportunity_type: newTypes,
    });
  };


  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 mb-6">
      {/* Search */}
      <div className="mb-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search opportunities..."
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            className="w-full pl-10 pr-4 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition bg-white"
          />
        </div>
      </div>

      {/* Opportunity Type Filters */}
      <div className="mb-3">
        <h3 className="text-xs font-semibold text-slate-600 mb-2 uppercase tracking-wide">Opportunity Type</h3>
        <div className="flex flex-wrap gap-1.5">
          {commonTypes.map((type) => (
            <button
              key={type}
              onClick={() => handleTypeClick(type)}
              className={cn(
                "px-3 py-1 rounded-full text-xs font-medium transition-all",
                filters.opportunity_type?.includes(type)
                  ? "bg-gradient-to-r from-slate-700 to-teal-600 text-white shadow-sm"
                  : "bg-slate-50 text-slate-600 hover:bg-slate-100 border border-slate-200"
              )}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Clear Filters */}
      {hasActiveFilters && (
        <div className="pt-3 border-t border-slate-200">
          <button
            onClick={clearFilters}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs text-slate-600 hover:text-slate-900 transition-colors"
          >
            <X className="w-3.5 h-3.5" />
            Clear all filters
          </button>
        </div>
      )}
    </div>
  );
}

