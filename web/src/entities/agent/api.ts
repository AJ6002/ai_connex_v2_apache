import { apiClient } from '@/api/client';
import type { AgentSpec, AgentRunLog } from './types';

export const agentApi = {
  listAgents: async (): Promise<AgentSpec[]> => {
    return apiClient.get<AgentSpec[]>('/api/v1/capabilities/list_agents');
  },

  getAgentById: async (agentId: string): Promise<AgentSpec> => {
    return apiClient.get<AgentSpec>(`/api/v1/capabilities/get_agent/${agentId}`);
  },

  triggerAgentRun: async (agentId: string, prompt: string): Promise<AgentRunLog> => {
    return apiClient.post<AgentRunLog>('/api/v1/capabilities/trigger_agent_run', {
      agentId,
      prompt,
    });
  },
};
