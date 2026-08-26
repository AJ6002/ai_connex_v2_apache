import React, { useState } from 'react';
import { Sparkles, CheckCircle2, ArrowRight, ShieldCheck, Zap, Server, Activity } from 'lucide-react';

export const DovetailInspiredWorkflow: React.FC = () => {
  const [activeStep, setActiveStep] = useState<number>(0);

  const steps = [
    {
      id: 0,
      stepNumber: "01",
      title: "Stream & Unify",
      tagline: "Ingest any industrial protocol without data pipelines breaking.",
      description: "Connect SCADA, OPC-UA, MQTT Sparkplug, and historians with zero-copy Apache DataFusion. Jane instantly normalizes diverse industrial schemas into a single governed time-series fabric.",
      features: [
        "Zero ETL setup with auto-discovery of PLC tag trees",
        "Edge caching prevents packet drops during plant network outages",
        "Sub-millisecond serialization on high-frequency vibration streams"
      ],
      previewType: "stream"
    },
    {
      id: 1,
      stepNumber: "02",
      title: "Analyze & Detect",
      tagline: "Unsupervised spatial-temporal models tuned to physical machinery.",
      description: "Generic ML fails in heavy industry. Jane combines thermodynamic constraints with unsupervised deep learning to isolate bearing micro-cracks, cavitation, and thermal degradation 72 hours before catastrophic failure.",
      features: [
        "Fourier transform (FFT) harmonics decomposition",
        "Dynamic baseline adaptation for ambient temperature shifts",
        "Continuous fleet-wide anomaly correlation"
      ],
      previewType: "analyze"
    },
    {
      id: 2,
      stepNumber: "03",
      title: "Synthesize with Jane",
      tagline: "Conversational root-cause diagnosis over complex engineering context.",
      description: "Ask Jane why an asset is behaving abnormally. Jane instantly cross-references live waveforms with OEM mechanical manuals, P&IDs, and 10 years of technician maintenance records.",
      features: [
        "Natural language mechanical diagnostic reasoning",
        "Interactive schematic pinpointing exact component failure points",
        "Precision severity scoring with probability confidence intervals"
      ],
      previewType: "jane"
    },
    {
      id: 3,
      stepNumber: "04",
      title: "Automate & Resolve",
      tagline: "Closed-loop work orders and telemetry verification.",
      description: "Move directly from detection to resolution. Jane automatically generates structured SAP PM / IBM Maximo work orders, reserves required spare parts, and verifies telemetry post-repair.",
      features: [
        "Automated work order creation with technician checklists",
        "Spare part inventory matching and tool requirement dispatch",
        "Autonomous closed-loop health validation before closing tickets"
      ],
      previewType: "resolve"
    }
  ];

  const current = steps[activeStep];

  return (
    <section className="py-16 sm:py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-[#E5E5E1]">
      {/* Header */}
      <div className="text-center max-w-3xl mx-auto mb-14">
        <div className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-[#6B6B6B] font-mono mb-3">
          <span className="w-2 h-2 rounded-full bg-[#1A1A1A]" />
          <span>DOVETAIL-INSPIRED WORKFLOW ARCHITECTURE</span>
        </div>
        <h2 className="text-3xl sm:text-5xl font-bold text-[#1A1A1A] tracking-tight leading-tight">
          How industrial teams run on AIConneX
        </h2>
        <p className="mt-4 text-[#6B6B6B] text-base sm:text-lg">
          A seamless 4-step continuum from physical telemetry ingestion to closed-loop resolution.
        </p>
      </div>

      {/* Step Tabs Navigation (Dovetail style segmented bar) */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-10">
        {steps.map((step) => (
          <button
            key={step.id}
            onClick={() => setActiveStep(step.id)}
            className={`p-4 rounded-2xl border text-left transition-all duration-200 cursor-pointer ${
              activeStep === step.id
                ? 'bg-[#1A1A1A] border-[#1A1A1A] text-white shadow-xs'
                : 'bg-white border-[#E5E5E1] text-[#6B6B6B] hover:border-[#1A1A1A]'
            }`}
          >
            <div className={`text-[11px] font-mono font-bold ${activeStep === step.id ? 'text-[#EEEBE5]' : 'text-[#A1A19A]'}`}>
              STEP {step.stepNumber}
            </div>
            <div className={`text-sm sm:text-base font-bold mt-1 ${activeStep === step.id ? 'text-white' : 'text-[#1A1A1A]'}`}>
              {step.title}
            </div>
          </button>
        ))}
      </div>

      {/* Active Step Deep Dive Card */}
      <div className="bg-white border border-[#E5E5E1] rounded-3xl p-6 sm:p-10 shadow-sm grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        {/* Left Explanation Column */}
        <div className="lg:col-span-6 space-y-5">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-bold bg-[#EEEBE5] text-[#1A1A1A]">
            <span>STEP {current.stepNumber} // {current.title.toUpperCase()}</span>
          </div>

          <h3 className="text-2xl sm:text-3xl font-bold text-[#1A1A1A] tracking-tight">
            {current.tagline}
          </h3>

          <p className="text-[#6B6B6B] text-base leading-relaxed">
            {current.description}
          </p>

          <div className="space-y-3 pt-2">
            {current.features.map((feat, fIdx) => (
              <div key={fIdx} className="flex items-start gap-3 text-sm text-[#1A1A1A]">
                <div className="p-1 rounded-full bg-[#EEEBE5] text-[#1A1A1A] mt-0.5 shrink-0">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                </div>
                <span>{feat}</span>
              </div>
            ))}
          </div>

          <div className="pt-4 flex items-center gap-3">
            <button
              onClick={() => setActiveStep((prev) => (prev + 1) % steps.length)}
              className="inline-flex items-center gap-2 bg-[#EEEBE5] hover:bg-[#E5E5E1] text-[#1A1A1A] text-xs font-bold uppercase tracking-wider px-5 py-2.5 rounded-full transition cursor-pointer"
            >
              <span>Next Step: {steps[(activeStep + 1) % steps.length].title}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Right Interactive Visual Graphic */}
        <div className="lg:col-span-6 bg-[#1A1A1A] rounded-2xl p-5 sm:p-6 text-[#EEEBE5] font-mono text-xs border border-[#333333] shadow-xl relative overflow-hidden">
          {/* Visual Header */}
          <div className="flex items-center justify-between pb-3 border-b border-[#333333] mb-4">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-[#555555]" />
              <span className="w-2.5 h-2.5 rounded-full bg-[#777777]" />
              <span className="w-2.5 h-2.5 rounded-full bg-[#999999]" />
              <span className="text-[11px] text-[#A1A19A] ml-2">AICONNEX_ENGINE // {current.title.toUpperCase()}</span>
            </div>
            <span className="text-[10px] text-white bg-[#333333] px-2 py-0.5 rounded">
              REALTIME PIPELINE
            </span>
          </div>

          {/* Dynamic Content */}
          {current.previewType === 'stream' && (
            <div className="space-y-3">
              <div className="p-3 bg-[#111111] rounded-xl border border-[#2A2A2A] flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Server className="w-4 h-4 text-[#EEEBE5]" />
                  <div>
                    <div className="text-white font-bold text-xs">OPC-UA Edge Node #08</div>
                    <div className="text-[10px] text-[#A1A19A]">Turbine Fleet Plant Alpha</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-white font-bold">120,400 msg/s</div>
                  <div className="text-[10px] text-[#A1A19A]">0.2ms latency</div>
                </div>
              </div>

              <div className="p-3 bg-[#111111] rounded-xl border border-[#2A2A2A] flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Activity className="w-4 h-4 text-[#EEEBE5]" />
                  <div>
                    <div className="text-white font-bold text-xs">SCADA Historian Relay</div>
                    <div className="text-[10px] text-[#A1A19A]">Boiler & Steam Pressure</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-white font-bold">48,200 msg/s</div>
                  <div className="text-[10px] text-[#A1A19A]">Zero duplicate buffer</div>
                </div>
              </div>

              <div className="bg-[#2A2A2A] p-2.5 rounded-lg text-[11px] text-[#EEEBE5] flex items-center gap-2">
                <Zap className="w-4 h-4 text-white shrink-0" />
                <span>Zero-copy memory pool active. CPU utilization: 1.4%.</span>
              </div>
            </div>
          )}

          {current.previewType === 'analyze' && (
            <div className="space-y-3">
              <div className="bg-[#111111] p-4 rounded-xl border border-[#2A2A2A]">
                <div className="flex justify-between items-center text-[#A1A19A] text-[11px] mb-2">
                  <span>SPECTRAL FFT ANALYSIS // BEARING_RACETRACK</span>
                  <span className="text-white">Harmonic Peak: 142 Hz</span>
                </div>
                {/* Visual waveform bars */}
                <div className="flex items-end gap-1.5 h-16 pt-2">
                  {[20, 25, 30, 22, 28, 45, 75, 95, 88, 55, 35, 25, 20, 18, 15, 12].map((v, i) => (
                    <div
                      key={i}
                      className={`flex-1 rounded-t-xs ${
                        i >= 6 && i <= 8 ? 'bg-white' : 'bg-[#555555]'
                      }`}
                      style={{ height: `${v}%` }}
                    />
                  ))}
                </div>
              </div>
              <div className="text-white text-[11px] bg-[#222222] p-2.5 rounded-lg border border-[#333333] flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 shrink-0 text-white" />
                <span>Spatial model confidence: 99.4% (Early micro-spall detected)</span>
              </div>
            </div>
          )}

          {current.previewType === 'jane' && (
            <div className="space-y-2.5">
              <div className="bg-[#111111] p-3 rounded-xl border border-[#2A2A2A]">
                <div className="text-[10px] text-[#A1A19A] uppercase">User Query:</div>
                <div className="text-white mt-1 font-sans text-xs">
                  "Jane, why is Compressor 4 head temperature trending 8% above normal?"
                </div>
              </div>

              <div className="bg-[#222222] p-3.5 rounded-xl border border-[#333333] space-y-2">
                <div className="flex items-center gap-2 text-white font-bold text-[11px]">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Jane Diagnostic Assessment</span>
                </div>
                <p className="text-[#EEEBE5] text-[11px] font-sans leading-relaxed">
                  Correlation with intake valve discharge telemetry indicates partial bypass leakage. Thermal degradation is progressing at 0.14°C/hr.
                </p>
                <div className="text-[10px] text-[#A1A19A] pt-1 border-t border-[#333333]">
                  Recommended Action: Replace Valve Seal Kit #VK-409 within 48 operational hours.
                </div>
              </div>
            </div>
          )}

          {current.previewType === 'resolve' && (
            <div className="space-y-3">
              <div className="p-3 bg-[#111111] rounded-xl border border-[#2A2A2A] space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-[#A1A19A] text-[10px]">ERP WORK ORDER CREATED</span>
                  <span className="text-white font-bold text-[10px]">#SAP-WO-84920</span>
                </div>
                <div className="text-white font-bold text-xs font-sans">
                  Scheduled Replacement: Stage 2 Bypass Valve Seal
                </div>
                <div className="grid grid-cols-2 gap-2 pt-1 text-[10px] text-[#A1A19A]">
                  <div>Assigned: Mechanical Crew #4</div>
                  <div>Parts: 2x Seal Rings Reserved</div>
                </div>
              </div>

              <div className="bg-[#222222] border border-[#333333] p-2.5 rounded-lg text-[11px] text-white flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0 text-white" />
                <span>Autonomous telemetry monitoring armed for post-repair signoff.</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
};

