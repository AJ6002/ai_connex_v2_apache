import React, { useState } from 'react';
import { Send, Bot, Sparkles, AlertTriangle, Wrench } from 'lucide-react';

interface PresetPrompt {
  id: string;
  query: string;
  category: string;
  asset: string;
  summary: string;
  rootCause: string;
  probability: string;
  leadTime: string;
  checklist: string[];
}

export const AskJaneInteractive: React.FC = () => {
  const presetPrompts: PresetPrompt[] = [
    {
      id: 'vibe-turbine',
      query: "Why did Turbine 4 spike in vibration at 14:02 today?",
      category: "Vibration FFT Drift",
      asset: "Siemens SGT-800 Gas Turbine #04",
      summary: "Harmonic analysis indicates high-frequency inner raceway defect on the thrust bearing assembly.",
      rootCause: "Sub-surface raceway spalling exacerbated by a 4°C lube oil thermal surge during peak load dispatch.",
      probability: "98.7% Confidence",
      leadTime: "72 Hours to Threshold Trip",
      checklist: [
        "Inspect lube oil filter delta-P and flow rate sensor #FT-301",
        "Perform optical borescope inspection of thrust bearing race",
        "Retorque bearing housing mount bolts to 320 Nm per OEM spec M-88"
      ]
    },
    {
      id: 'boiler-pressure',
      query: "Analyze steam boiler pressure anomalies in Plant Alpha",
      category: "Pressure Fluctuation",
      asset: "Industrial Superheater Boiler #02",
      summary: "Cyclic 12 PSI oscillations correlated with intermittent feedwater valve stem sticking.",
      rootCause: "Valve actuator diaphragm micro-leakage causing sluggish modulation under 45 bar header pressure.",
      probability: "96.2% Confidence",
      leadTime: "120 Hours to Pressure Relief",
      checklist: [
        "Test pneumatic actuator air supply pressure (target 6.2 bar)",
        "Inspect stem packing gland for overtightening or crystallization",
        "Calibrate digital valve positioner feedback 4-20mA loop"
      ]
    },
    {
      id: 'hydraulic-pump',
      query: "Check hydraulic cavitation risk on forging press pump",
      category: "Cavitation Risk",
      asset: "Rexroth Variable Displacement Pump #09",
      summary: "Acoustic ultrasonic signature shows micro-bubble collapse in the suction port assembly.",
      rootCause: "Partial clogging of suction strainer basket combined with elevated oil viscosity at cold startup.",
      probability: "94.5% Confidence",
      leadTime: "36 Hours to Impeller Erosion",
      checklist: [
        "Backflush suction strainer and verify intake pressure > -0.2 bar",
        "Check hydraulic reservoir oil temperature interlock (min 38°C)",
        "Sample fluid for ISO 4406 particulate cleanliness level"
      ]
    }
  ];

  const [selectedPrompt, setSelectedPrompt] = useState<PresetPrompt>(presetPrompts[0]);
  const [customInput, setCustomInput] = useState<string>('');
  const [isThinking, setIsThinking] = useState<boolean>(false);

  const handleSelectPrompt = (prompt: PresetPrompt) => {
    setIsThinking(true);
    setSelectedPrompt(prompt);
    setTimeout(() => {
      setIsThinking(false);
    }, 400);
  };

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customInput.trim()) return;
    setIsThinking(true);
    // Generate a contextual diagnosis for custom input
    setTimeout(() => {
      setSelectedPrompt({
        id: 'custom',
        query: customInput,
        category: "Custom Anomaly Diagnostic",
        asset: "Enterprise Monitored Asset // Auto-Discovered Tag",
        summary: `Telemetry telemetry analysis for "${customInput}" cross-referenced with machine parameters.`,
        rootCause: "Multi-variate trend deviation detected across thermal and load coefficients.",
        probability: "95.8% Model Confidence",
        leadTime: "48-72 Hours Advisory Window",
        checklist: [
          "Verify sensor calibration and zero-point baseline",
          "Check mechanical coupling alignment with laser gauge",
          "Execute automated diagnostic self-test in SCADA console"
        ]
      });
      setIsThinking(false);
      setCustomInput('');
    }, 600);
  };

  return (
    <section id="ask-jane" className="py-16 sm:py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-[#E5E5E1]">
      {/* Header */}
      <div className="text-center max-w-3xl mx-auto mb-12">
        <div className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-[#6B6B6B] font-mono mb-3">
          <span className="w-2 h-2 rounded-full bg-[#1A1A1A]" />
          <span>JANE COPILOT REASONING ENGINE</span>
        </div>
        <h2 className="text-3xl sm:text-5xl font-bold text-[#1A1A1A] tracking-tight leading-tight">
          Ask Jane anything about your physical machinery.
        </h2>
        <p className="mt-4 text-[#6B6B6B] text-base sm:text-lg">
          Try real engineering prompts below or enter your own machine telemetry question to see instant root-cause analysis.
        </p>
      </div>

      {/* Preset Prompts Chips */}
      <div className="flex flex-wrap items-center justify-center gap-2.5 max-w-4xl mx-auto mb-8">
        {presetPrompts.map((p) => (
          <button
            key={p.id}
            onClick={() => handleSelectPrompt(p)}
            className={`px-4 py-2 rounded-full text-xs font-medium transition-all cursor-pointer flex items-center gap-2 ${
              selectedPrompt.id === p.id
                ? 'bg-[#1A1A1A] text-white shadow-2xs'
                : 'bg-white border border-[#E5E5E1] hover:border-[#1A1A1A] text-[#6B6B6B]'
            }`}
          >
            <Sparkles className={`w-3.5 h-3.5 ${selectedPrompt.id === p.id ? 'text-white' : 'text-[#A1A19A]'}`} />
            <span>"{p.query}"</span>
          </button>
        ))}
      </div>

      {/* Interactive Chat Console & Assessment Box */}
      <div className="max-w-4xl mx-auto bg-white border border-[#E5E5E1] rounded-3xl shadow-sm overflow-hidden">
        {/* Top Chat Input Bar */}
        <form onSubmit={handleCustomSubmit} className="p-4 sm:p-5 bg-[#F9F9F8] border-b border-[#E5E5E1] flex items-center gap-3">
          <div className="p-2 rounded-xl bg-[#1A1A1A] text-white shrink-0">
            <Bot className="w-5 h-5" />
          </div>
          <input
            type="text"
            value={customInput}
            onChange={(e) => setCustomInput(e.target.value)}
            placeholder="Ask Jane: e.g., 'What is causing temperature surge on Compressor #3?'"
            className="flex-1 bg-white border border-[#E5E5E1] rounded-xl px-4 py-2.5 text-sm text-[#1A1A1A] placeholder:text-[#A1A19A] focus:outline-hidden focus:ring-2 focus:ring-[#1A1A1A]/10 focus:border-[#1A1A1A]"
          />
          <button
            type="submit"
            className="bg-[#1A1A1A] hover:opacity-85 text-white p-2.5 rounded-xl transition cursor-pointer shrink-0"
            aria-label="Submit query to Jane"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>

        {/* Diagnosis Body */}
        <div className="p-6 sm:p-8 space-y-6">
          {isThinking ? (
            <div className="py-12 text-center space-y-3 font-mono text-sm text-[#6B6B6B]">
              <div className="w-8 h-8 border-3 border-[#1A1A1A] border-t-transparent rounded-full animate-spin mx-auto" />
              <p>Jane is analyzing 142,000 telemetry records and P&ID schematics...</p>
            </div>
          ) : (
            <div className="space-y-6 animate-in fade-in duration-200">
              {/* Asset Badge & Lead Time Metric */}
              <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-[#E5E5E1]">
                <div>
                  <div className="text-[11px] font-mono font-bold uppercase tracking-widest text-[#6B6B6B]">
                    TARGET ASSET IDENTIFIED
                  </div>
                  <div className="text-lg font-bold text-[#1A1A1A] mt-0.5">
                    {selectedPrompt.asset}
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="bg-[#EEEBE5] border border-[#E5E5E1] px-3 py-1.5 rounded-xl text-right">
                    <div className="text-[10px] font-mono font-bold text-[#6B6B6B] uppercase">EARLY WARNING</div>
                    <div className="text-xs font-mono font-bold text-[#1A1A1A]">{selectedPrompt.leadTime}</div>
                  </div>
                  <div className="bg-[#EEEBE5] border border-[#E5E5E1] px-3 py-1.5 rounded-xl text-right">
                    <div className="text-[10px] font-mono font-bold text-[#6B6B6B] uppercase">CONFIDENCE</div>
                    <div className="text-xs font-mono font-bold text-[#1A1A1A]">{selectedPrompt.probability}</div>
                  </div>
                </div>
              </div>

              {/* Diagnosis Summary & Root Cause */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-[#F9F9F8] border border-[#E5E5E1] rounded-2xl p-4 sm:p-5">
                  <div className="flex items-center gap-2 text-xs font-bold font-mono text-[#1A1A1A] uppercase tracking-widest mb-2">
                    <Sparkles className="w-4 h-4 text-[#1A1A1A]" />
                    <span>Telemetry Signature</span>
                  </div>
                  <p className="text-sm text-[#6B6B6B] leading-relaxed">
                    {selectedPrompt.summary}
                  </p>
                </div>

                <div className="bg-[#EEEBE5] border border-[#E5E5E1] rounded-2xl p-4 sm:p-5">
                  <div className="flex items-center gap-2 text-xs font-bold font-mono text-[#1A1A1A] uppercase tracking-widest mb-2">
                    <AlertTriangle className="w-4 h-4 text-[#1A1A1A]" />
                    <span>Root Cause Isolation</span>
                  </div>
                  <p className="text-sm text-[#1A1A1A] leading-relaxed">
                    {selectedPrompt.rootCause}
                  </p>
                </div>
              </div>

              {/* Step by step engineering remediation checklist */}
              <div className="bg-[#1A1A1A] text-white rounded-2xl p-5 sm:p-6 space-y-3 font-mono text-xs border border-[#333333]">
                <div className="flex items-center justify-between text-[11px] text-white font-bold uppercase tracking-widest">
                  <span className="flex items-center gap-2">
                    <Wrench className="w-4 h-4" />
                    <span>Jane Actionable Engineering Checklist</span>
                  </span>
                  <span className="text-[#A1A19A]">READY FOR DISPATCH</span>
                </div>
                <div className="space-y-2 pt-1">
                  {selectedPrompt.checklist.map((item, idx) => (
                    <div key={idx} className="flex items-start gap-3 bg-[#111111] p-3 rounded-xl border border-[#2A2A2A] font-sans text-xs sm:text-sm text-[#EEEBE5]">
                      <span className="font-mono text-white font-bold text-xs shrink-0 mt-0.5">0{idx + 1}.</span>
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
};

