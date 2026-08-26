import React, { useState } from 'react';
import { ArrowUpRight, Calculator, Check } from 'lucide-react';

interface RoiCalculatorProps {
  onScheduleReview: () => void;
}

export const RoiCalculator: React.FC<RoiCalculatorProps> = ({ onScheduleReview }) => {
  const [assetCount, setAssetCount] = useState<number>(45);
  const [hourlyDowntimeCost, setHourlyDowntimeCost] = useState<number>(14000);
  const [annualOutages, setAnnualOutages] = useState<number>(12);
  const avgHoursPerOutage = 6.5;

  // Math: 
  // Baseline downtime hours = annualOutages * avgHoursPerOutage
  // Baseline total downtime cost = baseline hours * hourlyDowntimeCost
  // AIConneX reduces unplanned outages by 68% and MTTR by 45%
  const baselineHours = annualOutages * avgHoursPerOutage;
  
  const savedHours = Math.round(baselineHours * 0.68);
  const annualDollarSavings = Math.round(savedHours * hourlyDowntimeCost);
  const roiMultiplier = Math.round((annualDollarSavings / (assetCount * 4500)) * 10) / 10;

  return (
    <section id="roi-calculator" className="py-16 sm:py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-[#E5E5E1]">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
        {/* Left Explanation */}
        <div className="lg:col-span-5 space-y-5">
          <div className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-[#6B6B6B] font-mono">
            <span className="w-2 h-2 rounded-full bg-[#1A1A1A]" />
            <span>FINANCIAL & OPERATIONAL IMPACT</span>
          </div>

          <h2 className="text-3xl sm:text-5xl font-bold text-[#1A1A1A] tracking-tight leading-tight">
            Calculate your downtime savings in seconds.
          </h2>

          <p className="text-[#6B6B6B] text-base leading-relaxed">
            Unplanned equipment outages cost global industrial operators billions annually. See how much maintenance budget and production uptime AIConneX recovers for your specific plant profile.
          </p>

          <div className="space-y-3 pt-2">
            <div className="flex items-center gap-2.5 text-sm text-[#1A1A1A] font-medium">
              <Check className="w-4 h-4 text-[#1A1A1A] shrink-0" />
              <span>Validated across 44,000+ monitored industrial machines</span>
            </div>
            <div className="flex items-center gap-2.5 text-sm text-[#1A1A1A] font-medium">
              <Check className="w-4 h-4 text-[#1A1A1A] shrink-0" />
              <span>Zero hardware replacement needed (uses existing SCADA)</span>
            </div>
            <div className="flex items-center gap-2.5 text-sm text-[#1A1A1A] font-medium">
              <Check className="w-4 h-4 text-[#1A1A1A] shrink-0" />
              <span>Average payback period: under 4.2 months</span>
            </div>
          </div>
        </div>

        {/* Right Interactive Calculator Box */}
        <div className="lg:col-span-7 bg-white border border-[#E5E5E1] rounded-3xl p-6 sm:p-8 shadow-sm">
          <div className="flex items-center justify-between pb-4 border-b border-[#E5E5E1] mb-6">
            <div className="flex items-center gap-2 text-[#1A1A1A] font-bold text-base">
              <Calculator className="w-5 h-5 text-[#1A1A1A]" />
              <span>Industrial Downtime Simulator</span>
            </div>
            <span className="text-[11px] font-mono font-bold bg-[#EEEBE5] text-[#1A1A1A] px-2.5 py-1 rounded-full">
              LIVE MATH
            </span>
          </div>

          {/* Sliders */}
          <div className="space-y-6 mb-8">
            {/* Slider 1: Monitored Industrial Assets */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-mono font-bold">
                <span className="text-[#6B6B6B]">CRITICAL ASSET FLEET SIZE</span>
                <span className="text-[#1A1A1A] text-sm font-bold">{assetCount} Machines</span>
              </div>
              <input
                type="range"
                min="10"
                max="250"
                step="5"
                value={assetCount}
                onChange={(e) => setAssetCount(Number(e.target.value))}
                className="w-full h-2 bg-[#E5E5E1] rounded-lg appearance-none cursor-pointer accent-[#1A1A1A]"
              />
              <div className="flex justify-between text-[10px] text-[#A1A19A] font-mono">
                <span>10 units</span>
                <span>250 units</span>
              </div>
            </div>

            {/* Slider 2: Average Downtime Cost per Hour */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-mono font-bold">
                <span className="text-[#6B6B6B]">HOURLY DOWNTIME COST ($)</span>
                <span className="text-[#1A1A1A] text-sm font-bold">${hourlyDowntimeCost.toLocaleString()} / hr</span>
              </div>
              <input
                type="range"
                min="2000"
                max="50000"
                step="1000"
                value={hourlyDowntimeCost}
                onChange={(e) => setHourlyDowntimeCost(Number(e.target.value))}
                className="w-full h-2 bg-[#E5E5E1] rounded-lg appearance-none cursor-pointer accent-[#1A1A1A]"
              />
              <div className="flex justify-between text-[10px] text-[#A1A19A] font-mono">
                <span>$2,000/hr</span>
                <span>$50,000/hr</span>
              </div>
            </div>

            {/* Slider 3: Current Unplanned Outages / Year */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-mono font-bold">
                <span className="text-[#6B6B6B]">CURRENT UNPLANNED OUTAGES / YR</span>
                <span className="text-[#1A1A1A] text-sm font-bold">{annualOutages} Incidents</span>
              </div>
              <input
                type="range"
                min="2"
                max="40"
                step="1"
                value={annualOutages}
                onChange={(e) => setAnnualOutages(Number(e.target.value))}
                className="w-full h-2 bg-[#E5E5E1] rounded-lg appearance-none cursor-pointer accent-[#1A1A1A]"
              />
              <div className="flex justify-between text-[10px] text-[#A1A19A] font-mono">
                <span>2 outages</span>
                <span>40 outages</span>
              </div>
            </div>
          </div>

          {/* Results Outcome Box */}
          <div className="bg-[#1A1A1A] text-white rounded-2xl p-5 sm:p-6 space-y-4 border border-[#333333]">
            <div className="text-[11px] font-mono text-[#EEEBE5] uppercase font-bold tracking-widest">
              ESTIMATED ANNUAL VALUE RECOVERY
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <div className="text-xs text-[#A1A19A] font-mono">Direct Cost Avoidance</div>
                <div className="text-3xl sm:text-4xl font-bold text-white font-mono mt-1">
                  ${annualDollarSavings.toLocaleString()}
                </div>
                <div className="text-[11px] text-[#EEEBE5] font-mono mt-1">
                  + {roiMultiplier}x Estimated ROI
                </div>
              </div>

              <div>
                <div className="text-xs text-[#A1A19A] font-mono">Recovered Production Uptime</div>
                <div className="text-3xl sm:text-4xl font-bold text-white font-mono mt-1">
                  {savedHours} Hours
                </div>
                <div className="text-[11px] text-[#EEEBE5] font-mono mt-1">
                  68% reduction in outages
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-[#333333] flex flex-col sm:flex-row items-center justify-between gap-3">
              <span className="text-xs text-[#A1A19A]">
                Want an audited engineering business case?
              </span>
              <button
                id="roi-schedule-review-btn"
                onClick={onScheduleReview}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-1.5 bg-[#EEEBE5] hover:bg-[#E5E5E1] text-[#1A1A1A] font-bold px-5 py-2.5 rounded-full text-xs uppercase tracking-wider transition cursor-pointer"
              >
                <span>Request Custom Audit</span>
                <ArrowUpRight className="w-3.5 h-3.5 stroke-[2.5]" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

