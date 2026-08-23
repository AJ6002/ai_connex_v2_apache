import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  getDiscoveryArtifact,
  inspectArchive,
  promoteDataset,
  reviewDiscoverySegment,
} from './api';

export const DATASET_KEYS = {
  all: ['datasets'] as const,
  inspection: (uri: string) => ['datasets', 'inspection', uri] as const,
  discovery: (assetId: string) => ['datasets', 'discovery', assetId] as const,
};

export function useDiscoveryArtifact(assetId: string) {
  return useQuery({
    queryKey: DATASET_KEYS.discovery(assetId),
    queryFn: () => getDiscoveryArtifact(assetId),
  });
}

/** The single place "approve/reject a discovered segment" lives (guardrail §9.3). */
export function useReviewDiscoverySegment(assetId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: { segmentId: string; decision: 'APPROVED' | 'REJECTED' }) =>
      reviewDiscoverySegment(params.segmentId, params.decision),
    onSuccess: (artifact) => {
      queryClient.setQueryData(DATASET_KEYS.discovery(assetId), artifact);
    },
  });
}

export function useInspectArchive() {
  return useMutation({
    mutationFn: (archiveUri: string) => inspectArchive(archiveUri),
  });
}

export function usePromoteDataset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: { archiveUri: string; datasetName: string; schemaType?: string }) =>
      promoteDataset(params.archiveUri),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DATASET_KEYS.all });
    },
  });
}
