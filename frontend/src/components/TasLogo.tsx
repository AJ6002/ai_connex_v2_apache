import React from 'react';

interface TasLogoProps {
  className?: string;
  showSubtitle?: boolean;
}

export const TasLogo: React.FC<TasLogoProps> = ({ className = "h-8", showSubtitle = true }) => {
  return (
    <div className={`inline-flex items-center gap-3 select-none ${className}`}>
      {/* TAS Logo Box (White-to-light-gray gradient pill) */}
      <div className="relative px-3 py-1 bg-gradient-to-b from-white via-white to-slate-200 rounded-2xl border border-white/40 shadow-md flex items-center justify-center">
        <img
          src="/tas-logo.png"
          alt="Total Automation Solutions Logo"
          className="h-7 sm:h-8 w-auto object-contain block"
          loading="eager"
        />
      </div>

      {/* Sleek Vertical Divider Line with Solar Orange Tint */}
      <div className="h-7 w-[2px] bg-gradient-to-b from-[#FF6B35] via-[#FF6B35]/70 to-[#FF6B35]/20 rounded-full opacity-80" />

      {/* Styled Brand Wordmark: AI-ConneX */}
      {showSubtitle && (
        <div className="flex items-center text-left">
          <span className="font-headline font-black italic tracking-tighter text-2xl sm:text-3xl leading-none drop-shadow-sm select-none">
            <span className="text-[#FF6B35]">AI-</span>
            <span className="text-white">Conne</span>
            <span className="text-[#FF6B35]">X</span>
          </span>
        </div>
      )}
    </div>
  );
};
