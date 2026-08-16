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
      category: 'Core Workflow Studio',
      items: [
        { id: 'hero', label: 'Hero Page & Jane AI', shortLabel: 'Hero', icon: 'auto_awesome', badge: 'Hero' },
        { id: 'compiler', label: 'Upload Controller & Ingestion', shortLabel: 'Upload', icon: 'cloud_upload', badge: 'Studio' },
        { id: 'data_explorer', label: 'Data Explorer & Telemetry', shortLabel: 'Explore', icon: 'analytics', badge: 'Cleaned Data' },
        { id: 'model_explorer', label: 'Model Explorer & Ledger', shortLabel: 'Models', icon: 'auto_graph', badge: 'Trained Models' },
        { id: 'deployment', label: 'Deployment & Physics Layer', shortLabel: 'Deploy', icon: 'rocket_launch', badge: 'Edge Deploy' },
        { id: 'agent_manager', label: 'Agent Fleet Orchestrator', shortLabel: 'Agents', icon: 'smart_toy', badge: 'Multi-Agent' },
        { id: 'pipeline_studio', label: 'ML Studio & Pipeline Monitor', shortLabel: 'ML Studio', icon: 'monitoring', badge: 'Pipeline' },
      ],
    },
    {
      category: 'Administration & Master Data',
      items: [
        { id: 'master_data', label: 'Master Data & Recipes', shortLabel: 'Master', icon: 'database', badge: 'Recipes' },
        { id: 'administration', label: 'Administration & Envs', shortLabel: 'Admin', icon: 'admin_panel_settings' },
        { id: 'templates', label: 'Templates Library', shortLabel: 'Templates', icon: 'description' },
        { id: 'quotas', label: 'Quotas & GPU Spend', shortLabel: 'GPU', icon: 'payments' },
        { id: 'workspace', label: 'My Workspace', shortLabel: 'Workspace', icon: 'folder_shared' },
        { id: 'developer_studio', label: 'Developer Stdout Stream', shortLabel: 'Logs', icon: 'terminal' },
        { id: 'settings', label: 'Platform Settings', shortLabel: 'Settings', icon: 'settings' },
        { id: 'support', label: 'Support & Specs', shortLabel: 'Specs', icon: 'help_outline' },
      ],
    },
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
