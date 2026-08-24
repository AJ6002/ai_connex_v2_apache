import type { ArtifactPackage } from '@/entities/artifact/types';

/**
 * Intent Envelope — what the UI sends to start any piece of work.
 * Sourced from new-arch §5.2. Tenant/user identity come from the authenticated
 * app context, never generated client-side.
 */
export interface IntentEnvelope {
  intentUid: string;
  tenantUid: string;
  userUid: string;
  siteScope?: string;
  assetScope?: string;
  goal: string;
  domain?: string;
  requestedOutputs: string[];
  requiresModel: boolean;
  requiresVisualization: boolean;
  requiresService: boolean;
  autonomyRequested?: string;
  constraints?: Record<string, unknown>;
  sourceRefs: string[];
  policyRef?: string;
}

/** Payload the Intake screen collects before an Intent Envelope is built. */
export interface IntentDraft {
  goal: string;
  domain?: string;
  requestedOutputs: string[];
  sourceRefs: string[];
}

export type JobStatus =
  | 'QUEUED'
  | 'RUNNING'
  | 'AWAITING_CLARIFICATION'
  | 'COMPLETED'
  | 'FAILED';

/** The Data Studio Brain stages a plan may select (new-arch §9). */
export type BrainStage = 'PROFILER' | 'DAG_RECIPE' | 'PREPARE_MATH';

export interface JobStage {
  /** Stage key — pipeline stages beyond the Brain set are allowed. */
  key: string;
  label: string;
  status: 'PENDING' | 'RUNNING' | 'DONE' | 'SKIPPED' | 'FAILED';
  /** Optional live detail line for a running stage (e.g. "Epoch 12/20"). */
  detail?: string;
  /** Optional 0–100 progress for a running stage. */
  progressPct?: number;
}

export interface Job {
  jobId: string;
  tenantUid: string;
  schemaVersion: string;
  intentUid: string;
  status: JobStatus;
  /** Only the stages the backend plan actually selected are present. */
  stages: JobStage[];
  /** Present once the job reaches a terminal or clarification state. */
  artifact?: ArtifactPackage;
  /** Present when status is AWAITING_CLARIFICATION. */
  clarification?: ClarificationRequest;
  createdAt: string;
  updatedAt: string;

  /* ── Presentational metadata (from the job detail screens) ─────────────── */
  title?: string;
  startedAt?: string;
  durationLabel?: string;
  initiatedBy?: string;
  datasetRef?: string;
  /** Live execution log lines for the console panel. */
  logs?: string[];
  /** Failure reason when status is FAILED. */
  failureReason?: string;
}

export interface ClarificationRequest {
  question: string;
  options: string[];
}

/** Typed plan the agent proposes; the backend validator decides (new-arch §13). */
export interface ParsePlan {
  planId: string;
  intentUid: string;
  steps: string[];
}

export interface PlanValidation {
  planId: string;
  valid: boolean;
  issues: string[];
}
