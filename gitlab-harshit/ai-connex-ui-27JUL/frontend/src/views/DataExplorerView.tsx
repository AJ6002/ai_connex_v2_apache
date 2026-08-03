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

interface DataExplorerViewProps {
  compiledCsvPath?: string;
  runId?: string;
  dagId?: string;
  algorithmFamily?: string;
  onProceedToPrepare: () => void;
}

export const DataExplorerView: React.FC<DataExplorerViewProps> = ({
  compiledCsvPath,
  runId = 'run_20250115_143022',
  dagId = 'DAG_201',
  algorithmFamily = 'Anomaly Detection',
  onProceedToPrepare
}) => {
  const [activeTab, setActiveTab] = useState<'pre-prepare' | 'post-prepare' | 'post-fe' | 'post-train'>('pre-prepare');
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

  // Fetch backend profiling payload if backend is online
  useEffect(() => {
    if (compiledCsvPath) {
      const profilerForm = new FormData();
      profilerForm.append('file_path', compiledCsvPath);
      fetch('http://localhost:8000/api/v1/profile', {
        method: 'POST',
        body: profilerForm
      })
      .then(res => res.ok ? res.json() : null)
      .then(data => {
        if (data && data.profile) {
          setBackendProfile(data.profile);
        }
      })
      .catch(() => {});
    }
  }, [compiledCsvPath]);

  // Sidebar Icons definitions (MainPages Rail)
  const sidebarTopIcons = [
    { id: 'magic', icon: <Sparkles size={18} />, classes: "sidebar-icon-magic" },
    { id: 'chat', icon: <MessageSquare size={18} /> },
    { id: 'upload', icon: <UploadCloud size={18} /> },
    { id: 'analytics', icon: <BarChart2 size={18} />, classes: "sidebar-icon-active" },
    { id: 'cleanup', icon: <Eraser size={18} /> },
    { id: 'tasks', icon: <CheckSquare size={18} /> },
    { id: 'lab', icon: <Beaker size={18} /> },
    { id: 'flow', icon: <Workflow size={18} /> },
    { id: 'docs', icon: <FileText size={18} /> },
    { id: 'deploy', icon: <Rocket size={18} /> },
    { id: 'growth', icon: <TrendingUp size={18} /> },
  ];

  const sidebarBottomIcons = [
    { id: 'network', icon: <Network size={18} />, classes: "sidebar-icon-blue-active", badge: 9 },
    { id: 'security', icon: <Shield size={18} /> },
    { id: 'storage', icon: <Database size={18} /> }
  ];

  // Pipeline stage tabs
  const tabs = [
    { id: 'pre-prepare', label: 'Pre-Prepare', badge: 'Brain', number: 1 },
    { id: 'post-prepare', label: 'Post-Prepare', badge: 'Prepare', number: 2 },
    { id: 'post-fe', label: 'Post-F.E', badge: 'Feature Engineered', number: 3 },
    { id: 'post-train', label: 'Post-Train', badge: 'Training', number: 4 }
  ];

  // Render correct subpage
  const renderSubpage = () => {
    switch (activeTab) {
      case 'pre-prepare':
        return (
          <PrePrepare 
            onProceed={() => setActiveTab('post-prepare')}
            compiledCsvPath={compiledCsvPath}
            runId={runId}
            dagId={dagId}
            algorithmFamily={algorithmFamily}
          />
        );
      case 'post-prepare':
        return (
          <PostPrepare 
            onProceed={() => setActiveTab('post-fe')}
            compiledCsvPath={compiledCsvPath}
            runId={runId}
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
      default:
        return <PrePrepare onProceed={() => setActiveTab('post-prepare')} />;
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-canvas font-sans">
      
      {/* Sub-Header / Control Hub */}
      <section className="sub-header-container" style={{ backgroundColor: '#060914' }}>
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
              <span className={`stage-badge stage-badge-${tab.id === 'pre-prepare' ? 'brain' : tab.id === 'post-prepare' ? 'prepare' : tab.id === 'post-fe' ? 'fe' : 'training'}`}>
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
