import React, { useState } from 'react';
import { 
  Sparkles, 
  Calendar, 
  Settings2, 
  ArrowUp, 
  ArrowUpRight, 
  Plus, 
  Zap, 
  AtSign, 
  Link2, 
  CheckCircle2, 
  FileText, 
  Bot, 
  RotateCcw,
  BookOpen
} from 'lucide-react';

interface Citation {
  source: string;
  type: string;
  ref: string;
  snippet: string;
}

interface QueryResult {
  question: string;
  summary: string;
  keyPoints: string[];
  metrics?: { label: string; value: string; delta: string }[];
  citations: Citation[];
  confidence: number;
}

const PRESET_QUERIES: Record<string, QueryResult> = {
  "Which engineers are using AI most effectively?": {
    question: "Which engineers are using AI most effectively?",
    summary: "Reliability & Lead Automation Engineers across Line 4 and Turbine Hall exhibit the highest autonomous dispatch efficiency, achieving 94.2% closed-loop resolution with Jane AI assistant.",
    keyPoints: [
      "Marcus Vance (Shift Lead, Sector B) resolved 38 predictive alerts with 0 unverified false positives using CAD cross-referencing.",
      "Elena Rostova (Condition Monitoring) automated 14 preventative bearing replacements 72h prior to vibration threshold trips.",
      "Operations Team Alpha has reduced mean time to root cause diagnosis (MTTR) by 58% over the last 90 days."
    ],
    metrics: [
      { label: "AI Workflows Dispatched", value: "142", delta: "+28% MoM" },
      { label: "Closed-Loop Accuracy", value: "97.4%", delta: "+4.1%" },
      { label: "Hours Saved / Engineer", value: "18.5 hrs/wk", delta: "Top 5%" }
    ],
    citations: [
      { source: "SAP PM Work Orders 2026-Q1", type: "ERP Record", ref: "WO-98442", snippet: "Autonomous dispatch confirmation by M. Vance on High-Pressure Feed Pump #3." },
      { source: "Jane AI Telemetry Interaction Logs", type: "Audit Trail", ref: "LOG-0883-T", snippet: "Spectral FFT harmonic analysis verified against OEM vibration tolerance curve." },
      { source: "Reliability Shift Handover Notes", type: "Shift Log", ref: "SHIFT-B-44", snippet: "Zero unplanned downtime incidents reported on critical rotating equipment." }
    ],
    confidence: 98
  },
  "Analyze the strengths and weaknesses of our teams": {
    question: "Analyze the strengths and weaknesses of our teams",
    summary: "Across maintenance and operational squads, vibration telemetry interpretation and rapid sensor diagnostic velocity are standout strengths, while legacy SCADA manual tag mapping remains a bottleneck.",
    keyPoints: [
      "Strengths: Rapid execution of autonomous work orders (<15 min response time) and 99.1% adherence to ISO 10816 vibration guidelines.",
      "Strengths: High cross-functional collaboration between control room operators and mechanical field technicians.",
      "Weaknesses: Manual PLC tag entry in auxiliary facilities creates an average 42-minute delay before Jane automatic model training initiates."
    ],
    metrics: [
      { label: "Team Velocity Score", value: "9.2/10", delta: "+1.4 pts" },
      { label: "Diagnostic Lag", value: "4.2 min", delta: "-64%" },
      { label: "Manual Tag Overhead", value: "12%", delta: "Needs Auto-Map" }
    ],
    citations: [
      { source: "Plant Operations Review 2026", type: "Annual Audit", ref: "OPS-REV-2026", snippet: "Turbine maintenance squad achieved highest continuous uptime record in plant history." },
      { source: "Neuron Data Engine Pipeline Metrics", type: "Telemetry Stream", ref: "ND-9921", snippet: "Unmapped legacy Modbus tags identified in Auxiliary Water Treatment Substation." }
    ],
    confidence: 95
  },
  "Where are our deployment cycles getting stuck?": {
    question: "Where are our deployment cycles getting stuck?",
    summary: "Deployment friction is concentrated at the edge-gateway firewall handshake and manual approval queues for OEM spare-parts procurement exceeding $25,000.",
    keyPoints: [
      "Edge Gateway Ingestion: 62% of onboarding delays stem from IT/OT firewall rule approvals on air-gapped subnet 10.240.x.",
      "ERP PO Approvals: Replacement bearing kits take an average of 4.8 days for dual-signature approval in SAP PM.",
      "Neuron Zero-Copy Ingest: Data pipeline compilation and streaming latency are operating at near-zero friction (<12ms)."
    ],
    metrics: [
      { label: "IT Approval Latency", value: "3.6 days", delta: "Critical Path" },
      { label: "Edge Stream Latency", value: "8.4 ms", delta: "Optimal" },
      { label: "Procurement Hold Rate", value: "18.2%", delta: "-5.3%" }
    ],
    citations: [
      { source: "OT Network Security Audit", type: "Security Log", ref: "SEC-AIRGAP-04", snippet: "Pending subnet gateway certificate verification on 4 remote pumping stations." },
      { source: "SAP Procurement Tracking", type: "Supply Chain", ref: "PO-77291-B", snippet: "Awaiting Tier-2 approval on SKF Explorer spherical roller bearing assembly." }
    ],
    confidence: 96
  }
};

export const KnowledgeSearchSection: React.FC = () => {
  const [activeQuestion, setActiveQuestion] = useState<string | null>(null);
  const [inputValue, setInputValue] = useState("");
  const [selectedTimeRange, setSelectedTimeRange] = useState("Last 3 months");
  const [selectedMode, setSelectedMode] = useState("Auto");
  const [selectedDepth, setSelectedDepth] = useState("Normal");
  const [isProcessing, setIsProcessing] = useState(false);
  const [customResult, setCustomResult] = useState<QueryResult | null>(null);

  const handleQuerySelect = (questionText: string) => {
    setInputValue(questionText);
    setIsProcessing(true);
    setActiveQuestion(questionText);
    setCustomResult(null);

    setTimeout(() => {
      setIsProcessing(false);
    }, 450);
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    setIsProcessing(true);
    setActiveQuestion(inputValue);

    setTimeout(() => {
      if (PRESET_QUERIES[inputValue]) {
        setCustomResult(null);
      } else {
        setCustomResult({
          question: inputValue,
          summary: `Synthesized analysis from ${selectedTimeRange.toLowerCase()} telemetry streams, plant maintenance logs, and equipment manuals.`,
          keyPoints: [
            `Cross-correlated sensor time-series data with historical downtime logs matching "${inputValue}".`,
            "Identified 3 correlating operational parameters with statistical significance >94%.",
            "Continuous monitoring is active with automated Jane alerts configured for threshold variances."
          ],
          metrics: [
            { label: "Matching Records", value: "2,840", delta: "100% indexed" },
            { label: "Cross-Correlated Assets", value: "14 Units", delta: "Line 1-4" },
            { label: "Confidence Rating", value: "96.8%", delta: "Grounded" }
          ],
          citations: [
            { source: "SCADA & Telemetry Ingestion Hub", type: "Live Stream", ref: "TELEM-INDEX", snippet: `Records evaluated across ${selectedTimeRange} with verified timestamp alignment.` },
            { source: "Equipment Health Registry", type: "CMMS Master", ref: "ASSET-REG-2026", snippet: "Operational boundary models applied based on latest vibration baseline." }
          ],
          confidence: 97
        });
      }
      setIsProcessing(false);
    }, 550);
  };

  const currentResult = customResult || (activeQuestion ? PRESET_QUERIES[activeQuestion] : null);

  return (
    <section className="py-20 md:py-28 px-4 sm:px-6 lg:px-8 bg-[#F8F9FA] relative">
      <div className="max-w-5xl mx-auto">
        {/* Outer Browser/Canvas Card */}
        <div className="bg-[#FFFFFF] border border-[#E2E4E6] rounded-3xl p-6 sm:p-10 md:p-14 shadow-sm relative overflow-hidden transition-all">
          
          {/* Top Window Control Dots (macOS style: Red, Yellow, Green) */}
          <div className="flex items-center gap-2 mb-8">
            <span className="w-3 h-3 rounded-full bg-[#FF5F56] inline-block border border-[#E0443E]/20" />
            <span className="w-3 h-3 rounded-full bg-[#FFBD2E] inline-block border border-[#DEA123]/20" />
            <span className="w-3 h-3 rounded-full bg-[#27C93F] inline-block border border-[#1AAB29]/20" />
            <span className="ml-2 text-[11px] font-mono text-[#8C9196] uppercase tracking-wider">
              AIConneX Knowledge Intelligence Engine
            </span>
          </div>

          {/* Centered AIConneX Mascot Character */}
          <div className="flex flex-col items-center justify-center text-center mb-8">
            <div className="relative mb-3 group cursor-pointer">
              {/* AIConneX Avatar in Theme Dark & Accent */}
              <div className="w-16 h-16 rounded-full bg-[#191C1D] text-white flex items-center justify-center shadow-md relative border border-[#2D3133]">
                {/* Subtle Lime Accent Glow Ring */}
                <div className="absolute inset-1 rounded-full border border-dashed border-[#d4f658]/40 opacity-75" />
                {/* Mascot Icon */}
                <Sparkles className="w-6 h-6 text-[#d4f658] z-10" />
                
                {/* Arm / Indicator */}
                <div className="absolute -top-1 -right-1 text-xs text-[#d4f658] transform -rotate-12">
                  ✦
                </div>
                {/* Mascot legs */}
                <div className="absolute -bottom-1.5 flex gap-2">
                  <div className="w-1 h-2 bg-[#191C1D] rounded-full" />
                  <div className="w-1 h-2 bg-[#191C1D] rounded-full" />
                </div>
              </div>
            </div>

            {/* Main Headline */}
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-[#191C1D] tracking-tight font-sans">
              What do you want to know?
            </h2>
            <p className="text-sm text-[#666666] mt-2 font-mono max-w-lg">
              Ask anything across plant telemetry, maintenance work orders, sensor trends, and engineering handovers.
            </p>
          </div>

          {/* Main Interactive Input Card */}
          <form onSubmit={handleFormSubmit} className="max-w-3xl mx-auto mb-8">
            <div className="bg-[#FFFFFF] border border-[#E2E4E6] focus-within:border-[#191C1D] focus-within:ring-4 focus-within:ring-[#191C1D]/5 rounded-2xl p-4 sm:p-5 shadow-sm transition-all">
              {/* Input text field */}
              <div className="flex items-start gap-3">
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Ask your question..."
                  className="w-full bg-transparent text-[#191C1D] placeholder-[#8C9196] text-base sm:text-lg focus:outline-hidden py-1 font-sans"
                />
              </div>

              {/* Action Toolbar & Submit Button */}
              <div className="flex items-center justify-between pt-4 mt-2 border-t border-[#F0F2F4]">
                {/* Left quick actions */}
                <div className="flex items-center gap-1 sm:gap-2 text-[#757964]">
                  <button
                    type="button"
                    title="Attach file or OEM manual"
                    className="p-1.5 hover:bg-[#F3F4F5] hover:text-[#191C1D] rounded-lg transition"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                  <button
                    type="button"
                    title="Fast diagnostic"
                    className="p-1.5 hover:bg-[#F3F4F5] hover:text-[#191C1D] rounded-lg transition"
                  >
                    <Zap className="w-4 h-4" />
                  </button>
                  <button
                    type="button"
                    title="Tag equipment or team"
                    className="p-1.5 hover:bg-[#F3F4F5] hover:text-[#191C1D] rounded-lg transition"
                  >
                    <AtSign className="w-4 h-4" />
                  </button>
                  <button
                    type="button"
                    title="Link telemetry stream"
                    className="p-1.5 hover:bg-[#F3F4F5] hover:text-[#191C1D] rounded-lg transition"
                  >
                    <Link2 className="w-4 h-4" />
                  </button>
                </div>

                {/* Submit button (Dark Theme matching AIConneX) */}
                <button
                  type="submit"
                  disabled={!inputValue.trim() || isProcessing}
                  className="w-9 h-9 rounded-xl bg-[#000000] hover:bg-[#222222] disabled:opacity-30 text-white flex items-center justify-center transition cursor-pointer shadow-sm hover:scale-105 active:scale-95"
                  aria-label="Submit Question"
                >
                  {isProcessing ? (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <ArrowUp className="w-5 h-5 stroke-[2.5]" />
                  )}
                </button>
              </div>

              {/* Bottom filter scope pills */}
              <div className="flex flex-wrap items-center gap-2 pt-3 text-xs font-mono text-[#666666]">
                {/* Auto filter pill */}
                <button
                  type="button"
                  onClick={() => setSelectedMode(selectedMode === "Auto" ? "Strict" : "Auto")}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#F8F9FA] hover:bg-[#EEF0F2] border border-[#E2E4E6] text-[#191C1D] transition cursor-pointer"
                >
                  <Sparkles className="w-3 h-3 text-[#191C1D]" />
                  <span>{selectedMode}</span>
                </button>

                {/* Time Range Pill */}
                <button
                  type="button"
                  onClick={() => {
                    const ranges = ["Last 30 days", "Last 3 months", "Last 12 months"];
                    const next = ranges[(ranges.indexOf(selectedTimeRange) + 1) % ranges.length];
                    setSelectedTimeRange(next);
                  }}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#F8F9FA] hover:bg-[#EEF0F2] border border-[#E2E4E6] text-[#191C1D] transition cursor-pointer"
                >
                  <Calendar className="w-3 h-3 text-[#757964]" />
                  <span>{selectedTimeRange}</span>
                </button>

                {/* Depth Pill */}
                <button
                  type="button"
                  onClick={() => {
                    const modes = ["Normal", "Deep Reason", "Executive"];
                    const next = modes[(modes.indexOf(selectedDepth) + 1) % modes.length];
                    setSelectedDepth(next);
                  }}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#F8F9FA] hover:bg-[#EEF0F2] border border-[#E2E4E6] text-[#191C1D] transition cursor-pointer"
                >
                  <Settings2 className="w-3 h-3 text-[#757964]" />
                  <span>{selectedDepth}</span>
                </button>
              </div>
            </div>
          </form>

          {/* Interactive Answer View if a question has been asked */}
          {currentResult && (
            <div className="max-w-3xl mx-auto mb-10 p-6 sm:p-7 bg-[#FAFBFB] rounded-2xl border border-[#DCE0E4] shadow-inner animate-in fade-in slide-in-from-bottom-2 duration-300">
              <div className="flex items-center justify-between pb-4 border-b border-[#E2E4E6]">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-[#000000] text-[#d4f658] flex items-center justify-center text-xs font-bold font-mono">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-xs font-mono font-bold text-[#191C1D]">
                      Grounded Answer ({currentResult.confidence}% Confidence)
                    </div>
                    <div className="text-[11px] font-mono text-[#757964]">
                      Scoped to {selectedTimeRange} • Zero Hallucination Guardrail Active
                    </div>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => {
                    setActiveQuestion(null);
                    setCustomResult(null);
                    setInputValue("");
                  }}
                  className="inline-flex items-center gap-1 text-xs font-mono text-[#666666] hover:text-[#191C1D] transition cursor-pointer"
                >
                  <RotateCcw className="w-3 h-3" />
                  <span>Reset</span>
                </button>
              </div>

              {/* Summary */}
              <p className="text-base text-[#191C1D] font-medium leading-relaxed mt-4">
                {currentResult.summary}
              </p>

              {/* Key Bullet Points */}
              <div className="mt-4 space-y-2">
                {currentResult.keyPoints.map((point, i) => (
                  <div key={i} className="flex items-start gap-2.5 text-xs sm:text-sm text-[#44494D]">
                    <CheckCircle2 className="w-4 h-4 text-[#191C1D] shrink-0 mt-0.5" />
                    <span>{point}</span>
                  </div>
                ))}
              </div>

              {/* Metrics Pill Grid */}
              {currentResult.metrics && (
                <div className="grid grid-cols-3 gap-3 mt-5 pt-4 border-t border-[#E2E4E6]">
                  {currentResult.metrics.map((metric, i) => (
                    <div key={i} className="bg-white p-3 rounded-xl border border-[#E2E4E6]">
                      <div className="text-[10px] font-mono uppercase text-[#757964]">{metric.label}</div>
                      <div className="text-lg font-bold text-[#191C1D] mt-0.5">{metric.value}</div>
                      <div className="text-[10px] font-mono text-[#191C1D] font-bold mt-0.5">{metric.delta}</div>
                    </div>
                  ))}
                </div>
              )}

              {/* Citations Box */}
              <div className="mt-5 pt-4 border-t border-[#E2E4E6]">
                <div className="text-[11px] font-mono font-bold uppercase text-[#757964] mb-2 flex items-center gap-1.5">
                  <BookOpen className="w-3.5 h-3.5" />
                  <span>Verified Citations & Linked Sources ({currentResult.citations.length})</span>
                </div>
                <div className="space-y-2">
                  {currentResult.citations.map((cite, i) => (
                    <div key={i} className="p-2.5 bg-white rounded-lg border border-[#E2E4E6] text-xs font-mono">
                      <div className="flex items-center justify-between text-[#191C1D] font-bold">
                        <span className="flex items-center gap-1.5">
                          <FileText className="w-3 h-3 text-[#191C1D]" />
                          {cite.source}
                        </span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#F0F2F4] text-[#666666]">
                          {cite.ref}
                        </span>
                      </div>
                      <div className="text-[11px] text-[#666666] mt-1 font-sans">
                        "{cite.snippet}"
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Suggested Quick Inquiries List (Matching AIConneX Theme) */}
          <div className="max-w-3xl mx-auto space-y-3.5">
            {Object.keys(PRESET_QUERIES).map((queryText) => (
              <button
                key={queryText}
                type="button"
                onClick={() => handleQuerySelect(queryText)}
                className={`w-full text-left flex items-start gap-3 group transition py-1 cursor-pointer ${
                  activeQuestion === queryText ? 'text-[#000000]' : 'text-[#2D3133] hover:text-[#000000]'
                }`}
              >
                <ArrowUpRight className="w-4 h-4 text-[#000000] shrink-0 mt-1 transition-transform duration-200 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                <span className="text-base sm:text-lg font-medium tracking-tight font-sans">
                  {queryText}
                </span>
              </button>
            ))}
          </div>

          {/* Footer Note */}
          <div className="max-w-3xl mx-auto mt-8 pt-4 border-t border-[#F0F2F4] text-center sm:text-left">
            <p className="text-xs text-[#8C9196] font-mono">
              Every answer is grounded in your own records, and cites them.
            </p>
          </div>

        </div>
      </div>
    </section>
  );
};
