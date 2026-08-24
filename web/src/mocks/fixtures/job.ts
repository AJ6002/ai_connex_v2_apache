import type { ArtifactPackage } from '@/entities/artifact/types';
import type { IntentEnvelope, Job, ParsePlan, PlanValidation } from '@/entities/job/types';

/**
 * Realistic — but explicitly non-secret — fixtures for the mock layer.
 * Guardrail §9.2: never seed mocks with real-looking credentials/tokens.
 */

export const intentFixture: IntentEnvelope = {
  intentUid: 'intent_demo_0001',
  tenantUid: 'tenant_demo',
  userUid: 'user_demo',
  goal: 'Profile the uploaded telemetry dataset',
  requestedOutputs: ['profile'],
  requiresModel: false,
  requiresVisualization: true,
  requiresService: false,
  sourceRefs: ['asset_demo_0001'],
};

export const artifactFixture: ArtifactPackage = {
  artifactId: 'artifact_demo_0001',
  tenantUid: 'tenant_demo',
  schemaVersion: '1.0.0',
  status: 'READY_FOR_PROFILER',
  datasetRef: 'tenant_demo/site_a/dataset_demo',
  schemaRef: 'schema_demo_0001',
  warnings: [],
  createdAt: new Date().toISOString(),
};

export const jobFixture: Job = {
  jobId: 'job_demo_0001',
  tenantUid: intentFixture.tenantUid,
  schemaVersion: '1.0.0',
  intentUid: intentFixture.intentUid,
  status: 'COMPLETED',
  stages: [
    { key: 'DISCOVERY', label: 'Discovery', status: 'DONE' },
    { key: 'PARSE', label: 'Parse', status: 'DONE' },
    { key: 'PROFILER', label: 'Profiler', status: 'DONE' },
  ],
  artifact: artifactFixture,
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
};

export const parsePlanFixture: ParsePlan = {
  planId: 'plan_demo_0001',
  intentUid: intentFixture.intentUid,
  steps: ['discover', 'parse', 'profile'],
};

export const planValidationFixture: PlanValidation = {
  planId: parsePlanFixture.planId,
  valid: true,
  issues: [],
};

/* ── Job detail scenarios (one per STITCH job state) ───────────────────────── */

const TRAINING_LOGS = [
  '[10:50:30] INFO: Stage 3 Completed.',
  '[10:50:35] INFO: Starting Stage 4: Model Training (XGBoost)...',
  '[10:51:00] INFO: Epoch 1/20 - Loss: 0.891',
  '[10:52:30] INFO: Epoch 3/20 - Loss: 0.405',
  '[10:54:00] INFO: Epoch 5/20 - Loss: 0.190',
  '[10:56:15] INFO: Epoch 8/20 - Loss: 0.081',
  '[10:58:30] INFO: Epoch 11/20 - Loss: 0.051',
  '[10:59:15] INFO: Epoch 12/20 - Loss: 0.042 - Active...',
];

const trainingStages = (activeIndex: number, failedIndex = -1): Job['stages'] => {
  const labels = ['Intake', 'Profiling', 'Feature Eng', 'Model Training', 'Evaluation', 'Deployment'];
  const keys = ['INTAKE', 'PROFILER', 'FEATURE_ENG', 'TRAINING', 'EVALUATION', 'DEPLOYMENT'];
  return labels.map((label, i) => {
    let status: Job['stages'][number]['status'] = 'PENDING';
    if (failedIndex >= 0 && i === failedIndex) status = 'FAILED';
    else if (i < activeIndex) status = 'DONE';
    else if (i === activeIndex && failedIndex < 0) status = 'RUNNING';
    const stage: Job['stages'][number] = { key: keys[i], label, status };
    if (status === 'RUNNING' && i === 3) {
      stage.detail = 'Epoch 12/20 - Loss: 0.042';
      stage.progressPct = 64;
    }
    return stage;
  });
};

const baseDetail: Pick<Job, 'tenantUid' | 'schemaVersion' | 'title' | 'startedAt' | 'durationLabel' | 'initiatedBy' | 'datasetRef' | 'intentUid' | 'createdAt' | 'updatedAt'> = {
  tenantUid: 'tenant_demo',
  schemaVersion: '1.0.0',
  title: 'Model Training: Customer Churn V3',
  startedAt: '10:42 AM',
  durationLabel: '14m 22s',
  initiatedBy: 'Jane Agent',
  datasetRef: 'customer_interactions_2024',
  intentUid: 'intent_demo_0001',
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
};

/**
 * Resolves a job's clarification: returns the same job advanced to RUNNING
 * with the clarification cleared. Used by the request_clarification handler
 * so it responds for the *actual* job asked about, not a hardcoded stand-in.
 */
export function resolveJobClarification(jobId: string): Job {
  const base = jobForId(jobId);
  return {
    ...base,
    jobId,
    status: 'RUNNING',
    clarification: undefined,
    stages: trainingStages(2),
    logs: ['[10:46:00] INFO: Clarification resolved. Resuming pipeline...'],
  };
}

export function jobForId(id: string): Job {
  if (id.includes('completed')) {
    return {
      ...baseDetail,
      jobId: 'JOB-8294',
      status: 'COMPLETED',
      stages: trainingStages(6),
      artifact: { ...artifactFixture, status: 'MACHINE_READY' },
      logs: [...TRAINING_LOGS, '[11:04:00] INFO: All stages completed. Model registered.'],
    };
  }
  if (id.includes('failed')) {
    return {
      ...baseDetail,
      jobId: 'JOB-8294',
      status: 'FAILED',
      stages: trainingStages(3, 3),
      failureReason: 'Training diverged: NaN loss detected at epoch 6. Check feature scaling.',
      artifact: { ...artifactFixture, status: 'FAILED', warnings: ['NaN loss at epoch 6'] },
      logs: [...TRAINING_LOGS.slice(0, 5), '[10:55:00] ERROR: NaN loss detected. Aborting.'],
    };
  }
  if (id.includes('clarify')) {
    return {
      ...baseDetail,
      jobId: 'JOB-8294',
      status: 'AWAITING_CLARIFICATION',
      stages: trainingStages(1),
      clarification: {
        question: 'Multiple timestamp columns detected. Which should be the primary time index?',
        options: ['event_time', 'ingest_time', 'created_at'],
      },
      artifact: { ...artifactFixture, status: 'NEEDS_CLARIFICATION' },
    };
  }
  if (id.includes('profiling')) {
    return {
      ...baseDetail,
      jobId: 'JOB-8294',
      status: 'RUNNING',
      stages: trainingStages(1),
      logs: ['[10:44:10] INFO: Starting Stage 2: Profiling...', '[10:45:02] INFO: Scanning 24,000 rows...'],
    };
  }
  // default: running
  return {
    ...baseDetail,
    jobId: 'JOB-8294',
    status: 'RUNNING',
    stages: trainingStages(3),
    logs: TRAINING_LOGS,
  };
}
