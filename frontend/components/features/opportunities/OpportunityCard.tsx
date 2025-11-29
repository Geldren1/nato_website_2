"use client";

import { useState } from "react";
import { Opportunity } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { Calendar, Info, Link as LinkIcon, FileText } from "lucide-react";
import { Card, Badge } from "@/components/ui";
import OpportunityDetailsModal from "./OpportunityDetailsModal";

interface OpportunityCardProps {
  opportunity: Opportunity;
}

export default function OpportunityCard({ opportunity }: OpportunityCardProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const getTypeVariant = (type: string | null): "primary" | "success" | "warning" | "info" | "default" => {
    if (!type) return "default";
    if (type === "RFP") return "primary";
    if (type === "RFI") return "success";
    if (type === "IFIB") return "info";
    if (type === "NOI") return "warning";
    return "default";
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

        <div className="space-y-2 mb-4">
          {opportunity.bid_closing_date && (
            <div className="flex items-center gap-2 text-sm text-slate-700">
              <Calendar className="w-4 h-4 text-slate-400" />
              <span>
                <strong>Closing:</strong> {opportunity.bid_closing_date}
              </span>
            </div>
          )}
          {opportunity.clarification_deadline && (
            <div className="flex items-center gap-2 text-sm text-slate-700">
              <Calendar className="w-4 h-4 text-slate-400" />
              <span>
                <strong>Clarifications:</strong> {opportunity.clarification_deadline}
              </span>
            </div>
          )}
        </div>

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
            {opportunity.last_content_update && opportunity.last_content_update !== opportunity.created_at && (
              <span>Amended {formatDate(opportunity.last_content_update)}</span>
            )}
          </div>
        </div>
      </Card>
    </>
  );
}

