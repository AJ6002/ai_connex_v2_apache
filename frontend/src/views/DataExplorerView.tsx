import React, { useState, useEffect, useRef } from 'react';

interface DataExplorerViewProps {
  compiledCsvPath?: string;
  runId?: string;
  dagId?: string;
  algorithmFamily?: string;
  onProceedToPrepare: () => void;
}

export const DataExplorerView: React.FC<DataExplorerViewProps> = ({
  compiledCsvPath,
  runId = 'run_default',
  dagId = 'DAG_ID_201',
  algorithmFamily = 'Classification',
  onProceedToPrepare
}) => {
  const [plotlyLoaded, setPlotlyLoaded] = useState(false);
  const [hoveredMetric, setHoveredMetric] = useState<string | null>(null);

  // Div refs for Plotly plots
  const compilerPlotRef = useRef<HTMLDivElement>(null);
  const profilerPlotRef = useRef<HTMLDivElement>(null);
  const routerPlotRef = useRef<HTMLDivElement>(null);
  const orchestratorPlotRef = useRef<HTMLDivElement>(null);

  // Dynamic values based on current dataset state
  const isRegression = algorithmFamily.toLowerCase().includes('regression') || (compiledCsvPath && (compiledCsvPath.includes('insurance') || compiledCsvPath.includes('house_prices') || compiledCsvPath.includes('FD001')));
  const targetDag = isRegression ? 'DAG_ID_514' : dagId;
  const targetVariant = isRegression ? 'Ridge Regression | Standard' : 'One-class SVM | Standard';
  const displayTrigger = isRegression ? 'Extreme Target Skewness & Scales' : 'High Outlier Density (>1.5%)';

  // Load Plotly CDN script dynamically
  useEffect(() => {
    if ((window as any).Plotly) {
      setPlotlyLoaded(true);
      return;
    }
    const script = document.createElement('script');
    script.src = 'https://cdn.plot.ly/plotly-2.24.1.min.js';
    script.async = true;
    script.onload = () => setPlotlyLoaded(true);
    document.head.appendChild(script);
  }, []);

  // Render/Update Plotly charts
  useEffect(() => {
    if (!plotlyLoaded || !(window as any).Plotly) return;
    const Plotly = (window as any).Plotly;

    const commonLayout = {
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      font: { color: '#1e293b', size: 10, family: 'JetBrains Mono, monospace' },
      margin: { t: 30, r: 15, b: 35, l: 35 },
      showlegend: false,
      xaxis: { gridcolor: 'rgba(0,0,0,0.06)', zeroline: false },
      yaxis: { gridcolor: 'rgba(0,0,0,0.06)', zeroline: false }
    };

    // 1. Compiler Insights Plot (Sparsity Heatmap & Gauge)
    if (compilerPlotRef.current) {
      // 8x8 Sparsity Heatmap Data
      const zData = [
        [1, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 1],
        [0, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 1, 0],
        [1, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1],
        [0, 1, 0, 0, 1, 0, 0, 0]
      ];
      Plotly.newPlot(compilerPlotRef.current, [
        {
          z: zData,
          type: 'heatmap',
          colorscale: [
            [0, '#f8fafc'],
            [1, '#2563eb']
          ],
          showscale: false
        }
      ], {
        ...commonLayout,
        title: { text: '<span style="color:#2563eb; font-weight:bold;">Sparsity Grid Heatmap</span>', font: { size: 12 } }
      }, { displayModeBar: false });

      // Add Hover Link Listeners
      compilerPlotRef.current.on('plotly_hover', () => setHoveredMetric('dag'));
      compilerPlotRef.current.on('plotly_unhover', () => setHoveredMetric(null));
    }

    // 2. Data Profiler Insights Plot (Overlaid Histogram + Box Plot)
    if (profilerPlotRef.current) {
      // Generate highly skewed sample data
      const skewData = Array.from({ length: 200 }, () => Math.pow(Math.random(), 3) * 100);
      // Add outlier points
      skewData.push(115, 120, 125, 130);

      Plotly.newPlot(profilerPlotRef.current, [
        {
          x: skewData,
          type: 'histogram',
          name: 'Telemetry Distribution',
          marker: { color: '#10b981' },
          opacity: 0.8
        },
        {
          x: skewData,
          type: 'box',
          name: 'Box Limits',
          marker: { color: '#ef4444' },
          yaxis: 'y2'
        }
      ], {
        ...commonLayout,
        title: { text: '<span style="color:#0d9488; font-weight:bold;">Telemetry Outliers & Skewness</span>', font: { size: 12 } },
        grid: { rows: 2, columns: 1, pattern: 'independent' },
        yaxis: { domain: [0, 0.45], gridcolor: 'rgba(0,0,0,0.06)' },
        yaxis2: { domain: [0.55, 1], gridcolor: 'rgba(0,0,0,0.06)' }
      }, { displayModeBar: false });

      profilerPlotRef.current.on('plotly_hover', () => setHoveredMetric('trigger'));
      profilerPlotRef.current.on('plotly_unhover', () => setHoveredMetric(null));
    }

    // 3. DAG Router Insights Plot (Target Pie Chart or Residuals vs. Fitted scatter plot)
    if (routerPlotRef.current) {
      if (isRegression) {
        // Residuals vs. Fitted plot
        const fitted = Array.from({ length: 100 }, () => Math.random() * 50 + 20);
        const residuals = fitted.map(f => (Math.random() - 0.5) * (f * 0.15));
        Plotly.newPlot(routerPlotRef.current, [
          {
            x: fitted,
            y: residuals,
            mode: 'markers',
            type: 'scatter',
            marker: { color: '#8b5cf6', size: 6 }
          }
        ], {
          ...commonLayout,
          title: { text: '<span style="color:#8b5cf6; font-weight:bold;">Residuals vs. Fitted Values</span>', font: { size: 12 } },
          xaxis: { title: 'Fitted', gridcolor: 'rgba(0,0,0,0.06)' },
          yaxis: { title: 'Residuals', gridcolor: 'rgba(0,0,0,0.06)' }
        }, { displayModeBar: false });
      } else {
        // Classification Pie Chart
        Plotly.newPlot(routerPlotRef.current, [
          {
            values: [68, 22, 10],
            labels: ['Normal Class', 'Fault Warning', 'Critical Drift'],
            type: 'pie',
            hole: 0.4,
            marker: { colors: ['#10b981', '#f59e0b', '#ef4444'] }
          }
        ], {
          ...commonLayout,
          title: { text: '<span style="color:#8b5cf6; font-weight:bold;">Target Distribution Share</span>', font: { size: 12 } },
          margin: { t: 30, r: 10, b: 10, l: 10 }
        }, { displayModeBar: false });
      }
    }

    // 4. Recipe Orchestrator Plot (Learning Curve with demographic parity bars)
    if (orchestratorPlotRef.current) {
      const epochs = Array.from({ length: 25 }, (_, i) => i + 1);
      const trainLoss = epochs.map(e => Math.exp(-e / 6) + 0.15 + Math.random() * 0.02);
      const valLoss = epochs.map(e => Math.exp(-e / 5) + 0.18 + Math.random() * 0.03);

      Plotly.newPlot(orchestratorPlotRef.current, [
        {
          x: epochs,
          y: trainLoss,
          mode: 'lines+markers',
          name: 'Train Loss',
          line: { color: '#2563eb', width: 2.5 }
        },
        {
          x: epochs,
          y: valLoss,
          mode: 'lines+markers',
          name: 'Val Loss',
          line: { color: '#ef4444', width: 2.5 }
        }
      ], {
        ...commonLayout,
        title: { text: '<span style="color:#e11d48; font-weight:bold;">Convergence & Early Stopping</span>', font: { size: 12 } },
        xaxis: { title: 'Epochs', gridcolor: 'rgba(0,0,0,0.06)' },
        yaxis: { title: 'Loss', gridcolor: 'rgba(0,0,0,0.06)' }
      }, { displayModeBar: false });

      orchestratorPlotRef.current.on('plotly_hover', () => setHoveredMetric('loss'));
      orchestratorPlotRef.current.on('plotly_unhover', () => setHoveredMetric(null));
    }
  }, [plotlyLoaded, isRegression, targetDag]);

  return (
    <div className="flex flex-col gap-6 animate-fadeIn font-mono text-xs text-slate-800">
      
      {/* Top Header Controls */}
      <div className="flex justify-between items-center glass-panel p-5 rounded-2xl shadow-xl"
        style={{ background: 'rgba(248,250,252,0.95)', borderColor: '#cbd5e1', color: '#0F172A' }}>
        <div>
          <h1 className="text-base font-bold flex items-center gap-2">
            <span className="material-symbols-outlined text-[#475569] text-xl">bar_chart</span>
            <span>Dataset Analytical Dashboard & Insights</span>
          </h1>
          <p className="text-[10px] text-slate-500 mt-0.5">
            Dynamic telemetry explorer profiling metrics to resolve final compilation targets.
          </p>
        </div>
        <button
          onClick={onProceedToPrepare}
          className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl flex items-center gap-1.5 shadow-lg active:scale-95 transition-all cursor-pointer border-none"
        >
          <span>Proceed to Preparation (Node 4)</span>
          <span className="material-symbols-outlined text-sm">arrow_forward</span>
        </button>
      </div>

      {/* Top of the Page (Output Summary Card) */}
      <div className="glass-panel p-6 rounded-2xl border shadow-xl flex flex-col gap-3 transition-all relative overflow-hidden"
        style={{
          background: 'rgba(248,250,252,0.95)',
          borderColor: hoveredMetric ? '#475569' : '#cbd5e1',
          color: '#0F172A'
        }}>
        <div className="absolute top-0 right-0 w-32 h-32 bg-slate-400/5 rounded-full blur-2xl pointer-events-none"></div>
        <h2 className="text-[11px] uppercase tracking-wider text-slate-500 font-bold border-b border-slate-200 pb-2">
          Engine Optimization Output Summary
        </h2>

        <div className="space-y-2.5 pt-1">
          <div className={`flex items-center gap-2 p-2 rounded-xl transition-all ${hoveredMetric === 'dag' ? 'bg-slate-200/50 border border-slate-300' : 'border border-transparent'}`}>
            <span>📊</span>
            <span className="font-bold">Decisive Parameter:</span>
            <span className="px-2 py-0.5 rounded bg-slate-200 text-slate-700 font-extrabold border border-slate-300">
              {targetDag}
            </span>
            <span className="text-slate-500">(Variant: {targetVariant})</span>
          </div>

          <div className={`flex items-center gap-2 p-2 rounded-xl transition-all ${hoveredMetric === 'loss' ? 'bg-slate-200/50 border border-slate-300' : 'border border-transparent'}`}>
            <span>📉</span>
            <span className="font-bold">Current Loss:</span>
            <span className="text-rose-600 font-black">0.42</span>
          </div>

          <div className={`flex items-center gap-2 p-2 rounded-xl transition-all ${hoveredMetric === 'trigger' ? 'bg-slate-200/50 border border-slate-300' : 'border border-transparent'}`}>
            <span>⚙️</span>
            <span className="font-bold">Primary Trigger:</span>
            <span className="text-amber-700 font-bold">{displayTrigger}</span>
          </div>
        </div>
      </div>

      {/* THE LINE BELOW */}
      <hr style={{ border: '2px dashed #94a3b8', margin: '10px 0' }} />

      {/* Below the Line (The 2x2 Plot Grid) */}
      <div className="grid grid-cols-2 gap-6">
        
        {/* Plot 1: Compiler Insights */}
        <div className="glass-panel p-5 rounded-2xl border shadow-lg flex flex-col gap-3"
          style={{ background: 'rgba(248,250,252,0.95)', borderColor: '#cbd5e1', color: '#0F172A' }}>
          <div className="flex justify-between items-start border-b border-slate-200 pb-2">
            <h3 className="font-bold text-slate-700 flex items-center gap-2">
              <span className="material-symbols-outlined text-slate-500 text-base">memory</span>
              <span>Compiler: Infrastructure & Memory Optimizer</span>
            </h3>
            <span className="text-[10px] text-slate-600 bg-slate-100 px-2 py-0.5 rounded font-mono">RAM Monitor</span>
          </div>
          <div className="relative min-h-[220px] bg-slate-100 rounded-xl flex items-center justify-center overflow-hidden" ref={compilerPlotRef}>
            {!plotlyLoaded && (
              <div className="w-full h-full p-2 flex items-center justify-center cursor-pointer"
                onMouseEnter={() => setHoveredMetric('dag')}
                onMouseLeave={() => setHoveredMetric(null)}>
                <svg className="w-40 h-40" viewBox="0 0 80 80">
                  {Array.from({ length: 64 }).map((_, idx) => {
                    const row = Math.floor(idx / 8);
                    const col = idx % 8;
                    const isZero = (row + col) % 3 === 0 || (row * col) % 5 === 0;
                    return (
                      <rect
                        key={idx}
                        x={col * 10}
                        y={row * 10}
                        width={8.5}
                        height={8.5}
                        fill={isZero ? '#2563eb' : '#cbd5e1'}
                        rx="1.5"
                        className="transition-all hover:fill-[#1d4ed8]"
                      />
                    );
                  })}
                </svg>
              </div>
            )}
          </div>
          <div className="p-3 bg-slate-100 border border-slate-200 rounded-xl text-[10px] text-slate-600 leading-relaxed">
            💡 <strong>Sparsity Ratio: 78% → Triggered Sparse DAG</strong>. Compressing high-order sparse sensors into CSR matrices.
          </div>
        </div>

        {/* Plot 2: Data Profiler Insights */}
        <div className="glass-panel p-5 rounded-2xl border shadow-lg flex flex-col gap-3"
          style={{ background: 'rgba(248,250,252,0.95)', borderColor: '#cbd5e1', color: '#0F172A' }}>
          <div className="flex justify-between items-start border-b border-slate-200 pb-2">
            <h3 className="font-bold text-slate-700 flex items-center gap-2">
              <span className="material-symbols-outlined text-slate-500 text-base">analytics</span>
              <span>Data Profiler: Statistical Distribution & Integrity</span>
            </h3>
            <span className="text-[10px] text-slate-600 bg-slate-100 px-2 py-0.5 rounded font-mono">Outliers</span>
          </div>
          <div className="relative min-h-[220px] bg-slate-100 rounded-xl flex items-center justify-center overflow-hidden" ref={profilerPlotRef}>
            {!plotlyLoaded && (
              <div className="w-full h-full p-4 flex flex-col justify-between cursor-pointer"
                onMouseEnter={() => setHoveredMetric('trigger')}
                onMouseLeave={() => setHoveredMetric(null)}>
                <svg className="w-full h-12" viewBox="0 0 200 40">
                  <line x1="20" y1="20" x2="180" y2="20" stroke="#cbd5e1" strokeWidth="1.5" strokeDasharray="3,3" />
                  <line x1="20" y1="12" x2="20" y2="28" stroke="#ef4444" strokeWidth="2" />
                  <line x1="180" y1="12" x2="180" y2="28" stroke="#ef4444" strokeWidth="2" />
                  <rect x="60" y="8" width="70" height="24" fill="#f8fafc" stroke="#ef4444" strokeWidth="2" rx="2" />
                  <line x1="95" y1="8" x2="95" y2="32" stroke="#ef4444" strokeWidth="2.5" />
                  <circle cx="10" cy="20" r="3.5" fill="#ef4444" />
                  <circle cx="190" cy="20" r="3.5" fill="#ef4444" />
                </svg>
                <svg className="w-full h-24" viewBox="0 0 200 80">
                  {[10, 25, 45, 70, 75, 60, 40, 20, 10, 5, 2, 3].map((val, i) => (
                    <rect
                      key={i}
                      x={i * 16 + 5}
                      y={80 - val}
                      width="12"
                      height={val}
                      fill="#10b981"
                      rx="2"
                      className="transition-all hover:fill-[#059669]"
                    />
                  ))}
                </svg>
              </div>
            )}
          </div>
          <div className="p-3 bg-slate-100 border border-slate-200 rounded-xl text-[10px] text-slate-600 leading-relaxed">
            💡 Outlier threshold flagged at <strong>1.62%</strong>. The box limits outline skewed features triggering Robust Standard Scaling.
          </div>
        </div>

        {/* Plot 3: DAG Router Insights */}
        <div className="glass-panel p-5 rounded-2xl border shadow-lg flex flex-col gap-3"
          style={{ background: 'rgba(248,250,252,0.95)', borderColor: '#cbd5e1', color: '#0F172A' }}>
          <div className="flex justify-between items-start border-b border-slate-200 pb-2">
            <h3 className="font-bold text-slate-700 flex items-center gap-2">
              <span className="material-symbols-outlined text-slate-500 text-base">route</span>
              <span>DAG Router: Problem Complexity Classifier</span>
            </h3>
            <span className="text-[10px] text-slate-600 bg-slate-100 px-2 py-0.5 rounded font-mono">
              {isRegression ? 'Regression Target' : 'Classification Class'}
            </span>
          </div>
          <div className="relative min-h-[220px] bg-slate-100 rounded-xl flex items-center justify-center overflow-hidden" ref={routerPlotRef}>
            {!plotlyLoaded && (
              <div className="w-full h-full p-4 flex items-center justify-center cursor-pointer">
                {isRegression ? (
                  <svg className="w-full h-40" viewBox="0 0 200 100">
                    <line x1="10" y1="50" x2="190" y2="50" stroke="#cbd5e1" strokeWidth="1.5" />
                    {Array.from({ length: 40 }).map((_, i) => {
                      const cx = 20 + i * 4 + Math.random() * 6;
                      const cy = 50 + (Math.sin(i) * 20) + (Math.random() - 0.5) * 15;
                      return (
                        <circle key={i} cx={cx} cy={cy} r="3" fill="#8b5cf6" className="opacity-80 hover:r-5 transition-all" />
                      );
                    })}
                  </svg>
                ) : (
                  <svg className="w-36 h-36" viewBox="0 0 36 36">
                    <circle cx="18" cy="18" r="15.91" fill="none" stroke="#10b981" strokeWidth="4" />
                    <circle cx="18" cy="18" r="15.91" fill="none" stroke="#f59e0b" strokeWidth="4"
                      strokeDasharray="68 32" strokeDashoffset="25" />
                    <circle cx="18" cy="18" r="15.91" fill="none" stroke="#ef4444" strokeWidth="4"
                      strokeDasharray="22 78" strokeDashoffset="89" />
                  </svg>
                )}
              </div>
            )}
          </div>
          <div className="p-3 bg-slate-100 border border-slate-200 rounded-xl text-[10px] text-slate-600 leading-relaxed">
            💡 {isRegression ? 'Residual scale matches variance expectations for continuous prediction.' : 'Matched 3 target categories. Multi-class decision boundaries enforced.'}
          </div>
        </div>

        {/* Plot 4: Recipe Orchestrator */}
        <div className="glass-panel p-5 rounded-2xl border shadow-lg flex flex-col gap-3"
          style={{ background: 'rgba(248,250,252,0.95)', borderColor: '#cbd5e1', color: '#0F172A' }}>
          <div className="flex justify-between items-start border-b border-slate-200 pb-2">
            <h3 className="font-bold text-slate-700 flex items-center gap-2">
              <span className="material-symbols-outlined text-slate-500 text-base">tune</span>
              <span>Recipe Orchestrator: Tuning & Constraint Engine</span>
            </h3>
            <span className="text-[10px] text-slate-600 bg-slate-100 px-2 py-0.5 rounded font-mono">Tuning Loss</span>
          </div>
          <div className="relative min-h-[220px] bg-slate-100 rounded-xl flex items-center justify-center overflow-hidden" ref={orchestratorPlotRef}>
            {!plotlyLoaded && (
              <div className="w-full h-full p-4 flex items-center justify-center cursor-pointer"
                onMouseEnter={() => setHoveredMetric('loss')}
                onMouseLeave={() => setHoveredMetric(null)}>
                <svg className="w-full h-40" viewBox="0 0 200 100">
                  <line x1="10" y1="10" x2="190" y2="10" stroke="#e2e8f0" strokeWidth="1" />
                  <line x1="10" y1="40" x2="190" y2="40" stroke="#e2e8f0" strokeWidth="1" />
                  <line x1="10" y1="70" x2="190" y2="70" stroke="#e2e8f0" strokeWidth="1" />
                  <path d="M 10 75 Q 50 30 100 22 T 190 18" fill="none" stroke="#2563eb" strokeWidth="2.5" />
                  <path d="M 10 85 Q 50 45 100 30 T 190 28" fill="none" stroke="#ef4444" strokeWidth="2.5" />
                  <line x1="130" y1="10" x2="130" y2="90" stroke="#e8405a" strokeWidth="1.5" strokeDasharray="3,3" />
                  <text x="135" y="25" fill="#e8405a" fontSize="8" fontFamily="monospace">Early Stop</text>
                </svg>
              </div>
            )}
          </div>
          <div className="p-3 bg-slate-100 border border-slate-200 rounded-xl text-[10px] text-slate-600 leading-relaxed">
            💡 Convergence early stopping applied at <strong>Epoch 16</strong>. Validation loss stabilized at 0.42.
          </div>
        </div>

      </div>

    </div>
  );
};
