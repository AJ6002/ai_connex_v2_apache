import { ModelRegistryItem, EnvironmentVariable, BillableRun, DAGNode, SystemNotification } from '../types';

export const INITIAL_MODELS: ModelRegistryItem[] = [
  {
    id: 'm1',
    name: 'Alpha_Predict_V4',
    status: 'Deployed',
    version: 'v2.4.1',
    lastSync: '2 mins ago',
    accuracy: 94.2,
    latencyMs: 42,
    framework: 'PyTorch / TensorRT',
    author: 'Alex Riviera'
  },
  {
    id: 'm2',
    name: 'Maritime_Log_Analyzer',
    status: 'Training',
    version: 'v1.0.8',
    lastSync: '1 hour ago',
    accuracy: 91.8,
    latencyMs: 88,
    framework: 'XGBoost',
    author: 'M. Laurent'
  },
  {
    id: 'm3',
    name: 'Hull_Stress_Forecaster',
    status: 'Archived',
    version: 'v3.1.2',
    lastSync: '3 days ago',
    accuracy: 89.5,
    latencyMs: 120,
    framework: 'LightGBM',
    author: 'J. Doe'
  },
  {
    id: 'm4',
    name: 'Engine_Temp_Anomaly',
    status: 'Deployed',
    version: 'v1.1.0',
    lastSync: '12 mins ago',
    accuracy: 96.7,
    latencyMs: 28,
    framework: 'ONNX / CUDA',
    author: 'S. Ahmed'
  },
  {
    id: 'm5',
    name: 'Digital_Twin_Hydraulics',
    status: 'Validation',
    version: 'v0.9.4',
    lastSync: '45 mins ago',
    accuracy: 93.4,
    latencyMs: 65,
    framework: 'Scikit-Learn',
    author: 'A. Riviera'
  }
];

export const INITIAL_ENV_VARS: EnvironmentVariable[] = [
  {
    id: 'env-1',
    key: 'AWS_ACCESS_KEY_ID',
    value: 'AKIAIOSFODNN7EXAMPLE9823472918',
    description: 'IAM Identity access token for S3 artifact storage',
    isSecret: true,
    isMasked: true,
    lastUpdated: '2 hours ago'
  },
  {
    id: 'env-2',
    key: 'DATABASE_URL',
    value: 'postgresql://db_admin@precision-prod-cluster:5432/main',
    description: 'PostgreSQL main transactional database connection',
    isSecret: false,
    isMasked: false,
    lastUpdated: '1 day ago'
  },
  {
    id: 'env-3',
    key: 'DATABASE_PASSWORD',
    value: 'P@ssw0rd_Marine_Automation_2026_Secure!',
    description: 'Restricted credential for production DB write access',
    isSecret: true,
    isMasked: true,
    lastUpdated: '3 days ago'
  },
  {
    id: 'env-4',
    key: 'MAX_CONCURRENT_RUNS',
    value: '512',
    description: 'Global throttle for model training pipelines',
    isSecret: false,
    isMasked: false,
    lastUpdated: '5 days ago'
  },
  {
    id: 'env-5',
    key: 'LOG_LEVEL',
    value: 'INFO',
    description: 'Verbosity level for application telemetry',
    isSecret: false,
    isMasked: false,
    lastUpdated: '1 week ago'
  },
  {
    id: 'env-6',
    key: 'REDIS_PRIVATE_KEY',
    value: 'MIIEowIBAAKCAQEAz8qQ1P7j49yK6kY9m2vN8P1qQ2wE4rT7yU8iO9p0a1s2d3f4g5h6j7k8l9z',
    description: 'RSA Private key for distributed cache encryption',
    isSecret: true,
    isMasked: true,
    lastUpdated: '2 weeks ago'
  }
];

export const INITIAL_BILLABLE_RUNS: BillableRun[] = [
  {
    id: 'run-1',
    timestamp: '2026-07-22 14:22:01',
    userInitials: 'JD',
    userName: 'J. Doe',
    userColor: 'bg-[#2e4198] text-[#a6b4ff]',
    operation: 'Hyperparameter Tuning (V3)',
    resourceTier: 'A100-80GB',
    tierBadgeColor: 'bg-[#ffdad6] text-[#ba1a1a]',
    duration: '04h 12m',
    cost: 342.12
  },
  {
    id: 'run-2',
    timestamp: '2026-07-22 13:05:44',
    userInitials: 'ML',
    userName: 'M. Laurent',
    userColor: 'bg-[#bc000c]/20 text-[#bc000c]',
    operation: 'Data Preprocessing (Marine-S1)',
    resourceTier: 'STANDARD-CPU',
    tierBadgeColor: 'bg-[#e7e8e9] text-[#454652]',
    duration: '01h 55m',
    cost: 12.40
  },
  {
    id: 'run-3',
    timestamp: '2026-07-22 11:45:12',
    userInitials: 'JD',
    userName: 'J. Doe',
    userColor: 'bg-[#2e4198] text-[#a6b4ff]',
    operation: 'Model Validation (Legacy-X)',
    resourceTier: 'V100-32GB',
    tierBadgeColor: 'bg-[#2e4198] text-[#a6b4ff]',
    duration: '00h 48m',
    cost: 84.00
  },
  {
    id: 'run-4',
    timestamp: '2026-07-22 09:12:00',
    userInitials: 'SA',
    userName: 'S. Ahmed',
    userColor: 'bg-[#783600] text-[#ffa267]',
    operation: 'Pipeline Orchestration',
    resourceTier: 'STANDARD-CPU',
    tierBadgeColor: 'bg-[#e7e8e9] text-[#454652]',
    duration: '12h 00m',
    cost: 144.00
  },
  {
    id: 'run-5',
    timestamp: '2026-07-21 21:04:18',
    userInitials: 'AR',
    userName: 'A. Riviera',
    userColor: 'bg-[#122881] text-[#ffffff]',
    operation: 'Digital Twin Simulation Run #91',
    resourceTier: 'A100-80GB',
    tierBadgeColor: 'bg-[#ffdad6] text-[#ba1a1a]',
    duration: '06h 30m',
    cost: 512.80
  }
];

export const DAG_FAMILY_NODES: DAGNode[] = [
  { id: 'f1', label: 'CLASSIFICATION FAMILY', type: 'classifier', family: 'Classification' },
  { id: 'f2', label: 'REGRESSION FAMILY', type: 'classifier', family: 'Regression' },
  { id: 'f3', label: 'ANOMALY DETECTION FAMILY', type: 'classifier', family: 'Anomaly' },
  { id: 'f4', label: 'CLUSTERING FAMILY', type: 'classifier', family: 'Clustering' },
  { id: 'f5', label: 'TIME-SERIES FORECASTING FAMILY', type: 'classifier', family: 'TimeSeries' },
  { id: 'f6', label: 'DIGITAL TWIN FAMILY', type: 'classifier', family: 'DigitalTwin' },
  { id: 'f7', label: 'REINFORCEMENT LEARNING FAMILY', type: 'classifier', family: 'RL' },
  { id: 'f8', label: 'RECOMMENDATION FAMILY', type: 'classifier', family: 'Recommendation' },
  { id: 'f9', label: 'NLP/TEXT-CLASSIFICATION FAMILY', type: 'classifier', family: 'NLP' },
  { id: 'f10', label: 'COMPUTER VISION FAMILY', type: 'classifier', family: 'CV' },
];

export const RECIPE_STEPS_NODES: DAGNode[] = [
  { id: 'rec-prep', label: 'PREPARE', type: 'processing', description: 'Raw Data Profiling & Cleaning' },
  { id: 'rec-impute', label: 'IMPUTE', type: 'processing', description: 'Missing Value Imputation' },
  { id: 'rec-eng', label: 'ENGINEER', type: 'processing', description: 'Feature Engineering & Extractions' },
  { id: 'rec-outlier', label: 'OUTLIER', type: 'processing', description: 'Isolation Forest Outlier Removal' },
  { id: 'rec-encode', label: 'ENCODE', type: 'processing', description: 'One-Hot & Embeddings Encoding' },
  { id: 'rec-split', label: 'SPLIT', type: 'processing', description: 'Train/Val/Test Split Engine' },
  { id: 'rec-scale', label: 'SCALE', type: 'processing', description: 'MinMax / StandardScaler' },
  { id: 'rec-clean', label: 'TEXT_CLEAN', type: 'processing', description: 'Regex & Normalization' },
  { id: 'rec-train', label: 'TRAIN', type: 'processing', description: 'Distributed Model Training' },
  { id: 'rec-fetch', label: 'ALGO_FETCH', type: 'processing', description: 'Fetch Model Architecture' },
  { id: 'rec-tune', label: 'HYPER_TUNING', type: 'processing', description: 'Bayesian Hyperparameter Optimization' },
  { id: 'rec-deploy', label: 'DEPLOY', type: 'processing', description: 'Zero-Downtime Container Rollout' },
  { id: 'rec-mon', label: 'MONITOR', type: 'processing', description: 'Realtime Telemetry & Data Drift' },
  { id: 'rec-final', label: 'TRAIN_FINAL', type: 'processing', description: 'Final Production Checkpoint' },
  { id: 'rec-align', label: 'TIME_ALIGN', type: 'processing', description: 'Timestamp & Log Synchronization' },
  { id: 'rec-vg1', label: 'VG_1', type: 'gate', description: 'Validation Gateway 1 (Accuracy >= 90%)' },
  { id: 'rec-vg2', label: 'VG_2', type: 'gate', description: 'Validation Gateway 2 (Latency <= 50ms)' }
];

export const INITIAL_NOTIFICATIONS: SystemNotification[] = [
  {
    id: 'n1',
    title: 'Cluster Quota Warning',
    message: 'GPU Cluster usage peaked at 78%. Projection suggests quota exhaustion in 6 days.',
    timestamp: '10 mins ago',
    type: 'warning',
    read: false
  },
  {
    id: 'n2',
    title: 'Pipeline DAG Completed',
    message: 'Recipe Orchestration DAG #8042 successfully completed VG_1 & VG_2 validation gateways.',
    timestamp: '25 mins ago',
    type: 'success',
    read: false
  },
  {
    id: 'n3',
    title: 'New Model Registered',
    message: 'Alpha_Predict_V4 v2.4.1 was successfully registered by Alex Riviera.',
    timestamp: '1 hour ago',
    type: 'info',
    read: true
  }
];
