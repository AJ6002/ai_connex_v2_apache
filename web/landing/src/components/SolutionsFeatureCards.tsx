import React, { useState } from 'react';
import { ArrowUpRight, CheckCircle2 } from 'lucide-react';

interface SolutionsFeatureCardsProps {
  onLearnMore: (featureName: string) => void;
}

export const SolutionsFeatureCards: React.FC<SolutionsFeatureCardsProps> = ({ onLearnMore }) => {
  const [activeCard, setActiveCard] = useState<number>(0);

  const features = [
    {
      id: 1,
      tag: "FEATURE 01 // INGESTION",
      title: "Neuron Ingestion Engine",
      subtitle: "Zero-copy streaming from SCADA, OPC-UA, and historians without duplicate storage.",
      stats: "500k+ msg/sec",
      statLabel: "Zero-Copy Throughput",
      badgeColor: "bg-[#EEEBE5] text-[#1A1A1A]",
      bullets: [
        "Direct Apache DataFusion integration bypassing cloud serialization overhead",
        "Unified schema normalization across legacy Modbus, Profinet, and modern MQTT",
        "Edge-buffer failover for intermittent industrial plant network connectivity"
      ]
    },
    {
      id: 2,
      tag: "FEATURE 02 // PREDICTIVE ML",
      title: "Predictive Anomaly Detection",
      subtitle: "Unsupervised spatial-temporal models forecasting machine failures 72 hours ahead.",
      stats: "72 Hours",
      statLabel: "Pre-Failure Lead Time",
      badgeColor: "bg-[#EEEBE5] text-[#1A1A1A]",
      bullets: [
        "Continuous multi-variate vibration FFT & thermal degradation correlation",
        "Auto-adaptive baseline thresholds that dynamically adjust for seasonal plant load",
        "Zero false-positive suppression via automated signal filtering"
      ]
    },
    {
      id: 3,
      tag: "FEATURE 03 // JANE COPILOT",
      title: "Conversational Root Cause Analysis",
      subtitle: "Jane reasons across telemetry waveforms, OEM equipment manuals, and P&ID schematics.",
      stats: "99.4%",
      statLabel: "Diagnosis Accuracy",
      badgeColor: "bg-[#EEEBE5] text-[#1A1A1A]",
      bullets: [
        "Ask plain-English queries like 'Why did Pump 3 discharge pressure drop at 14:00?'",
        "Instant cross-reference with 10+ years of historical technician repair logs",
        "Generates step-by-step mechanical remediation checklists with torque specs"
      ]
    },
    {
      id: 4,
      tag: "FEATURE 04 // CLOSED-LOOP ORCHESTRATION",
      title: "Autonomous Dispatch & Action",
      subtitle: "Close the loop with instant CMMS integration, SAP PM work orders, and field routing.",
      stats: "< 30 Sec",
      statLabel: "Automated Dispatch Time",
      badgeColor: "bg-[#EEEBE5] text-[#1A1A1A]",
      bullets: [
        "Native two-way synchronization with SAP PM, IBM Maximo, and ServiceNow",
        "Automated spare part inventory reservation and technician skill-matching",
        "Closed-loop telemetry verification post-repair before closing work tickets"
      ]
    }
  ];

  return (
    <section id="solutions-features" className="py-16 sm:py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-[#E5E5E1]">
      {/* Section Header */}
      <div className="max-w-3xl mb-14">
        <div className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-[#6B6B6B] font-mono mb-3">
          <span className="w-2 h-2 rounded-full bg-[#1A1A1A]" />
          <span>SOLUTIONS & DATA ARCHITECTURE</span>
        </div>
        <h2 className="text-3xl sm:text-5xl font-bold text-[#1A1A1A] tracking-tight leading-tight">
          Engineered for the physical world. Built for mission-critical scale.
        </h2>
        <p className="mt-4 text-[#6B6B6B] text-base sm:text-lg">
          Explore the 4 core pillars that turn raw industrial noise into high-confidence predictive maintenance decisions.
        </p>
      </div>

      {/* 4 Feature Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {features.map((feat, idx) => (
          <div
            key={feat.id}
            id={`solution-card-${feat.id}`}
            onMouseEnter={() => setActiveCard(idx)}
            className={`rounded-3xl p-7 sm:p-8 border transition-all duration-300 relative flex flex-col justify-between ${
              activeCard === idx
                ? 'bg-white border-[#1A1A1A] shadow-md scale-[1.01]'
                : 'bg-white border-[#E5E5E1] hover:border-[#1A1A1A] shadow-2xs'
            }`}
          >
            <div>
              {/* Card Top Pill & Stat */}
              <div className="flex items-center justify-between gap-4 mb-6">
                <span className={`text-[11px] font-mono font-bold px-3 py-1 rounded-full ${feat.badgeColor}`}>
                  {feat.tag}
                </span>
                <div className="text-right">
                  <div className="text-lg font-bold font-mono text-[#1A1A1A]">{feat.stats}</div>
                  <div className="text-[10px] uppercase font-mono text-[#6B6B6B]">{feat.statLabel}</div>
                </div>
              </div>

              {/* Title & Subtitle */}
              <h3 className="text-xl sm:text-2xl font-bold text-[#1A1A1A] tracking-tight mb-3">
                {feat.title}
              </h3>
              <p className="text-[#6B6B6B] text-sm sm:text-base leading-relaxed mb-6">
                {feat.subtitle}
              </p>

              {/* Bullet Points */}
              <ul className="space-y-2.5 mb-8">
                {feat.bullets.map((bullet, bIdx) => (
                  <li key={bIdx} className="flex items-start gap-2.5 text-xs sm:text-sm text-[#1A1A1A]">
                    <CheckCircle2 className="w-4 h-4 text-[#1A1A1A] shrink-0 mt-0.5" />
                    <span>{bullet}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Bottom Card Action */}
            <div className="pt-4 border-t border-[#E5E5E1] flex items-center justify-between">
              <button
                onClick={() => onLearnMore(feat.title)}
                className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-[#1A1A1A] hover:opacity-75 transition cursor-pointer group"
              >
                <span>Deep Dive Architecture</span>
                <ArrowUpRight className="w-4 h-4 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
              </button>
              <span className="text-[11px] font-mono text-[#A1A19A]">0{feat.id} / 04</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};

