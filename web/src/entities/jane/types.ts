/**
 * Jane conversational session — sourced from STITCH-Design jane_intent_clarification_flow,
 * jane_analysis_intent_clarification(_refined). A session is a turn-by-turn transcript
 * that may pause on a clarification question and, once resolved, propose a typed action
 * for the user to execute (new-arch: agents propose, deterministic services execute).
 */
export type JaneTurnRole = 'user' | 'system';

export interface JaneTurn {
  turnId: string;
  role: JaneTurnRole;
  text: string;
  /** Substring(s) to render as highlighted code/entity references. */
  highlights?: string[];
}

export interface JaneClarification {
  question: string;
  options: string[];
  /** Set once the user picks an option; drives the "> Select: X" readout. */
  resolvedOption?: string;
}

export interface JaneActionParam {
  label: string;
  value: string;
}

export interface JaneProposedAction {
  title: string;
  targetLabel: string;
  params: JaneActionParam[];
  executeLabel: string;
  executed?: boolean;
}

export type JaneSessionStatus = 'ONLINE' | 'IDLE';

export interface JaneSession {
  sessionId: string;
  status: JaneSessionStatus;
  version: string;
  initializedAtUtc: string;
  turns: JaneTurn[];
  clarification?: JaneClarification;
  proposedAction?: JaneProposedAction;
}
