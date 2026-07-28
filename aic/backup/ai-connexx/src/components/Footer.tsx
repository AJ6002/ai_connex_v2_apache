import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="fixed bottom-0 left-0 right-0 w-full h-8 bg-slate-950/80 backdrop-blur-2xl border-t border-white/10 flex justify-between items-center px-6 font-mono text-[11px] text-slate-400 z-30">
      <div className="flex items-center gap-4">
        <span className="font-semibold text-emerald-400 flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          SYSTEM STATUS: OPERATIONAL
        </span>
        <span className="text-white/20">|</span>
        <span className="text-slate-400">© 2026 AI-Connexx Suite. All Rights Reserved.</span>
      </div>

      <div className="flex items-center gap-5 text-[11px]">
        <a href="#privacy" onClick={(e) => e.preventDefault()} className="hover:text-tas-red transition-colors">
          Privacy Policy
        </a>
        <a href="#terms" onClick={(e) => e.preventDefault()} className="hover:text-tas-red transition-colors">
          Terms of Service
        </a>
        <a href="#security" onClick={(e) => e.preventDefault()} className="hover:text-tas-red transition-colors">
          Security Standards
        </a>
      </div>
    </footer>
  );
};
