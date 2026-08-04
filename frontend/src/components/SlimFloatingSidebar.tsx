import React, { useState } from 'react';
import { ViewMode } from '../types';

interface SlimFloatingSidebarProps {
  currentView: ViewMode;
  onSelectView: (view: ViewMode) => void;
}

interface NavGroup {
  category: string;
  items: {
    id: ViewMode;
    label: string;
    shortLabel: string;
    icon: string;
    badge?: string;
  }[];
}

export const SlimFloatingSidebar: React.FC<SlimFloatingSidebarProps> = ({
  currentView,
  onSelectView,
}) => {
  const [showNodesMenu, setShowNodesMenu] = useState(false);

  const mainGroups: NavGroup[] = [
    {
      category: 'Pipeline Cascade',
      items: [
        { id: 'landing', label: 'Page 1: Landing Chatbox', shortLabel: 'Prompt', icon: 'chat', badge: 'Page 1' },
        { id: 'compiler', label: 'Page 2: Upload Page', shortLabel: 'Upload', icon: 'upload_file', badge: 'Page 2' },
        { id: 'data_explorer', label: 'Page 3: Data Explorer', shortLabel: 'Explore', icon: 'bar_chart', badge: 'Page 3' },
        { id: 'node4', label: 'Page 4: Prepare Node', shortLabel: 'Prepare', icon: 'cleaning_services', badge: 'Page 4' },
        { id: 'vg1', label: 'Page 5: Validation Gate 1', shortLabel: 'VG 1', icon: 'verified', badge: 'Page 5' },
        { id: 'node5', label: 'Page 6: Feature Engineer Node', shortLabel: 'Features', icon: 'science', badge: 'Page 6' },
        { id: 'node7', label: 'Page 7: Train Node', shortLabel: 'Train', icon: 'model_training', badge: 'Page 7' },
        { id: 'vg2', label: 'Page 8: Validation Gate 2', shortLabel: 'VG 2', icon: 'fact_check', badge: 'Page 8' },
        { id: 'node9', label: 'Page 9: Deploy Node', shortLabel: 'Deploy', icon: 'rocket_launch', badge: 'Page 9' },
        { id: 'pipeline_studio', label: 'Page 10: Monitor Node', shortLabel: 'Monitor', icon: 'monitoring', badge: 'Page 10' },
      ],
    },
    {
      category: 'Administration & Master Data',
      items: [
        { id: 'administration', label: 'Administration & Envs', shortLabel: 'Admin', icon: 'admin_panel_settings' },
        { id: 'master_data', label: 'Master Data & Recipes', shortLabel: 'Master', icon: 'database', badge: 'Recipes' },
        { id: 'templates', label: 'Templates Library', shortLabel: 'Templates', icon: 'description' },
        { id: 'quotas', label: 'Quotas & GPU Spend', shortLabel: 'GPU', icon: 'payments' },
        { id: 'workspace', label: 'My Workspace', shortLabel: 'Workspace', icon: 'folder_shared' },
        { id: 'developer_studio', label: 'Developer Stdout Stream', shortLabel: 'Logs', icon: 'terminal' },
        { id: 'settings', label: 'Platform Settings', shortLabel: 'Settings', icon: 'settings' },
        { id: 'support', label: 'Support & Specs', shortLabel: 'Specs', icon: 'help_outline' },
      ],
    },
  ];

  const nodeItems = [
    { id: 'node1' as ViewMode, label: 'Node 1: Dataset Profiler', num: '1', icon: 'analytics' },
    { id: 'node2' as ViewMode, label: 'Node 2: DAG Matcher', num: '2', icon: 'route' },
    { id: 'node3' as ViewMode, label: 'Node 3: Recipe Orchestrator', num: '3', icon: 'hub' },
    { id: 'node4' as ViewMode, label: 'Node 4: Data Prepare', num: '4', icon: 'cleaning_services' },
    { id: 'node5' as ViewMode, label: 'Node 5: Feature Engineering', num: '5', icon: 'science' },
    { id: 'node6' as ViewMode, label: 'Node 6: Validation Gate 1', num: '6', icon: 'verified' },
    { id: 'node7' as ViewMode, label: 'Node 7: Train API', num: '7', icon: 'model_training' },
    { id: 'node8' as ViewMode, label: 'Node 8: Validation Gate 2', num: '8', icon: 'fact_check' },
    { id: 'node9' as ViewMode, label: 'Node 9: Deploy API', num: '9', icon: 'rocket_launch' },
  ];

  const isAnyNodeActive = currentView.startsWith('node') || currentView.startsWith('vg');

  return (
    <aside className="fixed left-3 top-20 bottom-10 z-50 animate-fadeIn max-h-[calc(100vh-7.5rem)] overflow-y-auto no-scrollbar py-2">
      {/* Floating Slim Dock */}
      <div className="glass-panel backdrop-blur-2xl shadow-2xl rounded-2xl p-2 flex flex-col items-center gap-1.5"
        style={{background:'rgba(255,255,255,0.92)', border:'1.5px solid rgba(200,16,46,0.30)', boxShadow:'0 8px 32px rgba(13,21,51,0.18), inset 0 1px 0 rgba(255,255,255,1)'}}>
        {/* Brand Emblem */}
        <div className="w-9 h-9 rounded-xl flex items-center justify-center shadow-lg group relative cursor-pointer"
          style={{background:'linear-gradient(135deg,#C8102E 0%,#1E47C8 100%)'}}>
          <span className="material-symbols-outlined text-white text-lg animate-pulse">auto_awesome</span>
          {/* Brand Tooltip */}
          <div className="absolute left-full ml-3 px-3 py-1.5 glass-panel text-white text-xs font-mono font-bold rounded-xl shadow-2xl opacity-0 group-hover:opacity-100 transition-all pointer-events-none whitespace-nowrap z-50 transform origin-left group-hover:translate-x-1 animate-fadeIn"
            style={{border:'1px solid rgba(200,16,46,0.30)'}}>
            <span className="inline-flex items-center gap-0.5">AI-<img src="/connexx-white.png" alt="Connexx" className="h-3.5 w-auto object-contain inline-block align-middle" /> Navigation</span>
          </div>
        </div>

        <div className="w-5 h-[1px] my-0.5" style={{background:'rgba(13,21,51,0.10)'}} />

        {/* Primary Navigation Icons */}
        {mainGroups[0].items.map((item) => {
          const isActive = currentView === item.id;
          return (
            <div key={item.id} className="relative group">
              <button
                onClick={() => onSelectView(item.id)}
                className={`w-9.5 h-9.5 rounded-xl flex items-center justify-center transition-all duration-300 relative ${
                  isActive
                    ? 'text-white scale-105'
                    : 'scale-105'
                }`}
                style={isActive ? {
                  background: 'linear-gradient(135deg,#C8102E 0%,#A50D25 100%)',
                  boxShadow: '0 4px 16px rgba(200,16,46,0.40)'
                } : {color:'rgba(13,21,51,0.45)'}}>
                <span className="material-symbols-outlined text-lg">{item.icon}</span>

                {/* Active Glowing Left Dot */}
                {isActive && (
                  <span className="absolute -left-1 w-1.5 h-3.5 rounded-full" style={{background:'#E8405A', boxShadow:'0 0 8px rgba(200,16,46,0.80)'}} />
                )}
              </button>

              {/* Hover Tooltip - Full Name */}
              <div className="absolute left-full ml-3 top-1/2 -translate-y-1/2 px-3 py-1.5 glass-panel text-xs font-mono font-semibold rounded-xl shadow-lg opacity-0 group-hover:opacity-100 transition-all duration-200 pointer-events-none whitespace-nowrap z-50 translate-x-1 group-hover:translate-x-2 flex items-center gap-2"
                style={{border:'1px solid rgba(13,21,51,0.10)', color:'#0D1533', background:'rgba(255,255,255,0.92)'}}>
                <span>{item.label}</span>
                {item.badge && (
                  <span className="px-1.5 py-0.5 text-[10px] rounded-md" style={{background:'rgba(200,16,46,0.18)', color:'#E8405A', border:'1px solid rgba(200,16,46,0.30)'}}>
                    {item.badge}
                  </span>
                )}
              </div>
            </div>
          );
        })}

        <div className="w-5 h-[1px] my-0.5" style={{background:'rgba(13,21,51,0.10)'}} />

        {/* 9-Node Microservices Flyout Button */}
        <div className="relative group">
          <button
            onClick={() => onSelectView('orchestrator_board')}
            onMouseEnter={() => setShowNodesMenu(true)}
            className="w-9.5 h-9.5 rounded-xl flex items-center justify-center transition-all duration-300 relative text-white scale-105 hover:scale-110 active:scale-95"
            style={{
              background: 'linear-gradient(135deg,#1E47C8 0%,#1533A0 100%)',
              boxShadow: '0 4px 16px rgba(30,71,200,0.40)'
            }}
            aria-label="9-Node Microservices"
          >
            <span className="material-symbols-outlined text-lg">hub</span>
            <span className="absolute -top-1 -right-1 w-3.5 h-3.5 text-[8px] font-mono font-bold text-white rounded-full flex items-center justify-center"
              style={{background:'#1E47C8', border:'1.5px solid rgba(6,9,20,0.80)'}}>
              9
            </span>

            {isAnyNodeActive && (
              <span className="absolute -left-1 w-1.5 h-3.5 rounded-full" style={{background:'#5B8EF0', boxShadow:'0 0 8px rgba(30,71,200,0.80)'}} />
            )}
          </button>

          {/* Hover Tooltip */}
          {!showNodesMenu && (
            <div className="absolute left-full ml-3 top-1/2 -translate-y-1/2 px-3 py-1.5 glass-panel text-white text-xs font-mono font-semibold rounded-xl shadow-2xl opacity-0 group-hover:opacity-100 transition-all duration-200 pointer-events-none whitespace-nowrap z-50 translate-x-1 group-hover:translate-x-2 flex items-center gap-2"
              style={{border:'1px solid rgba(30,71,200,0.35)'}}>
              <span>9 Microservice Nodes</span>
              <span className="px-1.5 py-0.5 text-[10px] rounded-md" style={{background:'rgba(30,71,200,0.18)', color:'#7EB0FF', border:'1px solid rgba(30,71,200,0.30)'}}>
                Ports :8000–:8008
              </span>
            </div>
          )}

          {/* Expanded 9-Node Popover Dock */}
          {showNodesMenu && (
            <div
              onMouseLeave={() => setShowNodesMenu(false)}
              className="absolute left-full ml-3 top-1/2 -translate-y-1/2 glass-panel p-3 rounded-2xl shadow-2xl w-64 z-50 animate-fadeIn space-y-1"
              style={{border:'1px solid rgba(30,71,200,0.30)'}}
            >
              <div className="text-[10px] font-mono font-bold uppercase px-2 mb-2 pb-1 flex justify-between items-center" style={{borderBottom:'1px solid rgba(255,255,255,0.08)', color:'#7EB0FF'}}>
                <span>Microservice Nodes</span>
                <span className="text-white/30">Ports :8000-8008</span>
              </div>
              
              <button
                onClick={() => {
                  onSelectView('orchestrator_board');
                  setShowNodesMenu(false);
                }}
                className="w-full flex items-center justify-center gap-2 mb-2 py-1.5 rounded-lg text-[10px] font-mono font-bold uppercase transition-all bg-emerald-600/80 hover:bg-emerald-600 text-white border border-emerald-500/30"
              >
                <span className="material-symbols-outlined text-sm">dashboard</span>
                <span>Open Visual Board</span>
              </button>
              <div className="grid grid-cols-1 gap-1 max-h-72 overflow-y-auto pr-1">
                {nodeItems.map((node) => {
                  const isNodeActive = currentView === node.id;
                  return (
                    <button
                      key={node.id}
                      onClick={() => {
                        onSelectView(node.id);
                        setShowNodesMenu(false);
                      }}
                      className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-xl text-xs font-mono transition-all ${
                        isNodeActive
                          ? 'text-white font-bold'
                          : 'text-white/60 hover:text-white border border-transparent hover:border-white/10'
                      }`}
                      style={isNodeActive ? {
                        background: 'rgba(30,71,200,0.22)',
                        border: '1px solid rgba(30,71,200,0.40)'
                      } : {background: 'transparent'}}
                    >
                      <span className="material-symbols-outlined text-sm" style={{color:'#7EB0FF'}}>{node.icon}</span>
                      <span className="truncate flex-1 text-left">{node.label}</span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded font-mono" style={{background:'rgba(255,255,255,0.06)', color:'rgba(255,255,255,0.35)'}}>
                        :{8000 + parseInt(node.num) - 1}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        <div className="w-5 h-[1px] my-0.5" style={{background:'rgba(13,21,51,0.10)'}} />

        {/* System & Settings Navigation Icons */}
        {mainGroups[1].items.map((item) => {
          const isActive = currentView === item.id;
          return (
            <div key={item.id} className="relative group">
              <button
                onClick={() => onSelectView(item.id)}
                className={`w-9.5 h-9.5 rounded-xl flex items-center justify-center transition-all duration-300 relative ${
                  isActive
                    ? 'text-white scale-105'
                    : 'scale-105'
                }`}
                style={isActive ? {
                  background: 'linear-gradient(135deg,#C8102E 0%,#A50D25 100%)',
                  boxShadow: '0 4px 16px rgba(200,16,46,0.40)'
                } : {color:'rgba(13,21,51,0.45)'}}>
                <span className="material-symbols-outlined text-lg">{item.icon}</span>

                {isActive && (
                  <span className="absolute -left-1 w-1.5 h-3.5 rounded-full" style={{background:'#E8405A', boxShadow:'0 0 8px rgba(200,16,46,0.80)'}} />
                )}
              </button>

              {/* Hover Tooltip - Full Name */}
              <div className="absolute left-full ml-3 top-1/2 -translate-y-1/2 px-3 py-1.5 glass-panel text-white text-xs font-mono font-semibold rounded-xl shadow-2xl opacity-0 group-hover:opacity-100 transition-all duration-200 pointer-events-none whitespace-nowrap z-50 translate-x-1 group-hover:translate-x-2"
                style={{border:'1px solid rgba(255,255,255,0.14)'}}>
                {item.label}
              </div>
            </div>
          );
        })}
      </div>
    </aside>
  );
};
