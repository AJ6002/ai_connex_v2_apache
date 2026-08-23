export const workspaceFixture = {
  workspaceId: 'ws-prod-99x2a-bt4',
  name: 'Project Alpha - Prod',
  environment: 'PRODUCTION ENVIRONMENT',
  primaryRegion: 'us-east-1 (N. Virginia)',
  createdAt: '2023-10-14T08:22:00Z',
  quotas: {
    adminSeatsUsed: 1,
    adminSeatsTotal: 5,
    engineerSeatsUsed: 12,
    engineerSeatsTotal: 20,
    gpuHoursUsed: 820,
    gpuHoursQuota: 1000,
    billingEstimateUsd: 6100,
    billingLimitUsd: 10000,
    billingCycleEndsInDays: 12,
    storageHotUsedTb: 4.2,
    storageHotLimitTb: 5,
    storageColdUsedTb: 1.1,
    storageColdLimitTb: 2,
  },
  tenant: {
    privacyMode: 'PRIVATE_CLOUD' as const,
    privacyModeActive: true,
    dataResidency: 'US-Only (Enforced)',
  },
  policies: {
    autoQuarantineThreshold: 0.85,
    strictnessLevel: 'HIGH' as const,
    modelRetentionDays: 90,
    autoArchiveBeforeDeletion: true,
  },
};

export const personnelFixture = [
  { userId: 'USR-892B4X', name: 'Dr. Aris Vance', role: 'ADMIN' as const, status: 'ACTIVE' as const, lastActive: 'Just now' },
  { userId: 'USR-339M9Z', name: 'Elena Rostova', role: 'ENGINEER' as const, status: 'ACTIVE' as const, lastActive: '2h ago' },
];

export const credentialsFixture = [
  { keyId: 'KEY-001', name: 'Prod-Ingestion-Primary', maskedKey: 'ak_prod_••••••••••••9x2a', permissions: ['READ:DATASETS', 'WRITE:DATASETS'], createdAt: 'OCT 12, 2023', lastUsedAt: '5m ago' },
];

export const recentJobsFixture = [
  { jobId: 'JOB-8294', jobType: 'Training', status: 'RUNNING' as const, progressPct: 64, startTime: '10:42 AM' },
  { jobId: 'JOB-8293', jobType: 'Prep', status: 'CLARIFICATION' as const, progressPct: 12, startTime: '09:15 AM' },
  { jobId: 'JOB-8290', jobType: 'Deployment', status: 'COMPLETED' as const, progressPct: 100, startTime: 'Yesterday' },
];

export const recentDatasetsFixture = [
  { datasetRef: 'DS-1', name: 'customer_interactions_2024', status: 'ACTIVE' as const, sizeLabel: '4.2 TB', updatedLabel: 'UPDATED 2H AGO' },
  { datasetRef: 'DS-2', name: 'raw_telemetry_batch_07', status: 'PROCESSED' as const, sizeLabel: '850 GB', updatedLabel: 'UPDATED 1D AGO' },
  { datasetRef: 'DS-3', name: 'corrupted_log_stream', status: 'FAILED' as const, sizeLabel: '12 GB', updatedLabel: 'CHECK LOGS' },
];

export const auditLogsFixture = [
  { entryId: 'AL-1', timestampUtc: '2023-10-27 14:32:01', principal: 'jane.agent@enterprise.com', principalType: 'user' as const, action: 'POLICY_UPDATE', entityId: 'iam-role-xyz-098', status: 'SUCCESS' as const },
  { entryId: 'AL-2', timestampUtc: '2023-10-27 14:28:15', principal: 'system-service-account', principalType: 'service' as const, action: 'MODEL_DEPLOYMENT', entityId: 'dep-prd-v2.4.1', status: 'SUCCESS' as const },
  { entryId: 'AL-3', timestampUtc: '2023-10-27 14:15:42', principal: 'ext_auditor@thirdparty.org', principalType: 'user' as const, action: 'DATA_ACCESS_DENIED', entityId: 'dataset-phi-restricted', status: 'FAILURE' as const },
  { entryId: 'AL-4', timestampUtc: '2023-10-27 13:50:09', principal: 'jane.agent@enterprise.com', principalType: 'user' as const, action: 'LOGIN_ATTEMPT', entityId: 'auth-session-10293', status: 'SUCCESS' as const },
  { entryId: 'AL-5', timestampUtc: '2023-10-27 12:11:33', principal: 'api-key-ci-cd', principalType: 'service' as const, action: 'CONFIG_PATCH', entityId: 'env-vars-prd', status: 'SUCCESS' as const },
];
