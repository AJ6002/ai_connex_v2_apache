import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { artifactApi } from './api';

export const ARTIFACT_KEYS = {
  detail: (id: string) => ['artifacts', id] as const,
};

export function useArtifact(artifactId: string) {
  return useQuery({
    queryKey: ARTIFACT_KEYS.detail(artifactId),
    queryFn: () => artifactApi.getArtifactById(artifactId),
    enabled: Boolean(artifactId),
  });
}

export function useCreateDiscoveryArtifact() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (datasetRef: string) => artifactApi.createDiscoveryArtifact(datasetRef),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ARTIFACT_KEYS.detail(data.artifactId) });
    },
  });
}
