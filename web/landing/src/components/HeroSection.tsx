import React from 'react';
import { ArrowUpRight } from 'lucide-react';

interface HeroSectionProps {
  onGetStarted: () => void;
  onWatchDemo: () => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({ onGetStarted, onWatchDemo }) => {

  return (
    <section className="relative overflow-hidden hero-dot-grid pt-14 sm:pt-24 pb-20 sm:pb-28 px-4 sm:px-6 lg:px-8 border-b border-[#E2E4E6]">
      <div className="max-w-5xl mx-auto text-center relative z-10">
        {/* Animated Industrial Compressor GIF centered above headline */}
        <div className="flex items-center justify-center mb-6 sm:mb-8">
          <img
            src="/compresser.gif"
            alt="AIConneX Industrial Compressor Analytics"
            className="max-w-[280px] sm:max-w-[340px] w-full h-auto rounded-2xl border border-[#E2E4E6] shadow-xs bg-white object-contain"
          />
        </div>

        {/* Main Headline */}
        <h1 className="text-4xl sm:text-6xl md:text-[68px] font-bold text-[#191c1d] tracking-tight leading-[1.08] sm:leading-[1.05] max-w-4xl mx-auto font-sans">
          Turn <span className="text-[#666666] font-normal">industrial data</span> into <br className="hidden sm:inline" />
          intelligent decisions.
        </h1>

        {/* Subtitle */}
        <p className="mt-6 sm:mt-8 text-base sm:text-lg md:text-xl text-[#666666] max-w-2xl mx-auto leading-relaxed font-normal">
          Talk to Jane to explore your data, understand what is happening, build ML workflows, and move results toward deployment.
        </p>

        {/* Action Buttons */}
        <div className="mt-8 sm:mt-10 flex flex-wrap items-center justify-center gap-4">
          <button
            id="hero-get-started-btn"
            onClick={onGetStarted}
            className="flex items-center gap-2 bg-[#000000] hover:bg-[#1f2328] text-white font-mono font-bold px-8 py-3.5 rounded-full text-xs uppercase tracking-wider transition-all duration-200 shadow-sm cursor-pointer hover:scale-[1.02]"
          >
            <ArrowUpRight className="w-4 h-4 stroke-[2.5]" />
            <span>GET STARTED</span>
          </button>

          <button
            id="hero-watch-demo-btn"
            onClick={onWatchDemo}
            className="flex items-center gap-2 bg-transparent hover:bg-white border border-[#000000] text-[#000000] font-mono font-bold px-8 py-3.5 rounded-full text-xs uppercase tracking-wider transition-all duration-200 cursor-pointer shadow-2xs hover:scale-[1.02]"
          >
            <span>WATCH DEMO</span>
          </button>
        </div>
      </div>

      {/* Industrial Robotic Arm & Laptop Telemetry Illustration (Matching Reference Image) */}
      <div className="max-w-6xl mx-auto mt-12 sm:mt-16 relative flex justify-end">
        <div className="w-full sm:w-[460px] md:w-[500px] relative transition-transform hover:scale-[1.01] duration-300">
          {/* Base shadow pill in soft lime */}
          <div className="absolute -bottom-3 right-4 left-10 h-6 bg-[#d4f658]/40 rounded-full blur-xs pointer-events-none" />

          {/* Stylized Vector SVG matching reference layout with laptop & dual robotic arms */}
          <svg viewBox="0 0 520 280" className="w-full h-auto drop-shadow-md select-none">
            <defs>
              {/* Screen gradient */}
              <linearGradient id="screenGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#ffffff" />
                <stop offset="100%" stopColor="#f8f9fa" />
              </linearGradient>
              <linearGradient id="armGrad1" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#868e96" />
                <stop offset="100%" stopColor="#adb5bd" />
              </linearGradient>
              <linearGradient id="armGrad2" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#74c0fc" />
                <stop offset="100%" stopColor="#38d9a9" />
              </linearGradient>
              <linearGradient id="neonJoint" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#d4f658" />
                <stop offset="100%" stopColor="#b3d338" />
              </linearGradient>
            </defs>

            {/* Ground Plane platform */}
            <ellipse cx="280" cy="255" rx="200" ry="12" fill="#cff053" opacity="0.8" />

            {/* Laptop Base */}
            <path d="M 120 248 L 410 248 L 440 255 L 90 255 Z" fill="#555a60" />
            <path d="M 125 248 L 405 248 L 400 250 L 130 250 Z" fill="#868e96" />

            {/* Laptop Screen Frame (Open angled) */}
            <rect x="135" y="60" width="270" height="185" rx="10" fill="#2b2d31" stroke="#495057" strokeWidth="3" />
            
            {/* Screen Inner Display */}
            <rect x="145" y="70" width="250" height="165" rx="6" fill="url(#screenGrad)" />

            {/* Display Top Bar */}
            <rect x="145" y="70" width="250" height="22" rx="6" fill="#edeeef" />
            <circle cx="160" cy="81" r="3.5" fill="#adb5bd" />
            <circle cx="172" cy="81" r="3.5" fill="#adb5bd" />
            <circle cx="184" cy="81" r="3.5" fill="#adb5bd" />
            <text x="200" y="85" fontFamily="JetBrains Mono" fontSize="9" fill="#757964" fontWeight="bold">JANE-SCADA // T-408</text>
            <rect x="330" y="75" width="55" height="12" rx="6" fill="#d4f658" />
            <text x="338" y="84" fontFamily="JetBrains Mono" fontSize="7.5" fill="#000000" fontWeight="bold">● LIVE</text>

            {/* Display Telemetry Data Bars */}
            <rect x="160" y="105" width="70" height="10" rx="5" fill="#38d9a9" opacity="0.9" />
            <rect x="160" y="122" width="95" height="10" rx="5" fill="#38d9a9" opacity="0.9" />
            <rect x="160" y="139" width="60" height="10" rx="5" fill="#38d9a9" opacity="0.9" />

            {/* Mini Chart Graphic on right screen */}
            <rect x="275" y="102" width="105" height="52" rx="6" fill="#ffffff" stroke="#E2E4E6" strokeWidth="1.5" />
            <path d="M 285 140 L 300 132 L 315 138 L 330 120 L 345 125 L 360 112 L 372 118" fill="none" stroke="#006df8" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
            <circle cx="360" cy="112" r="3" fill="#ad1e7a" />

            {/* Display Diagnostic Log Card */}
            <rect x="160" y="165" width="220" height="58" rx="6" fill="#f3f4f5" stroke="#E2E4E6" strokeWidth="1" />
            <rect x="170" y="175" width="12" height="12" rx="3" fill="#d4f658" />
            <path d="M 173 181 L 176 184 L 180 177" fill="none" stroke="#000000" strokeWidth="1.5" />
            <text x="190" y="184" fontFamily="JetBrains Mono" fontSize="9" fill="#191c1d" fontWeight="600">Turbine Bearing 04 Normal</text>
            <text x="170" y="204" fontFamily="JetBrains Mono" fontSize="8" fill="#757964">Telemetry Stream: 2.4 GB/s • 0 Packet Loss</text>
            <text x="170" y="215" fontFamily="JetBrains Mono" fontSize="8" fill="#006df8">Autonomous Root-Cause Scan Complete</text>

            {/* Left Robotic Arm with Joints & Calibrator */}
            <g className="transition-all duration-300">
              {/* Base joint */}
              <circle cx="95" cy="245" r="14" fill="#6c757d" stroke="#495057" strokeWidth="2" />
              <circle cx="95" cy="245" r="6" fill="url(#neonJoint)" />
              {/* Lower arm segment */}
              <path d="M 95 245 L 80 145" stroke="#868e96" strokeWidth="16" strokeLinecap="round" />
              <path d="M 95 245 L 80 145" stroke="#adb5bd" strokeWidth="8" strokeLinecap="round" />
              {/* Elbow joint */}
              <circle cx="80" cy="145" r="12" fill="#495057" />
              <circle cx="80" cy="145" r="5" fill="url(#neonJoint)" />
              {/* Forearm segment reaching over laptop */}
              <path d="M 80 145 L 175 155" stroke="#868e96" strokeWidth="12" strokeLinecap="round" />
              <path d="M 80 145 L 175 155" stroke="#ced4da" strokeWidth="6" strokeLinecap="round" />
              {/* Wrist joint */}
              <circle cx="175" cy="155" r="9" fill="#343a40" />
              <circle cx="175" cy="155" r="4" fill="url(#neonJoint)" />
              {/* Micro sensor probe tip with spark/laser */}
              <path d="M 175 155 L 195 160" stroke="#343a40" strokeWidth="4" strokeLinecap="round" />
              <circle cx="197" cy="161" r="3" fill="#ad1e7a" />
              <path d="M 197 161 L 210 168" stroke="#38d9a9" strokeWidth="2" strokeDasharray="2,2" />
            </g>

            {/* Right Robotic Arm with Joint Overhang */}
            <g className="transition-all duration-300">
              {/* Right base joint */}
              <circle cx="450" cy="248" r="14" fill="#6c757d" stroke="#495057" strokeWidth="2" />
              <circle cx="450" cy="248" r="6" fill="url(#neonJoint)" />
              {/* Right arm segment up */}
              <path d="M 450 248 L 420 135" stroke="#868e96" strokeWidth="14" strokeLinecap="round" />
              <path d="M 450 248 L 420 135" stroke="#adb5bd" strokeWidth="7" strokeLinecap="round" />
              {/* Right elbow */}
              <circle cx="420" cy="135" r="11" fill="#495057" />
              <circle cx="420" cy="135" r="4.5" fill="url(#neonJoint)" />
              {/* Arm reaching over screen top right */}
              <path d="M 420 135 L 340 148" stroke="#868e96" strokeWidth="10" strokeLinecap="round" />
              <path d="M 420 135 L 340 148" stroke="#ced4da" strokeWidth="5" strokeLinecap="round" />
              {/* Calibration clamp */}
              <circle cx="340" cy="148" r="8" fill="#343a40" />
              <circle cx="340" cy="148" r="3" fill="url(#neonJoint)" />
              <path d="M 334 142 L 324 148 L 334 154" fill="none" stroke="#2b2d31" strokeWidth="3" strokeLinecap="round" />
            </g>
          </svg>
        </div>
      </div>
    </section>
  );
};


