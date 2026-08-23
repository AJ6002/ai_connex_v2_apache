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
        <span className="font-semibold flex items-center gap-1.5" style={{color:'#E86326'}}>
          <span className="w-2 h-2 rounded-full animate-pulse" style={{background:'#E86326', boxShadow:'0 0 6px rgba(232,99,38,0.60)'}}></span>
          SYSTEM STATUS: OPERATIONAL
        </span>
        <span style={{color:'rgba(43,0,99,0.20)'}}>|</span>
        <span className="inline-flex items-center gap-0.5 font-bold">
          © 2026 <span className="text-[#E86326] ml-1">AI-</span><span className="text-[#2B0063]">ConneX</span>. All Rights Reserved.
        </span>
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
