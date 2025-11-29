"use client";

import { Opportunity } from "@/lib/api";
import OpportunityCard from "./OpportunityCard";
import { Loader2 } from "lucide-react";

interface OpportunityListProps {
  opportunities: Opportunity[];
  isLoading?: boolean;
  total?: number;
}

export default function OpportunityList({
  opportunities,
  isLoading = false,
  total,
}: OpportunityListProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-teal-600" />
      </div>
    );
  }

  if (opportunities.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-600 text-lg">No opportunities found</p>
        <p className="text-slate-500 text-sm mt-2">
          Try adjusting your filters or check back later
        </p>
      </div>
    );
  }

  return (
    <div>
      {total !== undefined && (
        <div className="mb-4 text-sm text-slate-600">
          Showing {opportunities.length} of {total} opportunities
        </div>
      )}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {opportunities.map((opportunity) => (
          <OpportunityCard key={opportunity.id} opportunity={opportunity} />
        ))}
      </div>
    </div>
  );
}

