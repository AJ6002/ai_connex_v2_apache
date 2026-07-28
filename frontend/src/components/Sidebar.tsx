import React from 'react';
import { ViewMode, SidebarStyle } from '../types';
import { OrbitArcSidebar } from './OrbitArcSidebar';
import { SlimFloatingSidebar } from './SlimFloatingSidebar';

interface SidebarProps {
  currentView: ViewMode;
  onSelectView: (view: ViewMode) => void;
  sidebarStyle?: SidebarStyle;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentView,
  onSelectView,
  sidebarStyle = 'slim',
}) => {
  if (sidebarStyle === 'slim') {
    return <SlimFloatingSidebar currentView={currentView} onSelectView={onSelectView} />;
  }

  return <OrbitArcSidebar currentView={currentView} onSelectView={onSelectView} />;
};
