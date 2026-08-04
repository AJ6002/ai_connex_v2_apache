import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar, SidebarTab } from './components/Sidebar';
import { MainChatView } from './components/MainChatView';
import { SecondaryViews } from './components/SecondaryViews';
import { Footer } from './components/Footer';
import { ServicesModal } from './components/ServicesModal';
import { NotificationsDrawer } from './components/NotificationsDrawer';

export default function App() {
  const [darkMode, setDarkMode] = useState(false);
  const [activeTab, setActiveTab] = useState<SidebarTab>('chat');
  const [servicesModalOpen, setServicesModalOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [unreadNotifications, setUnreadNotifications] = useState(4);
  const [actionAlert, setActionAlert] = useState<string | null>(null);

  const handleActionSelect = (actionName: string) => {
    setActionAlert(`Executed Action: "${actionName}" across 9 online services.`);
    setTimeout(() => {
      setActionAlert(null);
    }, 4000);
  };

  const handleToggleNotifications = () => {
    setNotificationsOpen(!notificationsOpen);
    if (!notificationsOpen) {
      setUnreadNotifications(0);
    }
  };

  return (
    <div className={`min-h-screen font-sans transition-colors duration-200 ${darkMode ? 'bg-[#0B1329] text-slate-100' : 'bg-[#F8FAFC] text-slate-800'}`}>
      {/* Action Execution Alert Banner */}
      {actionAlert && (
        <div className="fixed top-16 left-1/2 -translate-x-1/2 z-50 bg-emerald-600 text-white font-mono text-xs px-4 py-2 rounded-xl shadow-2xl flex items-center gap-2 animate-in fade-in slide-in-from-top-4">
          <span className="w-2 h-2 rounded-full bg-white animate-ping" />
          <span>{actionAlert}</span>
        </div>
      )}

      {/* Top Navbar */}
      <Navbar
        darkMode={darkMode}
        setDarkMode={setDarkMode}
        onOpenServicesModal={() => setServicesModalOpen(true)}
        onActionSelect={handleActionSelect}
        onToggleNotifications={handleToggleNotifications}
        unreadNotifications={unreadNotifications}
      />

      {/* Left Sidebar Navigation Dock */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        darkMode={darkMode}
        onOpenServicesModal={() => setServicesModalOpen(true)}
      />

      {/* Main Content Workspace Area */}
      <main className="pb-16 pt-2 transition-all">
        {activeTab === 'chat' ? (
          <MainChatView
            darkMode={darkMode}
            onSelectStarter={(prompt) => {
              setActiveTab('chat');
            }}
          />
        ) : (
          <SecondaryViews
            activeTab={activeTab}
            darkMode={darkMode}
            onReturnToChat={() => setActiveTab('chat')}
          />
        )}
      </main>

      {/* Footer Status Bar */}
      <Footer darkMode={darkMode} />

      {/* Modals & Drawers */}
      <ServicesModal
        isOpen={servicesModalOpen}
        onClose={() => setServicesModalOpen(false)}
        darkMode={darkMode}
      />

      <NotificationsDrawer
        isOpen={notificationsOpen}
        onClose={() => setNotificationsOpen(false)}
        darkMode={darkMode}
      />
    </div>
  );
}
