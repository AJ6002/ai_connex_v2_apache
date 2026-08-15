import React, { useState } from 'react';
import { createPortal } from 'react-dom';
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

interface HoveredTooltipInfo {
  label: string;
  badge?: string;
  x: number;
  y: number;
}

export const SlimFloatingSidebar: React.FC<SlimFloatingSidebarProps> = ({
  currentView,
  onSelectView,
}) => {
  const [showNodesMenu, setShowNodesMenu] = useState(false);
  const [hoveredItem, setHoveredItem] = useState<HoveredTooltipInfo | null>(null);

  const mainGroups: NavGroup[] = [
    {
      category: 'Pipeline Cascade',
      items: [
        { id: 'hero', label: 'Getting Started: Hero Page', shortLabel: 'Hero', icon: 'auto_awesome', badge: 'Hero' },
        { id: 'compiler', label: 'Page 1: Upload Page', shortLabel: 'Upload', icon: 'upload_file', badge: 'Page 1' },
        { id: 'data_explorer', label: 'Page 2: Data Explorer', shortLabel: 'Explore', icon: 'bar_chart', badge: 'Page 2' },
        { id: 'node4', label: 'Page 3: Prepare Node', shortLabel: 'Prepare', icon: 'cleaning_services', badge: 'Page 3' },
        { id: 'vg1', label: 'Page 4: Validation Gate 1', shortLabel: 'VG 1', icon: 'verified', badge: 'Page 4' },
        { id: 'node5', label: 'Page 5: Feature Engineer Node', shortLabel: 'Features', icon: 'science', badge: 'Page 5' },
        { id: 'node7', label: 'Page 6: Train Node', shortLabel: 'Train', icon: 'model_training', badge: 'Page 6' },
        { id: 'vg2', label: 'Page 7: Validation Gate 2', shortLabel: 'VG 2', icon: 'fact_check', badge: 'Page 7' },
        { id: 'node9', label: 'Page 8: Deploy Node', shortLabel: 'Deploy', icon: 'rocket_launch', badge: 'Page 8' },
        { id: 'pipeline_studio', label: 'Page 9: Monitor Node', shortLabel: 'Monitor', icon: 'monitoring', badge: 'Page 9' },
      ],
    },
    {
      category: 'Administration & Master Data',
      items: [
        { id: 'administration', label: 'Administration & Envs', shortLabel: 'Admin', icon: 'admin_panel_settings' },
        { id: 'agent_manager', label: 'Agent Manager & API Fleet', shortLabel: 'Agents', icon: 'smart_toy', badge: 'Admin Only' },
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

  const updateHovered = (label: string, e: React.MouseEvent, badge?: string) => {
    setHoveredItem({
      label,
      badge,
      x: e.clientX,
      y: e.clientY,
    });
  };

  return (
    <>
      <aside className="fixed left-3 top-20 bottom-10 z-50 animate-fadeIn max-h-[calc(100vh-7.5rem)] overflow-y-auto no-scrollbar py-2">
        {/* Floating Slim Dock */}
        <div className="glass-panel backdrop-blur-2xl shadow-2xl rounded-2xl p-2.5 flex flex-col items-center gap-2"
          style={{background:'rgba(255,255,255,0.96)', border:'1.5px solid #E2E8F0', boxShadow:'0 12px 36px rgba(13,21,51,0.12), inset 0 1px 0 rgba(255,255,255,1)'}}>
          
          {/* Brand Emblem — Routes to Hero View */}
          <button 
            onClick={() => onSelectView('hero')}
            onMouseEnter={(e) => updateHovered('TAS AIConnex Hero Page', e)}
            onMouseMove={(e) => updateHovered('TAS AIConnex Hero Page', e)}
            onMouseLeave={() => setHoveredItem(null)}
            className="w-10 h-10 rounded-xl flex items-center justify-center shadow-md group relative cursor-pointer transition-all duration-200 hover:scale-105 active:scale-95"
            style={{background:'linear-gradient(135deg,#2B0063 0%,#3C1053 100%)', border:'1px solid rgba(232,99,38,0.40)'}}
            title="Go to TAS AIConnex Hero Page">
            <span className="material-symbols-outlined text-[#E86326] text-xl animate-pulse">auto_awesome</span>
          </button>

          <div className="w-6 h-[1px] my-0.5" style={{background:'rgba(13,21,51,0.12)'}} />

          {/* Primary Navigation Icons */}
          {mainGroups[0].items.map((item) => {
            const isActive = currentView === item.id;
            return (
              <div key={item.id} className="relative">
                <button
                  onClick={() => onSelectView(item.id)}
                  onMouseEnter={(e) => updateHovered(item.label, e, item.badge)}
                  onMouseMove={(e) => updateHovered(item.label, e, item.badge)}
                  onMouseLeave={() => setHoveredItem(null)}
                  className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 relative ${
                    isActive
                      ? 'scale-105 shadow-md'
                      : 'hover:scale-105'
                  }`}
                  style={isActive ? {
                    background: '#E86326',
                    border: '1.5px solid #2B0063',
                    boxShadow: '0 4px 16px rgba(232,99,38,0.50)',
                    color: '#FFFFFF'
                  } : {
                    background: '#F7F7F7',
                    border: '1px solid #E5E7EB',
                    color: '#333333'
                  }}>
                  <span className="material-symbols-outlined text-xl font-bold">{item.icon}</span>
                </button>
              </div>
            );
          })}

          <div className="w-6 h-[1px] my-0.5" style={{background:'rgba(13,21,51,0.12)'}} />

          {/* 9-Node Microservices Flyout Button */}
          <div className="relative">
            <button
              onClick={() => onSelectView('orchestrator_board')}
              onMouseEnter={(e) => {
                setShowNodesMenu(true);
                updateHovered('9 Microservice Nodes (Ports :8000–:8008)', e);
              }}
              onMouseMove={(e) => updateHovered('9 Microservice Nodes (Ports :8000–:8008)', e)}
              onMouseLeave={() => setHoveredItem(null)}
              className="w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 relative scale-105 hover:scale-110 active:scale-95"
              style={{
                background: '#E86326',
                border: '1.5px solid #2B0063',
                boxShadow: '0 4px 16px rgba(232,99,38,0.50)',
                color: '#FFFFFF'
              }}
              aria-label="9-Node Microservices"
            >
              <span className="material-symbols-outlined text-xl font-bold">hub</span>
              <span className="absolute -top-1 -right-1 w-4 h-4 text-[9px] font-mono font-extrabold text-white rounded-full flex items-center justify-center shadow-sm"
                style={{background:'#2B0063', border:'1px solid #E86326'}}>
                9
              </span>
            </button>

            {/* Expanded 9-Node Popover Dock */}
            {showNodesMenu && (
              <div
                onMouseLeave={() => setShowNodesMenu(false)}
                className="absolute left-full ml-3 top-1/2 -translate-y-1/2 glass-panel p-3 rounded-2xl shadow-2xl w-64 z-50 animate-fadeIn space-y-1"
                style={{background:'#2B0063', border:'1.5px solid #E86326'}}
              >
                <div className="text-[10px] font-mono font-bold uppercase px-2 mb-2 pb-1 flex justify-between items-center" style={{borderBottom:'1px solid rgba(232,99,38,0.25)', color:'#E86326'}}>
                  <span>Microservice Nodes</span>
                  <span className="text-white/50">Ports :8000-8008</span>
                </div>
                
                <button
                  onClick={() => {
                    onSelectView('orchestrator_board');
                    setShowNodesMenu(false);
                  }}
                  onMouseEnter={(e) => updateHovered('Open Visual Node Board', e)}
                  onMouseMove={(e) => updateHovered('Open Visual Node Board', e)}
                  onMouseLeave={() => setHoveredItem(null)}
                  className="w-full flex items-center justify-center gap-2 mb-2 py-2 rounded-xl text-xs font-mono font-bold uppercase transition-all bg-[#E86326] hover:bg-[#D5521B] text-white shadow-md"
                >
                  <span className="material-symbols-outlined text-sm font-bold">dashboard</span>
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
                        onMouseEnter={(e) => updateHovered(`${node.label} (Port :${8000 + parseInt(node.num) - 1})`, e)}
                        onMouseMove={(e) => updateHovered(`${node.label} (Port :${8000 + parseInt(node.num) - 1})`, e)}
                        onMouseLeave={() => setHoveredItem(null)}
                        className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-xl text-xs font-mono transition-all ${
                          isNodeActive
                            ? 'text-white font-bold bg-[#E86326] border border-white/40'
                            : 'text-white/70 hover:text-white border border-transparent hover:border-white/10'
                        }`}
                      >
                        <span className="material-symbols-outlined text-sm" style={{color: isNodeActive ? '#FFFFFF' : 'rgba(255,255,255,0.6)'}}>{node.icon}</span>
                        <span className="truncate flex-1 text-left">{node.label}</span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded font-mono" style={{background:'rgba(255,255,255,0.10)', color: isNodeActive ? '#FFFFFF' : 'rgba(255,255,255,0.60)'}}>
                          :{8000 + parseInt(node.num) - 1}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          <div className="w-6 h-[1px] my-0.5" style={{background:'rgba(13,21,51,0.12)'}} />

          {/* System & Settings Navigation Icons */}
          {mainGroups[1].items.map((item) => {
            const isActive = currentView === item.id;
            return (
              <div key={item.id} className="relative">
                <button
                  onClick={() => onSelectView(item.id)}
                  onMouseEnter={(e) => updateHovered(item.label, e, item.badge)}
                  onMouseMove={(e) => updateHovered(item.label, e, item.badge)}
                  onMouseLeave={() => setHoveredItem(null)}
                  className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 relative ${
                    isActive
                      ? 'scale-105 shadow-md'
                      : 'hover:scale-105'
                  }`}
                  style={isActive ? {
                    background: '#E86326',
                    border: '1.5px solid #2B0063',
                    boxShadow: '0 4px 16px rgba(232,99,38,0.50)',
                    color: '#FFFFFF'
                  } : {
                    background: '#F7F7F7',
                    border: '1px solid #E5E7EB',
                    color: '#333333'
                  }}>
                  <span className="material-symbols-outlined text-xl font-bold">{item.icon}</span>
                </button>
              </div>
            );
          })}
        </div>
      </aside>

      {/* Floating Under-Cursor Tooltip rendered via React Portal directly into document.body */}
      {hoveredItem &&
        createPortal(
          <div
            className="fixed pointer-events-none transition-transform duration-75 ease-out animate-fadeIn"
            style={{
              left: `${hoveredItem.x + 22}px`,
              top: `${hoveredItem.y + 12}px`,
              zIndex: 999999,
            }}
          >
            <div
              className="px-3.5 py-1.5 text-xs font-mono font-bold rounded-xl shadow-2xl flex items-center gap-2 whitespace-nowrap"
              style={{
                background: '#2B0063',
                border: '1.5px solid #FF6B35',
                color: '#FFFFFF',
                boxShadow: '0 12px 36px rgba(43,0,99,0.8), 0 0 16px rgba(255,107,53,0.5)',
              }}
            >
              <span>{hoveredItem.label}</span>
              {hoveredItem.badge && (
                <span className="px-1.5 py-0.5 text-[10px] rounded-md font-extrabold" style={{ background: '#FF6B35', color: '#FFFFFF' }}>
                  {hoveredItem.badge}
                </span>
              )}
            </div>
          </div>,
          document.body
        )}
    </>
  );
};
