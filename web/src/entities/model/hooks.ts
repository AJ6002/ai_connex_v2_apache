import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { modelApi } from './api';

export const MODEL_KEYS = {
  all: ['models'] as const,
  detail: (id: string) => ['models', id] as const,
};

export function useModels() {
  return useQuery({
    queryKey: MODEL_KEYS.all,
    queryFn: () => modelApi.listModels(),
  });
}

export function useModelDetail(modelId: string) {
  return useQuery({
    queryKey: MODEL_KEYS.detail(modelId),
    queryFn: () => modelApi.getModelById(modelId),
    enabled: Boolean(modelId),
  });
}

export function useEvaluateModel() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ modelId, testDatasetRef }: { modelId: string; testDatasetRef: string }) =>
      modelApi.evaluateModel(modelId, testDatasetRef),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: MODEL_KEYS.all });
      queryClient.invalidateQueries({ queryKey: MODEL_KEYS.detail(data.modelId) });
    },
  });
}
