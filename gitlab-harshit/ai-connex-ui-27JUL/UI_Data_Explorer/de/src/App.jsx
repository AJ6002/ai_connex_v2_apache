import { useState, useEffect } from 'react';
import { 
  Sparkles, 
  MessageSquare, 
  UploadCloud, 
  BarChart2, 
  Eraser, 
  CheckSquare, 
  Beaker, 
  Workflow, 
  FileText, 
  Rocket, 
  TrendingUp, 
  Network, 
  Shield, 
  Database,
  Bell,
  Sun,
  Moon,
  ChevronDown,
  Folder
} from 'lucide-react';

// Subpages
import PrePrepare from './pages/PrePrepare';
import PostPrepare from './pages/PostPrepare';
import PostFE from './pages/PostFE';
import PostTrain from './pages/PostTrain';

function App() {
  const [activeTab, setActiveTab] = useState('pre-prepare');
  const [theme, setTheme] = useState('light');
  const [actionsOpen, setActionsOpen] = useState(false);

  // Sync theme with HTML attribute
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  // Sidebar Icons definitions (Exactly matching the image rail)
  const sidebarTopIcons = [
    { id: 'magic', icon: <Sparkles size={18} />, classes: "sidebar-icon-magic" },
    { id: 'chat', icon: <MessageSquare size={18} /> },
    { id: 'upload', icon: <UploadCloud size={18} /> },
    { id: 'analytics', icon: <BarChart2 size={18} />, classes: "sidebar-icon-active" }, // Active stage dashboard
    { id: 'cleanup', icon: <Eraser size={18} /> },
    { id: 'tasks', icon: <CheckSquare size={18} /> },
    { id: 'lab', icon: <Beaker size={18} /> },
    { id: 'flow', icon: <Workflow size={18} /> },
    { id: 'docs', icon: <FileText size={18} /> },
    { id: 'deploy', icon: <Rocket size={18} /> },
    { id: 'growth', icon: <TrendingUp size={18} /> },
  ];

  const sidebarBottomIcons = [
    { id: 'network', icon: <Network size={18} />, classes: "sidebar-icon-blue-active", badge: 9 }, // Connected status badge
    { id: 'security', icon: <Shield size={18} /> },
    { id: 'storage', icon: <Database size={18} /> }
  ];

  // Pipeline stage tabs
  const tabs = [
    { id: 'pre-prepare', label: 'Pre-Prepare', badge: 'Brain', number: 1 },
    { id: 'post-prepare', label: 'Post-Prepare', badge: 'Prepare', number: 2 },
    { id: 'post-fe', label: 'Post-F.E', badge: 'Feature Engineered', number: 3 },
    { id: 'post-train', label: 'Post-Train', badge: 'Training', number: 4 }
  ];

  // Render correct subpage
  const renderSubpage = () => {
    switch (activeTab) {
      case 'pre-prepare':
        return <PrePrepare onProceed={() => setActiveTab('post-prepare')} />;
      case 'post-prepare':
        return <PostPrepare onProceed={() => setActiveTab('post-fe')} />;
      case 'post-fe':
        return <PostFE onProceed={() => setActiveTab('post-train')} />;
      case 'post-train':
        return <PostTrain />;
      default:
        return <PrePrepare onProceed={() => setActiveTab('post-prepare')} />;
    }
  };

  return (
    <div className="app-container">
      {/* Left Sidebar (Static navigation rail) */}
      <aside className="sidebar">
        <div className="sidebar-items-top">
          {sidebarTopIcons.map((item) => (
            <div 
              key={item.id} 
              className={`sidebar-icon-wrapper ${item.classes || ''}`}
              title={item.id}
            >
              {item.icon}
              {item.badge && <span className="sidebar-badge">{item.badge}</span>}
            </div>
          ))}
        </div>

        <div className="sidebar-items-bottom">
          {sidebarBottomIcons.map((item) => (
            <div 
              key={item.id} 
              className={`sidebar-icon-wrapper ${item.classes || ''}`}
              title={item.id}
            >
              {item.icon}
              {item.badge && <span className="sidebar-badge">{item.badge}</span>}
            </div>
          ))}
        </div>
      </aside>

      {/* Main Container Layout */}
      <main className="main-content">
        {/* Top Header */}
        <header className="top-header">
          <div className="header-left">
            <div className="header-logo-container">
              <span className="logo-tas">TAS</span>
              <div className="logo-divider">
                <Workflow size={16} style={{ color: 'rgba(255, 255, 255, 0.8)' }} />
              </div>
              <span className="logo-suite-text">
                AI-<span>Suite</span>
              </span>
            </div>
          </div>

          <div className="header-right">
            {/* Online Status */}
            <div className="services-status-badge">
              <span className="status-dot"></span>
              9 Services Online
            </div>

            {/* Actions Button */}
            <div style={{ position: 'relative' }}>
              <button 
                className="actions-dropdown-btn"
                onClick={() => setActionsOpen(!actionsOpen)}
              >
                Actions <ChevronDown size={14} />
              </button>
              {actionsOpen && (
                <div style={{
                  position: 'absolute',
                  top: '100%',
                  right: 0,
                  marginTop: '8px',
                  backgroundColor: 'var(--bg-card)',
                  border: '1px solid var(--border-medium)',
                  borderRadius: '6px',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                  minWidth: '150px',
                  zIndex: 200,
                  overflow: 'hidden'
                }}>
                  <button style={{ 
                    width: '100%', 
                    padding: '10px 16px', 
                    textAlign: 'left', 
                    fontSize: '12px',
                    color: 'var(--text-main)',
                    borderBottom: '1px solid var(--border-light)' 
                  }} onClick={() => { alert('Triggered pipeline restart'); setActionsOpen(false); }}>
                    Restart Pipeline
                  </button>
                  <button style={{ 
                    width: '100%', 
                    padding: '10px 16px', 
                    textAlign: 'left', 
                    fontSize: '12px',
                    color: 'var(--text-main)',
                    borderBottom: '1px solid var(--border-light)' 
                  }} onClick={() => { alert('Exporting dataset configurations'); setActionsOpen(false); }}>
                    Export Metadata
                  </button>
                  <button style={{ 
                    width: '100%', 
                    padding: '10px 16px', 
                    color: '#c51f33',
                    textAlign: 'left', 
                    fontSize: '12px' 
                  }} onClick={() => { alert('Terminated current process runs'); setActionsOpen(false); }}>
                    Terminate Run
                  </button>
                </div>
              )}
            </div>

            {/* Theme Toggle slider */}
            <div className="theme-toggle-container">
              <Sun size={14} className={`theme-icon ${theme === 'light' ? 'active' : ''}`} />
              <input 
                type="checkbox" 
                id="theme-checkbox" 
                className="theme-toggle-input"
                checked={theme === 'dark'}
                onChange={toggleTheme}
              />
              <label htmlFor="theme-checkbox" className="theme-toggle-label"></label>
              <Moon size={14} className={`theme-icon ${theme === 'dark' ? 'active' : ''}`} />
            </div>

            {/* Bell Icon Notification */}
            <button className="header-icon-btn">
              <Bell size={18} />
            </button>

            {/* Profile Avatar */}
            <div className="user-profile-circle">H</div>
          </div>
        </header>

        {/* Sub-Header / Control Hub */}
        <section className="sub-header-container">
          <div className="sub-header-top">
            <div className="window-dots-title">
              <div className="window-dots">
                <span className="dot dot-red"></span>
                <span className="dot dot-yellow"></span>
                <span className="dot dot-green"></span>
              </div>
              <div className="window-title">
                <Folder size={14} />
                Dataset Explorer Stage Transit Hub
              </div>
            </div>
          </div>

          {/* Navigation Pipeline Tabs */}
          <nav className="stages-tabs-container">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                className={`stage-tab ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <span className="stage-tab-text-title">{tab.label}</span>
                <span className={`stage-badge stage-badge-${tab.id === 'pre-prepare' ? 'brain' : tab.id === 'post-prepare' ? 'prepare' : tab.id === 'post-fe' ? 'fe' : 'training'}`}>
                  {tab.badge}
                </span>
                <span className="stage-tab-number">{tab.number}</span>
              </button>
            ))}
          </nav>
        </section>

        {/* Content Render Workspace */}
        <div style={{ flex: 1 }}>
          {renderSubpage()}
        </div>

        {/* Operational Footer */}
        <footer className="app-footer">
          <div className="footer-status">
            <span className="status-dot"></span>
            SYSTEM STATUS: OPERATIONAL
          </div>
          <div>
            © 2026 AI-Suite. All Rights Reserved.
          </div>
          <div className="footer-links">
            <a href="#privacy">Privacy Policy</a>
            <a href="#terms">Terms of Service</a>
            <a href="#security">Security Standards</a>
          </div>
        </footer>
      </main>
    </div>
  );
}

export default App;
