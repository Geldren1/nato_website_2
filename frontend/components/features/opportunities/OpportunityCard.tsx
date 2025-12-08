"use client";

import { useState } from "react";
import { Opportunity } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { Info, Link as LinkIcon, FileText, Sparkles, RefreshCw } from "lucide-react";
import { Card, Badge } from "@/components/ui";
import OpportunityDetailsModal from "./OpportunityDetailsModal";
import { getOpportunityFields } from "@/lib/opportunityFields";
import { OpportunityCardFields } from "./OpportunityFieldRenderers";

interface OpportunityCardProps {
  opportunity: Opportunity;
}

export default function OpportunityCard({ opportunity }: OpportunityCardProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  // Get field configuration for this opportunity type
  const fieldConfig = getOpportunityFields(opportunity.opportunity_type);

  const getTypeVariant = (type: string | null): "primary" | "success" | "warning" | "info" | "default" => {
    if (!type) return "default";
    if (type === "RFP") return "primary";
    if (type === "RFI") return "success";
    if (type === "RFIP") return "success";  // Same as RFI
    if (type === "IFIB") return "info";
    if (type === "NOI") return "warning";
    return "default";
  };

  // Check if opportunity is new (created today)
  const isNew = (): boolean => {
    if (!opportunity.created_at) return false;
    const createdDate = new Date(opportunity.created_at);
    const today = new Date();
    return (
      createdDate.getFullYear() === today.getFullYear() &&
      createdDate.getMonth() === today.getMonth() &&
      createdDate.getDate() === today.getDate()
    );
  };

  // Check if opportunity has a recent amendment (PDF URL contains _amdt and was amended in last 5 days)
  const hasRecentAmendment = (): boolean => {
    // Must have a PDF URL with amendment pattern
    if (!opportunity.pdf_url) return false;
    if (!opportunity.pdf_url.toLowerCase().includes('_amdt')) return false;
    
    // Must have been amended recently (within last 5 days)
    if (!opportunity.last_amendment_at) return false;
    const amendmentDate = new Date(opportunity.last_amendment_at);
    const today = new Date();
    const daysDiff = Math.floor((today.getTime() - amendmentDate.getTime()) / (1000 * 60 * 60 * 24));
    return daysDiff <= 5 && daysDiff >= 0;
  };

  return (
    <>
      <OpportunityDetailsModal
        opportunity={opportunity}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
      <Card variant="elevated" hover>
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-3 flex-wrap">
            {opportunity.opportunity_type && (
              <Badge variant={getTypeVariant(opportunity.opportunity_type)}>
                {opportunity.opportunity_type}
              </Badge>
            )}
            {opportunity.nato_body && (
              <Badge variant="default">{opportunity.nato_body}</Badge>
            )}
            {isNew() && (
              <Badge 
                variant="success" 
                className="flex items-center gap-1 bg-green-500 text-white font-semibold"
              >
                <Sparkles className="w-3 h-3" />
                NEW
              </Badge>
            )}
            {hasRecentAmendment() && !isNew() && (
              <Badge 
                variant="warning" 
                className="flex items-center gap-1 bg-orange-500 text-white font-semibold"
              >
                <RefreshCw className="w-3 h-3" />
                UPDATE
              </Badge>
            )}
            {opportunity.opportunity_code && (
              <span className="text-xs text-slate-500 font-mono">
                {opportunity.opportunity_code}
              </span>
            )}
          </div>
          <h3 className="text-xl font-bold text-slate-900 mb-2 leading-snug">
            {opportunity.opportunity_name}
          </h3>
        </div>

        <OpportunityCardFields opportunity={opportunity} fieldConfig={fieldConfig} />

        <div className="flex items-center gap-3 pt-4 border-t border-slate-200">
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-1.5 p-2 text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition"
            title="View Full Details"
            aria-label="View Full Details"
          >
            <Info className="w-4 h-4" />
          </button>
          {opportunity.url && (
            <a
              href={opportunity.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 p-2 text-slate-600 hover:text-slate-700 hover:bg-slate-50 rounded-lg transition"
              title="Link to opportunity page"
              aria-label="Link to opportunity page"
            >
              <LinkIcon className="w-4 h-4" />
            </a>
          )}
          {opportunity.pdf_url && (
            <a
              href={opportunity.pdf_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-700"
            >
              <FileText className="w-4 h-4" />
              PDF
            </a>
          )}
          <div className="text-xs text-slate-500 ml-auto flex flex-col items-end gap-0.5">
            {opportunity.created_at && (
              <span>Created {formatDate(opportunity.created_at)}</span>
            )}
            {opportunity.last_amendment_at && (
              <span>Amended {formatDate(opportunity.last_amendment_at)}</span>
            )}
          </div>
        </div>
      </Card>
    </>
  );
}

