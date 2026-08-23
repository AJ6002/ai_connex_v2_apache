/**
 * Model Entity Types
 * Sourced from STITCH-Design model registry & evaluation screens.
 */
export type ModelStatus = 'TRAINING' | 'EVALUATING' | 'READY' | 'DEPRECATED' | 'FAILED';

export interface ModelMetric {
  name: string;
  value: number;
  unit?: string;
  baseline?: number;
}

export interface ModelSpec {
  modelId: string;
  name: string;
  version: string;
  framework: string; // e.g. "PyTorch", "XGBoost", "LightGBM", "ONNX"
  status: ModelStatus;
  datasetRef: string;
  metrics: ModelMetric[];
  accuracy?: number;
  loss?: number;
  /** Originating training job id (registry "TRAINING RUN" column). */
  trainingRun?: string;
  /** Current deployment target label (registry "DEPLOYMENT" column). */
  deployment?: string;
  createdAt: string;
  updatedAt: string;
}
