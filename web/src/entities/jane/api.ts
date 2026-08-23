import { apiClient } from '@/api/client';
import type { JaneSession } from './types';

/** capability: get_jane_session */
export function getJaneSession(): Promise<JaneSession> {
  return apiClient.get<JaneSession>('/api/v1/capabilities/get_jane_session');
}

/** capability: resolve_jane_clarification */
export function resolveJaneClarification(option: string): Promise<JaneSession> {
  return apiClient.post<JaneSession>('/api/v1/capabilities/resolve_jane_clarification', { option });
}

/** capability: execute_jane_action */
export function executeJaneAction(): Promise<JaneSession> {
  return apiClient.post<JaneSession>('/api/v1/capabilities/execute_jane_action', {});
}
