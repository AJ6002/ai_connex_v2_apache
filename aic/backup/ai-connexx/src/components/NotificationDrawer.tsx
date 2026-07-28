import React from 'react';
import { SystemNotification } from '../types';

interface NotificationDrawerProps {
  notifications: SystemNotification[];
  isOpen: boolean;
  onClose: () => void;
  onMarkAllRead: () => void;
}

export const NotificationDrawer: React.FC<NotificationDrawerProps> = ({
  notifications,
  isOpen,
  onClose,
  onMarkAllRead,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed top-16 right-6 w-96 bg-white border border-slate-200 shadow-xl rounded-xl z-50 overflow-hidden animate-fadeIn">
      <div className="p-4 bg-[#0F172A] text-white flex justify-between items-center">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-lg text-tas-blue">notifications</span>
          <h3 className="font-headline font-bold text-sm text-white">System Alerts & Notifications</h3>
        </div>
        <button
          onClick={onMarkAllRead}
          className="text-[10px] font-mono uppercase bg-slate-800 hover:bg-slate-700 text-slate-200 px-2 py-1 rounded-md transition-colors"
        >
          Mark all read
        </button>
      </div>

      <div className="max-h-96 overflow-y-auto divide-y divide-slate-100">
        {notifications.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-400">No system notifications</div>
        ) : (
          notifications.map((n) => (
            <div
              key={n.id}
              className={`p-4 transition-colors ${
                n.read ? 'bg-white' : 'bg-tas-blue-light border-l-4 border-tas-blue'
              }`}
            >
              <div className="flex justify-between items-start mb-1">
                <span className="font-semibold text-xs text-slate-900">{n.title}</span>
                <span className="text-[10px] font-mono text-slate-400">{n.timestamp}</span>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">{n.message}</p>
            </div>
          ))
        )}
      </div>

      <div className="p-3 bg-slate-50 border-t border-slate-200 text-center">
        <button
          onClick={onClose}
          className="text-xs font-semibold text-tas-blue hover:text-tas-blue-hover hover:underline"
        >
          Close Drawer
        </button>
      </div>
    </div>
  );
};
