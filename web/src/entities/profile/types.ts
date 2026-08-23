/**
 * Profile summary produced by the Data Profiler (new-arch §9, capability
 * `read_profile_summary`). Structural / statistical / temporal description.
 */
export interface ColumnProfile {
  name: string;
  dtype: string;
  nullRatio: number;
  distinctCount: number;
}

export interface ProfileSummary {
  datasetRef: string;
  datasetName?: string;
  rowCount: number;
  columnCount?: number;
  columns: ColumnProfile[];
  recommendedDagId?: string;
  algorithmFamily?: string;
  narrative?: string;
}
