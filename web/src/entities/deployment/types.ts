/**
 * Deployment Entity Types
 * Sourced from STITCH-Design deployment registry & active configuration screens.
 */
export type DeploymentStatus = 'PENDING' | 'ACTIVE' | 'DEGRADED' | 'STOPPED' | 'FAILED';

export interface DeploymentMetrics {
  requestsPerSecond: number;
  cpuUtilizationPct: number;
  memoryUtilizationPct: number;
  avgLatencyMs: number;
}

export interface DeploymentSpec {
  deploymentId: string;
  tenantUid: string;
  schemaVersion: string;
  name: string;
  modelRef: string;
  environment: string; // e.g. "PRODUCTION", "STAGING"
  status: DeploymentStatus;
  replicas: number;
  endpointUrl: string;
  metrics: DeploymentMetrics;
  /** Serving compute region (e.g. "us-east-1"). */
  computeRegion?: string;
  /** Serving instance type (e.g. "ml.m5.xlarge"). */
  instanceType?: string;
  /** Error rate as a percentage (health panel). */
  errorRatePct?: number;
  createdAt: string;
  updatedAt: string;
}
