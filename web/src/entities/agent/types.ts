/**
 * Agent Entity Types
 * Sourced from STITCH-Design Jane agent & autonomous orchestration views.
 */
export type AgentStatus = 'IDLE' | 'BUSY' | 'OFFLINE' | 'SYSTEM_READY';

export interface AgentCapability {
  name: string;
  description: string;
  version: string;
}

export interface AgentSpec {
  agentId: string;
  tenantUid: string;
  schemaVersion: string;
  name: string; // e.g. "Jane Agent", "Data Intake Agent"
  role: string;
  status: AgentStatus;
  capabilities: AgentCapability[];
  lastActive: string;
}

export interface AgentRunLog {
  logId: string;
  agentId: string;
  message: string;
  timestamp: string;
  level: 'INFO' | 'WARN' | 'ERROR';
}
