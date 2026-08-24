import type { ArchiveInspection, Dataset, DiscoveryArtifact } from '@/entities/dataset/types';

export const archiveInspectionFixture: ArchiveInspection = {
  assetId: 'asset_demo_0001',
  archiveType: 'zip',
  memberInventory: ['telemetry.csv', 'readme.txt'],
  candidateFormats: ['csv'],
  securityFindings: [],
};

export const discoveryArtifactFixture: DiscoveryArtifact = {
  assetId: 'asset_demo_0001',
  candidateTimestampFields: ['timestamp'],
  candidateIdentifierFields: ['unit_id'],
  sampleHeaders: ['timestamp', 'unit_id', 'temp_c', 'vibration'],
  fileName: 'Q3_Financial_Export_RAW.csv',
  fileSizeLabel: '1.4GB',
  segments: [
    {
      segmentId: 'SEG_01',
      name: 'Transaction_Log',
      confidencePct: 98,
      ambiguous: false,
      sampleRows: [
        'tx_id,date,amount,currency,merchant',
        '1001,2023-10-01,150.00,USD,M_492',
        '1002,2023-10-01,25.50,USD,M_118',
        '...',
      ],
      estimatedRows: '~1.2M',
      estimatedCols: 5,
      reviewStatus: 'PENDING',
    },
    {
      segmentId: 'SEG_02',
      name: 'User_Metadata',
      confidencePct: 74,
      ambiguous: true,
      sampleRows: [
        'user_id,region,tier,signup_date',
        'U_8492,NA,Premium,2021-05-12',
        'U_1120,EU,Standard,2022-11-04',
        '...',
      ],
      estimatedRows: '~45K',
      estimatedCols: 4,
      reviewStatus: 'PENDING',
    },
    {
      segmentId: 'SEG_03',
      name: 'Unstructured_Notes',
      confidencePct: 22,
      ambiguous: true,
      sampleRows: [],
      estimatedRows: '—',
      estimatedCols: 0,
      reviewStatus: 'PENDING',
    },
  ],
};

/** Mutable module-level artifact used only by the mock handlers (dev/test only). */
let discoveryArtifactState: DiscoveryArtifact = discoveryArtifactFixture;

export function getDiscoveryArtifactState(): DiscoveryArtifact {
  return discoveryArtifactState;
}

export function reviewDiscoverySegmentState(
  segmentId: string,
  decision: 'APPROVED' | 'REJECTED',
): DiscoveryArtifact {
  discoveryArtifactState = {
    ...discoveryArtifactState,
    segments: discoveryArtifactState.segments?.map((s) =>
      s.segmentId === segmentId ? { ...s, reviewStatus: decision } : s,
    ),
  };
  return discoveryArtifactState;
}

export const datasetFixture: Dataset = {
  datasetId: 'dataset_demo_0001',
  tenantUid: 'tenant_demo',
  schemaVersion: '1.0.0',
  name: 'telemetry_demo',
  parquetRef: 'tenant_demo/site_a/dataset_demo/parsed/data.parquet',
  rowCount: 24000,
  columnCount: 12,
  promotedAt: new Date().toISOString(),
};
