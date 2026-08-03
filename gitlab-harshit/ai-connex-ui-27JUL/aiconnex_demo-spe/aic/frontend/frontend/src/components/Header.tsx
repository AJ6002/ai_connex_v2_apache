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
    { name: 'Node 5: Feature Eng', port: 8004, status: 'Online', latency: '18ms' },
    { name: 'Node 6: Zero-Leakage Split', port: 8005, status: 'Online', latency: '11ms' },
    { name: 'Node 7: HPO Trainer', port: 8006, status: 'Online', latency: '22ms' },
    { name: 'Node 8: Model Evaluator', port: 8007, status: 'Online', latency: '15ms' },
    { name: 'Node 9: Deploy & Monitor', port: 8008, status: 'Online', latency: '10ms' },
  ];

  const getViewTitle = () => {
    switch (currentView) {
      case 'compiler':
        return 'Relational Compiler Suite';
      case 'dag_inspector':
        return '1,993 Master DAGs Catalog';
      case 'workflow':
        return '9-Node MLOps Cascade Studio';
      case 'pipeline_studio':
        return 'Serving & Data Drift Monitor';
      case 'administration':
        return 'System Configurations';
      case 'quotas':
        return 'Quotas & Compute Usage';
      case 'developer_studio':
        return 'Developer Studio & Stdout Stream';
      case 'settings':
        return 'Platform Settings';
      case 'support':
        return 'Documentation & Support';
      default:
        return 'AI-Connexx Suite';
    }
  };

  return (
    <header className={`fixed top-0 left-0 right-0 w-full h-16 backdrop-blur-2xl text-white z-40 flex justify-between items-center pr-6 transition-all duration-300 ${
      sidebarStyle === 'slim' ? 'pl-24' : 'pl-6'
    }`}
      style={{
        /* Always dark blue — unaffected by light/dark theme */
        background: 'linear-gradient(135deg, #0B1F4A 0%, #0D2566 60%, #0A1B40 100%)',
        borderBottom: '1px solid rgba(255,255,255,0.10)',
        boxShadow: '0 4px 24px rgba(6,9,20,0.40), inset 0 -1px 0 rgba(255,255,255,0.06)',
      }}
    >
      {/* Left Title & Brand Logo */}
      <div className="flex items-center gap-4">
        <TasLogo className="h-8" showSubtitle={false} />

        <div className="h-5 w-px" style={{background:'rgba(255,255,255,0.15)'}}></div>

        <h1 className="font-headline text-base font-bold text-white tracking-tight whitespace-nowrap">
          {getViewTitle()}
        </h1>
      </div>

      {/* Right Controls & Status */}
      <div className="flex items-center gap-3">

        {/* 9-Microservice Health Heartbeat Status Badge */}
        <div className="relative">
          <button
            onClick={() => setIsHealthModalOpen(!isHealthModalOpen)}
            className="flex items-center gap-2 px-3 py-1 rounded-full transition-all text-xs font-mono font-bold backdrop-blur-md"
            style={{background:'rgba(34,197,94,0.12)', border:'1px solid rgba(34,197,94,0.28)', color:'#4ade80'}}
            title="Click to view 9 Microservices Status"
          >
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="hidden xl:inline">9 Services Online</span>
            <span className="xl:hidden">9/9</span>
          </button>

          {/* Microservices Health Popover */}
          {isHealthModalOpen && (
            <div className="absolute right-0 mt-2 w-80 glass-panel rounded-2xl shadow-2xl z-50 p-4 animate-fadeIn space-y-3">
              <div className="flex justify-between items-center pb-2" style={{borderBottom:'1px solid rgba(255,255,255,0.10)'}}>
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[#4ade80] text-lg">dns</span>
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
                      <span className="px-1.5 py-0.5 text-[9px] font-bold rounded-lg" style={{background:'rgba(34,197,94,0.15)', color:'#4ade80', border:'1px solid rgba(34,197,94,0.25)'}}>
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
            <div className="absolute right-0 mt-2 w-56 glass-panel text-white rounded-2xl shadow-2xl z-50 py-2 animate-fadeIn" style={{borderRadius:'16px'}}>
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
                <span className="material-symbols-outlined text-sm" style={{color:'#E8405A'}}>account_tree</span>
                <span>Run Recipe Orchestrator</span>
              </button>
              <button
                onClick={() => {
                  setIsQuickMenuOpen(false);
                  onRunQuickTask('Sync Cluster Quotas & Spend');
                }}
                className="w-full text-left px-3 py-2 text-xs text-white/80 hover:text-white hover:bg-white/[0.07] flex items-center gap-2 font-medium transition-colors"
              >
                <span className="material-symbols-outlined text-sm" style={{color:'#E8405A'}}>sync</span>
                <span>Sync Cluster Telemetry</span>
              </button>
              <button
                onClick={() => {
                  setIsQuickMenuOpen(false);
                  onRunQuickTask('Run Model Validation Gateway');
                }}
                className="w-full text-left px-3 py-2 text-xs text-white/80 hover:text-white hover:bg-white/[0.07] flex items-center gap-2 font-medium transition-colors"
              >
                <span className="material-symbols-outlined text-sm" style={{color:'#E8405A'}}>verified</span>
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

        {/* Notification Bell */}
        <button
          onClick={onToggleNotifications}
          className="relative p-2 rounded-full transition-all hover:bg-white/10"
          style={{color:'rgba(255,255,255,0.65)'}}
          title="Notifications"
        >
          <span className="material-symbols-outlined text-xl">notifications</span>
          {unreadCount > 0 && (
            <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-[#C8102E] rounded-full ring-2 ring-[#0B1F4A] animate-ping"></span>
          )}
        </button>
      </div>
    </header>
  );
};
