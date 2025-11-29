"use client";

import { useEffect } from "react";
import { Opportunity } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { X, ExternalLink, FileText, Calendar, Mail, User, DollarSign, Award, Clock } from "lucide-react";
import { cn } from "@/lib/utils";

interface OpportunityDetailsModalProps {
  opportunity: Opportunity;
  isOpen: boolean;
  onClose: () => void;
}

export default function OpportunityDetailsModal({
  opportunity,
  isOpen,
  onClose,
}: OpportunityDetailsModalProps) {
  // Handle ESC key to close modal
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      document.body.style.overflow = "hidden";
    }

    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "unset";
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const getTypeColor = (type: string | null) => {
    if (!type) return "bg-slate-100 text-slate-700";
    const colors: Record<string, string> = {
      RFP: "bg-blue-100 text-blue-700",
      RFI: "bg-green-100 text-green-700",
      IFIB: "bg-purple-100 text-purple-700",
      NOI: "bg-orange-100 text-orange-700",
    };
    return colors[type] || "bg-slate-100 text-slate-700";
  };

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto"
      aria-labelledby="modal-title"
      role="dialog"
      aria-modal="true"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      ></div>

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-2xl shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
          {/* Header */}
          <div className="flex items-start justify-between p-6 border-b border-slate-200 bg-gradient-to-r from-slate-50 to-white">
            <div className="flex-1 pr-4">
              <div className="flex items-center gap-2 mb-3 flex-wrap">
                {opportunity.opportunity_type && (
                  <span
                    className={cn(
                      "px-3 py-1 rounded-lg text-xs font-semibold",
                      getTypeColor(opportunity.opportunity_type)
                    )}
                  >
                    {opportunity.opportunity_type}
                  </span>
                )}
                {opportunity.nato_body && (
                  <span className="px-3 py-1 rounded-lg text-xs font-medium bg-slate-100 text-slate-700">
                    {opportunity.nato_body}
                  </span>
                )}
                {opportunity.opportunity_code && (
                  <span className="text-xs text-slate-500 font-mono">
                    {opportunity.opportunity_code}
                  </span>
                )}
              </div>
              <h2 className="text-2xl font-bold text-slate-900 leading-tight">
                {opportunity.opportunity_name}
              </h2>
            </div>
            <button
              onClick={onClose}
              className="flex-shrink-0 p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition"
              aria-label="Close modal"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Scrollable Content */}
          <div className="flex-1 overflow-y-auto p-6">
            <div className="space-y-6">
              {/* Summary */}
              {opportunity.summary && (
                <div>
                  <h3 className="text-sm font-semibold text-slate-700 mb-2 uppercase tracking-wide">
                    Summary
                  </h3>
                  <p className="text-slate-600 leading-relaxed">{opportunity.summary}</p>
                </div>
              )}

              {/* Important Dates */}
              {(opportunity.clarification_deadline ||
                opportunity.bid_closing_date ||
                opportunity.expected_contract_award_date) && (
                <div>
                  <h3 className="text-sm font-semibold text-slate-700 mb-3 uppercase tracking-wide flex items-center gap-2">
                    <Calendar className="w-4 h-4" />
                    Important Dates
                  </h3>
                  <div className="space-y-2">
                    {opportunity.clarification_deadline && (
                      <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                        <Clock className="w-5 h-5 text-slate-400 mt-0.5 flex-shrink-0" />
                        <div>
                          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
                            Clarification Deadline
                          </div>
                          <div className="text-slate-900">{opportunity.clarification_deadline}</div>
                        </div>
                      </div>
                    )}
                    {opportunity.bid_closing_date && (
                      <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                        <Calendar className="w-5 h-5 text-slate-400 mt-0.5 flex-shrink-0" />
                        <div>
                          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
                            Bid Closing Date
                          </div>
                          <div className="text-slate-900">{opportunity.bid_closing_date}</div>
                        </div>
                      </div>
                    )}
                    {opportunity.expected_contract_award_date && (
                      <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                        <Award className="w-5 h-5 text-slate-400 mt-0.5 flex-shrink-0" />
                        <div>
                          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
                            Expected Contract Award Date
                          </div>
                          <div className="text-slate-900">{opportunity.expected_contract_award_date}</div>
                        </div>
                      </div>
                    )}
                    {opportunity.contract_duration && (
                      <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                        <Clock className="w-5 h-5 text-slate-400 mt-0.5 flex-shrink-0" />
                        <div>
                          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
                            Contract Duration
                          </div>
                          <div className="text-slate-900">{opportunity.contract_duration}</div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Contract Details */}
              {(opportunity.contract_type || opportunity.currency || opportunity.eligible_organization_types || opportunity.partial_bidding_allowed !== null) && (
                <div>
                  <h3 className="text-sm font-semibold text-slate-700 mb-3 uppercase tracking-wide flex items-center gap-2">
                    <Award className="w-4 h-4" />
                    Contract Details
                  </h3>
                  <div className="space-y-2">
                    {opportunity.contract_type && (
                      <div className="p-3 bg-slate-50 rounded-lg">
                        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">
                          Contract Type
                        </div>
                        <div className="text-slate-900">{opportunity.contract_type}</div>
                      </div>
                    )}
                    {opportunity.currency && (
                      <div className="p-3 bg-slate-50 rounded-lg">
                        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">
                          Currency
                        </div>
                        <div className="text-slate-900">{opportunity.currency}</div>
                      </div>
                    )}
                    {opportunity.eligible_organization_types && (
                      <div className="p-3 bg-slate-50 rounded-lg">
                        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">
                          Eligible Organization Types
                        </div>
                        <div className="text-slate-900">{opportunity.eligible_organization_types}</div>
                      </div>
                    )}
                    {opportunity.partial_bidding_allowed !== null && (
                      <div className="p-3 bg-slate-50 rounded-lg">
                        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">
                          Partial Bidding Allowed
                        </div>
                        <div className="text-slate-900">{opportunity.partial_bidding_allowed ? "Yes" : "No"}</div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Submission Requirements */}
              {(opportunity.proposal_content || opportunity.submission_instructions || opportunity.clarification_instructions) && (
                <div>
                  <h3 className="text-sm font-semibold text-slate-700 mb-3 uppercase tracking-wide">
                    Submission Requirements
                  </h3>
                  <div className="space-y-2">
                    {opportunity.proposal_content && (
                      <div className="p-3 bg-slate-50 rounded-lg">
                        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">
                          Proposal Content
                        </div>
                        <div className="text-slate-900">{opportunity.proposal_content}</div>
                      </div>
                    )}
                    {opportunity.submission_instructions && (
                      <div className="p-3 bg-slate-50 rounded-lg">
                        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">
                          Submission Instructions
                        </div>
                        <div className="text-slate-900 whitespace-pre-wrap">{opportunity.submission_instructions}</div>
                      </div>
                    )}
                    {opportunity.clarification_instructions && (
                      <div className="p-3 bg-slate-50 rounded-lg">
                        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">
                          Clarification Instructions
                        </div>
                        <div className="text-slate-900 whitespace-pre-wrap">{opportunity.clarification_instructions}</div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Evaluation Criteria */}
              {(opportunity.evaluation_criteria || opportunity.evaluation_criteria_full) && (
                <div>
                  <h3 className="text-sm font-semibold text-slate-700 mb-3 uppercase tracking-wide">
                    Evaluation Criteria
                  </h3>
                  <div className="space-y-2">
                    {opportunity.evaluation_criteria && (
                      <div className="p-3 bg-slate-50 rounded-lg">
                        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">
                          Summary
                        </div>
                        <div className="text-slate-900">{opportunity.evaluation_criteria}</div>
                      </div>
                    )}
                    {opportunity.evaluation_criteria_full && (
                      <div className="p-3 bg-slate-50 rounded-lg">
                        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">
                          Full Details
                        </div>
                        <div className="text-slate-900 whitespace-pre-wrap">{opportunity.evaluation_criteria_full}</div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Compliance Criteria */}
              {opportunity.bid_compliance_criteria && (
                <div>
                  <h3 className="text-sm font-semibold text-slate-700 mb-3 uppercase tracking-wide">
                    Bid Compliance Criteria
                  </h3>
                  <div className="p-3 bg-slate-50 rounded-lg">
                    <div className="text-slate-900 whitespace-pre-wrap">{opportunity.bid_compliance_criteria}</div>
                  </div>
                </div>
              )}

              {/* Contact Information */}
              {(opportunity.contact_person || opportunity.contact_email) && (
                <div>
                  <h3 className="text-sm font-semibold text-slate-700 mb-3 uppercase tracking-wide">
                    Contact Information
                  </h3>
                  <div className="space-y-2">
                    {opportunity.contact_person && (
                      <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                        <User className="w-5 h-5 text-slate-400 flex-shrink-0" />
                        <div>
                          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
                            Contact Person
                          </div>
                          <div className="text-slate-900">{opportunity.contact_person}</div>
                        </div>
                      </div>
                    )}
                    {opportunity.contact_email && (
                      <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                        <Mail className="w-5 h-5 text-slate-400 flex-shrink-0" />
                        <div>
                          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
                            Contact Email
                          </div>
                          <a
                            href={`mailto:${opportunity.contact_email}`}
                            className="text-blue-600 hover:text-blue-700 hover:underline"
                          >
                            {opportunity.contact_email}
                          </a>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Footer with Actions */}
          <div className="flex items-center justify-between p-6 border-t border-slate-200 bg-slate-50">
            <div className="flex items-center gap-3">
              {opportunity.url && (
                <a
                  href={opportunity.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg hover:bg-slate-50 transition text-sm font-medium"
                >
                  Link to opportunity page
                  <ExternalLink className="w-4 h-4" />
                </a>
              )}
              {opportunity.pdf_url && (
                <a
                  href={opportunity.pdf_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg hover:bg-slate-50 transition text-sm font-medium"
                >
                  <FileText className="w-4 h-4" />
                  View PDF
                </a>
              )}
            </div>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-800 transition text-sm font-medium"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

