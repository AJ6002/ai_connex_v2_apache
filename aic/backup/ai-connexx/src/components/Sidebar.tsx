import React from 'react';
import { ViewMode } from '../types';
import { OrbitArcSidebar } from './OrbitArcSidebar';

interface SidebarProps {
  currentView: ViewMode;
  onSelectView: (view: ViewMode) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentView, onSelectView }) => {
  return <OrbitArcSidebar currentView={currentView} onSelectView={onSelectView} />;
};

