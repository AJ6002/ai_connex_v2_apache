/**
 * Workspace & Admin Entity Types
 * Sourced from STITCH-Design admin access control, usage quotas, and workspace config screens.
 */
export type UserRole = 'ADMIN' | 'ENGINEER' | 'ANALYST';

export interface PersonnelUser {
  userId: string;
  name: string;
  role: UserRole;
  status: 'ACTIVE' | 'INACTIVE';
  lastActive: string;
}

export interface ApiCredential {
  keyId: string;
  name: string;
  maskedKey: string;
  permissions: string[];
  createdAt: string;
  lastUsedAt?: string;
}

export interface QuotaUsage {
  adminSeatsUsed: number;
  adminSeatsTotal: number;
  engineerSeatsUsed: number;
  engineerSeatsTotal: number;
  gpuHoursUsed: number;
  gpuHoursQuota: number;
  /** Billing cycle spend, in USD. */
  billingEstimateUsd?: number;
  billingLimitUsd?: number;
  billingCycleEndsInDays?: number;
  /** Storage tiers, in TB. */
  storageHotUsedTb?: number;
  storageHotLimitTb?: number;
  storageColdUsedTb?: number;
  storageColdLimitTb?: number;
}

export interface PlatformPolicies {
  autoQuarantineThreshold: number; // 0.0 - 1.0
  strictnessLevel: 'LOW' | 'MEDIUM' | 'HIGH';
  modelRetentionDays: number;
  autoArchiveBeforeDeletion: boolean;
}

export interface TenantConfig {
  privacyMode: 'PRIVATE_CLOUD' | 'SHARED_CLOUD';
  privacyModeActive: boolean;
  dataResidency: string; // e.g. "US-Only (Enforced)"
}

export interface WorkspaceSpec {
  workspaceId: string;
  name: string;
  environment: string; // e.g. "PRODUCTION ENVIRONMENT"
  quotas: QuotaUsage;
  primaryRegion?: string;
  createdAt?: string;
  tenant?: TenantConfig;
  policies?: PlatformPolicies;
}

export type AuditStatus = 'SUCCESS' | 'FAILURE';

export interface AuditLogEntry {
  entryId: string;
  timestampUtc: string;
  principal: string;
  principalType: 'user' | 'service';
  action: string;
  entityId: string;
  status: AuditStatus;
}

/** Row shape for the "Active & Recent Jobs" overview widget. */
export interface RecentJobSummary {
  jobId: string;
  jobType: string;
  status: 'RUNNING' | 'CLARIFICATION' | 'COMPLETED' | 'FAILED' | 'QUEUED';
  progressPct: number;
  startTime: string;
}

/** Row shape for the "Recent Datasets" overview widget. */
export interface RecentDatasetSummary {
  datasetRef: string;
  name: string;
  status: 'ACTIVE' | 'PROCESSED' | 'FAILED';
  sizeLabel: string;
  updatedLabel: string;
}
