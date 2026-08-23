import { apiClient } from '@/api/client';
import type {
  WorkspaceSpec,
  PersonnelUser,
  ApiCredential,
  AuditLogEntry,
  RecentJobSummary,
  RecentDatasetSummary,
} from './types';

export const workspaceApi = {
  getWorkspaceInfo: async (): Promise<WorkspaceSpec> => {
    return apiClient.get<WorkspaceSpec>('/api/v1/capabilities/get_workspace');
  },

  listPersonnel: async (): Promise<PersonnelUser[]> => {
    return apiClient.get<PersonnelUser[]>('/api/v1/capabilities/list_personnel');
  },

  listCredentials: async (): Promise<ApiCredential[]> => {
    return apiClient.get<ApiCredential[]>('/api/v1/capabilities/list_credentials');
  },

  createCredential: async (name: string, permissions: string[]): Promise<ApiCredential> => {
    return apiClient.post<ApiCredential>('/api/v1/capabilities/create_credential', {
      name,
      permissions,
    });
  },

  listAuditLogs: async (): Promise<AuditLogEntry[]> => {
    return apiClient.get<AuditLogEntry[]>('/api/v1/capabilities/list_audit_logs');
  },

  listRecentJobs: async (): Promise<RecentJobSummary[]> => {
    return apiClient.get<RecentJobSummary[]>('/api/v1/capabilities/list_recent_jobs');
  },

  listRecentDatasets: async (): Promise<RecentDatasetSummary[]> => {
    return apiClient.get<RecentDatasetSummary[]>('/api/v1/capabilities/list_recent_datasets');
  },

  createWorkspace: async (input: {
    name: string;
    primaryRegion: string;
    privacyMode: 'PRIVATE_CLOUD' | 'SHARED_CLOUD';
  }): Promise<WorkspaceSpec> => {
    return apiClient.post<WorkspaceSpec>('/api/v1/capabilities/create_workspace', input);
  },
};
