import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { executeJaneAction, getJaneSession, resolveJaneClarification } from './api';

const JANE_KEY = ['jane', 'session'] as const;

export function useJaneSession() {
  return useQuery({ queryKey: JANE_KEY, queryFn: getJaneSession });
}

/** The single place "answer Jane's clarification" lives (guardrail §9.3). */
export function useResolveJaneClarification() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (option: string) => resolveJaneClarification(option),
    onSuccess: (session) => qc.setQueryData(JANE_KEY, session),
  });
}

export function useExecuteJaneAction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => executeJaneAction(),
    onSuccess: (session) => qc.setQueryData(JANE_KEY, session),
  });
}
