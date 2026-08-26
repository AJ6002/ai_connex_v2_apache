import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface StepData {
  stepNum: string;
  shortTitle: string;
  pillTag: string;
  heading: string;
  description: string;
  bullets: string[];
  nextStepTitle?: string;
  engineHeader: string;
  rows: Array<{
    name: string;
    sub: string;
    metric: string;
    detail: string;
  }>;
  footerBanner: string;
}

const STEPS: StepData[] = [
  {
    stepNum: 'STEP 01',
    shortTitle: 'Stream & Unify',
    pillTag: 'STEP 01 // STREAM & UNIFY',
    heading: 'Ingest any industrial protocol without data pipelines breaking.',
    description:
      'Connect SCADA, OPC-UA, MQTT Sparkplug, and historians with zero-copy Apache DataFusion. Jane instantly normalizes diverse industrial schemas into a single governed time-series fabric.',
    bullets: [
      'Zero ETL setup with auto-discovery of PLC tag trees',
      'Edge caching prevents packet drops during plant network outages',
      'Sub-millisecond serialization on high-frequency vibration streams',
    ],
    nextStepTitle: 'ANALYZE & DETECT',
    engineHeader: 'AICONNEX_ENGINE // STREAM & UNIFY',
    rows: [
      {
        name: 'OPC-UA Edge Node #08',
        sub: 'Turbine Fleet Plant Alpha',
        metric: '120,400 msg/s',
        detail: '0.2ms latency',
      },
      {
        name: 'SCADA Historian Relay',
        sub: 'Boiler & Steam Pressure',
        metric: '48,200 msg/s',
        detail: 'Zero duplicate buffer',
      },
    ],
    footerBanner: '⚡ Zero-copy memory pool active. CPU utilization: 1.4%.',
  },
  {
    stepNum: 'STEP 02',
    shortTitle: 'Analyze & Detect',
    pillTag: 'STEP 02 // ANALYZE & DETECT',
    heading: 'Unsupervised spatial-temporal ML detects failures 72 hrs ahead.',
    description:
      'Continuous multi-variate FFT vibration and thermal degradation modeling across historical baseline loads. Auto-adaptive thresholds eliminate false positives.',
    bullets: [
      'Continuous vibration FFT & thermal degradation correlation',
      'Auto-adaptive baseline thresholds adjusting for seasonal plant load',
      'Zero false-positive suppression via automated signal filtering',
    ],
    nextStepTitle: 'SYNTHESIZE WITH JANE',
    engineHeader: 'AICONNEX_ENGINE // ANALYZE & DETECT',
    rows: [
      {
        name: 'Pump 3 Bearing Assembly',
        sub: 'Vibration Waveform Anomaly',
        metric: '99.4% Confidence',
        detail: '72hr lead time',
      },
      {
        name: 'Compressor Stator Thermal',
        sub: 'Heat Flux Deviation',
        metric: '88.6% Risk Level',
        detail: 'P0 Priority',
      },
    ],
    footerBanner: '⚡ Anomaly detection model sync complete. 0.00ms telemetry lag.',
  },
  {
    stepNum: 'STEP 03',
    shortTitle: 'Synthesize with Jane',
    pillTag: 'STEP 03 // SYNTHESIZE WITH JANE',
    heading: 'Jane reasons across telemetry, OEM manuals, and P&ID schematics.',
    description:
      'Ask plain-English queries like "Why did Pump 3 discharge pressure drop at 14:00?" Jane cross-references 10+ years of repair logs to generate exact checklists.',
    bullets: [
      'Natural language telemetry & OEM manual cross-referencing',
      'Historical technician repair log synthesis and root-cause analysis',
      'Step-by-step mechanical remediation checklists with exact torque specs',
    ],
    nextStepTitle: 'AUTOMATE & RESOLVE',
    engineHeader: 'AICONNEX_ENGINE // SYNTHESIZE WITH JANE',
    rows: [
      {
        name: 'Root Cause Diagnosis',
        sub: 'Mechanical Seal Degradation',
        metric: 'Match: OEM §4.2',
        detail: 'Checklist generated',
      },
      {
        name: 'Technician Guidance',
        sub: 'Torque Spec: 45 Nm / M12',
        metric: '99.8% Precision',
        detail: 'Parts reserved',
      },
    ],
    footerBanner: '⚡ Jane Copilot reasoning engine active. Knowledge graph connected.',
  },
  {
    stepNum: 'STEP 04',
    shortTitle: 'Automate & Resolve',
    pillTag: 'STEP 04 // AUTOMATE & RESOLVE',
    heading: 'Closed-loop CMMS work order dispatch & automated verification.',
    description:
      'Automatically create work orders in SAP PM, IBM Maximo, or ServiceNow. Skill-matching dispatches technicians with reserved spare parts in under 30 seconds.',
    bullets: [
      'Native 2-way sync with SAP PM, IBM Maximo, and ServiceNow',
      'Automated spare part inventory reservation and technician dispatch',
      'Closed-loop post-repair telemetry verification before closing tickets',
    ],
    nextStepTitle: 'STREAM & UNIFY',
    engineHeader: 'AICONNEX_ENGINE // AUTOMATE & RESOLVE',
    rows: [
      {
        name: 'SAP PM Work Order #4402',
        sub: 'Dispatched to Field Tech Alpha',
        metric: '< 30s Dispatch',
        detail: 'Parts Locked',
      },
      {
        name: 'Closed-Loop Verification',
        sub: 'Post-Repair Telemetry Check',
        metric: 'Verified 100%',
        detail: 'Ticket Resolved',
      },
    ],
    footerBanner: '⚡ Ticket auto-closed after telemetry baseline stabilization.',
  },
];

const cardVariants = {
  enter: (dir: number) => ({
    x: dir >= 0 ? 30 : -30,
    opacity: 0,
  }),
  center: {
    x: 0,
    opacity: 1,
  },
  exit: (dir: number) => ({
    x: dir >= 0 ? -30 : 30,
    opacity: 0,
  }),
};

export function WorkflowArchitecture() {
  const [activeStepIndex, setActiveStepIndex] = useState<number>(0);
  const [direction, setDirection] = useState<number>(1);

  const currentStep = STEPS[activeStepIndex];

  const handleStepSelect = (newIdx: number) => {
    if (newIdx === activeStepIndex) return;
    setDirection(newIdx > activeStepIndex ? 1 : -1);
    setActiveStepIndex(newIdx);
  };

  const handleNextStep = () => {
    setDirection(1);
    setActiveStepIndex((prev) => (prev + 1) % STEPS.length);
  };

  return (
    <section className="lp__section lp__workflow-section" id="workflow">
      <div className="container--1286">
        <div className="lp__section-header lp__reveal">
          <div className="eyebrow-wrapper">
            <span className="lp__eyebrow-dot" />
            <span className="eyebrow--text">DOVETAIL-INSPIRED WORKFLOW ARCHITECTURE</span>
          </div>
          <h2 className="heading--h2">How industrial teams run on AIConneX</h2>
          <p className="section--subtitle-text">
            A seamless 4-step continuum from physical telemetry ingestion to closed-loop resolution.
          </p>
        </div>

        {/* ── 4-Step Animated Indicator Row (React Bits Stepper Style) ──────── */}
        <div className="lp__workflow-tabs lp__reveal" role="tablist">
          {STEPS.map((step, idx) => {
            const isActive = activeStepIndex === idx;
            return (
              <button
                key={step.stepNum}
                type="button"
                className={`lp__workflow-tab-btn${isActive ? ' lp__workflow-tab-btn--active' : ''}`}
                onClick={() => handleStepSelect(idx)}
                role="tab"
                aria-selected={isActive}
              >
                {isActive && (
                  <motion.div
                    layoutId="activeWorkflowTabPill"
                    className="lp__workflow-tab-pill-highlight"
                    transition={{ type: 'spring', stiffness: 400, damping: 35 }}
                  />
                )}
                <span className="lp__workflow-tab-step">{step.stepNum}</span>
                <span className="lp__workflow-tab-title">{step.shortTitle}</span>
              </button>
            );
          })}
        </div>

        {/* ── Animated Active Step Panel Container ───────────────────────── */}
        <div className="lp__workflow-card-wrapper relative overflow-hidden">
          <AnimatePresence initial={false} mode="wait" custom={direction}>
            <motion.div
              key={activeStepIndex}
              custom={direction}
              variants={cardVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.35, ease: 'easeInOut' }}
              className="lp__workflow-card lp__reveal"
            >
              <div className="lp__workflow-card-left">
                <span className="lp__workflow-pill">{currentStep.pillTag}</span>
                <h3 className="lp__workflow-heading">{currentStep.heading}</h3>
                <p className="lp__workflow-desc">{currentStep.description}</p>

                <ul className="lp__workflow-bullets">
                  {currentStep.bullets.map((bullet) => (
                    <li key={bullet}>
                      <span className="lp__bullet-check">✓</span>
                      <span>{bullet}</span>
                    </li>
                  ))}
                </ul>

                {currentStep.nextStepTitle && (
                  <button
                    type="button"
                    className="lp__workflow-next-btn"
                    onClick={handleNextStep}
                  >
                    NEXT STEP: {currentStep.nextStepTitle} <span className="lp__arrow">→</span>
                  </button>
                )}
              </div>

              <div className="lp__workflow-card-right">
                <div className="lp__engine-terminal">
                  <div className="lp__engine-top">
                    <div className="lp__engine-dots">
                      <span className="lp__mockup-dot" />
                      <span className="lp__mockup-dot" />
                      <span className="lp__mockup-dot" />
                    </div>
                    <span className="lp__engine-title">{currentStep.engineHeader}</span>
                    <span className="lp__engine-badge">REALTIME PIPELINE</span>
                  </div>

                  <div className="lp__engine-rows">
                    {currentStep.rows.map((row) => (
                      <div key={row.name} className="lp__engine-row">
                        <div className="lp__engine-row-left">
                          <span className="material-symbols-outlined lp__engine-icon">memory</span>
                          <div>
                            <div className="lp__engine-node-name">{row.name}</div>
                            <div className="lp__engine-node-sub">{row.sub}</div>
                          </div>
                        </div>
                        <div className="lp__engine-row-right">
                          <div className="lp__engine-metric">{row.metric}</div>
                          <div className="lp__engine-detail">{row.detail}</div>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="lp__engine-footer">{currentStep.footerBanner}</div>
                </div>
              </div>
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </section>
  );
}

export default WorkflowArchitecture;
