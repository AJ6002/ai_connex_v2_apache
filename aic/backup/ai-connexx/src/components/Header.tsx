import React, { useState } from 'react';
import { ViewMode, SystemNotification } from '../types';
import { TasLogo } from './TasLogo';

interface HeaderProps {
  currentView: ViewMode;
  notifications: SystemNotification[];
  onToggleNotifications: () => void;
  onRunQuickTask: (taskTitle: string) => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  selectedWorkspace?: string;
  onSelectWorkspace?: (ws: string) => void;
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
}) => {
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
    <header className="fixed top-0 left-0 right-0 w-full h-16 bg-slate-900/80 backdrop-blur-2xl text-white border-b border-white/10 shadow-2xl z-40 flex justify-between items-center px-6">
      {/* Left Title & Brand Logo */}
      <div className="flex items-center gap-4">
        <TasLogo className="h-8" showSubtitle={false} />

        <div className="h-5 w-px bg-white/20 hidden sm:block"></div>

        <h1 className="font-headline text-base font-bold text-white tracking-tight whitespace-nowrap">
          {getViewTitle()}
        </h1>

        <div className="h-5 w-px bg-white/20 hidden sm:block"></div>

        {/* Workspace Selector */}
        <div className="hidden lg:flex items-center gap-2">
          <span className="text-[10px] font-mono text-slate-400 uppercase font-bold">Workspace:</span>
          <select
            value={selectedWorkspace}
            onChange={(e) => onSelectWorkspace && onSelectWorkspace(e.target.value)}
            className="bg-slate-950/60 border border-white/20 rounded-xl px-2.5 py-1 text-xs font-mono text-white font-bold outline-none focus:ring-2 focus:ring-tas-red"
          >
            <option value="/cmapss" className="bg-slate-900 text-white">/cmapss (Turbofan)</option>
            <option value="/scada_telemetry" className="bg-slate-900 text-white">/scada_telemetry (Wind)</option>
            <option value="/igbt_aging" className="bg-slate-900 text-white">/igbt_aging (Semiconductor)</option>
          </select>
        </div>

        {/* Global Search Bar */}
        <div className="relative w-48 md:w-64">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm">
            search
          </span>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search DAGs, features, models..."
            className="w-full bg-slate-950/50 border border-white/15 rounded-xl pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-tas-red focus:border-tas-red transition-all font-sans"
          />
        </div>
      </div>

      {/* Right Controls & Status */}
      <div className="flex items-center gap-3">
        {/* Active Run Tracker Pill */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1 bg-slate-950/80 border border-white/10 text-white rounded-full font-mono text-xs shadow-inner">
          <span className="w-2 h-2 rounded-full bg-tas-red animate-pulse"></span>
          <span className="text-[10px] text-slate-400 uppercase font-bold">Active Run:</span>
          <span className="font-bold text-tas-red">run_5cffcec1</span>
        </div>

        {/* 9-Microservice Health Heartbeat Status Badge */}
        <div className="relative">
          <button
            onClick={() => setIsHealthModalOpen(!isHealthModalOpen)}
            className="flex items-center gap-2 px-3 py-1 bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-300 border border-emerald-500/30 rounded-full transition-all text-xs font-mono font-bold backdrop-blur-md"
            title="Click to view 9 Microservices Status"
          >
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="hidden xl:inline">9 Services Online</span>
            <span className="xl:hidden">9/9</span>
          </button>

          {/* Microservices Health Popover */}
          {isHealthModalOpen && (
            <div className="absolute right-0 mt-2 w-80 bg-slate-900/90 border border-white/20 rounded-2xl shadow-2xl backdrop-blur-2xl z-50 p-4 animate-fadeIn space-y-3">
              <div className="flex justify-between items-center pb-2 border-b border-white/10">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-emerald-400 text-lg">dns</span>
                  <h4 className="font-headline font-bold text-xs text-white">
                    9 Microservice Fleet Status (:8000–:8008)
                  </h4>
                </div>
                <button
                  onClick={() => setIsHealthModalOpen(false)}
                  className="text-slate-400 hover:text-white text-xs"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-1.5 font-mono text-[11px] max-h-64 overflow-y-auto">
                {microservices.map((ms) => (
                  <div key={ms.port} className="flex items-center justify-between p-2 bg-slate-950/60 rounded-xl border border-white/10">
                    <div>
                      <p className="font-bold text-white">{ms.name}</p>
                      <p className="text-[10px] text-slate-400">Port: :{ms.port}</p>
                    </div>
                    <div className="text-right">
                      <span className="px-1.5 py-0.5 bg-emerald-500/20 text-emerald-300 text-[9px] font-bold rounded">
                        {ms.status}
                      </span>
                      <p className="text-[9px] text-slate-400">{ms.latency}</p>
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
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-gradient-to-r from-tas-red to-tas-red-hover hover:scale-105 text-white rounded-xl text-xs font-bold shadow-lg transition-all active:scale-95"
          >
            <span className="material-symbols-outlined text-sm">play_arrow</span>
            <span>Actions</span>
            <span className="material-symbols-outlined text-sm">arrow_drop_down</span>
          </button>

          {isQuickMenuOpen && (
            <div className="absolute right-0 mt-2 w-56 bg-slate-900/90 text-white border border-white/20 rounded-2xl shadow-2xl backdrop-blur-2xl z-50 py-2 divide-y divide-white/10">
              <div className="px-3 py-1.5 text-[10px] font-mono text-slate-400 uppercase tracking-wider font-semibold">
                Quick Pipeline Triggers
              </div>
              <button
                onClick={() => {
                  setIsQuickMenuOpen(false);
                  onRunQuickTask('Execute DAG Recipe Pipeline');
                }}
                className="w-full text-left px-3 py-2 text-xs text-slate-200 hover:bg-white/10 flex items-center gap-2 font-medium"
              >
                <span className="material-symbols-outlined text-sm text-tas-red">account_tree</span>
                <span>Run Recipe Orchestrator</span>
              </button>
              <button
                onClick={() => {
                  setIsQuickMenuOpen(false);
                  onRunQuickTask('Sync Cluster Quotas & Spend');
                }}
                className="w-full text-left px-3 py-2 text-xs text-slate-200 hover:bg-white/10 flex items-center gap-2 font-medium"
              >
                <span className="material-symbols-outlined text-sm text-tas-red">sync</span>
                <span>Sync Cluster Telemetry</span>
              </button>
              <button
                onClick={() => {
                  setIsQuickMenuOpen(false);
                  onRunQuickTask('Run Model Validation Gateway');
                }}
                className="w-full text-left px-3 py-2 text-xs text-slate-200 hover:bg-white/10 flex items-center gap-2 font-medium"
              >
                <span className="material-symbols-outlined text-sm text-tas-red">verified</span>
                <span>Run Validation Gateways</span>
              </button>
            </div>
          )}
        </div>

        {/* Notification Bell */}
        <button
          onClick={onToggleNotifications}
          className="relative p-2 text-slate-300 hover:text-white hover:bg-white/10 rounded-full transition-all"
          title="Notifications"
        >
          <span className="material-symbols-outlined text-xl">notifications</span>
          {unreadCount > 0 && (
            <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-tas-red rounded-full ring-2 ring-slate-900 animate-ping"></span>
          )}
        </button>
      </div>
    </header>
  );
};
