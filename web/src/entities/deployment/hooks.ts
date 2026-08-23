import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { deploymentApi } from './api';

export const DEPLOYMENT_KEYS = {
  all: ['deployments'] as const,
  detail: (id: string) => ['deployments', id] as const,
};

export function useDeployments() {
  return useQuery({
    queryKey: DEPLOYMENT_KEYS.all,
    queryFn: () => deploymentApi.listDeployments(),
  });
}

export function useDeploymentDetail(deploymentId: string) {
  return useQuery({
    queryKey: DEPLOYMENT_KEYS.detail(deploymentId),
    queryFn: () => deploymentApi.getDeploymentById(deploymentId),
    enabled: Boolean(deploymentId),
  });
}

export function useCreateDeployment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: { name: string; modelRef: string; environment: string; replicas: number }) =>
      deploymentApi.createDeployment(params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DEPLOYMENT_KEYS.all });
    },
  });
}

export function useStopDeployment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (deploymentId: string) => deploymentApi.stopDeployment(deploymentId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: DEPLOYMENT_KEYS.all });
      queryClient.invalidateQueries({ queryKey: DEPLOYMENT_KEYS.detail(data.deploymentId) });
    },
  });
}
