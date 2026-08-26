import React, { useState } from 'react';
import { SpecularCard } from './SpecularButton';
import { VoicePoweredOrb } from '@/components/ui/voice-powered-orb';
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
  BookOpen,
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
  'Which engineers are using AI most effectively?': {
    question: 'Which engineers are using AI most effectively?',
    summary:
      'Reliability & Lead Automation Engineers across Line 4 and Turbine Hall exhibit the highest autonomous dispatch efficiency, achieving 94.2% closed-loop resolution with Jane AI assistant.',
    keyPoints: [
      'Marcus Vance (Shift Lead, Sector B) resolved 38 predictive alerts with 0 unverified false positives using CAD cross-referencing.',
      'Elena Rostova (Condition Monitoring) automated 14 preventative bearing replacements 72h prior to vibration threshold trips.',
      'Operations Team Alpha has reduced mean time to root cause diagnosis (MTTR) by 58% over the last 90 days.',
    ],
    metrics: [
      { label: 'AI Workflows Dispatched', value: '142', delta: '+28% MoM' },
      { label: 'Closed-Loop Accuracy', value: '97.4%', delta: '+4.1%' },
      { label: 'Hours Saved / Engineer', value: '18.5 hrs/wk', delta: 'Top 5%' },
    ],
    citations: [
      { source: 'SAP PM Work Orders 2026-Q1', type: 'ERP Record', ref: 'WO-98442', snippet: 'Autonomous dispatch confirmation by M. Vance on High-Pressure Feed Pump #3.' },
      { source: 'Jane AI Telemetry Interaction Logs', type: 'Audit Trail', ref: 'LOG-0883-T', snippet: 'Spectral FFT harmonic analysis verified against OEM vibration tolerance curve.' },
      { source: 'Reliability Shift Handover Notes', type: 'Shift Log', ref: 'SHIFT-B-44', snippet: 'Zero unplanned downtime incidents reported on critical rotating equipment.' },
    ],
    confidence: 98,
  },
  'Analyze the strengths and weaknesses of our teams': {
    question: 'Analyze the strengths and weaknesses of our teams',
    summary:
      'Across maintenance and operational squads, vibration telemetry interpretation and rapid sensor diagnostic velocity are standout strengths, while legacy SCADA manual tag mapping remains a bottleneck.',
    keyPoints: [
      'Strengths: Rapid execution of autonomous work orders (<15 min response time) and 99.1% adherence to ISO 10816 vibration guidelines.',
      'Strengths: High cross-functional collaboration between control room operators and mechanical field technicians.',
      'Weaknesses: Manual PLC tag entry in auxiliary facilities creates an average 42-minute delay before Jane automatic model training initiates.',
    ],
    metrics: [
      { label: 'Team Velocity Score', value: '9.2/10', delta: '+1.4 pts' },
      { label: 'Diagnostic Lag', value: '4.2 min', delta: '-64%' },
      { label: 'Manual Tag Overhead', value: '12%', delta: 'Needs Auto-Map' },
    ],
    citations: [
      { source: 'Plant Operations Review 2026', type: 'Annual Audit', ref: 'OPS-REV-2026', snippet: 'Turbine maintenance squad achieved highest continuous uptime record in plant history.' },
      { source: 'Neuron Data Engine Pipeline Metrics', type: 'Telemetry Stream', ref: 'ND-9921', snippet: 'Unmapped legacy Modbus tags identified in Auxiliary Water Treatment Substation.' },
    ],
    confidence: 95,
  },
  'Where are our deployment cycles getting stuck?': {
    question: 'Where are our deployment cycles getting stuck?',
    summary:
      'Deployment friction is concentrated at the edge-gateway firewall handshake and manual approval queues for OEM spare-parts procurement exceeding $25,000.',
    keyPoints: [
      'Edge Gateway Ingestion: 62% of onboarding delays stem from IT/OT firewall rule approvals on air-gapped subnet 10.240.x.',
      'ERP PO Approvals: Replacement bearing kits take an average of 4.8 days for dual-signature approval in SAP PM.',
      'Neuron Zero-Copy Ingest: Data pipeline compilation and streaming latency are operating at near-zero friction (<12ms).',
    ],
    metrics: [
      { label: 'IT Approval Latency', value: '3.6 days', delta: 'Critical Path' },
      { label: 'Edge Stream Latency', value: '8.4 ms', delta: 'Optimal' },
      { label: 'Procurement Hold Rate', value: '18.2%', delta: '-5.3%' },
    ],
    citations: [
      { source: 'OT Network Security Audit', type: 'Security Log', ref: 'SEC-AIRGAP-04', snippet: 'Pending subnet gateway certificate verification on 4 remote pumping stations.' },
      { source: 'SAP Procurement Tracking', type: 'Supply Chain', ref: 'PO-77291-B', snippet: 'Awaiting Tier-2 approval on SKF Explorer spherical roller bearing assembly.' },
    ],
    confidence: 96,
  },
};

export const KnowledgeSearchSection: React.FC = () => {
  const [activeQuestion, setActiveQuestion] = useState<string | null>(null);
  const [inputValue, setInputValue] = useState('');
  const [selectedTimeRange, setSelectedTimeRange] = useState('Last 3 months');
  const [selectedMode, setSelectedMode] = useState('Auto');
  const [selectedDepth, setSelectedDepth] = useState('Normal');
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
            'Identified 3 correlating operational parameters with statistical significance >94%.',
            'Continuous monitoring is active with automated Jane alerts configured for threshold variances.',
          ],
          metrics: [
            { label: 'Matching Records', value: '2,840', delta: '100% indexed' },
            { label: 'Cross-Correlated Assets', value: '14 Units', delta: 'Line 1-4' },
            { label: 'Confidence Rating', value: '96.8%', delta: 'Grounded' },
          ],
          citations: [
            { source: 'SCADA & Telemetry Ingestion Hub', type: 'Live Stream', ref: 'TELEM-INDEX', snippet: `Records evaluated across ${selectedTimeRange} with verified timestamp alignment.` },
            { source: 'Equipment Health Registry', type: 'CMMS Master', ref: 'ASSET-REG-2026', snippet: 'Operational boundary models applied based on latest vibration baseline.' },
          ],
          confidence: 97,
        });
      }
      setIsProcessing(false);
    }, 550);
  };

  const currentResult = customResult || (activeQuestion ? PRESET_QUERIES[activeQuestion] : null);

  return (
    <section className="lp__section lp__ks-section" id="knowledge-search">
      <div className="container--1286">
        {/* Outer Browser/Canvas Card */}
        <div className="lp__ks-card lp__reveal">
          {/* Top Window Control Dots (macOS style: Red, Yellow, Green) */}
          <div className="lp__ks-top-bar">
            <div className="lp__ks-dots">
              <span className="lp__ks-dot lp__ks-dot--red" />
              <span className="lp__ks-dot lp__ks-dot--yellow" />
              <span className="lp__ks-dot lp__ks-dot--green" />
            </div>
            <span className="lp__ks-header-text">AIConneX Knowledge Intelligence Engine</span>
          </div>

          {/* Centered Mascot Character Header */}
          <div className="lp__ks-mascot-header">
            <div className="lp__ks-mascot-avatar">
              <VoicePoweredOrb className="absolute inset-0 rounded-full overflow-hidden opacity-75" enableVoiceControl={false} hue={280} />
              <div className="lp__ks-mascot-ring" />
              <Sparkles className="lp__ks-sparkle-icon" />
              <span className="lp__ks-star">✦</span>
              <div className="lp__ks-legs">
                <span />
                <span />
              </div>
            </div>

            <h2 className="heading--h2 lp__ks-title">What do you want to know?</h2>
            <p className="section--subtitle-text lp__ks-subtitle">
              Ask anything across plant telemetry, maintenance work orders, sensor trends, and engineering handovers.
            </p>
          </div>

          {/* Main Interactive Input Card */}
          <form onSubmit={handleFormSubmit} className="lp__ks-form">
            <SpecularCard
              radius={20}
              lineColor="var(--lp-charcoal, #191c1d)"
              baseColor="var(--lp-outline-variant, #b0b5ba)"
              intensity={2.2}
              shineSize={32}
              shineFade={55}
              thickness={2.5}
              followMouse={true}
              proximity={500}
              className="lp__ks-specular-card"
            >
              <div className="lp__ks-input-box">
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Ask your question..."
                  className="lp__ks-input"
                />

                {/* Action Toolbar & Submit Button */}
                <div className="lp__ks-toolbar">
                  <div className="lp__ks-toolbar-left">
                    <button type="button" title="Attach file or OEM manual" className="lp__ks-tool-btn">
                      <Plus className="w-4 h-4" />
                    </button>
                    <button type="button" title="Fast diagnostic" className="lp__ks-tool-btn">
                      <Zap className="w-4 h-4" />
                    </button>
                    <button type="button" title="Tag equipment or team" className="lp__ks-tool-btn">
                      <AtSign className="w-4 h-4" />
                    </button>
                    <button type="button" title="Link telemetry stream" className="lp__ks-tool-btn">
                      <Link2 className="w-4 h-4" />
                    </button>
                  </div>

                  <button
                    type="submit"
                    disabled={!inputValue.trim() || isProcessing}
                    className="lp__ks-submit-btn"
                    aria-label="Submit Question"
                  >
                    {isProcessing ? (
                      <div className="lp__ks-spinner" />
                    ) : (
                      <ArrowUp className="w-5 h-5 stroke-[2.5]" />
                    )}
                  </button>
                </div>

                {/* Bottom Filter Scope Pills */}
                <div className="lp__ks-filters">
                  <button
                    type="button"
                    onClick={() => setSelectedMode(selectedMode === 'Auto' ? 'Strict' : 'Auto')}
                    className="lp__ks-filter-pill"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>{selectedMode}</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      const ranges = ['Last 30 days', 'Last 3 months', 'Last 12 months'];
                      const next = ranges[(ranges.indexOf(selectedTimeRange) + 1) % ranges.length];
                      setSelectedTimeRange(next);
                    }}
                    className="lp__ks-filter-pill"
                  >
                    <Calendar className="w-3.5 h-3.5" />
                    <span>{selectedTimeRange}</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      const modes = ['Normal', 'Deep Reason', 'Executive'];
                      const next = modes[(modes.indexOf(selectedDepth) + 1) % modes.length];
                      setSelectedDepth(next);
                    }}
                    className="lp__ks-filter-pill"
                  >
                    <Settings2 className="w-3.5 h-3.5" />
                    <span>{selectedDepth}</span>
                  </button>
                </div>
              </div>
            </SpecularCard>
          </form>

          {/* Interactive Answer View if a question has been asked */}
          {currentResult && (
            <div className="lp__ks-result-card">
              <div className="lp__ks-res-top">
                <div className="lp__ks-res-brand">
                  <div className="lp__ks-bot-avatar">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="lp__ks-res-head">
                      Grounded Answer ({currentResult.confidence}% Confidence)
                    </div>
                    <div className="lp__ks-res-sub">
                      Scoped to {selectedTimeRange} • Zero Hallucination Guardrail Active
                    </div>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => {
                    setActiveQuestion(null);
                    setCustomResult(null);
                    setInputValue('');
                  }}
                  className="lp__ks-reset-btn"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Reset</span>
                </button>
              </div>

              <p className="lp__ks-summary">{currentResult.summary}</p>

              <div className="lp__ks-points">
                {currentResult.keyPoints.map((point, i) => (
                  <div key={i} className="lp__ks-point-row">
                    <CheckCircle2 className="w-4 h-4 text-[#0f1012] shrink-0 mt-0.5" />
                    <span>{point}</span>
                  </div>
                ))}
              </div>

              {currentResult.metrics && (
                <div className="lp__ks-metrics-grid">
                  {currentResult.metrics.map((metric, i) => (
                    <div key={i} className="lp__ks-metric-card">
                      <div className="lp__ks-m-label">{metric.label}</div>
                      <div className="lp__ks-m-val">{metric.value}</div>
                      <div className="lp__ks-m-delta">{metric.delta}</div>
                    </div>
                  ))}
                </div>
              )}

              <div className="lp__ks-citations-wrap">
                <div className="lp__ks-cite-title">
                  <BookOpen className="w-3.5 h-3.5" />
                  <span>Verified Citations & Linked Sources ({currentResult.citations.length})</span>
                </div>
                <div className="lp__ks-cite-list">
                  {currentResult.citations.map((cite, i) => (
                    <div key={i} className="lp__ks-cite-card">
                      <div className="lp__ks-cite-head">
                        <span className="lp__ks-cite-source">
                          <FileText className="w-3.5 h-3.5" />
                          {cite.source}
                        </span>
                        <span className="lp__ks-cite-ref">{cite.ref}</span>
                      </div>
                      <div className="lp__ks-cite-snippet">"{cite.snippet}"</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Suggested Quick Inquiries List */}
          <div className="lp__ks-preset-list">
            {Object.keys(PRESET_QUERIES).map((queryText) => (
              <button
                key={queryText}
                type="button"
                onClick={() => handleQuerySelect(queryText)}
                className={`lp__ks-preset-btn${activeQuestion === queryText ? ' lp__ks-preset-btn--active' : ''}`}
              >
                <ArrowUpRight className="w-4 h-4 text-[#0f1012] shrink-0 mt-1 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                <span>{queryText}</span>
              </button>
            ))}
          </div>

          <div className="lp__ks-footer-note">
            <p>Every answer is grounded in your own records, and cites them.</p>
          </div>
        </div>
      </div>
    </section>
  );
};
