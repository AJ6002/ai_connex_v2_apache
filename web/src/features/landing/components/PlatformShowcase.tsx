import { useState } from 'react';

interface PlatformTab {
  id: string;
  name: string;
  label: string;
  subtext: string;
  colorClass: string;
  iconSvg: React.ReactNode;
}

const PLATFORM_TABS: PlatformTab[] = [
  {
    id: 'Neuron',
    name: 'Neuron',
    label: 'Data platform',
    subtext: 'Get your messy, multi-source data machine-ready.',
    colorClass: 'lp__tab-icon--neuron',
    iconSvg: (
      <svg width="100%" viewBox="0 0 24 24" fill="none" className="hp--platform-tabs-link-icon">
        <path d="M21.75 18.9641V6.96411H15.25V18.9641" stroke="currentColor" strokeWidth="2" />
        <path d="M15.25 18.9641V12.9282L8.75 12.9641V18.9641" stroke="currentColor" strokeWidth="2" />
        <path d="M8.75 18.9641V1.96411H2.25V18.9641" stroke="currentColor" strokeWidth="2" />
        <path d="M1.25 21.9641H22.75" stroke="currentColor" strokeWidth="2" />
      </svg>
    ),
  },
  {
    id: 'Atomic',
    name: 'Atomic',
    label: 'Process builder',
    subtext: 'Document manual workflows for automation.',
    colorClass: 'lp__tab-icon--atomic',
    iconSvg: (
      <svg width="100%" viewBox="0 0 24 24" fill="none" className="hp--platform-tabs-link-icon">
        <g clipPath="url(#clip_atomic_icon)">
          <path d="M17 4V10.5L12 13L7 10.5V4L12 1.5L17 4Z" stroke="currentColor" strokeWidth="2" />
          <path d="M12 13V19.5L7 22L2 19.5V13L7 10.5L12 13Z" stroke="currentColor" strokeWidth="2" />
          <path d="M22 13V19.5L17 22L12 19.5V13L17 10.5L22 13Z" stroke="currentColor" strokeWidth="2" />
          <path d="M12 13L7 15.5L2 13" stroke="currentColor" strokeWidth="2" />
          <path d="M22 13L17 15.5L12 13" stroke="currentColor" strokeWidth="2" />
          <path d="M17 4L12 6.5L7 4" stroke="currentColor" strokeWidth="2" />
        </g>
        <defs>
          <clipPath id="clip_atomic_icon">
            <rect width="24" height="24" fill="currentColor" />
          </clipPath>
        </defs>
      </svg>
    ),
  },
  {
    id: 'Meridial',
    name: 'Meridial',
    label: 'Expert network',
    subtext: 'We source elite domain experts for on-demand projects.',
    colorClass: 'lp__tab-icon--meridial',
    iconSvg: (
      <svg width="100%" viewBox="0 0 24 24" fill="none" className="hp--platform-tabs-link-icon">
        <g>
          <path d="M15 22V18H19V14H21.5L18.6539 6.60007C17.3562 3.22623 14.1148 1 10.5 1C5.80558 1 2 4.80558 2 9.5C2 12.5419 3.59785 15.2105 6 16.7124V22" stroke="currentColor" strokeWidth="2" />
          <path d="M10.7693 4.59155L6.26953 6.95155V11.9515L10.7695 14.3215L15.2695 11.9515V6.95155L10.7693 4.59155Z" stroke="currentColor" strokeWidth="2" />
          <path d="M10.7695 8.45142V10.4514" stroke="currentColor" strokeWidth="2" />
        </g>
      </svg>
    ),
  },
  {
    id: 'Synapse',
    name: 'Synapse',
    label: 'Evaluations',
    subtext: 'Run rigorous evaluation for quality, safety, and accuracy.',
    colorClass: 'lp__tab-icon--synapse',
    iconSvg: (
      <svg width="100%" viewBox="0 0 24 24" fill="none" className="hp--platform-tabs-link-icon">
        <g clipPath="url(#clip_synapse_icon)">
          <path d="M1 17V1H17L23 7V23H7L1 17Z" stroke="currentColor" strokeWidth="2" />
          <path d="M7 23V7H23" stroke="currentColor" strokeWidth="2" />
          <path d="M17 1V17H1" stroke="currentColor" strokeWidth="2" />
          <path d="M1 1L7 7" stroke="currentColor" strokeWidth="2" />
          <path d="M17 17L23 23" stroke="currentColor" strokeWidth="2" />
        </g>
        <defs>
          <clipPath id="clip_synapse_icon">
            <rect width="24" height="24" fill="currentColor" />
          </clipPath>
        </defs>
      </svg>
    ),
  },
  {
    id: 'Axon',
    name: 'Axon',
    label: 'Agents',
    subtext: 'Build governed agents that mirror your workflows.',
    colorClass: 'lp__tab-icon--axon',
    iconSvg: (
      <svg width="100%" viewBox="0 0 24 24" fill="none" className="hp--platform-tabs-link-icon">
        <g clipPath="url(#clip_axon_icon)">
          <path d="M15.502 7.5H16.502V8.5H15.502V7.5Z" stroke="currentColor" strokeWidth="2" />
          <path d="M22.0058 18.4952V5.49522L12.0058 1.09521L2.00586 5.49522V18.4952L12.0058 22.9052L22.0058 18.4952Z" stroke="currentColor" strokeWidth="2" />
          <path d="M5.5 13.75C8.27778 13.75 10.5 11.5278 10.5 8.75C10.5 11.5278 12.7222 13.75 15.5 13.75C12.7222 13.75 10.5 15.9722 10.5 18.75C10.5 15.9722 8.27778 13.75 5.5 13.75Z" stroke="currentColor" strokeWidth="2" />
        </g>
        <defs>
          <clipPath id="clip_axon_icon">
            <rect width="24" height="24" fill="currentColor" />
          </clipPath>
        </defs>
      </svg>
    ),
  },
];

export function PlatformShowcase() {
  const [activeTab, setActiveTab] = useState<string>('Neuron');

  const currentTab = PLATFORM_TABS.find((t) => t.id === activeTab) || PLATFORM_TABS[0];

  return (
    <section className="lp__showcase" id="platform">
      <div className="container--1286">
        <div className="component--head-row-2-col lp__reveal">
          <div className="section--heading">
            <div className="eyebrow-wrapper">
              <div data-wf--pulsing-dot--variant="laserpink-brand" className="pulsing-dot--wrapper">
                <div className="pulsing-dot--static" />
                <div className="pulsing-dot--animated" />
              </div>
              <div className="eyebrow--text">Our platform</div>
            </div>
            <h2 className="heading--h2">
              Building blocks,<br className="lp__h2-br" />not black boxes
            </h2>
          </div>
          <div className="section--subtitle">
            <div className="text--body _800">
              Deploy on your existing stack, configure for your operations, train on your data. Models get smarter as your business changes.
              <br /><br />
              Infrastructure that evolves with AI, not software dated at rollout.&nbsp;
            </div>
          </div>
        </div>

        {/* CTA link bar */}
        <div className="cta--link lp__reveal">
          <div className="text--body-large">Get a tailored walkthrough</div>
          <a href="#demo" className="hp--swiper-cta-button electric-blue w-inline-block">
            <div className="caption--uppercase">Book a demo</div>
            <svg width="100%" viewBox="0 0 12 12" fill="none" className="svg-arrow">
              <g clipPath="url(#clip_demo_arrow)">
                <path d="M9.3666 1.95002L0.938476 1.95002L0.938476 0.918775L10.1102 0.918774L10.1102 1.92659L11.118 1.92659L11.118 11.0977L10.0861 11.0983L10.0861 2.66956L1.6375 11.1188L0.917969 11.1188L0.917969 10.3987L9.3666 1.95002Z" fill="currentColor" />
              </g>
              <defs>
                <clipPath id="clip_demo_arrow">
                  <rect width="12" height="12" fill="currentColor" />
                </clipPath>
              </defs>
            </svg>
          </a>
        </div>

        <div className="hp--platform-tabs w-tabs lp__reveal">
          <div className="hp--platform-tabs-menu w-tab-menu" role="tablist">
            {PLATFORM_TABS.map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  type="button"
                  className={`hp--platform-tabs-link w-inline-block w-tab-link${isActive ? ' w--current' : ''}`}
                  onClick={() => setActiveTab(tab.id)}
                  aria-selected={isActive}
                  role="tab"
                >
                  <div className="hp--platform-tabs-link-label">
                    <span className={`hp--platform-tabs-icon-wrap ${isActive ? tab.colorClass : ''}`}>
                      {tab.iconSvg}
                    </span>
                    <div>{tab.label}</div>
                  </div>
                  <svg
                    width="100%"
                    viewBox="0 0 29 29"
                    fill="none"
                    className="hp--platform-tabs-link-arrow"
                    style={{ opacity: isActive ? 1 : 0 }}
                  >
                    <g clipPath="url(#clip_tab_arrow)">
                      <path d="M22.9283 13.2935L12.9957 3.36083L14.211 2.14549L25.0199 12.9544L23.8322 14.1421L25.0199 15.3299L14.2117 26.1381L12.995 24.9228L22.9283 14.9894L3.01399 14.9901L2.16602 14.1421L3.01468 13.2935H22.9283Z" fill="currentColor" />
                    </g>
                    <defs>
                      <clipPath id="clip_tab_arrow">
                        <rect width="20" height="20" fill="currentColor" transform="translate(0 14.1421) rotate(-45)" />
                      </clipPath>
                    </defs>
                  </svg>
                </button>
              );
            })}
          </div>

          <div className="hp--platform-tabs-content w-tab-content">
            <div className="hp--platform-tabs-pane w-tab-pane w--tab-active">
              <div className="hp--platform-tabs-header">
                <div>
                  <h3 className="hp--platform-tabs-h3">{currentTab.name}</h3>
                  <div className="hp--platform-tabs-text">{currentTab.subtext}</div>
                </div>
                <svg
                  width="100%"
                  viewBox="0 0 36 36"
                  fill="none"
                  className="hp--platform-tabs-pane-icon"
                >
                  <g clipPath="url(#clip_pane_icon)">
                    <path d="M18 9.00403L18 15.754" stroke="currentColor" strokeWidth="2" className="lp__stroke-grey-500" />
                    <path d="M18 20.2474V26.9955" stroke="currentColor" strokeWidth="2" className="lp__stroke-grey-500" />
                    <path d="M8.99805 18.0001H15.748" stroke="currentColor" strokeWidth="2" className="lp__stroke-grey-500" />
                    <path d="M20.25 18.0001H27" stroke="currentColor" strokeWidth="2" className="lp__stroke-grey-500" />
                    <path d="M1.5 18C1.5 22.3761 3.23839 26.573 6.33274 29.6673C9.42709 32.7617 13.6239 34.5 18 34.5C22.3761 34.5 26.573 32.7617 29.6673 29.6673C32.7617 26.573 34.5 22.3761 34.5 18C34.5 13.6239 32.7617 9.42709 29.6673 6.33274C26.573 3.23839 22.3761 1.5 18 1.5C13.6239 1.5 9.42709 3.23839 6.33274 6.33274C3.23839 9.42709 1.5 13.6239 1.5 18Z" stroke="currentColor" strokeWidth="2" className="lp__stroke-grey-300" />
                  </g>
                  <defs>
                    <clipPath id="clip_pane_icon">
                      <rect width="36" height="36" fill="currentColor" />
                    </clipPath>
                  </defs>
                </svg>
              </div>

              {/* Interactive UI Mockup Preview Frame */}
              <div className="lp__mockup-window">
                <div className="lp__mockup-topbar">
                  <span className="lp__mockup-dot" />
                  <span className="lp__mockup-dot" />
                  <span className="lp__mockup-dot" />
                </div>

                <div className="lp__mockup-body">
                  <div className="lp__mockup-header">
                    <h4 className="lp__mockup-title">{currentTab.name} Overview</h4>
                    <p className="lp__mockup-sub">{currentTab.subtext}</p>
                  </div>

                  {/* Metrics row */}
                  <div className="lp__mockup-stats">
                    <div className="lp__stat-card">
                      <span className="lp__stat-label">Active Workflows</span>
                      <div className="lp__stat-val-row">
                        <span className="lp__stat-val">12</span>
                        <span className="lp__stat-badge lp__stat-badge--up">↗ 24%</span>
                      </div>
                    </div>
                    <div className="lp__stat-card">
                      <span className="lp__stat-label">Model Accuracy</span>
                      <div className="lp__stat-val-row">
                        <span className="lp__stat-val">99.4%</span>
                        <span className="lp__stat-badge lp__stat-badge--up">↗ 1.2%</span>
                      </div>
                    </div>
                    <div className="lp__stat-card">
                      <span className="lp__stat-label">Processed Items</span>
                      <div className="lp__stat-val-row">
                        <span className="lp__stat-val">142.8k</span>
                        <span className="lp__stat-badge lp__stat-badge--up">↗ 18%</span>
                      </div>
                    </div>
                  </div>

                  {/* Table */}
                  <div className="lp__mockup-table-wrap">
                    <table className="lp__mockup-table">
                      <thead>
                        <tr>
                          <th>Workflow / Pipeline</th>
                          <th>Status</th>
                          <th>Priority</th>
                          <th>Completion</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td className="lp__td-name">Multi-Source Ingestion Engine</td>
                          <td><span className="lp__badge lp__badge--active">ACTIVE</span></td>
                          <td><span className="lp__badge lp__badge--p0">P0</span></td>
                          <td>94.2%</td>
                        </tr>
                        <tr>
                          <td className="lp__td-name">Real-Time Event Triage & Routing</td>
                          <td><span className="lp__badge lp__badge--active">ACTIVE</span></td>
                          <td><span className="lp__badge lp__badge--p0">P0</span></td>
                          <td>88.6%</td>
                        </tr>
                        <tr>
                          <td className="lp__td-name">Automated Validation & Evaluation</td>
                          <td><span className="lp__badge lp__badge--scaling">SCALING UP</span></td>
                          <td><span className="lp__badge lp__badge--p1">P1</span></td>
                          <td>76.0%</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
