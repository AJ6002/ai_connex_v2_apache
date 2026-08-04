import React from 'react';

interface TasLogoProps {
  className?: string;
  showSubtitle?: boolean;
}

export const TasLogo: React.FC<TasLogoProps> = ({ className = "h-9", showSubtitle = true }) => {
  return (
    <div className={`inline-flex items-center gap-3 select-none group ${className}`}>
      {/* TAS Logo (Left) */}
      <div className="relative p-1 bg-white rounded-xl border border-white/30 shadow-md flex items-center justify-center">
        <img
          src="/tas-logo.png"
          alt="Total Automation Solutions Logo"
          className="h-7 sm:h-8 w-auto object-contain block"
          loading="eager"
        />
      </div>

      {/* AI- Connexx Wordmark (Center) */}
      {showSubtitle && (
        <div className="flex flex-col justify-center text-left">
          <span className="font-headline font-black tracking-tight text-white text-base leading-none flex items-center gap-1.5 drop-shadow">
            AI-<img src="/connexx-white.png" alt="Connexx" className="h-5 w-auto object-contain inline-block align-middle" loading="eager" />
            <span className="inline-block w-2 h-2 rounded-full bg-tas-red animate-pulse shadow-[0_0_8px_#E30613]"></span>
          </span>
          <span className="font-mono text-[9px] font-extrabold uppercase text-tas-red tracking-wider leading-tight mt-0.5">
            TOTAL AUTOMATION
          </span>
        </div>
      )}

      {/* Connex Logo Icon (Right) */}
      <div className="relative p-1 bg-white/10 rounded-xl border border-white/20 shadow-md flex items-center justify-center backdrop-blur-sm">
        <img
          src="/connex-logo.png"
          alt="Connex Logo"
          className="h-7 sm:h-8 w-auto object-contain block"
          loading="eager"
        />
      </div>
    </div>
  );
};
