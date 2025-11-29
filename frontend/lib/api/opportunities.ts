/**
 * API functions for opportunities.
 */

import { api } from "./client";

export interface Opportunity {
  id: number;
  opportunity_code: string;
  opportunity_type: string | null;
  nato_body: string | null;
  opportunity_name: string;
  url: string;
  pdf_url: string | null;
  source_url: string | null;
  contract_type: string | null;
  document_classification: string | null;
  response_classification: string | null;
  contract_duration: string | null;
  currency: string | null;
  eligible_organization_types: string | null;
  clarification_deadline: string | null;
  clarification_instructions: string | null;
  bid_closing_date: string | null;
  expected_contract_award_date: string | null;
  bid_validity_days: number | null;
  clarification_deadline_parsed: string | null;
  bid_closing_date_parsed: string | null;
  expected_contract_award_date_parsed: string | null;
  required_documents: string | null;
  proposal_content: string | null;
  submission_instructions: string | null;
  evaluation_criteria: string | null;
  evaluation_criteria_full: string | null;
  bid_compliance_criteria: string | null;
  partial_bidding_allowed: boolean | null;
  contact_person: string | null;
  contact_email: string | null;
  summary: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_checked_at: string | null;
  opportunity_posted_date: string | null;
  extracted_at: string | null;
  content_hash: string | null;
  last_content_update: string | null;
  update_count: number;
  last_changed_fields: string[] | null;
  amendment_count: number;
  has_amendments: boolean;
  last_amendment_at: string | null;
  removed_at: string | null;
}

export interface OpportunityListResponse {
  items: Opportunity[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// For compatibility with original structure
export interface OpportunityListResponseLegacy {
  opportunities: Opportunity[];
  total: number;
  page: number;
  page_size: number;
}

export interface GetOpportunitiesParams {
  is_active?: boolean;
  page?: number;
  page_size?: number;
  opportunity_type?: string[];
  nato_body?: string[];
  search?: string;
  closing_in_7_days?: boolean;
  new_this_week?: boolean;
  updated_this_week?: boolean;
  sort_by?: string;
}

export async function getOpportunities(
  params: GetOpportunitiesParams = {}
): Promise<OpportunityListResponseLegacy> {
  const searchParams = new URLSearchParams();
  
  if (params.is_active !== undefined) {
    searchParams.append("is_active", params.is_active.toString());
  }
  if (params.page !== undefined) {
    searchParams.append("page", params.page.toString());
  }
  if (params.page_size !== undefined) {
    searchParams.append("page_size", params.page_size.toString());
  }
  if (params.opportunity_type && params.opportunity_type.length > 0) {
    params.opportunity_type.forEach(type => {
      searchParams.append("opportunity_type", type);
    });
  }
  if (params.nato_body && params.nato_body.length > 0) {
    params.nato_body.forEach(body => {
      searchParams.append("nato_body", body);
    });
  }
  if (params.search) {
    searchParams.append("search", params.search);
  }
  if (params.closing_in_7_days !== undefined && params.closing_in_7_days === true) {
    searchParams.append("closing_in_7_days", "true");
  }
  if (params.new_this_week !== undefined && params.new_this_week === true) {
    searchParams.append("new_this_week", "true");
  }
  if (params.updated_this_week !== undefined && params.updated_this_week === true) {
    searchParams.append("updated_this_week", "true");
  }
  if (params.sort_by) {
    searchParams.append("sort_by", params.sort_by);
  }

  const queryString = searchParams.toString();
  const endpoint = `/api/v1/opportunities${queryString ? `?${queryString}` : ""}`;
  
  const response = await api.get<OpportunityListResponse>(endpoint);
  
  // Convert to legacy format for compatibility
  return {
    opportunities: response.items,
    total: response.total,
    page: response.page,
    page_size: response.page_size,
  };
}

export async function getOpportunity(id: number): Promise<Opportunity> {
  return api.get<Opportunity>(`/api/v1/opportunities/${id}`);
}

