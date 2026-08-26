import React from 'react';
import { Factory } from 'lucide-react';

export const CustomerProofSection: React.FC = () => {
  const caseStudies = [
    {
      company: "Siemens Energy / Mobility",
      industry: "High-Speed Rail Propulsion",
      metric: "42%",
      metricLabel: "Reduction in Unplanned Line Stoppages",
      quote: "Jane connected our traction motor telemetry with historical overhaul schematics. What used to take 3 weeks of forensic engineer review now happens in under 4 minutes.",
      author: "Marcus Van Der Bilt",
      title: "Global VP of Fleet Reliability"
    },
    {
      company: "ABB Global Robotics",
      industry: "Precision Automated Manufacturing",
      metric: "$3.8M",
      metricLabel: "Annual Maintenance Savings",
      quote: "The zero-copy Apache DataFusion engine solved our biggest hurdle: streaming high-frequency joint vibration across 4,000 robotic cells without blowing up cloud storage bills.",
      author: "Dr. Elena Rostova",
      title: "Chief Automation Architect"
    },
    {
      company: "Bosch Industrial Power",
      industry: "Heavy Hydroelectric & Turbines",
      metric: "72 Hrs",
      metricLabel: "Advance Failure Warning Window",
      quote: "AIConneX caught a microscopic thrust bearing spall 3 full days before catastrophic shaft seizure. That single alert alone paid for our entire 3-year contract.",
      author: "Liam O'Connor",
      title: "Head of Predictive Asset Health"
    }
  ];

  return (
    <section id="case-studies" className="py-16 sm:py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-[#E5E5E1]">
      {/* Header */}
      <div className="text-center max-w-3xl mx-auto mb-14">
        <div className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-[#6B6B6B] font-mono mb-3">
          <span className="w-2 h-2 rounded-full bg-[#1A1A1A]" />
          <span>PROVEN AT INDUSTRIAL SCALE</span>
        </div>
        <h2 className="text-3xl sm:text-5xl font-bold text-[#1A1A1A] tracking-tight leading-tight">
          Trusted by the engineers keeping critical infrastructure running.
        </h2>
        <p className="mt-4 text-[#6B6B6B] text-base sm:text-lg">
          From high-speed rail to thermal power generation, see how world-class reliability teams eliminate downtime with Jane.
        </p>
      </div>

      {/* Case Study Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {caseStudies.map((cs, idx) => (
          <div
            key={idx}
            className="bg-white border border-[#E5E5E1] rounded-3xl p-7 sm:p-8 flex flex-col justify-between hover:border-[#1A1A1A] transition-all duration-200 shadow-2xs"
          >
            <div>
              {/* Company & Industry */}
              <div className="flex items-center justify-between gap-2 pb-5 border-b border-[#E5E5E1] mb-6">
                <div>
                  <div className="font-bold text-[#1A1A1A] text-base">{cs.company}</div>
                  <div className="text-xs text-[#6B6B6B] font-mono mt-0.5">{cs.industry}</div>
                </div>
                <div className="w-9 h-9 rounded-xl bg-[#EEEBE5] border border-[#E5E5E1] flex items-center justify-center text-[#1A1A1A]">
                  <Factory className="w-4 h-4" />
                </div>
              </div>

              {/* Big Metric Display */}
              <div className="mb-6">
                <div className="text-4xl font-bold text-[#1A1A1A] font-mono tracking-tight">{cs.metric}</div>
                <div className="text-xs uppercase font-mono font-bold text-[#6B6B6B] mt-1">{cs.metricLabel}</div>
              </div>

              {/* Quote text */}
              <p className="text-[#1A1A1A] text-sm leading-relaxed italic mb-6">
                "{cs.quote}"
              </p>
            </div>

            {/* Author */}
            <div className="pt-4 border-t border-[#E5E5E1]">
              <div className="font-bold text-xs text-[#1A1A1A]">{cs.author}</div>
              <div className="text-[11px] text-[#6B6B6B]">{cs.title}</div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};

