import React from 'react';
import { X, Bell, CheckCircle2, AlertTriangle, Cpu, Zap, Activity } from 'lucide-react';

interface NotificationsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  darkMode: boolean;
}

export const NotificationsDrawer: React.FC<NotificationsDrawerProps> = ({ isOpen, onClose, darkMode }) => {
  if (!isOpen) return null;

  const notifications = [
    {
      id: 1,
      title: 'DAG Topology Compiled',
      desc: 'Compiler automatically matched schema #812-B for sensor node cluster A-4.',
      time: '2 mins ago',
      type: 'success',
      icon: CheckCircle2,
    },
    {
      id: 2,
      title: 'Training Recipe Updated',
      desc: 'Recipe #44 compiled with 99.4% prediction accuracy on equipment dataset.',
      time: '14 mins ago',
      type: 'info',
      icon: Zap,
    },
    {
      id: 3,
      title: 'Telemetry Telemetry Stream Synchronized',
      desc: 'Edge node latency steady at 0.8ms across all 9 online services.',
      time: '45 mins ago',
      type: 'info',
      icon: Activity,
    },
    {
      id: 4,
      title: 'Vibration Anomaly Resolved',
      desc: 'Predictive maintenance goal updated for Turbine B-2.',
      time: '1 hour ago',
      type: 'warning',
      icon: AlertTriangle,
    },
  ];

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-80 sm:w-96 p-4 shadow-2xl animate-in slide-in-from-right duration-300">
      <div
        className={`h-full w-full rounded-3xl p-5 border flex flex-col justify-between transition-colors ${
          darkMode ? 'bg-slate-900 border-slate-800 text-white shadow-black/80' : 'bg-white border-slate-200 text-slate-800 shadow-xl'
        }`}
      >
        <div>
          {/* Header */}
          <div className="flex items-center justify-between pb-3 mb-4 border-b dark:border-slate-800">
            <div className="flex items-center gap-2">
              <Bell className="w-4 h-4 text-blue-500" />
              <h3 className="font-bold text-sm">System Logs & Alerts</h3>
            </div>
            <button
              onClick={onClose}
              className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* List */}
          <div className="space-y-3 max-h-[75vh] overflow-y-auto pr-1 custom-scrollbar">
            {notifications.map((n) => {
              const Icon = n.icon;
              return (
                <div
                  key={n.id}
                  className={`p-3 rounded-2xl border text-xs font-mono transition-colors ${
                    darkMode ? 'bg-slate-800/60 border-slate-700/80' : 'bg-slate-50 border-slate-200/80'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold flex items-center gap-1.5 text-blue-600 dark:text-blue-400">
                      <Icon className="w-3.5 h-3.5" /> {n.title}
                    </span>
                    <span className="text-[10px] text-slate-400">{n.time}</span>
                  </div>
                  <p className="text-slate-500 dark:text-slate-400 leading-relaxed">{n.desc}</p>
                </div>
              );
            })}
          </div>
        </div>

        <div className="pt-3 border-t dark:border-slate-800 text-center">
          <button
            onClick={onClose}
            className="text-xs font-mono text-blue-600 dark:text-blue-400 hover:underline cursor-pointer"
          >
            Clear All Notifications
          </button>
        </div>
      </div>
    </div>
  );
};
