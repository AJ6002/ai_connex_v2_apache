export type ViewMode = 
  | 'compiler'
  | 'dag_inspector'
  | 'workflow'
  | 'pipeline_studio'
  | 'administration'
  | 'quotas'
  | 'developer_studio'
  | 'settings'
  | 'support';

export interface ModelRegistryItem {
  id: string;
  name: string;
  status: 'Deployed' | 'Training' | 'Archived' | 'Validation';
  version: string;
  lastSync: string;
  accuracy: number;
  latencyMs: number;
  framework: string;
  author: string;
}

export interface EnvironmentVariable {
  id: string;
  key: string;
  value: string;
  description: string;
  isSecret: boolean;
  isMasked: boolean;
  lastUpdated: string;
}

export interface BillableRun {
  id: string;
  timestamp: string;
  userInitials: string;
  userName: string;
  userColor: string;
  operation: string;
  resourceTier: string;
  tierBadgeColor: string;
  duration: string;
  cost: number;
}

export interface DAGNode {
  id: string;
  label: string;
  type: 'profiler' | 'classifier' | 'orchestrator' | 'recipe' | 'processing' | 'gate' | 'output';
  status?: 'idle' | 'running' | 'completed' | 'failed' | 'warning';
  family?: string;
  progress?: number;
  description?: string;
  inputPort?: string;
  outputPort?: string;
}

export interface AsyncJobStep {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  detail?: string;
}

export interface AsyncJobProgress {
  jobId: string;
  title: string;
  subtitle: string;
  currentStepIndex: number;
  totalSteps: number;
  overallPercent: number;
  isFinished: boolean;
  hasError?: boolean;
  errorMessage?: string;
  steps: AsyncJobStep[];
  logs: string[];
}

export interface SystemNotification {
  id: string;
  title: string;
  message: string;
  timestamp: string;
  type: 'info' | 'warning' | 'success' | 'error';
  read: boolean;
}
