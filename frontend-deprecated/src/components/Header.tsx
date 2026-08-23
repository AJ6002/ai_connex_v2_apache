import React, { useState } from 'react';
import { ViewMode, SidebarStyle, SystemNotification } from '../types';
import { TasLogo } from './TasLogo';
import { useTheme } from '../context/ThemeContext';

interface HeaderProps {
  currentView: ViewMode;
  notifications: SystemNotification[];
  onToggleNotifications: () => void;
  onRunQuickTask: (taskTitle: string) => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  selectedWorkspace?: string;
  onSelectWorkspace?: (ws: string) => void;
  sidebarStyle?: SidebarStyle;
  onOpenChatBot?: () => void;
  onSelectView?: (view: ViewMode) => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentView,
  notifications,
  onToggleNotifications,
  onRunQuickTask,
  searchQuery,
  onSearchChange,
  selectedWorkspace = '/cmapss',
  onSelectWorkspace,
  sidebarStyle,
  onOpenChatBot,
  onSelectView,
}) => {
  const { isDark, toggleTheme } = useTheme();
  const unreadCount = notifications.filter((n) => !n.read).length;
  const [isQuickMenuOpen, setIsQuickMenuOpen] = useState(false);
  const [isHealthModalOpen, setIsHealthModalOpen] = useState(false);

  // 9 Microservices fleet status
  const microservices = [
    { name: 'Node 1: Dataset Profiler', port: 8000, status: 'Online', latency: '12ms' },
    { name: 'Node 2: DAG Matcher', port: 8001, status: 'Online', latency: '8ms' },
    { name: 'Node 3: Recipe Orchestrator', port: 8002, status: 'Online', latency: '14ms' },
    { name: 'Node 4: Data Prepare', port: 8003, status: 'Online', latency: '9ms' },
    { name: 'Node 5: Feature Synthesizer', port: 8004, status: 'Online', latency: '22ms' },
    { name: 'Node 6: Validation Gate 1', port: 8005, status: 'Online', latency: '11ms' },
    { name: 'Node 7: HPO AutoML Trainer', port: 8006, status: 'Online', latency: '45ms' },
    { name: 'Node 8: Validation Gate 2', port: 8007, status: 'Online', latency: '15ms' },
    { name: 'Node 9: Model Serving / Monitor', port: 8008, status: 'Online', latency: '6ms' },
  ];

  const getViewTitle = () => {
    switch (currentView) {
      case 'hero':
        return null;
      case 'compiler':
        return 'Data-Studio — Multi-Table Compiler';
      case 'data_explorer':
        return 'Data-Studio — Dataset Explorer';
      case 'prepare':
        return 'Data-Studio — Prepare Node';
      case 'feature_engineering':
        return 'ML-Studio — Feature Synthesis (Node 5)';
      case 'train':
        return 'ML-Studio — AutoML HPO Trainer (Node 7)';
      case 'deploy':
        return 'ML-Studio — Model Deployment (Node 9)';
      case 'pipeline_studio':
        return 'ML-Studio — Monitoring & Inference Playground';
      case 'agent_manager':
        return 'Agent-Studio — Fleet Orchestration & LLM Keys';
      case 'orchestrator_board':
        return '9-Microservice Execution Cascade';
      case 'settings':
        return 'Settings & System Preferences';
      case 'support':
        return 'Support & Documentation Hub';
      case 'administration':
        return 'Enterprise Administration';
      case 'templates':
        return 'Pipeline Templates & Blueprints';
      case 'quotas':
        return 'Quotas & Resource Allocation';
      default:
        return null;
    }
  };

  return (
    <header className={`fixed top-0 left-0 right-0 w-full h-16 backdrop-blur-2xl text-white z-40 flex justify-between items-center pr-6 transition-all duration-300 ${
      sidebarStyle === 'slim' ? 'pl-24' : 'pl-6'
    }`}
      style={{
        /* Deep Obsidian Navy — matching hero design palette */
        background: 'linear-gradient(135deg, #2B0063 0%, #3C1053 60%, #1D0042 100%)',
        borderBottom: '1px solid rgba(255,255,255,0.10)',
        boxShadow: '0 4px 24px rgba(6,9,20,0.40), inset 0 -1px 0 rgba(255,255,255,0.06)',
      }}
    >
      {/* Left Title & Brand Logo — Routes to Hero on click */}
      <div className="flex items-center gap-3.5">
        <div 
          onClick={() => onSelectView && onSelectView('hero')} 
          title="Go to TAS AIConnex Hero Page" 
          className="hover:opacity-90 transition-opacity cursor-pointer active:scale-95 flex items-center"
        >
          <TasLogo className="h-8" showSubtitle={true} />
        </div>

        {getViewTitle() && (
          <>
            <div className="h-5 w-px" style={{background:'rgba(255,255,255,0.20)'}}></div>
            <h1 className="font-headline text-xs sm:text-sm font-bold text-white/90 tracking-tight whitespace-nowrap bg-white/10 px-2.5 py-1 rounded-lg border border-white/10">
              {getViewTitle()}
            </h1>
          </>
        )}
      </div>

      {/* Right Controls & Status */}
      <div className="flex items-center gap-3">

        {/* 9-Microservice Health Heartbeat Status Badge */}
        <div className="relative">
          <button
            onClick={() => setIsHealthModalOpen(!isHealthModalOpen)}
            className="flex items-center gap-2 px-3 py-1 rounded-full transition-all text-xs font-mono font-bold backdrop-blur-md"
            style={{background:'rgba(232,99,38,0.18)', border:'1px solid rgba(232,99,38,0.35)', color:'#E86326'}}
            title="Click to view 9 Microservices Status"
          >
            <span className="w-2 h-2 rounded-full bg-[#E86326] animate-pulse"></span>
            <span className="hidden xl:inline">9 Services Online</span>
            <span className="xl:hidden">9/9</span>
          </button>

          {/* Microservices Health Popover */}
          {isHealthModalOpen && (
            <div className="absolute right-0 mt-2 w-80 glass-panel rounded-2xl shadow-2xl z-50 p-4 animate-fadeIn space-y-3 floating-window">
              <div className="flex justify-between items-center pb-2" style={{borderBottom:'1px solid rgba(255,255,255,0.10)'}}>
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[#E86326] text-lg">dns</span>
                  <h4 className="font-headline font-bold text-xs text-white">
                    9 Microservice Fleet Status (:8000–:8008)
                  </h4>
                </div>
                <button
                  onClick={() => setIsHealthModalOpen(false)}
                  className="text-white/40 hover:text-white text-xs transition-colors"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-1.5 font-mono text-[11px] max-h-64 overflow-y-auto">
                {microservices.map((ms) => (
                  <div key={ms.port} className="flex items-center justify-between p-2.5 glass-card rounded-xl">
                    <div>
                      <p className="font-bold text-white text-[11px]">{ms.name}</p>
                      <p className="text-[10px] text-white/40 mt-0.5">Port: :{ms.port}</p>
                    </div>
                    <div className="text-right">
                      <span className="px-1.5 py-0.5 text-[9px] font-bold rounded-lg" style={{background:'rgba(232,99,38,0.20)', color:'#E86326', border:'1px solid rgba(232,99,38,0.40)'}}>
                        {ms.status}
                      </span>
                      <p className="text-[9px] text-white/30 mt-0.5">{ms.latency}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Quick Action Button */}
        <div className="relative">
          <button
            onClick={() => setIsQuickMenuOpen(!isQuickMenuOpen)}
            className="flex items-center gap-1.5 px-3.5 py-1.5 btn-primary rounded-xl text-xs font-bold shadow-lg transition-all active:scale-95"
          >
            <span className="material-symbols-outlined text-sm">play_arrow</span>
            <span>Actions</span>
            <span className="material-symbols-outlined text-sm">arrow_drop_down</span>
          </button>

          {isQuickMenuOpen && (
            <div className="absolute right-0 mt-2 w-56 glass-panel text-white rounded-2xl shadow-2xl z-50 py-2 animate-fadeIn floating-window" style={{borderRadius:'16px'}}>
              <div className="px-3 py-1.5 text-[10px] font-mono text-white/40 uppercase tracking-wider font-semibold">
                Quick Pipeline Triggers
              </div>
              <div style={{borderTop:'1px solid rgba(255,255,255,0.08)'}}>
              <button
                onClick={() => {
                  setIsQuickMenuOpen(false);
                  onRunQuickTask('Execute DAG Recipe Pipeline');
                }}
                className="w-full text-left px-3 py-2 text-xs text-white/80 hover:text-white hover:bg-white/[0.07] flex items-center gap-2 font-medium transition-colors"
              >
                <span className="material-symbols-outlined text-sm text-[#E86326]">account_tree</span>
                <span>Run Recipe Orchestrator</span>
              </button>
              <button
                onClick={() => {
                  setIsQuickMenuOpen(false);
                  onRunQuickTask('Sync Cluster Quotas & Spend');
                }}
                className="w-full text-left px-3 py-2 text-xs text-white/80 hover:text-white hover:bg-white/[0.07] flex items-center gap-2 font-medium transition-colors"
              >
                <span className="material-symbols-outlined text-sm text-[#E86326]">sync</span>
                <span>Sync Cluster Telemetry</span>
              </button>
              <button
                onClick={() => {
                  setIsQuickMenuOpen(false);
                  onRunQuickTask('Run Model Validation Gateway');
                }}
                className="w-full text-left px-3 py-2 text-xs text-white/80 hover:text-white hover:bg-white/[0.07] flex items-center gap-2 font-medium transition-colors"
              >
                <span className="material-symbols-outlined text-sm text-[#E86326]">verified</span>
                <span>Run Validation Gateways</span>
              </button>
              </div>
            </div>
          )}
        </div>

        {/* Theme Toggle */}
        <div className="flex items-center gap-1.5">
          <span className="material-symbols-outlined" style={{color: isDark ? 'rgba(255,255,255,0.50)' : '#FCD34D', fontSize:'17px'}}>
            {isDark ? 'dark_mode' : 'light_mode'}
          </span>
          <button
            className={`theme-toggle ${isDark ? 'dark' : 'light'}`}
            onClick={toggleTheme}
            title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            aria-label="Toggle dark/light mode"
          >
            <div className="theme-toggle-track" />
            <div className="theme-toggle-thumb">
              {isDark ? '🌙' : '☀️'}
            </div>
          </button>
        </div>

        {/* Jane AI Assistant Trigger */}
        <button
          onClick={onOpenChatBot}
          className="hidden sm:flex items-center gap-1.5 px-3.5 py-1.5 bg-[#E86326] hover:bg-[#D5521B] text-white font-bold text-xs rounded-full shadow-sm transition-all active:scale-95"
          title="Talk to Jane (AI Assistant & Copilot)"
        >
          <span className="material-symbols-outlined text-sm font-bold" style={{ fontVariationSettings: "'FILL' 1" }}>
            smart_toy
          </span>
          <span>Talk to Jane</span>
        </button>

        {/* Notification Bell */}
        <button
          onClick={onToggleNotifications}
          className="relative p-2 rounded-full transition-all hover:bg-white/10"
          style={{color:'rgba(255,255,255,0.65)'}}
          title="Notifications"
        >
          <span className="material-symbols-outlined text-xl">notifications</span>
          {unreadCount > 0 && (
            <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-[#E86326] rounded-full ring-2 ring-[#2B0063] animate-ping"></span>
          )}
        </button>
      </div>
    </header>
  );
};
