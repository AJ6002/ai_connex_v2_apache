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
    <div className="fixed top-16 right-6 w-96 glass-panel shadow-2xl rounded-2xl z-50 overflow-hidden animate-fadeIn"
      style={{border:'1px solid rgba(255,255,255,0.14)'}}>
      {/* Drawer Header */}
      <div className="p-4 flex justify-between items-center" style={{background:'rgba(6,9,20,0.70)', borderBottom:'1px solid rgba(255,255,255,0.08)'}}>
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-lg" style={{color:'#3B6FE8'}}>notifications</span>
          <h3 className="font-headline font-bold text-sm text-white">System Alerts &amp; Notifications</h3>
        </div>
        <button
          onClick={onMarkAllRead}
          className="text-[10px] font-mono uppercase px-2 py-1 rounded-lg transition-colors"
          style={{background:'rgba(255,255,255,0.08)', color:'rgba(237,240,250,0.70)', border:'1px solid rgba(255,255,255,0.12)'}}
        >
          Mark all read
        </button>
      </div>

      <div className="max-h-96 overflow-y-auto" style={{borderBottom:'1px solid rgba(255,255,255,0.06)'}}>
        {notifications.length === 0 ? (
          <div className="p-8 text-center text-xs" style={{color:'rgba(237,240,250,0.40)'}}>No system notifications</div>
        ) : (
          notifications.map((n) => (
            <div
              key={n.id}
              className="p-4 transition-colors"
              style={n.read
                ? {background:'rgba(255,255,255,0.03)', borderBottom:'1px solid rgba(255,255,255,0.06)'}
                : {background:'rgba(30,71,200,0.10)', borderLeft:'3px solid #1E47C8', borderBottom:'1px solid rgba(30,71,200,0.20)'}
              }
            >
              <div className="flex justify-between items-start mb-1">
                <span className="font-semibold text-xs text-white">{n.title}</span>
                <span className="text-[10px] font-mono" style={{color:'rgba(237,240,250,0.40)'}}>{n.timestamp}</span>
              </div>
              <p className="text-xs leading-relaxed" style={{color:'rgba(237,240,250,0.65)'}}>{n.message}</p>
            </div>
          ))
        )}
      </div>

      <div className="p-3 text-center" style={{background:'rgba(6,9,20,0.50)'}}>
        <button
          onClick={onClose}
          className="text-xs font-semibold transition-colors hover:text-white"
          style={{color:'rgba(59,111,232,0.90)'}}
        >
          Close Drawer
        </button>
      </div>
    </div>
  );
};
