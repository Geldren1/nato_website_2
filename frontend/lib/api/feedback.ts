/**
 * API functions for feedback and roadmap.
 */

import { api } from "./client";

export interface Feedback {
  id: number;
  type: "bug" | "improvement";
  title: string;
  description: string;
  status: "open" | "in_progress" | "resolved" | "rejected";
  priority: "low" | "medium" | "high" | "critical" | null;
  submitted_by: string | null;
  submitted_at: string;
  resolved_at: string | null;
  resolution_notes: string | null;
  submission_metadata: Record<string, any> | null;
}

export interface FeedbackCreate {
  type: "bug" | "improvement";
  title: string;
  description: string;
  submitted_by?: string | null;
  priority?: "low" | "medium" | "high" | "critical" | null;
  submission_metadata?: Record<string, any> | null;
}

export interface FeedbackListResponse {
  items: Feedback[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface RoadmapItem {
  id: number;
  title: string;
  description: string | null;
  category: "new_feature" | "improvement";
  status: "planned" | "in_progress" | "completed" | "cancelled";
  priority: number | null;
  target_date: string | null;
  created_at: string;
  updated_at: string;
  related_feedback_ids: number[] | null;
}

export interface RoadmapListResponse {
  items: RoadmapItem[];
  total: number;
}

/**
 * Submit new feedback.
 */
export async function createFeedback(
  feedback: FeedbackCreate
): Promise<Feedback> {
  return api.post<Feedback>("/api/v1/feedback", feedback);
}

/**
 * Get list of feedback with pagination and filtering.
 */
export async function getFeedback(params?: {
  page?: number;
  page_size?: number;
  type?: "bug" | "improvement";
  status?: "open" | "in_progress" | "resolved" | "rejected";
}): Promise<FeedbackListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.append("page", params.page.toString());
  if (params?.page_size) searchParams.append("page_size", params.page_size.toString());
  if (params?.type) searchParams.append("type", params.type);
  if (params?.status) searchParams.append("status", params.status);

  const queryString = searchParams.toString();
  const endpoint = `/api/v1/feedback${queryString ? `?${queryString}` : ""}`;
  
  return api.get<FeedbackListResponse>(endpoint);
}

/**
 * Get roadmap items.
 */
export async function getRoadmap(params?: {
  category?: "new_feature" | "improvement";
  status?: "planned" | "in_progress" | "completed" | "cancelled";
}): Promise<RoadmapListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.category) searchParams.append("category", params.category);
  if (params?.status) searchParams.append("status", params.status);

  const queryString = searchParams.toString();
  const endpoint = `/api/v1/feedback/roadmap${queryString ? `?${queryString}` : ""}`;
  
  return api.get<RoadmapListResponse>(endpoint);
}

