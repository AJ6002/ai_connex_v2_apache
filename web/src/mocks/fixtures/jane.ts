import type { JaneSession } from '@/entities/jane/types';

export const janeSessionFixture: JaneSession = {
  sessionId: 'jane-session-0001',
  status: 'ONLINE',
  version: 'v4.2.1',
  initializedAtUtc: '14:02:45 UTC',
  turns: [
    {
      turnId: 't1',
      role: 'user',
      text: "Jane, analyze the drift in the 'customer_churn_v3' dataset and prepare a profiling job.",
    },
    {
      turnId: 't2',
      role: 'system',
      text: 'Acknowledged. Locating dataset customer_churn_v3 in the primary registry. Initial scan confirms schema match. Preparing drift analysis pipeline sequence.',
      highlights: ['customer_churn_v3'],
    },
  ],
  clarification: {
    question: 'Which environment should I pull the baseline from? Staging or Production?',
    options: ['Staging', 'Production'],
  },
};

/** Mutable module-level session used only by the mock handlers (dev/test only). */
let janeSessionState: JaneSession = janeSessionFixture;

export function getJaneSessionState(): JaneSession {
  return janeSessionState;
}

export function resolveJaneClarificationState(option: string): JaneSession {
  if (!janeSessionState.clarification) return janeSessionState;
  janeSessionState = {
    ...janeSessionState,
    clarification: { ...janeSessionState.clarification, resolvedOption: option },
    proposedAction: {
      title: 'Data Profiling Job',
      targetLabel: `Target: customer_churn_v3 • Baseline: ${option}`,
      params: [
        { label: 'COMPUTE_NODE', value: 'instance-m5-large' },
        { label: 'DRIFT_THRESHOLD', value: '0.05 (K-S test)' },
        { label: 'TIMEOUT', value: '3600s' },
      ],
      executeLabel: 'EXECUTE_JOB',
    },
  };
  return janeSessionState;
}

export function executeJaneActionState(): JaneSession {
  if (!janeSessionState.proposedAction) return janeSessionState;
  janeSessionState = {
    ...janeSessionState,
    proposedAction: { ...janeSessionState.proposedAction, executed: true },
    turns: [
      ...janeSessionState.turns,
      { turnId: `t${janeSessionState.turns.length + 1}`, role: 'system', text: 'Job submitted. Tracking as JOB-8294.' },
    ],
  };
  return janeSessionState;
}
