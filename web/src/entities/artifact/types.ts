/**
 * Artifact Package — the result of any route, and the frontend's core state
 * machine. Sourced from new-arch §14. Every status below must have an explicit,
 * intentional visual treatment in the UI (enforced in Sprint 4).
 */
export type ArtifactStatus =
  | 'MACHINE_READY'
  | 'MACHINE_READY_WITH_WARNINGS'
  | 'READY_FOR_PROFILER'
  | 'NEEDS_CLARIFICATION'
  | 'NEEDS_USER_CORRECTION'
  | 'QUARANTINED'
  | 'FAILED'
  /** Blocked by registry policy — must render a distinct, non-dismissable treatment.
   * See Frontend Phase 1.1.2. Never fall through to generic ErrorState. */
  | 'BLOCK';

export interface ArtifactPackage {
  artifactId: string;
  tenantUid: string;
  schemaVersion: string;
  status: ArtifactStatus;
  datasetRef?: string;
  schemaRef?: string;
  qualitySummaryRef?: string;
  lineageRef?: string;
  warnings: string[];
  createdAt: string;
}
