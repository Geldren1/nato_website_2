/**
 * API functions for email subscriptions.
 */

import { api } from "./client";

export interface SubscribeRequest {
  email: string;
  preferences?: {
    opportunity_types?: string[];
    nato_bodies?: string[];
    notify_on_updates?: boolean;
  };
}

export interface SubscribeResponse {
  success: boolean;
  message: string;
  email: string;
}

export interface UnsubscribeRequest {
  email: string;
}

export interface UnsubscribeResponse {
  success: boolean;
  message: string;
}

/**
 * Subscribe an email address to opportunity alerts.
 */
export async function subscribeEmail(
  request: SubscribeRequest
): Promise<SubscribeResponse> {
  return api.post<SubscribeResponse>("/api/v1/subscribe", request);
}

/**
 * Unsubscribe an email address from opportunity alerts.
 */
export async function unsubscribeEmail(
  request: UnsubscribeRequest
): Promise<UnsubscribeResponse> {
  return api.post<UnsubscribeResponse>("/api/v1/subscribe/unsubscribe", request);
}

