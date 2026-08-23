import { apiClient } from '@/api/client';
import type { ArchiveInspection, Dataset, DiscoveryArtifact } from './types';

/**
 * Dataset-scoped capabilities from the new-arch Capability Registry (§13).
 * The UI calls these named capabilities — never a service port.
 */

/** capability: inspect_archive */
export function inspectArchive(assetId: string): Promise<ArchiveInspection> {
  return apiClient.post<ArchiveInspection>('/api/v1/capabilities/inspect_archive', { assetId });
}

/** capability: create_discovery_artifact */
export function createDiscoveryArtifact(assetId: string): Promise<DiscoveryArtifact> {
  return apiClient.post<DiscoveryArtifact>(
    '/api/v1/capabilities/create_discovery_artifact',
    { assetId },
  );
}

/** capability: get_discovery_artifact — fetch a previously created artifact for review. */
export function getDiscoveryArtifact(assetId: string): Promise<DiscoveryArtifact> {
  return apiClient.get<DiscoveryArtifact>(
    `/api/v1/capabilities/get_discovery_artifact?assetId=${encodeURIComponent(assetId)}`,
  );
}

/** capability: review_discovery_segment — approve or reject a detected segment. */
export function reviewDiscoverySegment(
  segmentId: string,
  decision: 'APPROVED' | 'REJECTED',
): Promise<DiscoveryArtifact> {
  return apiClient.post<DiscoveryArtifact>('/api/v1/capabilities/review_discovery_segment', {
    segmentId,
    decision,
  });
}

/** capability: promote_dataset */
export function promoteDataset(artifactId: string): Promise<Dataset> {
  return apiClient.post<Dataset>('/api/v1/capabilities/promote_dataset', { artifactId });
}
