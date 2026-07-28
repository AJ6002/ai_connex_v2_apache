import React, { useState, useEffect } from 'react';
import {
  ViewMode,
  ModelRegistryItem,
  EnvironmentVariable,
  BillableRun,
  SystemNotification,
  AsyncJobProgress,
  AsyncJobStep,
} from './types';

import {
  INITIAL_MODELS,
  INITIAL_ENV_VARS,
  INITIAL_BILLABLE_RUNS,
  INITIAL_NOTIFICATIONS,
} from './data/initialData';

import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { Footer } from './components/Footer';
import { AsyncLoadingModal } from './components/AsyncLoadingModal';
import { NotificationDrawer } from './components/NotificationDrawer';
import { InteractiveDotGrid } from './components/InteractiveDotGrid';

import { CompilerView } from './views/CompilerView';
import { DagInspectorView } from './views/DagInspectorView';
import { WorkflowView } from './views/WorkflowView';
import { PipelineStudioView } from './views/PipelineStudioView';
import { QuotasView } from './views/QuotasView';
import { AdministrationView } from './views/AdministrationView';
import { DeveloperStudioView } from './views/DeveloperStudioView';
import { SettingsView } from './views/SettingsView';
import { SupportView } from './views/SupportView';

export default function App() {
  const [currentView, setCurrentView] = useState<ViewMode>('compiler');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedWorkspace, setSelectedWorkspace] = useState('/cmapss');

  // Domain Data States
  const [models, setModels] = useState<ModelRegistryItem[]>(INITIAL_MODELS);
  const [envVars, setEnvVars] = useState<EnvironmentVariable[]>(INITIAL_ENV_VARS);
  const [billableRuns, setBillableRuns] = useState<BillableRun[]>(INITIAL_BILLABLE_RUNS);
  const [notifications, setNotifications] = useState<SystemNotification[]>(INITIAL_NOTIFICATIONS);

  // UI States
  const [isNotificationOpen, setIsNotificationOpen] = useState(false);
  const [activeJob, setActiveJob] = useState<AsyncJobProgress | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage((prev) => (prev === msg ? null : prev));
    }, 4000);
  };

  // Helper function to create and run simulated background job with clear descriptive steps
  const startDescriptiveJob = (
    title: string,
    subtitle: string,
    steps: Array<{ title: string; description: string; detail?: string }>,
    onComplete?: () => void
  ) => {
    const jobId = 'JOB-' + Math.floor(1000 + Math.random() * 9000);
    const totalSteps = steps.length;

    const initialSteps: AsyncJobStep[] = steps.map((s, i) => ({
      id: `step-${i}`,
      title: s.title,
      description: s.description,
      status: i === 0 ? 'running' : 'pending',
      detail: s.detail,
    }));

    const jobProgress: AsyncJobProgress = {
      jobId,
      title,
      subtitle,
      currentStepIndex: 0,
      totalSteps,
      overallPercent: 10,
      isFinished: false,
      steps: initialSteps,
      logs: [`[${new Date().toLocaleTimeString()}] ${jobId} initialized on Node 1 Dataset Profiler (:8000).`],
    };

    setActiveJob(jobProgress);

    let stepIdx = 0;
    const interval = setInterval(() => {
      stepIdx++;
      if (stepIdx >= totalSteps) {
        clearInterval(interval);
        setActiveJob((prev) => {
          if (!prev) return null;
          return {
            ...prev,
            currentStepIndex: totalSteps - 1,
            overallPercent: 100,
            isFinished: true,
            steps: prev.steps.map((st) => ({ ...st, status: 'completed' })),
            logs: [
              ...prev.logs,
              `[${new Date().toLocaleTimeString()}] ${jobId} successfully completed across all 9 microservices (:8000–:8008).`,
            ],
          };
        });

        setTimeout(() => {
          setActiveJob(null);
          if (onComplete) onComplete();
          showToast(`Completed async action: "${title}"`);
        }, 800);
      } else {
        const percent = Math.round(((stepIdx + 1) / totalSteps) * 100);
        setActiveJob((prev) => {
          if (!prev) return null;
          const updatedSteps: AsyncJobStep[] = prev.steps.map((st, i) => {
            if (i < stepIdx) return { ...st, status: 'completed' };
            if (i === stepIdx) return { ...st, status: 'running' };
            return { ...st, status: 'pending' };
          });

          return {
            ...prev,
            currentStepIndex: stepIdx,
            overallPercent: percent,
            steps: updatedSteps,
            logs: [
              ...prev.logs,
              `[${new Date().toLocaleTimeString()}] Executing Stage ${stepIdx + 1}: ${
                steps[stepIdx].title
              }...`,
            ],
          };
        });
      }
    }, 1200);
  };

  // Handlers for async domain tasks
  const handleRunDagPipeline = (familyLabel: string) => {
    startDescriptiveJob(
      `Orchestrating 9-Node MLOps Cascade (${familyLabel})`,
      'Executing Node 1 Profiler through Node 9 Deployment with VG_1 / VG_2 gateways',
      [
        {
          title: 'Node 1: Dataset Profiler (:8000)',
          description: 'Analyzing 20,631 compiled rows and computing PCA complexity radar.',
          detail: 'Checking feature distribution across 27 compiled input columns.',
        },
        {
          title: 'Node 2: DAG Matcher (:8001)',
          description: 'Classifying pipeline into family & selecting DAG_906 from 1,993 Master DAGs.',
          detail: 'Condition evaluation rules matched 98.4% confidence score.',
        },
        {
          title: 'Node 3 & 4: Recipe Orchestration & Data Prepare (:8002-:8003)',
          description: 'Running Median Imputation, RobustScaler, and Chronological sorting.',
          detail: 'Zero random shuffle rule enforced on time axis time_cycle.',
        },
        {
          title: 'Node 5 & 6: Feature Eng & Zero-Leakage Split (:8004-:8005)',
          description: 'Generating lag vectors (t-1..t-10) and 70/15/15 chronological split.',
          detail: 'Entity boundary guard verified zero unit_id cross-leakage.',
        },
        {
          title: 'Node 7: HPO Trainer (:8006)',
          description: 'Executing 25 trial iterations using LightGBM & PyTorch LSTM.',
          detail: 'Best hyperparameter set: lr=0.001, num_leaves=31.',
        },
        {
          title: 'Node 8: Model Evaluator (:8007)',
          description: 'Sanity Gate VG_1 (5/5 passed) & VG_2 (+20% noise injection robustness).',
          detail: 'Primary metrics: R²=0.948, RMSE=12.4, MAE=9.1.',
        },
        {
          title: 'Node 9: Deploy & Drift Monitor (:8008)',
          description: 'Promoting model artifact to REST endpoint :8001/predict with zero downtime.',
          detail: 'PSI Feature Drift Monitor active on telemetry stream.',
        },
      ],
      () => {
        // Add new notification
        const newNotif: SystemNotification = {
          id: 'n-' + Date.now(),
          title: '9-Node MLOps Cascade Succeeded',
          message: `Pipeline for ${familyLabel} passed VG_1 & VG_2 gateways successfully. Endpoint live at :8001/predict.`,
          timestamp: 'Just now',
          type: 'success',
          read: false,
        };
        setNotifications((prev) => [newNotif, ...prev]);
      }
    );
  };

  const handleSendToMLOpsFromCompiler = () => {
    setCurrentView('workflow');
    handleRunDagPipeline('TIME-SERIES DEGRADATION REGRESSION');
  };

  const handleSelectDagForPipeline = (dagId: string) => {
    setCurrentView('workflow');
    handleRunDagPipeline(`MASTER DAG ${dagId}`);
  };

  const handleRegisterModel = (name: string, framework: string) => {
    startDescriptiveJob(
      `Registering Model: ${name}`,
      'Storing weights artifact in S3 bucket and registering endpoint in registry',
      [
        {
          title: 'Artifact Checksum Verification',
          description: 'Verifying SHA-256 hash of model weights binary.',
        },
        {
          title: 'Container Image Build',
          description: `Bundling ${framework} inference runtime into Cloud Run container.`,
        },
        {
          title: 'Registry Entry Creation',
          description: 'Assigning version tag v1.0.0 and generating secure API tokens.',
        },
      ],
      () => {
        const newItem: ModelRegistryItem = {
          id: 'm-' + Date.now(),
          name,
          status: 'Deployed',
          version: 'v1.0.0',
          lastSync: 'Just now',
          accuracy: 95.1,
          latencyMs: 32,
          framework,
          author: 'Alex Riviera',
        };
        setModels((prev) => [newItem, ...prev]);
      }
    );
  };

  const handleRunInference = async (jsonInput: string) => {
    try {
      const res = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ jsonInput }),
      });
      const data = await res.json();
      return {
        status: data.status || 'nominal',
        action: data.action || 'No action required',
        confidence: data.confidence || 94.2,
        latencyMs: data.latencyMs || 28,
      };
    } catch {
      return {
        status: 'nominal',
        action: 'Telemetry parameters within normal bounds',
        confidence: 94.8,
        latencyMs: 30,
      };
    }
  };

  const handleExportReport = () => {
    startDescriptiveJob(
      'Exporting Resource Usage Report',
      'Aggregating compute expenditures, GPU core hours, and billable runs into PDF/CSV',
      [
        {
          title: 'Fetching Fleet Telemetry',
          description: 'Gathering GPU and CPU usage logs from US-EAST-1 cluster.',
        },
        {
          title: 'Calculating Cost Allocations',
          description: 'Summarizing month-to-date spend ($14,204) across active users.',
        },
        {
          title: 'Generating PDF & CSV Artifacts',
          description: 'Encoding report payload into downloadable binary.',
        },
      ],
      () => {
        // Trigger dummy file download
        const blob = new Blob(
          [`AI-Connexx Resource Usage Report\nGenerated: ${new Date().toISOString()}\nTotal Spend: $14,204\nActive Runs: 42`],
          { type: 'text/plain' }
        );
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'AI-Connexx_Resource_Usage_Report.txt';
        a.click();
      }
    );
  };

  const handleAdjustQuotas = () => {
    startDescriptiveJob(
      'Adjusting Cluster Quotas',
      'Modifying GPU/CPU compute throttles and budget allocation caps',
      [
        {
          title: 'Auditing GPU Cluster Load',
          description: 'Checking current 78% GPU load on US-EAST-1 nodes.',
        },
        {
          title: 'Applying Policy Throttle',
          description: 'Increasing GPU cluster quota to 3,000 allocated hours.',
        },
        {
          title: 'Zero-Downtime Cluster Sync',
          description: 'Propagating updated quota rules to active worker nodes.',
        },
      ]
    );
  };

  const handleAddVariable = (key: string, value: string, description: string, isSecret: boolean) => {
    startDescriptiveJob(
      `Saving Environment Variable: ${key}`,
      'Updating cluster secret vault and initiating zero-downtime rolling restart',
      [
        {
          title: 'Encrypting Secret Payload',
          description: 'Applying AES-256 vault encryption to environment value.',
        },
        {
          title: 'Cluster Propagation',
          description: 'Synchronizing configuration to US-EAST-1 production pods.',
        },
      ],
      () => {
        const newVar: EnvironmentVariable = {
          id: 'env-' + Date.now(),
          key,
          value,
          description,
          isSecret,
          isMasked: isSecret,
          lastUpdated: 'Just now',
        };
        setEnvVars((prev) => [newVar, ...prev]);
      }
    );
  };

  const handleToggleMaskSecret = (id: string) => {
    setEnvVars((prev) =>
      prev.map((v) => (v.id === id ? { ...v, isMasked: !v.isMasked } : v))
    );
  };

  const handleRunQuickTask = (taskTitle: string) => {
    if (taskTitle.includes('DAG')) {
      handleRunDagPipeline('CLASSIFICATION FAMILY');
    } else if (taskTitle.includes('Sync')) {
      startDescriptiveJob(
        'Syncing 9-Microservice Telemetry',
        'Pinging ports :8000–:8008 across active compute nodes and refreshing data drift indicators',
        [
          {
            title: 'Node Heartbeat Ping',
            description: 'Pinging Node 1 through Node 9 across cluster.',
          },
          {
            title: 'PSI Data Drift Recalculation',
            description: 'Updated drift index to 12.4% (Caution threshold).',
          },
        ]
      );
    } else {
      handleRunDagPipeline('ANOMALY DETECTION FAMILY');
    }
  };

  return (
    <div className="min-h-screen text-slate-900 font-sans flex relative overflow-hidden select-none">
      {/* Interactive Dot Grid Background Canvas with Mouse Fluid Physics */}
      <InteractiveDotGrid />

      {/* Persistent Left Sidebar */}
      <Sidebar currentView={currentView} onSelectView={setCurrentView} />

      {/* Top App Header */}
      <Header
        currentView={currentView}
        notifications={notifications}
        onToggleNotifications={() => setIsNotificationOpen(!isNotificationOpen)}
        onRunQuickTask={handleRunQuickTask}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        selectedWorkspace={selectedWorkspace}
        onSelectWorkspace={setSelectedWorkspace}
      />

      {/* Toast Notification Banner */}
      {toastMessage && (
        <div className="fixed top-20 right-6 z-50 bg-[#0F172A]/90 backdrop-blur-xl text-white px-4 py-2.5 rounded-2xl shadow-2xl font-mono text-xs flex items-center gap-2 border border-white/20 animate-bounce">
          <span className="material-symbols-outlined text-emerald-400 text-base">check_circle</span>
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Main Content Workspace with iOS Glassmorphism & 100% Canvas Width */}
      <main className="w-full pt-20 pb-28 px-6 flex-1 overflow-y-auto min-h-screen relative z-10">
        <div className="max-w-[1600px] mx-auto">
          {currentView === 'compiler' && (
            <CompilerView onSendToMLOps={handleSendToMLOpsFromCompiler} />
          )}

          {currentView === 'dag_inspector' && (
            <DagInspectorView onSelectDagForPipeline={handleSelectDagForPipeline} />
          )}

          {currentView === 'workflow' && (
            <WorkflowView
              onRunDagPipeline={handleRunDagPipeline}
              isJobRunning={!!activeJob}
            />
          )}

          {currentView === 'pipeline_studio' && (
            <PipelineStudioView
              models={models}
              onRegisterModel={handleRegisterModel}
              onRunInference={handleRunInference}
            />
          )}

          {currentView === 'quotas' && (
            <QuotasView
              billableRuns={billableRuns}
              onExportReport={handleExportReport}
              onAdjustQuotas={handleAdjustQuotas}
            />
          )}

          {currentView === 'administration' && (
            <AdministrationView
              envVars={envVars}
              onAddVariable={handleAddVariable}
              onToggleMaskSecret={handleToggleMaskSecret}
            />
          )}

          {currentView === 'developer_studio' && <DeveloperStudioView />}

          {currentView === 'settings' && <SettingsView />}

          {currentView === 'support' && <SupportView />}
        </div>
      </main>

      {/* Persistent Footer Status Bar */}
      <Footer />

      {/* Notifications Drawer */}
      <NotificationDrawer
        isOpen={isNotificationOpen}
        notifications={notifications}
        onClose={() => setIsNotificationOpen(false)}
        onMarkAllRead={() => setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))}
      />

      {/* Descriptive Async Loading Modal Overlay */}
      <AsyncLoadingModal
        job={activeJob}
        onDismissToBackground={() => {
          showToast('Job running in background. Check Notification Drawer for completion.');
          setActiveJob(null);
        }}
        onCancelJob={() => {
          showToast('Job canceled by user.');
          setActiveJob(null);
        }}
      />
    </div>
  );
}
