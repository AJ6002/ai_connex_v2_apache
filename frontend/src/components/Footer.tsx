import React from 'react';
import { SidebarStyle } from '../types';

interface FooterProps {
  sidebarStyle?: SidebarStyle;
}

export const Footer: React.FC<FooterProps> = ({ sidebarStyle }) => {
  return (
    <footer
      className={`fixed bottom-0 left-0 right-0 w-full h-8 backdrop-blur-2xl flex justify-between items-center pr-6 font-mono text-[11px] z-30 transition-all duration-300 ${
        sidebarStyle === 'slim' ? 'pl-24' : 'pl-6'
      }`}
      style={{
        background: 'rgba(255,255,255,0.85)',
        borderTop: '1px solid rgba(13,21,51,0.08)',
        color: 'rgba(13,21,51,0.50)'
      }}
    >
      <div className="flex items-center gap-4">
        <span className="font-semibold flex items-center gap-1.5" style={{color:'#4ade80'}}>
          <span className="w-2 h-2 rounded-full animate-pulse" style={{background:'#22c55e', boxShadow:'0 0 6px rgba(34,197,94,0.60)'}}></span>
          SYSTEM STATUS: OPERATIONAL
        </span>
        <span style={{color:'rgba(13,21,51,0.20)'}}>|</span>
        <span className="inline-flex items-center gap-0.5">© 2026 AI-<img src="/connexx-dark.png" alt="Connexx" className="h-3.5 w-auto object-contain inline-block align-middle" /> Suite. All Rights Reserved.</span>
      </div>

      <div className="flex items-center gap-5 text-[11px]">
        <a href="#privacy" onClick={(e) => e.preventDefault()} className="transition-colors hover:text-white/80"
          style={{color:'rgba(237,240,250,0.40)'}}>
          Privacy Policy
        </a>
        <a href="#terms" onClick={(e) => e.preventDefault()} className="transition-colors hover:text-white/80"
          style={{color:'rgba(237,240,250,0.40)'}}>
          Terms of Service
        </a>
        <a href="#security" onClick={(e) => e.preventDefault()} className="transition-colors hover:text-white/80"
          style={{color:'rgba(237,240,250,0.40)'}}>
          Security Standards
        </a>
      </div>
    </footer>
  );
};
