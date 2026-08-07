export type ViewMode = 
  | 'compiler'
  | 'dag_inspector'
  | 'workflow'
  | 'pipeline_studio'
  | 'master_data'
  | 'templates'
  | 'workspace'
  | 'administration'
  | 'quotas'
  | 'developer_studio'
  | 'settings'
  | 'support'
  | 'vg1'
  | 'vg2'
  | 'node1'
  | 'node2'
  | 'node3'
  | 'node4'
  | 'node5'
  | 'node6'
  | 'node7'
  | 'node8'
  | 'node9'
  | 'orchestrator_board'
  | 'data_explorer';

export type SidebarStyle = 'orbital' | 'slim';

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
