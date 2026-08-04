import React from 'react';
import { SidebarTab } from './Sidebar';
import {
  Sparkles,
  FileUp,
  BarChart2,
  Brush,
  BadgeCheck,
  FlaskConical,
  Network,
  ClipboardCheck,
  Rocket,
  TrendingUp,
  Cpu,
  Layers,
  Zap,
  Activity,
  CheckCircle2
} from 'lucide-react';

interface SecondaryViewsProps {
  activeTab: SidebarTab;
  darkMode: boolean;
  onReturnToChat: () => void;
}

export const SecondaryViews: React.FC<SecondaryViewsProps> = ({ activeTab, darkMode, onReturnToChat }) => {
  const containerStyle = `pl-16 sm:pl-20 py-8 px-6 max-w-5xl mx-auto min-h-[calc(100vh-7rem)] flex flex-col justify-center animate-in fade-in duration-300 ${
    darkMode ? 'text-slate-100' : 'text-slate-800'
  }`;

  const cardStyle = `rounded-3xl p-6 sm:p-8 border shadow-xl transition-colors ${
    darkMode ? 'bg-slate-900/90 border-slate-800' : 'bg-white border-slate-200'
  }`;

  if (activeTab === 'sparkles') {
    return (
      <div className={containerStyle}>
        <div className={cardStyle}>
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 rounded-2xl bg-gradient-to-tr from-purple-600 to-indigo-500 text-white shadow-md">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold font-sans">AI Compiler Intelligence</h2>
              <p className="text-xs font-mono text-slate-500 dark:text-slate-400">Automated DAG Topology & Recipe Compiler Engine</p>
            </div>
          </div>
          <div className="space-y-4 font-mono text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
            <div className="p-4 rounded-2xl bg-slate-100 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
              <div className="font-bold text-purple-600 dark:text-purple-400 mb-1">Compiler Status: Ready</div>
              <p>Analyzing telemetry structure. Ready to bind DAG graph nodes to live industrial sensor feeds.</p>
            </div>
            <button
              onClick={onReturnToChat}
              className="bg-purple-600 hover:bg-purple-700 text-white font-medium text-xs px-5 py-2.5 rounded-xl transition-all cursor-pointer shadow-md"
            >
              Open AI Connexx Chat Assistant →
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (activeTab === 'upload') {
    return (
      <div className={containerStyle}>
        <div className={cardStyle}>
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 rounded-2xl bg-blue-500/10 text-blue-600 dark:text-blue-400">
              <FileUp className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold font-sans">Dataset Topology Upload</h2>
              <p className="text-xs font-mono text-slate-500 dark:text-slate-400">Import operational telemetry CSV, JSON, or parquet datasets</p>
            </div>
          </div>
          <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-3xl p-10 text-center hover:border-blue-500 transition-colors cursor-pointer bg-slate-50/50 dark:bg-slate-800/30">
            <FileUp className="w-10 h-10 text-slate-400 mx-auto mb-3" />
            <p className="font-mono text-xs font-bold text-slate-700 dark:text-slate-200 mb-1">
              Drag & Drop operational dataset or click to browse
            </p>
            <p className="font-mono text-[11px] text-slate-400">Supported: .csv, .parquet, .json, .hdf5 (Max 500MB)</p>
          </div>
        </div>
      </div>
    );
  }

  if (activeTab === 'analytics') {
    return (
      <div className={containerStyle}>
        <div className={cardStyle}>
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
              <BarChart2 className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold font-sans">Operational Analytics & Metrics</h2>
              <p className="text-xs font-mono text-slate-500 dark:text-slate-400">Real-time equipment throughput, latency, and health telemetry</p>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono text-xs">
            <div className="p-4 rounded-2xl bg-slate-100 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
              <span className="text-slate-400 text-[10px] block mb-1">COMPILER THROUGHPUT</span>
              <span className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">99.8%</span>
              <span className="text-[10px] text-slate-500 block mt-1">+1.4% vs last week</span>
            </div>
            <div className="p-4 rounded-2xl bg-slate-100 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
              <span className="text-slate-400 text-[10px] block mb-1">DAG MATCH LATENCY</span>
              <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">1.2 ms</span>
              <span className="text-[10px] text-slate-500 block mt-1">Ultra-low latency</span>
            </div>
            <div className="p-4 rounded-2xl bg-slate-100 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
              <span className="text-slate-400 text-[10px] block mb-1">EQUIPMENT HEALTH</span>
              <span className="text-2xl font-bold text-purple-600 dark:text-purple-400">98.4 / 100</span>
              <span className="text-[10px] text-slate-500 block mt-1">Zero critical anomalies</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (activeTab === 'topology') {
    return (
      <div className={containerStyle}>
        <div className={cardStyle}>
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 rounded-2xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400">
              <Network className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold font-sans">Network & Topology Visualizer</h2>
              <p className="text-xs font-mono text-slate-500 dark:text-slate-400">Active DAG execution graph & sensor routing nodes</p>
            </div>
          </div>
          <div className="p-6 rounded-2xl bg-slate-950 text-emerald-400 font-mono text-xs border border-slate-800 space-y-2">
            <div>[NODE-1: Sensor Ingestion] ─── (0.4ms) ───► [NODE-2: DAG Schema Match]</div>
            <div>                                                 │</div>
            <div>                                           (1.1ms latency)</div>
            <div>                                                 ▼</div>
            <div>[NODE-4: Edge Inference]  ◄─── (0.8ms) ─── [NODE-3: Training Recipe Compiler]</div>
            <div className="pt-2 text-slate-500 text-[10px]">Topology topology_id: #DAG-9041-A • Status: 9 Services Synchronized</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={containerStyle}>
      <div className={cardStyle}>
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-2xl bg-blue-500/10 text-blue-600 dark:text-blue-400">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold font-sans capitalize">{activeTab} Operational View</h2>
            <p className="text-xs font-mono text-slate-500 dark:text-slate-400">Integrated module of AI-Connexx Suite</p>
          </div>
        </div>
        <p className="font-mono text-xs text-slate-600 dark:text-slate-300 mb-6">
          This module is synced live with the 9 online microservices. Return to the main assistant to send commands or compile recipes.
        </p>
        <button
          onClick={onReturnToChat}
          className="bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs px-5 py-2.5 rounded-xl transition-all cursor-pointer shadow-md"
        >
          ← Return to AI Connexx Chat Assistant
        </button>
      </div>
    </div>
  );
};
