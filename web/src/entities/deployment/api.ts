import { apiClient } from '@/api/client';
import type { DeploymentSpec } from './types';

export const deploymentApi = {
  listDeployments: async (): Promise<DeploymentSpec[]> => {
    return apiClient.get<DeploymentSpec[]>('/api/v1/capabilities/list_deployments');
  },

  getDeploymentById: async (deploymentId: string): Promise<DeploymentSpec> => {
    return apiClient.get<DeploymentSpec>(`/api/v1/capabilities/get_deployment/${deploymentId}`);
  },

  createDeployment: async (params: {
    name: string;
    modelRef: string;
    environment: string;
    replicas: number;
  }): Promise<DeploymentSpec> => {
    return apiClient.post<DeploymentSpec>('/api/v1/capabilities/create_deployment', params);
  },

  stopDeployment: async (deploymentId: string): Promise<DeploymentSpec> => {
    return apiClient.post<DeploymentSpec>('/api/v1/capabilities/stop_deployment', { deploymentId });
  },
};
