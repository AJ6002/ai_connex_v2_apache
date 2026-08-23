import { apiClient } from '@/api/client';
import type { ModelSpec } from './types';

export const modelApi = {
  listModels: async (): Promise<ModelSpec[]> => {
    return apiClient.get<ModelSpec[]>('/api/v1/capabilities/list_models');
  },

  getModelById: async (modelId: string): Promise<ModelSpec> => {
    return apiClient.get<ModelSpec>(`/api/v1/capabilities/get_model/${modelId}`);
  },

  evaluateModel: async (modelId: string, testDatasetRef: string): Promise<ModelSpec> => {
    return apiClient.post<ModelSpec>('/api/v1/capabilities/evaluate_model', {
      modelId,
      testDatasetRef,
    });
  },
};
