import type { ProfileSummary } from '@/entities/profile/types';

export const profileSummaryFixture: ProfileSummary = {
  datasetRef: 'tenant_demo/site_a/dataset_demo',
  tenantUid: 'tenant_demo',
  schemaVersion: '1.0.0',
  datasetName: 'transactions_main',
  rowCount: 24000,
  columnCount: 12,
  columns: [
    { name: 'timestamp', dtype: 'datetime', nullRatio: 0, distinctCount: 24000 },
    { name: 'temp_c', dtype: 'float', nullRatio: 0.01, distinctCount: 8123 },
    { name: 'vibration', dtype: 'float', nullRatio: 0.02, distinctCount: 9044 },
  ],
  recommendedDagId: 'DAG_906',
  algorithmFamily: 'Time-Series Regression',
  narrative: 'Time-indexed multi-sensor telemetry suitable for RUL profiling.',
};
