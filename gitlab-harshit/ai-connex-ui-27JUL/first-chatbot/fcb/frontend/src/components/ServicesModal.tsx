import React from 'react';
import { X, CheckCircle2, Activity, Cpu, Network, Zap, ShieldCheck, Database, Server, Radio } from 'lucide-react';

interface ServicesModalProps {
  isOpen: boolean;
  onClose: () => void;
  darkMode: boolean;
}

export const ServicesModal: React.FC<ServicesModalProps> = ({ isOpen, onClose, darkMode }) => {
  if (!isOpen) return null;

  const microservices = [
    { name: 'DAG Topology Compiler', status: 'Optimal', latency: '1.2ms', icon: Cpu, desc: 'Assigns data topologies to DAG pipeline execution graph' },
    { name: 'Sensor Ingestion Stream', status: 'Active', latency: '0.8ms', icon: Radio, desc: 'Real-time telemetry ingestion from multi-node sensor grid' },
    { name: 'Recipe Training Engine', status: 'Online', latency: '3.4ms', icon: Zap, desc: 'Compiles hyperparameter configurations for neural models' },
    { name: 'Anomaly Classifier', status: 'Online', latency: '2.1ms', icon: Activity, desc: 'Vibration, temperature, and acoustic failure detector' },
    { name: 'Maintenance Goal Scheduler', status: 'Active', latency: '1.5ms', icon: CheckCircle2, desc: 'Aligns preventive downtime with operational targets' },
    { name: 'Neural Equipment Health', status: 'Optimal', latency: '4.0ms', icon: Network, desc: 'Calculates wear degradation scores across components' },
    { name: 'Telemetry Synchronizer', status: 'Active', latency: '0.5ms', icon: Server, desc: 'Clock-synced stream alignment across edge nodes' },
    { name: 'Feature Store Pipeline', status: 'Online', latency: '2.8ms', icon: Database, desc: 'Low-latency feature extraction for live inference' },
    { name: 'Edge Inference Node', status: 'Optimal', latency: '0.9ms', icon: ShieldCheck, desc: 'Sub-millisecond local node model execution' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div
        className={`w-full max-w-2xl rounded-3xl p-6 shadow-2xl border transition-colors relative ${
          darkMode ? 'bg-slate-900 border-slate-800 text-white' : 'bg-white border-slate-200 text-slate-800'
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b pb-4 mb-4 dark:border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse"></div>
            <div>
              <h2 className="text-lg font-bold font-sans">9 Services Online</h2>
              <p className="text-xs font-mono text-slate-400">AI-Connexx Suite Operational Infrastructure</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Services List Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-[60vh] overflow-y-auto pr-1 custom-scrollbar">
          {microservices.map((svc, idx) => {
            const Icon = svc.icon;
            return (
              <div
                key={idx}
                className={`p-3.5 rounded-2xl border flex items-start gap-3 transition-colors ${
                  darkMode ? 'bg-slate-800/60 border-slate-700/80' : 'bg-slate-50 border-slate-200/80'
                }`}
              >
                <div className="p-2 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5">
                  <Icon className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold truncate">{svc.name}</span>
                    <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                      {svc.status}
                    </span>
                  </div>
                  <p className="text-[11px] font-mono text-slate-500 dark:text-slate-400 leading-tight mb-1">
                    {svc.desc}
                  </p>
                  <span className="text-[9px] font-mono text-slate-400">Latency: {svc.latency}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="mt-5 pt-4 border-t dark:border-slate-800 flex items-center justify-between text-xs font-mono text-slate-400">
          <span>Overall Health: 100% Operational</span>
          <button
            onClick={onClose}
            className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-1.5 rounded-xl transition-all cursor-pointer"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
