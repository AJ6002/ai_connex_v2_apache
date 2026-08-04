import React from 'react';

interface TASLogoProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const TASLogo: React.FC<TASLogoProps> = ({ size = 'md', className = '' }) => {
  const sizeClasses = {
    sm: 'h-6 text-xs px-2 py-0.5',
    md: 'h-8 text-sm px-3 py-1',
    lg: 'h-12 text-lg px-4 py-2',
  };

  return (
    <div className={`bg-white rounded-lg border border-slate-200/80 shadow-sm flex items-center gap-2 select-none ${sizeClasses[size]} ${className}`}>
      {/* TAS Stylized Logo Mark */}
      <div className="flex items-center font-black tracking-tight font-sans">
        <span className="text-[#DC2626]">T</span>
        <span className="text-[#1D4ED8]">A</span>
        <span className="text-[#1D4ED8]">S</span>
      </div>
      <div className="h-3 w-[1px] bg-slate-300"></div>
      <div className="flex flex-col justify-center leading-none">
        <span className="text-[7px] font-bold text-slate-800 uppercase tracking-wider">TOTAL AUTOMATION</span>
        <span className="text-[6px] font-semibold text-slate-500 uppercase tracking-widest">SOLUTIONS</span>
      </div>
    </div>
  );
};
