import React from 'react';
import {
  Sparkles,
  MessageSquare,
  FileUp,
  BarChart2,
  Brush,
  BadgeCheck,
  FlaskConical,
  Network,
  ClipboardCheck,
  Rocket,
  TrendingUp,
  Share2
} from 'lucide-react';

export type SidebarTab =
  | 'chat'
  | 'sparkles'
  | 'upload'
  | 'analytics'
  | 'cleaner'
  | 'verification'
  | 'lab'
  | 'topology'
  | 'checklist'
  | 'deploy'
  | 'trends'
  | 'nodes';

interface SidebarProps {
  activeTab: SidebarTab;
  setActiveTab: (tab: SidebarTab) => void;
  darkMode: boolean;
  onOpenServicesModal: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  darkMode,
  onOpenServicesModal,
}) => {
  const navItems = [
    {
      id: 'sparkles' as SidebarTab,
      label: 'AI Compiler Intelligence',
      icon: Sparkles,
      special: 'sparkles',
    },
    {
      id: 'chat' as SidebarTab,
      label: 'AI Connexx Chat Assistant',
      icon: MessageSquare,
      selectedBg: 'bg-[#990022] text-white shadow-md shadow-red-900/20',
    },
    {
      id: 'upload' as SidebarTab,
      label: 'Dataset Topology Upload',
      icon: FileUp,
    },
    {
      id: 'analytics' as SidebarTab,
      label: 'Operational Analytics & Metrics',
      icon: BarChart2,
    },
    {
      id: 'cleaner' as SidebarTab,
      label: 'Data Sanitization & Cleaning',
      icon: Brush,
    },
    {
      id: 'verification' as SidebarTab,
      label: 'Schema & DAG Verification',
      icon: BadgeCheck,
    },
    {
      id: 'lab' as SidebarTab,
      label: 'Recipe Training Experiments',
      icon: FlaskConical,
    },
    {
      id: 'topology' as SidebarTab,
      label: 'Network & Topology Visualizer',
      icon: Network,
    },
    {
      id: 'checklist' as SidebarTab,
      label: 'Maintenance Audit Checklist',
      icon: ClipboardCheck,
    },
    {
      id: 'deploy' as SidebarTab,
      label: 'Deployment & Edge Execution',
      icon: Rocket,
    },
    {
      id: 'trends' as SidebarTab,
      label: 'Predictive Health Trends',
      icon: TrendingUp,
    },
  ];

  return (
    <aside className="fixed left-3 top-16 bottom-12 z-30 flex flex-col items-center justify-between pointer-events-auto">
      {/* Dock Container */}
      <div
        className={`w-13 py-3 px-1.5 rounded-2xl flex flex-col items-center gap-2.5 shadow-xl transition-colors border select-none ${
          darkMode
            ? 'bg-slate-900/90 border-slate-800 text-slate-300 shadow-black/40'
            : 'bg-white/95 border-slate-200/90 text-slate-600 shadow-slate-200/80 backdrop-blur-md'
        }`}
      >
        {/* Top items */}
        <div className="flex flex-col items-center gap-2 w-full">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;

            if (item.special === 'sparkles') {
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className="group relative p-2.5 rounded-xl bg-gradient-to-tr from-purple-600 to-indigo-500 text-white shadow-md hover:scale-105 active:scale-95 transition-all cursor-pointer"
                  title={item.label}
                >
                  <Icon className="w-4 h-4" />
                  {/* Tooltip */}
                  <div className="absolute left-14 top-1/2 -translate-y-1/2 bg-slate-900 text-white text-xs font-mono px-2.5 py-1 rounded-md shadow-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50">
                    {item.label}
                  </div>
                </button>
              );
            }

            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`group relative p-2.5 rounded-xl transition-all cursor-pointer ${
                  isActive
                    ? item.selectedBg ||
                      (darkMode ? 'bg-slate-800 text-white' : 'bg-slate-900 text-white')
                    : darkMode
                    ? 'hover:bg-slate-800/60 text-slate-400 hover:text-slate-100'
                    : 'hover:bg-slate-100 text-slate-500 hover:text-slate-800'
                }`}
                title={item.label}
              >
                <Icon className="w-4 h-4" />
                {/* Tooltip */}
                <div className="absolute left-14 top-1/2 -translate-y-1/2 bg-slate-900 text-white text-xs font-mono px-2.5 py-1 rounded-md shadow-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50">
                  {item.label}
                </div>
              </button>
            );
          })}
        </div>

        {/* Bottom Nodes Pill Button with Notification Badge 9 */}
        <div className="pt-1 w-full flex justify-center border-t border-slate-200/50 dark:border-slate-800">
          <button
            onClick={onOpenServicesModal}
            className="group relative p-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white shadow-md active:scale-95 transition-all cursor-pointer flex items-center justify-center"
            title="View 9 Active Topology Nodes"
          >
            <Share2 className="w-4 h-4" />
            <span className="absolute -top-1.5 -right-1.5 bg-blue-900 text-white text-[9px] font-mono font-bold w-4 h-4 rounded-full flex items-center justify-center ring-2 ring-white dark:ring-slate-900">
              9
            </span>
            <div className="absolute left-14 top-1/2 -translate-y-1/2 bg-slate-900 text-white text-xs font-mono px-2.5 py-1 rounded-md shadow-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50">
              9 Active Nodes & Microservices
            </div>
          </button>
        </div>
      </div>
    </aside>
  );
};
