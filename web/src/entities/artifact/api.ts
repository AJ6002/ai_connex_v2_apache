import { apiClient } from '@/api/client';
import type { ArtifactPackage } from './types';

export const artifactApi = {
  getArtifactById: async (artifactId: string): Promise<ArtifactPackage> => {
    return apiClient.get<ArtifactPackage>(`/api/v1/capabilities/get_artifact/${artifactId}`);
  },

  createDiscoveryArtifact: async (datasetRef: string): Promise<ArtifactPackage> => {
    return apiClient.post<ArtifactPackage>('/api/v1/capabilities/create_discovery_artifact', {
      datasetRef,
    });
  },
};
