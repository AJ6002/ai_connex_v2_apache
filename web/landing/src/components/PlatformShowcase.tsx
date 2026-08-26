import React, { useState } from 'react';
import { ArrowUpRight, Database, Cpu, Users, Bot, Plus, Check, RefreshCw } from 'lucide-react';
import { PlatformTab } from '../types';

interface PlatformShowcaseProps {
  onBookDemo: () => void;
}

export const PlatformShowcase: React.FC<PlatformShowcaseProps> = ({ onBookDemo }) => {
  const [activeTab, setActiveTab] = useState<PlatformTab>('neuron');
  const [filterSource, setFilterSource] = useState('all');
  const [isSimulating, setIsSimulating] = useState(false);

  const handleSimulate = () => {
    setIsSimulating(true);
    setTimeout(() => {
      setIsSimulating(false);
    }, 1500);
  };

  return (
    <section id="platform-section" className="py-16 sm:py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-[#E2E4E6]">
      {/* Platform Header Badge & Description */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start mb-10">
        <div className="lg:col-span-6 space-y-4">
          <div className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-[#757964] font-mono">
            <span className="w-2 h-2 rounded-full bg-[#d4f658]" />
            <span>AI CONNE X PLATFORM</span>
          </div>

          <h2 className="text-3xl sm:text-5xl font-bold text-[#191c1d] tracking-tight leading-[1.1] font-sans">
            One platform. <br />
            Every AI workflow.
          </h2>
        </div>

        <div className="lg:col-span-6 space-y-4 text-[#666666] text-base sm:text-lg leading-relaxed pt-2">
          <p>
            Jane connects your data, analytics, ML and agentic workflows in one governed system.
          </p>
          <p>
            From exploration to deployment, the platform evolves with your workflow—not around it.
          </p>
        </div>
      </div>

      {/* Tailored Walkthrough Banner */}
      <div className="mb-10 bg-[#f3f4f5] border border-[#E2E4E6] rounded-2xl px-5 py-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-2xs">
        <div className="flex items-center gap-3">
          <span className="w-2 h-2 rounded-full bg-[#006df8]" />
          <span className="text-sm font-bold text-[#191c1d]">
            Get a tailored walkthrough with your plant telemetry
          </span>
        </div>
        <button
          id="platform-book-demo-banner-btn"
          onClick={onBookDemo}
          className="inline-flex items-center gap-1.5 text-xs font-mono font-bold text-[#000000] bg-[#d4f658] hover:bg-[#c4ea42] px-4 py-2 rounded-full uppercase tracking-wider cursor-pointer group transition-all"
        >
          <span>BOOK A DEMO</span>
          <ArrowUpRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform stroke-[2.5]" />
        </button>
      </div>

      {/* Main Interactive Showcase Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Navigation Tabs */}
        <div className="lg:col-span-4 space-y-3">
          {/* Tab 1: Data Platform (Neuron) */}
          <button
            id="tab-btn-neuron"
            onClick={() => setActiveTab('neuron')}
            className={`w-full text-left p-5 rounded-2xl border transition-all flex items-center justify-between cursor-pointer ${
              activeTab === 'neuron'
                ? 'bg-white border-[#191c1d] shadow-sm'
                : 'bg-[#f8f9fa] border-[#E2E4E6] hover:border-[#191c1d] text-[#666666]'
            }`}
          >
            <div className="flex items-center gap-3.5">
              <div className={`p-2.5 rounded-xl ${activeTab === 'neuron' ? 'bg-[#000000] text-white' : 'bg-[#e2e4e6] text-[#191c1d]'}`}>
                <Database className="w-5 h-5" />
              </div>
              <div>
                <div className={`text-base font-bold ${activeTab === 'neuron' ? 'text-[#191c1d]' : 'text-[#666666]'}`}>
                  Data platform
                </div>
                <div className="text-xs text-[#757964]">Neuron zero-copy engine</div>
              </div>
            </div>
            <ArrowUpRight className={`w-4 h-4 ${activeTab === 'neuron' ? 'text-[#191c1d]' : 'text-[#757964]'}`} />
          </button>

          {/* Tab 2: Process Builder */}
          <button
            id="tab-btn-process"
            onClick={() => setActiveTab('process-builder')}
            className={`w-full text-left p-5 rounded-2xl border transition-all flex items-center justify-between cursor-pointer ${
              activeTab === 'process-builder'
                ? 'bg-white border-[#191c1d] shadow-sm'
                : 'bg-[#f8f9fa] border-[#E2E4E6] hover:border-[#191c1d] text-[#666666]'
            }`}
          >
            <div className="flex items-center gap-3.5">
              <div className={`p-2.5 rounded-xl ${activeTab === 'process-builder' ? 'bg-[#000000] text-white' : 'bg-[#e2e4e6] text-[#191c1d]'}`}>
                <Cpu className="w-5 h-5" />
              </div>
              <div>
                <div className={`text-base font-bold ${activeTab === 'process-builder' ? 'text-[#191c1d]' : 'text-[#666666]'}`}>
                  Process builder
                </div>
                <div className="text-xs text-[#757964]">Visual DAG orchestration</div>
              </div>
            </div>
            <ArrowUpRight className={`w-4 h-4 ${activeTab === 'process-builder' ? 'text-[#191c1d]' : 'text-[#757964]'}`} />
          </button>

          {/* Tab 3: Expert Network */}
          <button
            id="tab-btn-expert"
            onClick={() => setActiveTab('expert-network')}
            className={`w-full text-left p-5 rounded-2xl border transition-all flex items-center justify-between cursor-pointer ${
              activeTab === 'expert-network'
                ? 'bg-white border-[#191c1d] shadow-sm'
                : 'bg-[#f8f9fa] border-[#E2E4E6] hover:border-[#191c1d] text-[#666666]'
            }`}
          >
            <div className="flex items-center gap-3.5">
              <div className={`p-2.5 rounded-xl ${activeTab === 'expert-network' ? 'bg-[#000000] text-white' : 'bg-[#e2e4e6] text-[#191c1d]'}`}>
                <Users className="w-5 h-5" />
              </div>
              <div>
                <div className={`text-base font-bold ${activeTab === 'expert-network' ? 'text-[#191c1d]' : 'text-[#666666]'}`}>
                  Expert network
                </div>
                <div className="text-xs text-[#757964]">Human-in-the-loop validation</div>
              </div>
            </div>
            <ArrowUpRight className={`w-4 h-4 ${activeTab === 'expert-network' ? 'text-[#191c1d]' : 'text-[#757964]'}`} />
          </button>

          {/* Tab 4: Jane Agent */}
          <button
            id="tab-btn-jane"
            onClick={() => setActiveTab('jane-agent')}
            className={`w-full text-left p-5 rounded-2xl border transition-all flex items-center justify-between cursor-pointer ${
              activeTab === 'jane-agent'
                ? 'bg-white border-[#191c1d] shadow-sm'
                : 'bg-[#f8f9fa] border-[#E2E4E6] hover:border-[#191c1d] text-[#666666]'
            }`}
          >
            <div className="flex items-center gap-3.5">
              <div className={`p-2.5 rounded-xl ${activeTab === 'jane-agent' ? 'bg-[#006df8] text-white' : 'bg-[#e2e4e6] text-[#191c1d]'}`}>
                <Bot className="w-5 h-5" />
              </div>
              <div>
                <div className={`text-base font-bold ${activeTab === 'jane-agent' ? 'text-[#191c1d]' : 'text-[#666666]'}`}>
                  Jane Agent
                </div>
                <div className="text-xs text-[#757964]">Autonomous industrial AI</div>
              </div>
            </div>
            <ArrowUpRight className={`w-4 h-4 ${activeTab === 'jane-agent' ? 'text-[#191c1d]' : 'text-[#757964]'}`} />
          </button>
        </div>

        {/* Right UI Interactive Screen Container */}
        <div className="lg:col-span-8 bg-white border border-[#E2E4E6] rounded-3xl p-6 sm:p-8 shadow-sm">
          {/* Header of Active View */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#E2E4E6]">
            <div>
              <h3 className="text-2xl sm:text-3xl font-bold text-[#191c1d] tracking-tight font-sans">
                {activeTab === 'neuron' && 'Neuron Data Platform'}
                {activeTab === 'process-builder' && 'Process Builder'}
                {activeTab === 'expert-network' && 'Expert Network'}
                {activeTab === 'jane-agent' && 'Jane Autonomous Agent'}
              </h3>
              <p className="text-sm text-[#666666] mt-1">
                {activeTab === 'neuron' && 'Get your multi-source industrial telemetry machine-ready with zero-copy Apache DataFusion.'}
                {activeTab === 'process-builder' && 'Compose visual DAG pipelines from sensor streams to edge inference models.'}
                {activeTab === 'expert-network' && 'Certified reliability engineers confirming high-risk anomaly dispatches.'}
                {activeTab === 'jane-agent' && 'Continuous spatial-temporal reasoning over mechanical telemetry and vibration spectra.'}
              </p>
            </div>

            <div className="flex items-center gap-2 self-start sm:self-center">
              <button 
                onClick={handleSimulate}
                disabled={isSimulating}
                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full border border-[#E2E4E6] bg-[#f8f9fa] hover:bg-[#f3f4f5] text-xs font-mono font-bold text-[#191c1d] transition cursor-pointer"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isSimulating ? 'animate-spin text-[#006df8]' : ''}`} />
                <span>{isSimulating ? 'Processing...' : 'Live Refresh'}</span>
              </button>
              <div className="w-8 h-8 rounded-full border border-[#E2E4E6] flex items-center justify-center text-[#666666] bg-[#f8f9fa]">
                <Plus className="w-4 h-4" />
              </div>
            </div>
          </div>

          {/* Sub-Card Window Mockup */}
          <div className="mt-6 bg-[#f8f9fa] border border-[#E2E4E6] rounded-2xl p-4 sm:p-6">
            {/* Top Stat Pills Row */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5 mb-6">
              <div className="bg-white border border-[#E2E4E6] rounded-xl p-4 shadow-2xs">
                <div className="text-[11px] font-bold uppercase tracking-widest text-[#757964] font-mono">
                  ACTIVE WORKFLOWS
                </div>
                <div className="mt-2 flex items-baseline justify-between">
                  <span className="text-2xl font-bold text-[#191c1d] font-mono">12</span>
                  <span className="inline-flex items-center text-xs font-bold text-[#000000] bg-[#d4f658] px-2 py-0.5 rounded-md font-mono">
                    ↗ 24%
                  </span>
                </div>
              </div>

              <div className="bg-white border border-[#E2E4E6] rounded-xl p-4 shadow-2xs">
                <div className="text-[11px] font-bold uppercase tracking-widest text-[#757964] font-mono">
                  MODEL ACCURACY
                </div>
                <div className="mt-2 flex items-baseline justify-between">
                  <span className="text-2xl font-bold text-[#191c1d] font-mono">99.4%</span>
                  <span className="inline-flex items-center text-xs font-bold text-[#000000] bg-[#d4f658] px-2 py-0.5 rounded-md font-mono">
                    ↗ 1.2%
                  </span>
                </div>
              </div>

              <div className="bg-white border border-[#E2E4E6] rounded-xl p-4 shadow-2xs">
                <div className="text-[11px] font-bold uppercase tracking-widest text-[#757964] font-mono">
                  PROCESSED ITEMS
                </div>
                <div className="mt-2 flex items-baseline justify-between">
                  <span className="text-2xl font-bold text-[#191c1d] font-mono">142.8k</span>
                  <span className="inline-flex items-center text-xs font-bold text-[#000000] bg-[#d4f658] px-2 py-0.5 rounded-md font-mono">
                    ↗ 18%
                  </span>
                </div>
              </div>
            </div>

            {/* Dynamic View Content based on Tab */}
            {activeTab === 'neuron' && (
              <div className="space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2 pb-2">
                  <span className="text-xs font-bold uppercase tracking-widest text-[#757964] font-mono">
                    Industrial Telemetry Stream (Zero-Copy DataFusion)
                  </span>
                  <div className="flex items-center gap-1.5">
                    {['all', 'scada', 'mqtt', 'opc-ua'].map((src) => (
                      <button
                        key={src}
                        onClick={() => setFilterSource(src)}
                        className={`text-[11px] px-2.5 py-1 rounded-md font-mono font-medium transition cursor-pointer ${
                          filterSource === src
                            ? 'bg-[#000000] text-white'
                            : 'bg-white text-[#666666] border border-[#E2E4E6] hover:bg-[#f3f4f5]'
                        }`}
                      >
                        {src.toUpperCase()}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Telemetry Stream Table */}
                <div className="overflow-x-auto bg-white border border-[#E2E4E6] rounded-xl">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-[#f8f9fa] text-[#757964] border-b border-[#E2E4E6]">
                      <tr>
                        <th className="py-2.5 px-3 font-semibold">ASSET / SENSOR</th>
                        <th className="py-2.5 px-3 font-semibold">PROTOCOL</th>
                        <th className="py-2.5 px-3 font-semibold">CURRENT VALUE</th>
                        <th className="py-2.5 px-3 font-semibold">ANOMALY SCORE</th>
                        <th className="py-2.5 px-3 font-semibold text-right">STATUS</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#E2E4E6]">
                      <tr className="hover:bg-[#f8f9fa] transition">
                        <td className="py-2.5 px-3 font-medium text-[#191c1d] flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-[#d4f658]" />
                          <span>Turbine_04 // Bearing_Vibe_X</span>
                        </td>
                        <td className="py-2.5 px-3 text-[#666666]">OPC-UA (100Hz)</td>
                        <td className="py-2.5 px-3 text-[#191c1d] font-bold">2.42 mm/s</td>
                        <td className="py-2.5 px-3 text-[#666666] font-semibold">0.03 (Normal)</td>
                        <td className="py-2.5 px-3 text-right">
                          <span className="bg-[#d4f658] text-[#000000] text-[10px] px-2 py-0.5 rounded font-bold">SYNCHRONIZED</span>
                        </td>
                      </tr>
                      <tr className="hover:bg-[#f8f9fa] transition bg-[#ad1e7a]/5">
                        <td className="py-2.5 px-3 font-medium text-[#191c1d] flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-[#ad1e7a] animate-pulse" />
                          <span>Compressor_12 // Head_Temp</span>
                        </td>
                        <td className="py-2.5 px-3 text-[#666666]">SCADA Modbus</td>
                        <td className="py-2.5 px-3 text-[#ad1e7a] font-bold">94.8 °C</td>
                        <td className="py-2.5 px-3 text-[#ad1e7a] font-semibold">0.82 (High Drift)</td>
                        <td className="py-2.5 px-3 text-right">
                          <span className="bg-[#ad1e7a] text-white text-[10px] px-2 py-0.5 rounded font-bold">ALERT JANE</span>
                        </td>
                      </tr>
                      <tr className="hover:bg-[#f8f9fa] transition">
                        <td className="py-2.5 px-3 font-medium text-[#191c1d] flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-[#d4f658]" />
                          <span>Hydraulic_Pump // Discharge_PSI</span>
                        </td>
                        <td className="py-2.5 px-3 text-[#666666]">MQTT Sparkplug</td>
                        <td className="py-2.5 px-3 text-[#191c1d] font-bold">2,140 PSI</td>
                        <td className="py-2.5 px-3 text-[#666666] font-semibold">0.01 (Optimal)</td>
                        <td className="py-2.5 px-3 text-right">
                          <span className="bg-[#d4f658] text-[#000000] text-[10px] px-2 py-0.5 rounded font-bold">SYNCHRONIZED</span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'process-builder' && (
              <div className="bg-white border border-[#E2E4E6] rounded-xl p-5 space-y-4">
                <div className="text-xs font-mono font-bold text-[#757964] uppercase tracking-widest">Visual DAG Pipeline Execution</div>
                <div className="flex flex-wrap items-center gap-3">
                  <div className="p-3 bg-[#000000] text-white rounded-xl text-xs font-mono flex items-center gap-2">
                    <Database className="w-4 h-4 text-[#d4f658]" />
                    <span>Raw OPC-UA Stream</span>
                  </div>
                  <span className="text-[#757964] font-mono">⟶</span>
                  <div className="p-3 bg-[#f8f9fa] border border-[#E2E4E6] text-[#191c1d] rounded-xl text-xs font-mono flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-[#006df8]" />
                    <span>FFT Frequency Transform</span>
                  </div>
                  <span className="text-[#757964] font-mono">⟶</span>
                  <div className="p-3 bg-[#f8f9fa] border border-[#E2E4E6] text-[#191c1d] rounded-xl text-xs font-mono flex items-center gap-2">
                    <Bot className="w-4 h-4 text-[#006df8]" />
                    <span>Jane Temporal Anomaly Model</span>
                  </div>
                  <span className="text-[#757964] font-mono">⟶</span>
                  <div className="p-3 bg-[#d4f658] border border-[#d4f658] text-[#000000] rounded-xl text-xs font-mono flex items-center gap-2 font-bold">
                    <Check className="w-4 h-4 text-[#000000]" />
                    <span>SAP PM Work Order Dispatch</span>
                  </div>
                </div>
                <div className="text-xs text-[#666666] font-mono pt-2">
                  Total Pipeline Latency: <strong className="text-[#191c1d]">4.2ms (Zero-Copy Memory Buffer)</strong>
                </div>
              </div>
            )}

            {activeTab === 'expert-network' && (
              <div className="bg-white border border-[#E2E4E6] rounded-xl p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="text-xs font-mono font-bold text-[#757964] uppercase tracking-widest">Reliability Engineering Peer-Review</div>
                  <span className="text-[10px] bg-[#d4f658] text-[#000000] font-mono font-bold px-2 py-0.5 rounded">3 EXPERTS ONLINE</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="p-3 bg-[#f8f9fa] rounded-xl border border-[#E2E4E6] text-xs">
                    <div className="font-bold text-[#191c1d]">Dr. Aris Thorne (Rotating Machinery)</div>
                    <div className="text-[#666666] text-[11px] mt-0.5">Verified Turbine #4 bearing raceway fatigue recommendation.</div>
                    <div className="mt-2 text-[10px] font-mono text-[#000000] bg-[#d4f658] inline-block px-1.5 py-0.5 rounded font-bold">
                      STATUS: SIGNED OFF
                    </div>
                  </div>
                  <div className="p-3 bg-[#f8f9fa] rounded-xl border border-[#E2E4E6] text-xs">
                    <div className="font-bold text-[#191c1d]">Sarah Lindqvist (Hydraulics Specialist)</div>
                    <div className="text-[#666666] text-[11px] mt-0.5">Calibrated pressure relief valve trigger thresholds.</div>
                    <div className="mt-2 text-[10px] font-mono text-[#191c1d] bg-[#f3f4f5] inline-block px-1.5 py-0.5 rounded font-bold">
                      STATUS: LIVE MONITORING
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'jane-agent' && (
              <div className="bg-white border border-[#E2E4E6] rounded-xl p-5 space-y-3 font-mono">
                <div className="flex items-center justify-between text-xs font-bold text-[#757964] uppercase tracking-widest">
                  <span>Jane Autonomous Reasoner Log</span>
                  <span className="text-[#191c1d] flex items-center gap-1.5 font-bold">
                    <span className="w-2 h-2 rounded-full bg-[#d4f658] animate-ping" />
                    AUTONOMOUS MODE ACTIVE
                  </span>
                </div>
                <div className="bg-[#0e1824] text-white p-4 rounded-xl text-xs space-y-2 border border-[#1f2d3d]">
                  <p className="text-[#8899a6]">[14:02:18] Telemetry Stream: Ingested 18,400 points from Plant #2.</p>
                  <p className="text-[#d4f658]">[14:02:19] Warning: High frequency vibration harmonic detected in Gearbox #3 (98.2 Hz).</p>
                  <p className="text-[#ffffff]">[14:02:20] Cross-correlated with historic lubricant degradation models. Failure probability in 68 hours: 91.4%.</p>
                  <p className="text-[#74c0fc]">[14:02:21] Auto-drafted maintenance order #WO-9082 for scheduled weekend bearing replacement.</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
};

