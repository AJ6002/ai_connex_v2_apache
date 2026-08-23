import { useQuery } from '@tanstack/react-query';
import { readProfileSummary } from './api';

export function useProfileSummary(datasetRef: string | undefined) {
  return useQuery({
    queryKey: ['profile', datasetRef],
    queryFn: () => readProfileSummary(datasetRef as string),
    enabled: Boolean(datasetRef),
  });
}
