import { apiClient } from '@/api/client';
import type {
  IntentDraft,
  IntentEnvelope,
  Job,
  ParsePlan,
  PlanValidation,
} from './types';

/**
 * Intent / Job / plan capabilities from the new-arch Capability Registry (§13).
 * Submitting an Intent yields a Job the UI then polls.
 */

/** capability: narrow_intent — turns a raw draft into a typed Intent Envelope. */
export function narrowIntent(draft: IntentDraft): Promise<IntentEnvelope> {
  return apiClient.post<IntentEnvelope>('/api/v1/capabilities/narrow_intent', draft);
}

/** capability: request_clarification — resolve an AWAITING_CLARIFICATION job. */
export function requestClarification(jobId: string, answer: string): Promise<Job> {
  return apiClient.post<Job>('/api/v1/capabilities/request_clarification', { jobId, answer });
}

/** capability: create_parse_plan */
export function createParsePlan(intentUid: string): Promise<ParsePlan> {
  return apiClient.post<ParsePlan>('/api/v1/capabilities/create_parse_plan', { intentUid });
}

/** capability: validate_parse_plan */
export function validateParsePlan(planId: string): Promise<PlanValidation> {
  return apiClient.post<PlanValidation>('/api/v1/capabilities/validate_parse_plan', { planId });
}

/** capability: submit_parse_job — creates the Job for a validated intent. */
export function submitParseJob(intent: IntentEnvelope): Promise<Job> {
  return apiClient.post<Job>('/api/v1/capabilities/submit_parse_job', { intent });
}

/** capability: get_job_status */
export function getJobStatus(jobId: string): Promise<Job> {
  return apiClient.get<Job>(`/api/v1/capabilities/get_job_status/${jobId}`);
}

/** capability: request_compilation */
export function requestCompilation(jobId: string): Promise<Job> {
  return apiClient.post<Job>('/api/v1/capabilities/request_compilation', { jobId });
}

/** capability: request_math_analysis */
export function requestMathAnalysis(jobId: string): Promise<Job> {
  return apiClient.post<Job>('/api/v1/capabilities/request_math_analysis', { jobId });
}
