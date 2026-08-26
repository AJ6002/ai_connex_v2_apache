interface PillarCard {
  featureTag: string;
  metricVal: string;
  metricLabel: string;
  title: string;
  subtitle: string;
  bullets: string[];
  cardNumber: string;
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
  },
];

export function CorePillars() {
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
            Built for mission-critical scale.
          </h2>
          <p className="section--subtitle-text">
            Explore the 4 core pillars that turn raw industrial noise into high-confidence predictive maintenance decisions.
          </p>
        </div>

        {/* ── 2x2 Grid of Feature Pillar Cards ───────────────────────── */}
        <div className="lp__pillars-grid lp__reveal">
          {PILLARS.map((card) => (
            <div key={card.featureTag} className="lp__pillar-card">
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
          ))}
        </div>
      </div>
    </section>
  );
}
