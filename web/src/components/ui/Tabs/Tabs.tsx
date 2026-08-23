import React, { createContext, useContext, useState } from 'react';
import './Tabs.css';

interface TabsContextType {
  active: string;
  setActive: (id: string) => void;
  orientation: 'horizontal' | 'vertical';
}

const TabsContext = createContext<TabsContextType | null>(null);

const useTabsContext = () => {
  const ctx = useContext(TabsContext);
  if (!ctx) throw new Error('<Tab*> must be used inside <Tabs>');
  return ctx;
};

export interface TabsProps {
  defaultTab: string;
  orientation?: 'horizontal' | 'vertical';
  className?: string;
  style?: React.CSSProperties;
  children: React.ReactNode;
  onTabChange?: (tabId: string) => void;
}

export const Tabs: React.FC<TabsProps> = ({
  defaultTab,
  orientation = 'horizontal',
  className = '',
  style,
  children,
  onTabChange,
}) => {
  const [active, setActiveState] = useState(defaultTab);
  const setActive = (id: string) => {
    setActiveState(id);
    onTabChange?.(id);
  };
  return (
    <TabsContext.Provider value={{ active, setActive, orientation }}>
      <div className={`tabs tabs--${orientation} ${className}`} style={style}>{children}</div>
    </TabsContext.Provider>
  );
};

export interface TabListProps {
  className?: string;
  children: React.ReactNode;
}

export const TabList: React.FC<TabListProps> = ({ className = '', children }) => {
  const { orientation } = useTabsContext();
  return (
    <div
      role="tablist"
      className={`tab-list tab-list--${orientation} ${className}`}
      aria-orientation={orientation}
    >
      {children}
    </div>
  );
};

export interface TabTriggerProps {
  id: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  disabled?: boolean;
}

export const TabTrigger: React.FC<TabTriggerProps> = ({
  id,
  icon,
  children,
  className = '',
  disabled = false,
}) => {
  const { active, setActive } = useTabsContext();
  const isActive = active === id;

  return (
    <button
      role="tab"
      id={`tab-${id}`}
      aria-selected={isActive}
      aria-controls={`tabpanel-${id}`}
      disabled={disabled}
      className={`tab-trigger ${isActive ? 'tab-trigger--active' : ''} ${className}`}
      onClick={() => setActive(id)}
    >
      {icon && <span className="tab-trigger__icon" aria-hidden="true">{icon}</span>}
      <span className="tab-trigger__label">{children}</span>
      {isActive && <span className="tab-trigger__indicator" aria-hidden="true" />}
    </button>
  );
};

export interface TabPanelProps {
  id: string;
  className?: string;
  children: React.ReactNode;
}

export const TabPanel: React.FC<TabPanelProps> = ({ id, className = '', children }) => {
  const { active } = useTabsContext();
  if (active !== id) return null;

  return (
    <div
      role="tabpanel"
      id={`tabpanel-${id}`}
      aria-labelledby={`tab-${id}`}
      className={`tab-panel animate-fade-in ${className}`}
    >
      {children}
    </div>
  );
};
