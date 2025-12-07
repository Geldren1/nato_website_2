/**
 * Field mapping configuration for different opportunity types.
 * Defines which fields are relevant for each opportunity type.
 */

import { Opportunity } from "./api";

export interface OpportunityFieldConfig {
  primaryDates: Array<keyof Opportunity>;
  secondaryDates: Array<keyof Opportunity>;
  showSections: string[];
  specialFields?: Array<keyof Opportunity>;
  cardHighlightFields?: Array<keyof Opportunity>;
}

export const OPPORTUNITY_TYPE_FIELDS: Record<string, OpportunityFieldConfig> = {
  IFIB: {
    primaryDates: ['bid_closing_date', 'clarification_deadline'],
    secondaryDates: ['expected_contract_award_date'],
    showSections: ['submission', 'evaluation', 'compliance'],
    cardHighlightFields: ['bid_closing_date', 'clarification_deadline'],
  },
  NOI: {
    primaryDates: ['target_issue_date', 'target_bid_closing_date'],
    secondaryDates: [],
    showSections: ['contract_details'],
    specialFields: ['estimated_value'],
    cardHighlightFields: ['target_bid_closing_date', 'estimated_value'],
  },
};

/**
 * Get field configuration for an opportunity type.
 * Returns default configuration if type is not found.
 */
export function getOpportunityFields(
  opportunityType: string | null
): OpportunityFieldConfig {
  if (!opportunityType) {
    // Default to IFIB-like fields
    return OPPORTUNITY_TYPE_FIELDS.IFIB;
  }
  
  return (
    OPPORTUNITY_TYPE_FIELDS[opportunityType.toUpperCase()] ||
    OPPORTUNITY_TYPE_FIELDS.IFIB
  );
}

