import { apiClient } from '@/api/client';
import type { ProfileSummary } from './types';

/** capability: read_profile_summary (new-arch §13). */
export function readProfileSummary(datasetRef: string): Promise<ProfileSummary> {
  return apiClient.get<ProfileSummary>(
    `/api/v1/capabilities/read_profile_summary?datasetRef=${encodeURIComponent(datasetRef)}`,
  );
}
