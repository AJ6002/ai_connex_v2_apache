import React from 'react';

interface TasLogoProps {
  className?: string;
  showSubtitle?: boolean;
}

export const TasLogo: React.FC<TasLogoProps> = ({ className = "h-9", showSubtitle = true }) => {
  // SVG Data URI representing the official sharp TAS Logo mark with precision colors (#E30613 red and #23388B navy)
  const logoDataUri = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 280 90" fill="none"><rect x="0" y="8" width="60" height="16" fill="%23E30613"/><path d="M28 24v50c0 10 8 14 20 14h12V24H28z" fill="%2323388B"/><path d="M48 24l-14-16h26l18 16H48z" fill="%2323388B"/><path d="M56 88l26-52 28-26h20l-32 78H56z" fill="%2323388B"/><path d="M98 10l60 78h-26l-24-34-22 34H62l36-78z" fill="%2323388B"/><path d="M142 10h60c10 0 16 6 16 15 0 12-12 18-30 22l-20 4c-12 2-18 8-18 16 0 10 10 14 24 14h42v12h-46c-18 0-34-8-34-26 0-14 14-22 30-26l20-4c12-2 18-6 18-14 0-6-8-8-18-8h-48V10z" fill="%2323388B"/><text x="0" y="88" font-family="system-ui, sans-serif" font-weight="900" font-size="10" fill="%23E30613" letter-spacing="2">TOTAL AUTOMATION SOLUTIONS</text></svg>`;

  return (
    <div className={`inline-flex items-center gap-2 select-none group ${className}`}>
      <div className="relative p-1 bg-white rounded-lg border border-slate-200/80 shadow-2xs transition-all duration-200 group-hover:border-tas-blue/40 group-hover:shadow-xs flex items-center">
        <img
          src={logoDataUri}
          alt="Total Automation Solutions Logo"
          className="h-7 sm:h-8 w-auto object-contain block drop-shadow-2xs"
          loading="eager"
        />
      </div>
      {showSubtitle && (
        <div className="flex flex-col justify-center text-left">
          <span className="font-headline font-black tracking-tight text-slate-900 text-sm leading-none flex items-center gap-1">
            AI-CONNEXX
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-tas-red animate-pulse"></span>
          </span>
          <span className="font-mono text-[9px] font-extrabold uppercase text-[#E30613] tracking-widest leading-tight mt-0.5">
            TOTAL AUTOMATION
          </span>
        </div>
      )}
    </div>
  );
};
