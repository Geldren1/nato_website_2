/**
 * Type-specific field renderers for opportunity cards.
 * These components render fields based on opportunity type configuration.
 */

import React from "react";
import { Opportunity } from "@/lib/api";
import { Calendar, DollarSign } from "lucide-react";

interface DateFieldProps {
  label: string;
  value: string | null;
}

export function DateField({ label, value }: DateFieldProps) {
  if (!value) return null;
  
  return (
    <div className="flex items-center gap-2 text-sm text-slate-700">
      <Calendar className="w-4 h-4 text-slate-400" />
      <span>
        <strong>{label}:</strong> {value}
      </span>
    </div>
  );
}

interface EstimatedValueFieldProps {
  value: string | null;
}

export function EstimatedValueField({ value }: EstimatedValueFieldProps) {
  if (!value) return null;
  
  return (
    <div className="flex items-center gap-2 text-sm text-slate-700">
      <DollarSign className="w-4 h-4 text-slate-400" />
      <span>
        <strong>Estimated Value:</strong> {value}
      </span>
    </div>
  );
}

interface OpportunityCardFieldsProps {
  opportunity: Opportunity;
  fieldConfig: {
    primaryDates: Array<keyof Opportunity>;
    cardHighlightFields?: Array<keyof Opportunity>;
  };
}

export function OpportunityCardFields({
  opportunity,
  fieldConfig,
}: OpportunityCardFieldsProps) {
  const fields: React.ReactElement[] = [];
  
  // Render primary dates
  fieldConfig.primaryDates.forEach((fieldName) => {
    const value = opportunity[fieldName] as string | null;
    if (value) {
      let label = "";
      switch (fieldName) {
        case "bid_closing_date":
          label = "Closing";
          break;
        case "clarification_deadline":
          label = "Clarifications";
          break;
        case "target_bid_closing_date":
          label = "Target Closing";
          break;
        case "target_issue_date":
          label = "Target Issue";
          break;
        default:
          label = fieldName.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
      }
      fields.push(<DateField key={fieldName} label={label} value={value} />);
    }
  });
  
  // Render special fields (like estimated_value)
  if (fieldConfig.cardHighlightFields) {
    fieldConfig.cardHighlightFields.forEach((fieldName) => {
      if (fieldName === "estimated_value") {
        const value = opportunity[fieldName] as string | null;
        if (value) {
          fields.push(<EstimatedValueField key={fieldName} value={value} />);
        }
      }
    });
  }
  
  if (fields.length === 0) return null;
  
  return <div className="space-y-2 mb-4">{fields}</div>;
}

