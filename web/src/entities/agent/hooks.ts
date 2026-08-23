import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { agentApi } from './api';

export const AGENT_KEYS = {
  all: ['agents'] as const,
  detail: (id: string) => ['agents', id] as const,
};

export function useAgents() {
  return useQuery({
    queryKey: AGENT_KEYS.all,
    queryFn: () => agentApi.listAgents(),
  });
}

export function useAgentDetail(agentId: string) {
  return useQuery({
    queryKey: AGENT_KEYS.detail(agentId),
    queryFn: () => agentApi.getAgentById(agentId),
    enabled: Boolean(agentId),
  });
}

export function useTriggerAgentRun() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ agentId, prompt }: { agentId: string; prompt: string }) =>
      agentApi.triggerAgentRun(agentId, prompt),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: AGENT_KEYS.all });
    },
  });
}
