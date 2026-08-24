/**
 * Dataset + discovery/inspection artifacts. Sourced from new-arch §6.3 / §13.
 */
export interface ArchiveInspection {
  assetId: string;
  archiveType: string;
  memberInventory: string[];
  candidateFormats: string[];
  securityFindings: string[];
}

export interface DiscoveryArtifact {
  assetId: string;
  candidateTimestampFields: string[];
  candidateIdentifierFields: string[];
  sampleHeaders: string[];
  /** Detected table segments within the raw asset, pending user review. */
  segments?: DiscoverySegment[];
  fileName?: string;
  fileSizeLabel?: string;
}

export type SegmentReviewStatus = 'PENDING' | 'APPROVED' | 'REJECTED';

export interface DiscoverySegment {
  segmentId: string;
  name: string;
  confidencePct: number;
  ambiguous: boolean;
  sampleRows: string[];
  estimatedRows: string;
  estimatedCols: number;
  reviewStatus: SegmentReviewStatus;
}

export interface Dataset {
  datasetId: string;
  tenantUid: string;
  schemaVersion: string;
  name: string;
  parquetRef: string;
  rowCount?: number;
  columnCount?: number;
  promotedAt?: string;
}
