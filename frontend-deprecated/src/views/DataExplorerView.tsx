import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  MessageSquare, 
  UploadCloud, 
  BarChart2, 
  Eraser, 
  CheckSquare, 
  Beaker, 
  Workflow, 
  FileText, 
  Rocket, 
  TrendingUp, 
  Network, 
  Shield, 
  Database,
  Bell,
  Sun,
  Moon,
  ChevronDown,
  Folder
} from 'lucide-react';

import PrePrepare from './DataExplorer/PrePrepare';
import PostPrepare from './DataExplorer/PostPrepare';
import PostFE from './DataExplorer/PostFE';
import PostTrain from './DataExplorer/PostTrain';
import AdHocExplorer from './DataExplorer/AdHocExplorer';

interface DataExplorerViewProps {
  compiledCsvPath?: string;
  runId?: string;
  dagId?: string;
  algorithmFamily?: string;
  onProceedToPrepare: () => void;
  onApproveDeliverables?: () => void;
  executionMode?: 'EXPLORATION_ONLY' | 'PREPARATION_ONLY' | 'FULL_AUTOML' | 'DIRECT_NAVIGATION';
  janeSessionId?: string;
}

export const DataExplorerView: React.FC<DataExplorerViewProps> = ({
  compiledCsvPath,
  runId,
  dagId = 'DAG_201',
  algorithmFamily = 'Anomaly Detection',
  onProceedToPrepare,
  onApproveDeliverables,
  executionMode = 'FULL_AUTOML',
  janeSessionId,
}) => {
  const [activeTab, setActiveTab] = useState<'pre-prepare' | 'exhaustive-eda' | 'post-prepare' | 'post-fe' | 'post-train' | 'ad-hoc'>('pre-prepare');
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [actionsOpen, setActionsOpen] = useState(false);
  const [backendProfile, setBackendProfile] = useState<any>(null);

  // Sync theme with document attribute
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  // Fetch backend profiling payload if dataset is active
  useEffect(() => {
    if (!compiledCsvPath) {
      setBackendProfile(null);
      return;
    }
    const profilerForm = new FormData();
    profilerForm.append('file_path', compiledCsvPath);
    if (janeSessionId) {
      profilerForm.append('session_id', janeSessionId);
    }
    fetch('http://localhost:8000/api/v1/profile', {
      method: 'POST',
      body: profilerForm
    })
    .then(res => res.ok ? res.json() : null)
    .then(data => {
      if (data && data.profile) {
        const combinedProfile = {
          ...data.profile,
          qwen_semantics: data.qwen_semantics || data.profile?.qwen_semantics || {},
          phi4_story: data.narrative || data.phi4_story || data.profile?.phi4_story || '',
          phi4_story_html: data.phi4_story_html || data.narrative_html || data.profile?.phi4_story_html || '',
          profile_narrative: data.profile_narrative || data.profile?.profile_narrative || '',
          profile_narrative_html: data.profile_narrative_html || data.profile?.profile_narrative_html || '',
        };
        setBackendProfile(combinedProfile);
        // Bind profile summary to Jane session memory
        if (janeSessionId && data.profile_narrative) {
          fetch('http://localhost:8000/api/v1/session/bind_profile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              session_id: janeSessionId,
              run_id: runId || data.run_id || 'session_live',
              compiled_csv_path: compiledCsvPath,
              profile_narrative: data.profile_narrative,
              execution_mode: executionMode
            })
          }).catch(() => {});
        }
      }
    })
    .catch(() => {});
  }, [compiledCsvPath, janeSessionId, executionMode]);

  // Sidebar Icons definitions (MainPages Rail)
  const sidebarTopIcons = [
    { icon: Sparkles, id: 'aic-agent', label: 'AI Intelligence' },
    { icon: MessageSquare, id: 'chat-dock', label: 'Jane Assistant' },
    { icon: UploadCloud, id: 'upload-hub', label: 'Data Ingestion' },
    { icon: BarChart2, id: 'profiler', label: 'Statistical Profiler' },
    { icon: Eraser, id: 'cleaner', label: 'Data Cleansing' },
    { icon: CheckSquare, id: 'validation', label: 'Industrial Rules' },
    { icon: Beaker, id: 'experiments', label: 'Feature Lab' },
    { icon: Workflow, id: 'dag-studio', label: 'DAG Studio' },
    { icon: FileText, id: 'audit-log', label: 'Audit Manifest' },
    { icon: Rocket, id: 'deployment', label: 'Edge Gateway' },
  ];

  const sidebarBottomIcons = [
    { id: 'network', icon: <Network size={18} />, classes: "sidebar-icon-blue-active", badge: 9 },
    { id: 'security', icon: <Shield size={18} /> },
    { id: 'storage', icon: <Database size={18} /> }
  ];

  // Pipeline Execution Stage Tabs definition (Mode-Aware)
  const isExploreMode = executionMode === 'EXPLORATION_ONLY' || executionMode === 'PREPARATION_ONLY';
  const tabs = isExploreMode
    ? [
        { id: 'pre-prepare', label: 'Data Health', badge: 'Profiler', number: '01' },
        { id: 'exhaustive-eda', label: 'Deep EDA', badge: 'Statistics', number: '02' },
        { id: 'ad-hoc', label: 'Visual Query', badge: 'Graphic Walker', number: '03' },
      ]
    : [
        { id: 'pre-prepare', label: 'Pre-Prepare', badge: 'Brain', number: '01' },
        { id: 'exhaustive-eda', label: 'Exhaustive EDA', badge: 'Deep-EDA', number: '02' },
        { id: 'post-prepare', label: 'Post-Prepare', badge: 'Cleaned', number: '03' },
        { id: 'post-fe', label: 'Post-FE', badge: 'Features', number: '04' },
        { id: 'post-train', label: 'Post-Train', badge: 'Model', number: '05' },
        { id: 'ad-hoc', label: 'Ad-Hoc Explorer', badge: 'Visual', number: '06' },
      ];

  // Render correct subpage
  const renderSubpage = () => {
    switch (activeTab) {
      case 'pre-prepare':
        return (
          <PrePrepare 
            onProceed={() => setActiveTab('post-prepare')}
            compiledCsvPath={compiledCsvPath}
            runId={runId || 'session_live'}
            dagId={dagId}
            algorithmFamily={algorithmFamily}
            backendProfile={backendProfile}
            onApproveDeliverables={onApproveDeliverables}
            executionMode={executionMode}
            onOpenGraphicWalker={() => setActiveTab('ad-hoc')}
          />
        );
      case 'exhaustive-eda':
        const activeCsvName = compiledCsvPath ? compiledCsvPath.replace(/\\/g, '/').split('/').pop() : 'No Dataset Loaded';
        return (
          <div className="p-6 max-w-[1700px] mx-auto animate-fadeIn space-y-4">
            <div className="flex items-center justify-between bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <div className="flex items-center gap-3.5">
                <div className="w-10 h-10 flex items-center justify-center bg-[#FF6B35]/10 border border-[#FF6B35]/30 rounded-xl text-[#FF6B35]">
                  <span className="material-symbols-outlined text-xl">insights</span>
                </div>
                <div>
                  <h2 className="text-base font-bold text-slate-900 flex items-center gap-2.5">
                    Exhaustive Statistical EDA Report
                    <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">
                      Live fg-data-profiling
                    </span>
                  </h2>
                  <p className="text-xs text-slate-500 mt-1 flex items-center gap-2">
                    <span>Source: <strong className="text-slate-700 font-mono bg-slate-100 border border-slate-200 px-2 py-0.5 rounded">{activeCsvName}</strong></span>
                    <span className="text-slate-300">•</span>
                    <span>Real histograms, time-series PACF &amp; missingness heatmaps (&lt; 2 MB fast load)</span>
                  </p>
                </div>
              </div>
              <button 
                onClick={() => setActiveTab('pre-prepare')}
                className="px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold rounded-xl transition-all border border-slate-200 hover:border-slate-300 shadow-2xs cursor-pointer flex items-center gap-1.5"
              >
                <span>← Back to Pre-Prepare</span>
              </button>
            </div>
            
            <iframe 
              src={`http://localhost:8000/api/v1/reports/eda_report.html?theme=${theme}&file_path=${encodeURIComponent(compiledCsvPath || '')}`}
              className="w-full h-[82vh] rounded-2xl border border-slate-200 shadow-sm bg-white transition-all"
              title="Exhaustive Data Profiling Report"
            />
          </div>
        );

      case 'post-prepare':
        return (
          <PostPrepare 
            onProceed={() => setActiveTab('post-fe')}
            compiledCsvPath={compiledCsvPath}
            runId={runId || 'session_live'}
            dagId={dagId}
          />
        );
      case 'post-fe':
        return (
          <PostFE 
            onProceed={() => setActiveTab('post-train')}
            compiledCsvPath={compiledCsvPath}
            runId={runId}
            dagId={dagId}
          />
        );
      case 'post-train':
        return (
          <PostTrain 
            compiledCsvPath={compiledCsvPath}
            runId={runId}
            dagId={dagId}
          />
        );
      case 'ad-hoc':
        return (
          <AdHocExplorer
            compiledCsvPath={compiledCsvPath}
            runId={runId}
            dagId={dagId}
            algorithmFamily={algorithmFamily}
          />
        );
      default:
        return <PrePrepare onProceed={() => setActiveTab('post-prepare')} />;
    }
  };


  return (
    <div className="flex flex-col min-h-screen bg-canvas font-sans animate-slideInRight">
      
      {/* Sub-Header / Control Hub */}
      <section className="sub-header-container">
        <div className="sub-header-top">
          <div className="window-dots-title">
            <div className="window-dots">
              <span className="dot dot-red" style={{ backgroundColor: '#C8102E' }}></span>
              <span className="dot dot-yellow"></span>
              <span className="dot dot-green"></span>
            </div>
            <div className="window-title">
              <Folder size={14} />
              Dataset Explorer Stage Transit Hub
            </div>
          </div>
        </div>

        {/* Navigation Pipeline Tabs */}
        <nav className="stages-tabs-container">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={`stage-tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id as any)}
            >
              <span className="stage-tab-text-title">{tab.label}</span>
              <span className={`stage-badge stage-badge-${tab.id === 'pre-prepare' ? 'brain' : tab.id === 'post-prepare' ? 'prepare' : tab.id === 'post-fe' ? 'fe' : tab.id === 'post-train' ? 'training' : 'adhoc'}`}>
                {tab.badge}
              </span>
              <span className="stage-tab-number">{tab.number}</span>
            </button>
          ))}
        </nav>
      </section>

      {/* Content Render Workspace */}
      <div style={{ flex: 1 }}>
        {renderSubpage()}
      </div>

      {/* Operational Footer */}
      <footer className="app-footer">
        <div className="footer-status">
          <span className="status-dot"></span>
          SYSTEM STATUS: OPERATIONAL
        </div>
        <div>
          © 2026 TAS AI-Suite. All Rights Reserved.
        </div>
        <div className="footer-links">
          <a href="#privacy">Privacy Policy</a>
          <a href="#terms">Terms of Service</a>
          <a href="#security">Security Standards</a>
        </div>
      </footer>

    </div>
  );
};

export default DataExplorerView;
