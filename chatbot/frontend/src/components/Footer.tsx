import React from 'react';

interface FooterProps {
  darkMode: boolean;
}

export const Footer: React.FC<FooterProps> = ({ darkMode }) => {
  return (
    <footer
      className={`fixed bottom-0 left-0 right-0 z-20 border-t py-2 px-6 flex flex-wrap items-center justify-between text-[11px] font-mono transition-colors ${
        darkMode
          ? 'bg-slate-900/90 border-slate-800 text-slate-400'
          : 'bg-white/90 border-slate-200 text-slate-500 backdrop-blur-sm'
      }`}
    >
      {/* Left System Operational & Copyright */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 font-bold text-emerald-600 dark:text-emerald-400">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>SYSTEM STATUS: OPERATIONAL</span>
        </div>
        <span className="text-slate-300 dark:text-slate-700">|</span>
        <span>© 2026 AI-Connexx Suite. All Rights Reserved.</span>
      </div>

      {/* Right Legal / Standard Links */}
      <div className="flex items-center gap-4 text-slate-400 dark:text-slate-500">
        <a href="#privacy" className="hover:text-slate-700 dark:hover:text-slate-300 transition-colors">
          Privacy Policy
        </a>
        <a href="#terms" className="hover:text-slate-700 dark:hover:text-slate-300 transition-colors">
          Terms of Service
        </a>
        <a href="#security" className="hover:text-slate-700 dark:hover:text-slate-300 transition-colors">
          Security Standards
        </a>
      </div>
    </footer>
  );
};
