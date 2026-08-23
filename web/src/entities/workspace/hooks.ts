import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { workspaceApi } from './api';

export const WORKSPACE_KEYS = {
  info: ['workspace'] as const,
  personnel: ['workspace', 'personnel'] as const,
  credentials: ['workspace', 'credentials'] as const,
};

export function useWorkspaceInfo() {
  return useQuery({
    queryKey: WORKSPACE_KEYS.info,
    queryFn: () => workspaceApi.getWorkspaceInfo(),
  });
}

export function usePersonnel() {
  return useQuery({
    queryKey: WORKSPACE_KEYS.personnel,
    queryFn: () => workspaceApi.listPersonnel(),
  });
}

export function useCredentials() {
  return useQuery({
    queryKey: WORKSPACE_KEYS.credentials,
    queryFn: () => workspaceApi.listCredentials(),
  });
}

export function useRecentJobs() {
  return useQuery({
    queryKey: ['workspace', 'recent-jobs'] as const,
    queryFn: () => workspaceApi.listRecentJobs(),
  });
}

export function useRecentDatasets() {
  return useQuery({
    queryKey: ['workspace', 'recent-datasets'] as const,
    queryFn: () => workspaceApi.listRecentDatasets(),
  });
}

export function useCreateWorkspace() {
  return useMutation({
    mutationFn: (input: { name: string; primaryRegion: string; privacyMode: 'PRIVATE_CLOUD' | 'SHARED_CLOUD' }) =>
      workspaceApi.createWorkspace(input),
  });
}

export function useAuditLogs() {
  return useQuery({
    queryKey: ['workspace', 'audit-logs'] as const,
    queryFn: () => workspaceApi.listAuditLogs(),
  });
}

export function useCreateCredential() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ name, permissions }: { name: string; permissions: string[] }) =>
      workspaceApi.createCredential(name, permissions),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: WORKSPACE_KEYS.credentials });
    },
  });
}
