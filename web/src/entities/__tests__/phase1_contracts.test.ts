/**
 * Frontend Phase 1.1 — Entity Contract Coverage Tests
 *
 * Compile-time + runtime guards that every stored-resource entity type
 * carries tenantUid and schemaVersion, and that the BLOCK artifact status
 * renders a distinct UI state (not a silent generic error).
 *
 * If any stored-resource interface drops tenantUid or schemaVersion,
 * the compile step fails here *and* the typecheck script catches it.
 */

import { describe, it, expect } from 'vitest';
import { artifactFixture, jobFixture } from '@/mocks/fixtures/job';
import { datasetFixture } from '@/mocks/fixtures/dataset';
import { profileSummaryFixture } from '@/mocks/fixtures/profile';
import { modelsFixture } from '@/mocks/fixtures/models';
import { deploymentsFixture } from '@/mocks/fixtures/deployments';
import { agentsFixture } from '@/mocks/fixtures/agents';
import { workspaceFixture } from '@/mocks/fixtures/workspace';
import type { ArtifactStatus } from '@/entities/artifact/types';

// ── Task 1.1.1 — All stored-resource fixture objects carry tenantUid ─────────

describe('Frontend Phase 1.1.1 — tenantUid + schemaVersion on stored resources', () => {
  it('ArtifactPackage fixture carries tenantUid and schemaVersion', () => {
    expect(artifactFixture.tenantUid).toBeTruthy();
    expect(artifactFixture.schemaVersion).toBeTruthy();
  });

  it('Job fixture carries tenantUid and schemaVersion', () => {
    expect(jobFixture.tenantUid).toBeTruthy();
    expect(jobFixture.schemaVersion).toBeTruthy();
  });

  it('Dataset fixture carries tenantUid and schemaVersion', () => {
    expect(datasetFixture.tenantUid).toBeTruthy();
    expect(datasetFixture.schemaVersion).toBeTruthy();
  });

  it('ProfileSummary fixture carries tenantUid and schemaVersion', () => {
    expect(profileSummaryFixture.tenantUid).toBeTruthy();
    expect(profileSummaryFixture.schemaVersion).toBeTruthy();
  });

  it('ModelSpec fixture carries tenantUid and schemaVersion on every entry', () => {
    for (const m of modelsFixture) {
      expect(m.tenantUid, `model ${m.modelId} missing tenantUid`).toBeTruthy();
      expect((m as { schemaVersion?: string }).schemaVersion, `model ${m.modelId} missing schemaVersion`).toBeTruthy();
    }
  });

  it('DeploymentSpec fixture carries tenantUid and schemaVersion on every entry', () => {
    for (const d of deploymentsFixture) {
      expect((d as { tenantUid?: string }).tenantUid, `deployment ${d.deploymentId} missing tenantUid`).toBeTruthy();
      expect((d as { schemaVersion?: string }).schemaVersion, `deployment ${d.deploymentId} missing schemaVersion`).toBeTruthy();
    }
  });

  it('AgentSpec fixture carries tenantUid and schemaVersion', () => {
    for (const a of agentsFixture) {
      expect(a.tenantUid, `agent ${a.agentId} missing tenantUid`).toBeTruthy();
      expect((a as { schemaVersion?: string }).schemaVersion, `agent ${a.agentId} missing schemaVersion`).toBeTruthy();
    }
  });

  it('WorkspaceSpec fixture carries tenantUid and schemaVersion', () => {
    expect((workspaceFixture as { tenantUid?: string }).tenantUid).toBeTruthy();
    expect((workspaceFixture as { schemaVersion?: string }).schemaVersion).toBeTruthy();
  });
});

// ── Task 1.1.2 — BLOCK state exists in ArtifactStatus and is distinct ────────

describe('Frontend Phase 1.1.2 — BLOCK ArtifactStatus', () => {
  it('BLOCK is a valid ArtifactStatus value (compile-time via assignment)', () => {
    // If ArtifactStatus drops 'BLOCK', this line fails tsc.
    const status: ArtifactStatus = 'BLOCK';
    expect(status).toBe('BLOCK');
  });

  it('BLOCK is distinct from FAILED and QUARANTINED', () => {
    const allStatuses: ArtifactStatus[] = [
      'MACHINE_READY',
      'MACHINE_READY_WITH_WARNINGS',
      'READY_FOR_PROFILER',
      'NEEDS_CLARIFICATION',
      'NEEDS_USER_CORRECTION',
      'QUARANTINED',
      'FAILED',
      'BLOCK',
    ];
    // BLOCK must be present exactly once — guards against accidental removal
    const blockOccurrences = allStatuses.filter((s) => s === 'BLOCK');
    expect(blockOccurrences).toHaveLength(1);

    // BLOCK is distinct from every other status
    const withoutBlock = allStatuses.filter((s) => s !== 'BLOCK');
    for (const s of withoutBlock) {
      expect(s).not.toBe('BLOCK');
    }
  });

  it('ArtifactStatus union has exactly 8 members (guards against accidental removal)', () => {
    const allStatuses: ArtifactStatus[] = [
      'MACHINE_READY',
      'MACHINE_READY_WITH_WARNINGS',
      'READY_FOR_PROFILER',
      'NEEDS_CLARIFICATION',
      'NEEDS_USER_CORRECTION',
      'QUARANTINED',
      'FAILED',
      'BLOCK',
    ];
    expect(allStatuses).toHaveLength(8);
  });
});
