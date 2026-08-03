import React, { useState } from 'react';
import { TASLogo } from './TASLogo';
import { Play, ChevronDown, Sun, Moon, Bell, CheckCircle2, Zap, Cpu, RefreshCw, Activity, Layers, Terminal } from 'lucide-react';

interface NavbarProps {
  darkMode: boolean;
  setDarkMode: (val: boolean) => void;
  onOpenServicesModal: () => void;
  onActionSelect: (actionName: string) => void;
  onToggleNotifications: () => void;
  unreadNotifications: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  darkMode,
  setDarkMode,
  onOpenServicesModal,
  onActionSelect,
  onToggleNotifications,
  unreadNotifications
}) => {
  const [actionsOpen, setActionsOpen] = useState(false);

  const actionItems = [
    { id: 'compile', label: 'Compile Training Recipes', icon: Zap, desc: 'Generate optimized model recipes for datasets' },
    { id: 'dag', label: 'Match DAG Schemas', icon: Layers, desc: 'Align pipeline nodes to operational topology' },
    { id: 'topology', label: 'Assign Data Topology', icon: Cpu, desc: 'Map sensor telemetry streaming routes' },
    { id: 'diagnostics', label: 'Run System Diagnostics', icon: Activity, desc: 'Execute full telemetry health inspection' },
    { id: 'clear', label: 'Clear Compiler Cache', icon: RefreshCw, desc: 'Reset intermediate state and compilation logs' },
  ];

  return (
    <header className="h-14 bg-[#0A193D] border-b border-slate-800 text-white px-4 flex items-center justify-between sticky top-0 z-40 select-none shadow-md">
      {/* Left Brand Area */}
      <div className="flex items-center gap-3">
        <TASLogo size="sm" />
        <span className="font-bold text-sm tracking-wide text-white font-sans flex items-center gap-2">
          AI-Connexx Suite
        </span>
      </div>

      {/* Right Controls Area */}
      <div className="flex items-center gap-3 sm:gap-4">
        {/* 9 Services Online Pill Badge */}
        <button
          onClick={onOpenServicesModal}
          className="bg-slate-900/80 hover:bg-slate-800 text-emerald-400 border border-slate-700/80 rounded-full px-3 py-1 text-xs font-mono flex items-center gap-2 cursor-pointer transition-all shadow-sm hover:border-emerald-500/50"
          title="Click to view all 9 running microservices"
        >
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>9 Services Online</span>
        </button>

        {/* Red Actions Button Dropdown */}
        <div className="relative">
          <button
            onClick={() => setActionsOpen(!actionsOpen)}
            className="bg-[#DC2626] hover:bg-[#B91C1C] text-white text-xs font-semibold px-3.5 py-1.5 rounded-md flex items-center gap-1.5 transition-all shadow-md active:scale-95 cursor-pointer"
          >
            <Play className="w-3 h-3 fill-current" />
            <span>Actions</span>
            <ChevronDown className={`w-3 h-3 transition-transform duration-200 ${actionsOpen ? 'rotate-180' : ''}`} />
          </button>

          {actionsOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setActionsOpen(false)} />
              <div className="absolute right-0 mt-2 w-64 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl z-20 py-1 overflow-hidden animate-in fade-in slide-in-from-top-2">
                <div className="px-3 py-2 border-b border-slate-800 text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                  Suite Actions & Tools
                </div>
                {actionItems.map((item) => {
                  const Icon = item.icon;
                  return (
                    <button
                      key={item.id}
                      onClick={() => {
                        onActionSelect(item.label);
                        setActionsOpen(false);
                      }}
                      className="w-full text-left px-3.5 py-2.5 hover:bg-slate-800 flex items-start gap-2.5 transition-colors group cursor-pointer"
                    >
                      <Icon className="w-4 h-4 text-slate-400 group-hover:text-red-400 shrink-0 mt-0.5" />
                      <div>
                        <div className="text-xs font-medium text-slate-200 group-hover:text-white">
                          {item.label}
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono">
                          {item.desc}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </>
          )}
        </div>

        {/* Theme Toggle (Sun/Moon switch capsule) */}
        <div className="bg-slate-900 border border-slate-700 rounded-full p-0.5 flex items-center relative gap-1">
          <button
            onClick={() => setDarkMode(false)}
            className={`p-1 rounded-full transition-all cursor-pointer ${
              !darkMode ? 'bg-amber-500 text-slate-950 shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
            title="Light Mode"
          >
            <Sun className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setDarkMode(true)}
            className={`p-1 rounded-full transition-all cursor-pointer ${
              darkMode ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
            title="Dark Mode"
          >
            <Moon className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Notification Bell */}
        <button
          onClick={onToggleNotifications}
          className="relative p-1.5 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
          title="Notifications"
        >
          <Bell className="w-4 h-4" />
          {unreadNotifications > 0 && (
            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full ring-2 ring-[#0A193D]" />
          )}
        </button>
      </div>
    </header>
  );
};
