import { useState } from 'react';

interface PillarCard {
  featureTag: string;
  metricVal: string;
  metricLabel: string;
  title: string;
  subtitle: string;
  bullets: string[];
  cardNumber: string;
  keyword: string;
}

const PILLARS: PillarCard[] = [
  {
    featureTag: 'FEATURE 01 // INGESTION',
    metricVal: '500k+ msg/sec',
    metricLabel: 'ZERO-COPY THROUGHPUT',
    title: 'Neuron Ingestion Engine',
    subtitle: 'Zero-copy streaming from SCADA, OPC-UA, and historians without duplicate storage.',
    bullets: [
      'Direct Apache DataFusion integration bypassing cloud serialization overhead',
      'Unified schema normalization across legacy Modbus, Profinet, and modern MQTT',
      'Edge-buffer failover for intermittent industrial plant network connectivity',
    ],
    cardNumber: '01 / 04',
    keyword: 'ingestion',
  },
  {
    featureTag: 'FEATURE 02 // PREDICTIVE ML',
    metricVal: '72 Hours',
    metricLabel: 'PRE-FAILURE LEAD TIME',
    title: 'Predictive Anomaly Detection',
    subtitle: 'Unsupervised spatial-temporal models forecasting machine failures 72 hours ahead.',
    bullets: [
      'Continuous multi-variate vibration FFT & thermal degradation correlation',
      'Auto-adaptive baseline thresholds that dynamically adjust for seasonal plant load',
      'Zero false-positive suppression via automated signal filtering',
    ],
    cardNumber: '02 / 04',
    keyword: 'predictive ML',
  },
  {
    featureTag: 'FEATURE 03 // JANE COPILOT',
    metricVal: '99.4%',
    metricLabel: 'DIAGNOSIS ACCURACY',
    title: 'Conversational Root Cause Analysis',
    subtitle: 'Jane reasons across telemetry waveforms, OEM equipment manuals, and P&ID schematics.',
    bullets: [
      'Ask plain-English queries like "Why did Pump 3 discharge pressure drop at 14:00?"',
      'Instant cross-reference with 10+ years of historical technician repair logs',
      'Generates step-by-step mechanical remediation checklists with torque specs',
    ],
    cardNumber: '03 / 04',
    keyword: 'reasoning',
  },
  {
    featureTag: 'FEATURE 04 // CLOSED-LOOP ORCHESTRATION',
    metricVal: '< 30 Sec',
    metricLabel: 'AUTOMATED DISPATCH TIME',
    title: 'Autonomous Dispatch & Action',
    subtitle: 'Close the loop with instant CMMS integration, SAP PM work orders, and field routing.',
    bullets: [
      'Native two-way synchronization with SAP PM, IBM Maximo, and ServiceNow',
      'Automated spare part inventory reservation and technician skill-matching',
      'Closed-loop telemetry verification post-repair before closing work tickets',
    ],
    cardNumber: '04 / 04',
    keyword: 'automation',
  },
];

const TRIPLE_PILLARS = [...PILLARS, ...PILLARS, ...PILLARS];

export function CorePillars() {
  const [focusedIndex, setFocusedIndex] = useState<number>(0);

  const activeCard = PILLARS[focusedIndex % PILLARS.length];

  return (
    <section className="lp__section lp__pillars-section" id="solutions">
      <div className="container--1286">
        <div className="lp__section-header lp__reveal">
          <div className="eyebrow-wrapper">
            <span className="lp__eyebrow-dot" />
            <span className="eyebrow--text">SOLUTIONS & DATA ARCHITECTURE</span>
          </div>
          <h2 className="heading--h2">
            Engineered for the physical world.<br />
            Built for <span className="lp__title-highlight-blue">{activeCard.keyword}</span> scale.
          </h2>
          <p className="section--subtitle-text">
            Explore the core pillars turning raw industrial telemetry into high-confidence autonomous maintenance decisions. Hover over any card to inspect.
          </p>
        </div>
      </div>

      {/* ── Infinite Horizontal Scrolling Card Marquee Carousel ───────── */}
      <div className="lp__pillars-marquee-wrapper lp__reveal">
        <div className="lp__pillars-marquee-track">
          {TRIPLE_PILLARS.map((card, idx) => {
            const pillarIndex = idx % PILLARS.length;
            const isFocused = pillarIndex === (focusedIndex % PILLARS.length);

            return (
              <div
                key={`${card.featureTag}-${idx}`}
                className={`lp__pillar-card ${
                  isFocused ? 'lp__pillar-card--focused' : 'lp__pillar-card--unfocused'
                }`}
                onMouseEnter={() => setFocusedIndex(pillarIndex)}
              >
                <div className="lp__pillar-header">
                  <span className="lp__pillar-tag">{card.featureTag}</span>
                  <div className="lp__pillar-metric-box">
                    <div className="lp__pillar-metric-val">{card.metricVal}</div>
                    <div className="lp__pillar-metric-label">{card.metricLabel}</div>
                  </div>
                </div>

                <h3 className="lp__pillar-title">{card.title}</h3>
                <p className="lp__pillar-sub">{card.subtitle}</p>

                <ul className="lp__pillar-bullets">
                  {card.bullets.map((b) => (
                    <li key={b}>
                      <span className="lp__bullet-check">✓</span>
                      <span>{b}</span>
                    </li>
                  ))}
                </ul>

                <div className="lp__pillar-footer">
                  <a href="#deep-dive" className="lp__pillar-link">
                    DEEP DIVE ARCHITECTURE <span className="lp__arrow">↗</span>
                  </a>
                  <span className="lp__pillar-num">{card.cardNumber}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

export default CorePillars;
