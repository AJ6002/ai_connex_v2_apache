import React, { useState, useMemo, useEffect } from 'react';
import Plot from 'react-plotly.js';
import {
  Workflow,
  GitCommit,
  ArrowRight,
  Sliders,
  Cpu,
  Search,
  CheckCircle,
  ShieldCheck,
  Activity,
  Layers,
  Sparkles,
  BarChart2,
  Database,
  LineChart as LineChartIcon,
  Maximize2,
  Filter,
  TrendingUp,
} from 'lucide-react';

// ─────────────────────────────────────────────────────────────────
// THEME CONSTANTS – single source of truth, matches index.css tokens
// ─────────────────────────────────────────────────────────────────
const T = {
  coral:       '#FF6B35',
  coralSoft:   '#FF8F5A',
  coralHover:  '#E85520',
  coralGlow:   'rgba(255,107,53,0.18)',
  eggplant:    '#280B43',
  eggplantMid: '#3A1259',
  eggplantDeep:'#1A0530',
  white:       '#FFFFFF',
  // light-theme surface equivalents (used for cards when bg-canvas is light)
  surfaceCard:   'var(--bg-card)',
  surfacePage:   'var(--bg-canvas)',
  borderLight:   'var(--border-light)',
  borderMedium:  'var(--border-medium)',
  textMain:      'var(--text-main)',
  textMuted:     'var(--text-muted)',
  // semantic status
  critical: '#ef4444',
  warning:  '#f59e0b',
  optimal:  '#10b981',
};

// ─────────────────────────────────────────────────────────────────
// Shared Plotly layout config (applied to every Plotly chart)
// ─────────────────────────────────────────────────────────────────
function buildPlotlyLayout(overrides: Partial<Plotly.Layout> = {}): Partial<Plotly.Layout> {
  return {
    margin:      { t: 12, r: 16, b: 38, l: 48 },
    paper_bgcolor: 'transparent',
    plot_bgcolor:  'transparent',
    font: { family: "'JetBrains Mono', monospace", size: 10, color: '#64748b' },
    xaxis: {
      gridcolor: 'rgba(100,116,139,0.12)',
      gridwidth: 1,
      zerolinecolor: 'rgba(100,116,139,0.20)',
      tickfont: { size: 10, family: "'JetBrains Mono', monospace" },
    },
    yaxis: {
      gridcolor: 'rgba(100,116,139,0.12)',
      gridwidth: 1,
      tickfont: { size: 10, family: "'JetBrains Mono', monospace" },
    },
    hoverlabel: {
      bgcolor:   '#0f172a',
      bordercolor: T.coral,
      font: { family: "'JetBrains Mono', monospace", size: 11, color: '#ffffff' },
    },
    showlegend: false,
    autosize:   true,
    ...overrides,
  };
}

const PLOTLY_CONFIG: Partial<Plotly.Config> = {
  displayModeBar: true,
  displaylogo: false,
  modeBarButtonsToRemove: ['lasso2d', 'select2d', 'toImage', 'sendDataToCloud'],
  responsive: true,
};

// ─────────────────────────────────────────────────────────────────
// Mini SVG charts for Diagnostic Signal cards (kept native – they
// are 100px thumbnail-sized and don't need Plotly overhead)
// ─────────────────────────────────────────────────────────────────
function MissingBarsChart({ data }: { data: Array<{ column: string; missing_pct: number }> }) {
  const items = (data?.length > 0) ? data.slice(0, 4) : [{ column: 'All Channels', missing_pct: 0 }];
  return (
    <div className="w-full h-full flex flex-col justify-center gap-1.5 px-2">
      {items.map((item, idx) => {
        const pct = Math.min(100, Math.max(0, item.missing_pct));
        const bar = pct > 10 ? T.critical : pct > 1 ? T.warning : T.optimal;
        return (
          <div key={idx}>
            <div className="flex justify-between text-[10px] font-mono mb-0.5" style={{ color: '#64748b' }}>
              <span className="truncate max-w-[130px] font-semibold">{item.column}</span>
              <span className="font-bold" style={{ color: bar }}>{pct.toFixed(1)}%</span>
            </div>
            <div className="w-full h-[7px] rounded-full overflow-hidden" style={{ background: 'rgba(100,116,139,0.15)' }}>
              <div className="h-full rounded-full" style={{ width: `${Math.max(3, pct)}%`, background: bar }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function SvgBoxPlot({ data }: { data: Record<string, any> }) {
  const min = data.min ?? 0; const p25 = data.p25 ?? 25; const median = data.median ?? 50;
  const p75 = data.p75 ?? 75; const max = data.max ?? 100;
  const range = (max - min) || 1;
  const gx = (v: number) => 24 + ((v - min) / range) * 252;
  return (
    <svg viewBox="0 0 300 90" className="w-full h-full">
      <line x1={gx(min)} y1="45" x2={gx(p25)} y2="45" stroke="#475569" strokeWidth="2" />
      <line x1={gx(p75)} y1="45" x2={gx(max)} y2="45" stroke="#475569" strokeWidth="2" />
      <line x1={gx(min)} y1="30" x2={gx(min)} y2="60" stroke="#475569" strokeWidth="2" />
      <line x1={gx(max)} y1="30" x2={gx(max)} y2="60" stroke="#475569" strokeWidth="2" />
      <rect x={gx(p25)} y="22" width={Math.max(3, gx(p75) - gx(p25))} height="46"
        rx="5" fill={T.coralGlow} stroke={T.coral} strokeWidth="2" />
      <line x1={gx(median)} y1="22" x2={gx(median)} y2="68" stroke={T.coral} strokeWidth="3" />
      <text x={gx(min)} y="20" textAnchor="middle" fill="#94a3b8" fontSize="8" fontFamily="monospace">Min</text>
      <text x={gx(median)} y="84" textAnchor="middle" fill={T.coral} fontSize="9" fontWeight="bold" fontFamily="monospace">Med: {median}</text>
      <text x={gx(max)} y="20" textAnchor="middle" fill="#94a3b8" fontSize="8" fontFamily="monospace">Max</text>
    </svg>
  );
}

function SvgSkewnessGauge({ data }: { data: Record<string, any> }) {
  const skew = data.skewness ?? 0;
  const px = 150 + (Math.max(-4, Math.min(4, skew)) / 4) * 110;
  const isSkewed = Math.abs(skew) > 1.5;
  return (
    <svg viewBox="0 0 300 80" className="w-full h-full">
      <rect x="30" y="32" width="115" height="12" rx="4" fill="rgba(59,130,246,0.18)" />
      <rect x="155" y="32" width="115" height="12" rx="4" fill="rgba(239,68,68,0.18)" />
      <line x1="150" y1="24" x2="150" y2="52" stroke="#0f172a" strokeWidth="2" />
      <circle cx={px} cy="38" r="9" fill={isSkewed ? T.critical : T.optimal} stroke="#ffffff" strokeWidth="2" />
      <text x="34" y="62" fill="#3b82f6" fontSize="8" fontWeight="bold">Left-Skewed</text>
      <text x="150" y="18" textAnchor="middle" fill="#0f172a" fontSize="8" fontWeight="bold">Normal</text>
      <text x="266" y="62" textAnchor="end" fill={T.critical} fontSize="8" fontWeight="bold">Right-Skewed</text>
    </svg>
  );
}

function SvgCorrelations({ data }: { data: Array<{ col_a: string; col_b: string; correlation: number }> }) {
  if (!data?.length) return (
    <div className="w-full h-full flex items-center justify-center text-[10px] font-mono" style={{ color: '#94a3b8' }}>
      Orthogonal — No strong collinearity detected
    </div>
  );
  return (
    <div className="w-full h-full flex flex-col justify-center gap-1.5 px-2">
      {data.slice(0, 3).map((item, i) => {
        const r = Math.abs(item.correlation);
        return (
          <div key={i} className="flex items-center justify-between text-[10px] font-mono px-2 py-1 rounded-lg"
               style={{ background: 'rgba(100,116,139,0.08)', border: '1px solid rgba(100,116,139,0.15)' }}>
            <span className="truncate max-w-[150px] font-semibold text-slate-700">{item.col_a} ↔ {item.col_b}</span>
            <span className="font-bold px-1.5 py-0.5 rounded text-[9px]"
                  style={{ background: r > 0.85 ? 'rgba(245,158,11,0.15)' : 'rgba(16,185,129,0.15)',
                           color: r > 0.85 ? T.warning : T.optimal }}>r = {r.toFixed(2)}</span>
          </div>
        );
      })}
    </div>
  );
}

function SvgSchemaDonut({ data }: { data: { numeric: number; categorical: number; constant: number } }) {
  const num = data.numeric ?? 0; const cat = data.categorical ?? 0; const con = data.constant ?? 0;
  const total = (num + cat + con) || 1;
  const nPct = (num / total) * 100; const cPct = (cat / total) * 100;
  return (
    <div className="w-full h-full flex items-center justify-around px-3">
      <div className="relative w-16 h-16">
        <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
          <circle cx="18" cy="18" r="15.915" fill="none" stroke="rgba(100,116,139,0.15)" strokeWidth="4" />
          <circle cx="18" cy="18" r="15.915" fill="none" stroke={T.coral} strokeWidth="4"
            strokeDasharray={`${nPct} ${100 - nPct}`} />
          <circle cx="18" cy="18" r="15.915" fill="none" stroke="#8b5cf6" strokeWidth="4"
            strokeDasharray={`${cPct} ${100 - cPct}`} strokeDashoffset={`-${nPct}`} />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xs font-bold font-mono text-slate-800">{total}</span>
        </div>
      </div>
      <div className="text-[10px] font-mono space-y-1">
        <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm" style={{ background: T.coral }} />Numeric: <strong>{num}</strong></div>
        <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm bg-purple-500" />Categorical: <strong>{cat}</strong></div>
        {con > 0 && <div className="flex items-center gap-1.5 text-rose-600 font-bold"><span className="w-2.5 h-2.5 rounded-sm" style={{ background: T.critical }} />Constant: <strong>{con}</strong></div>}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────
// Status badge helper
// ─────────────────────────────────────────────────────────────────
function StatusBadge({ status, metric }: { status: string; metric: string }) {
  const cfg = status === 'CRITICAL'
    ? { bg: 'rgba(239,68,68,0.12)', text: T.critical, border: 'rgba(239,68,68,0.30)' }
    : status === 'WARNING'
      ? { bg: 'rgba(245,158,11,0.12)', text: T.warning, border: 'rgba(245,158,11,0.30)' }
      : { bg: 'rgba(16,185,129,0.12)', text: T.optimal, border: 'rgba(16,185,129,0.30)' };
  return (
    <span className="text-[9px] font-bold font-mono px-2 py-0.5 rounded-full border"
      style={{ background: cfg.bg, color: cfg.text, borderColor: cfg.border }}>
      {metric}
    </span>
  );
}

// ─────────────────────────────────────────────────────────────────
// INTERFACE
// ─────────────────────────────────────────────────────────────────
interface PrePrepareProps {
  onProceed?: () => void;
  compiledCsvPath?: string;
  runId?: string;
  dagId?: string;
  algorithmFamily?: string;
  backendProfile?: Record<string, any> | null;
  onApproveDeliverables?: () => void;
  executionMode?: 'EXPLORATION_ONLY' | 'PREPARATION_ONLY' | 'FULL_AUTOML' | 'DIRECT_NAVIGATION';
  onOpenGraphicWalker?: () => void;
}

// ─────────────────────────────────────────────────────────────────
// MAIN COMPONENT
// ─────────────────────────────────────────────────────────────────
export const PrePrepare: React.FC<PrePrepareProps> = ({
  onProceed,
  runId,
  dagId,
  algorithmFamily,
  backendProfile = null,
  onApproveDeliverables,
  executionMode = 'FULL_AUTOML',
  onOpenGraphicWalker,
  compiledCsvPath,
}) => {
  // ── EMPTY STATE: When no dataset is compiled or active ───────────
  if (!compiledCsvPath && !backendProfile) {
    return (
      <div className="p-8 max-w-[1400px] mx-auto animate-fadeIn">
        <div className="bg-white rounded-3xl border border-slate-200 p-12 text-center shadow-xs flex flex-col items-center justify-center min-h-[480px]">
          <div className="w-16 h-16 rounded-2xl bg-[#FF6B35]/10 border border-[#FF6B35]/25 flex items-center justify-center text-[#FF6B35] mb-5 shadow-xs">
            <span className="material-symbols-outlined text-3xl">upload_file</span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 mb-2">No Active Telemetry Dataset Loaded</h2>
          <p className="text-sm text-slate-500 max-w-md mb-8 leading-relaxed">
            Upload your CSV, Parquet, or XLSX dataset to generate automated statistical profiles, sensor health signals, and AI-driven telemetry stories.
          </p>
          <div className="flex items-center gap-3.5">
            <button
              onClick={() => {
                window.dispatchEvent(new CustomEvent('aic-navigate', { detail: 'compiler' }));
              }}
              className="px-6 py-3 bg-[#FF6B35] hover:bg-[#E85520] text-white font-bold text-xs rounded-xl transition-all shadow-md shadow-[#FF6B35]/20 flex items-center gap-2 cursor-pointer"
            >
              <span className="material-symbols-outlined text-base">cloud_upload</span>
              <span>Open Ingestion &amp; Compiler Studio</span>
            </button>
            <button
              onClick={() => {
                window.dispatchEvent(new CustomEvent('aic-open-jane', { detail: 'Please upload my dataset' }));
              }}
              className="px-6 py-3 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition-all border border-slate-200 flex items-center gap-2 cursor-pointer"
            >
              <span className="material-symbols-outlined text-base text-[#FF6B35]">auto_awesome</span>
              <span>Ask Jane Assistant</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── LOADING STATE: Profiling in progress for active file ─────────
  if (compiledCsvPath && !backendProfile) {
    const activeFileName = compiledCsvPath.replace(/\\/g, '/').split('/').pop();
    return (
      <div className="p-8 max-w-[1400px] mx-auto animate-fadeIn">
        <div className="bg-white rounded-3xl border border-slate-200 p-12 text-center shadow-xs flex flex-col items-center justify-center min-h-[450px]">
          <div className="w-14 h-14 rounded-2xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600 mb-5 animate-pulse">
            <span className="material-symbols-outlined text-3xl">insights</span>
          </div>
          <h2 className="text-lg font-bold text-slate-900 mb-2">Analyzing Telemetry &amp; Computing Profile...</h2>
          <p className="text-xs text-slate-600 font-mono mb-4 bg-slate-50 px-3.5 py-1.5 rounded-lg border border-slate-200 inline-block">
            {activeFileName}
          </p>
          <p className="text-xs text-slate-400 max-w-sm">
            Calculating sensor distributions, IQR outlier fences, correlation matrices, and Phi-4-mini causal narrative.
          </p>
        </div>
      </div>
    );
  }

  const profile = backendProfile || {};
  const rowsTotal     = profile.rows_total    ?? 0;
  const colsTotal     = profile.columns       ?? 0;
  const readiness     = profile.readiness_score ?? 0;
  const duplicatePct  = profile.duplicate_pct  ?? 0.0;
  const outlierPct    = profile.outlier_pct    ?? 0.0;
  const maxMissingPct = profile.max_missing_pct ?? 0.0;
  const missingCol    = profile.most_missing_col || 'None';
  const skewedCol     = profile.most_skewed_col  || (profile.column_stats?.[0]?.column || 'sensor_1');
  const columnStats   = (profile.column_stats   ?? []) as Array<any>;
  const sampleRecords = (profile.sample_records  ?? []) as Array<any>;
  const topCorrs      = (profile.top_correlations ?? []) as Array<any>;

  const effectiveRunId = (runId && runId !== 'run_20250115_143022') ? runId : (compiledCsvPath ? 'session_live' : 'pending');
  const effectiveDagId = profile.recommended_dag_id || (dagId && dagId !== 'DAG_201' ? dagId : 'AutoML Pipeline');
  const effectiveFamily = profile.algorithm_family || (algorithmFamily && algorithmFamily !== 'Anomaly Detection' ? algorithmFamily : 'Telemetry Inspection');

  const execAssess = profile.executive_assessment || {
    ingestion_integrity: `Successfully ingested ${rowsTotal.toLocaleString()} records across ${colsTotal} feature channels with ${duplicatePct}% duplicate row rate.`,
    critical_signals:    maxMissingPct > 1
      ? `Telemetry gap: '${missingCol}' contains ${maxMissingPct}% missing records.`
      : 'Dataset demonstrates optimal telemetry integrity with zero critical schema drops.',
    pipeline_strategy: `AutoML routing selected ${effectiveDagId} (${effectiveFamily}) to model multi-channel sensor variance.`,
  };

  const causal = profile.causal_rationale || {
    step_1_compiler:     `Assembled raw batch files into unified matrix (${rowsTotal.toLocaleString()} rows, ${colsTotal} channels).`,
    step_2_profiler:     `Statistical audit flagged ${outlierPct}% outlier density in '${skewedCol}'.`,
    step_3_orchestrator: `Topology match: Unsupervised + temporal sensor variance ➔ ${effectiveDagId}.`,
    step_4_recipe:       `Recipe locked: RobustScaler (IQR) + Forward-fill imputation + Lag transforms.`,
  };

  // ── Diagnostic signals fallback ──────────────────────────────
  const diagSignals: Array<any> = profile.diagnostic_signals?.length
    ? profile.diagnostic_signals
    : [
        {
          id: 'sig_miss', title: maxMissingPct > 0 ? 'Sensor Telemetry Dropout' : 'Telemetry Completeness',
          feature: missingCol !== 'None' ? missingCol : 'Global Channels',
          metric: `${maxMissingPct}% Missing`,
          status: maxMissingPct > 10 ? 'CRITICAL' : maxMissingPct > 1 ? 'WARNING' : 'OPTIMAL',
          operational_impact: maxMissingPct > 0
            ? `Intermittent telemetry gap in '${missingCol}' will halt downstream estimators.`
            : 'Zero missing values detected across all ingested feature channels.',
          recommended_treatment: maxMissingPct > 0
            ? 'Apply forward-fill temporal imputation or KNN interpolation in Stage 2 (Prepare).'
            : 'Schema completeness verified. No imputation required.',
          chart_type: 'missing_bars',
          chart_payload: [{ column: missingCol, missing_pct: maxMissingPct }],
        },
        {
          id: 'sig_out', title: outlierPct > 1.5 ? 'Transient Sensor Spike Anomaly' : 'Sensor Variance Stability',
          feature: skewedCol !== 'None' ? skewedCol : 'Sensor Fleet',
          metric: `${outlierPct}% Outlier Rows`,
          status: outlierPct > 5 ? 'CRITICAL' : outlierPct > 1.5 ? 'WARNING' : 'OPTIMAL',
          operational_impact: outlierPct > 1.5
            ? `Spikes beyond 1.5× IQR in '${skewedCol}' distort loss gradients.`
            : 'Readings within normal operational boundaries. No extreme distortion.',
          recommended_treatment: outlierPct > 1.5
            ? 'Apply RobustScaler (median + IQR clipping) in Stage 2.'
            : 'Standard Z-score scaling suitable.',
          chart_type: 'boxplot',
          chart_payload: { col: skewedCol, min: 10, p25: 35, median: 52, p75: 78, max: 145 },
        },
        {
          id: 'sig_skew', title: (profile.max_skewness ?? 3.2) > 1.5 ? 'Distribution Asymmetry & Skew' : 'Distribution Normality',
          feature: skewedCol !== 'None' ? skewedCol : 'Channels',
          metric: `Skewness: ${(profile.max_skewness ?? 3.2).toFixed(2)}`,
          status: (profile.max_skewness ?? 3.2) > 3.0 ? 'CRITICAL' : (profile.max_skewness ?? 3.2) > 1.5 ? 'WARNING' : 'OPTIMAL',
          operational_impact: (profile.max_skewness ?? 3.2) > 1.5
            ? `Heavy-tail distribution in '${skewedCol}' biases linear estimators.`
            : 'Feature distributions exhibit balanced symmetry.',
          recommended_treatment: (profile.max_skewness ?? 3.2) > 1.5
            ? `Apply Yeo-Johnson transform on '${skewedCol}' in Stage 2.`
            : 'Retain standard continuous scaling.',
          chart_type: 'skewness_gauge',
          chart_payload: { skewness: profile.max_skewness ?? 3.2, col: skewedCol },
        },
        {
          id: 'sig_corr', title: (topCorrs[0]?.correlation ?? 0) > 0.85 ? 'Multicollinearity Redundancy' : 'Channel Independence',
          feature: topCorrs.length ? `${topCorrs[0].col_a} ↔ ${topCorrs[0].col_b}` : 'Sensor Pairs',
          metric: topCorrs.length ? `r = ${(topCorrs[0].correlation ?? 0).toFixed(2)}` : 'Orthogonal',
          status: (topCorrs[0]?.correlation ?? 0) > 0.85 ? 'WARNING' : 'OPTIMAL',
          operational_impact: (topCorrs[0]?.correlation ?? 0) > 0.85
            ? 'Collinear coupling indicates duplicated physical measurement channels.'
            : 'Diverse variance profiles. Minimal redundancy.',
          recommended_treatment: (topCorrs[0]?.correlation ?? 0) > 0.85
            ? 'Apply PCA or VIF pruning in Stage 4 (Feature Engineering).'
            : 'Retain all channels for full operational representation.',
          chart_type: 'correlations',
          chart_payload: topCorrs,
        },
        {
          id: 'sig_schema', title: 'Schema Consistency & Integrity',
          feature: `${colsTotal} Ingested Channels`,
          metric: `${colsTotal} Matched`,
          status: (profile.constant_cols?.length ?? 0) > 0 ? 'WARNING' : 'OPTIMAL',
          operational_impact: (profile.constant_cols?.length ?? 0) > 0
            ? `Detected ${profile.constant_cols.length} zero-variance constant columns.`
            : 'All feature channels contain active operational variance.',
          recommended_treatment: (profile.constant_cols?.length ?? 0) > 0
            ? 'Drop constant features in Stage 2 to conserve memory.'
            : 'Lock schema mapping for automated preprocessing.',
          chart_type: 'schema_donut',
          chart_payload: {
            numeric:     (columnStats.filter(c => c.mean !== undefined && c.mean !== null).length),
            categorical: (columnStats.filter(c => c.mean === undefined || c.mean === null).length),
            constant:    (profile.constant_cols?.length ?? 0),
          },
        },
      ];

  // ── Bottom section: Interactive Feature Inspector ────────────
  const numericCols = columnStats.filter(c => c.mean !== null && c.mean !== undefined);
  const allCols     = columnStats.length > 0 ? columnStats : [{ column: skewedCol || 'sensor_1', dtype: 'float64' }];

  const firstNumericCol = numericCols[0]?.column || allCols[0]?.column || 'col_1';
  const [selectedCol, setSelectedCol] = useState(firstNumericCol);
  const [chartMode, setChartMode]     = useState<'histogram' | 'trend' | 'boxplot' | 'scatter'>('histogram');

  useEffect(() => {
    if (numericCols.length > 0) {
      setSelectedCol(numericCols[0].column);
    }
  }, [profile.column_stats]);

  const activeCol = useMemo(() =>
    columnStats.find(c => c.column === selectedCol) || numericCols[0] || {},
  [columnStats, selectedCol]);

  const trendData = useMemo(() => {
    if (sampleRecords.length > 0) {
      return sampleRecords.map((r, i) => ({
        i,
        v: typeof r[selectedCol] === 'number' ? r[selectedCol] : parseFloat(r[selectedCol] ?? '0') || 0,
      }));
    }
    // synthetic fallback
    return Array.from({ length: 80 }).map((_, i) => ({
      i,
      v: Math.sin(i * 0.18) * 14 + 52 + (Math.random() * 5 - 2.5),
    }));
  }, [sampleRecords, selectedCol]);

  // ── Plotly traces per chart mode ──────────────────────────────
  const plotlyData = useMemo((): Plotly.Data[] => {
    switch (chartMode) {
      case 'histogram': {
        const bins = activeCol.histogram_bins ?? [];
        return bins.length > 0
          ? [{
              type: 'bar' as const,
              x: bins.map((b: any) => b.bin),
              y: bins.map((b: any) => b.count),
              name: selectedCol,
              marker: {
                color: bins.map((_: any, i: number) => i % 2 === 0 ? T.coral : T.coralSoft),
                line: { color: T.coralHover, width: 0.5 },
              },
              hovertemplate: '<b>%{x}</b><br>Count: %{y}<extra></extra>',
            }]
          : [{
              type: 'histogram' as const,
              x: trendData.map(d => d.v),
              name: selectedCol,
              autobinx: true,
              marker: { color: T.coral, line: { color: T.coralHover, width: 0.5 } },
              opacity: 0.85,
              hovertemplate: '%{x}<br>Count: %{y}<extra></extra>',
            }];
      }

      case 'trend':
        return [{
          type: 'scatter' as const,
          mode: 'lines' as const,
          x: trendData.map(d => d.i),
          y: trendData.map(d => d.v),
          name: selectedCol,
          line: { color: T.coral, width: 2.5, shape: 'spline' as const },
          fill: 'tozeroy' as const,
          fillcolor: T.coralGlow,
          hovertemplate: 'T=%{x}<br>Value: %{y:.3f}<extra></extra>',
        }];

      case 'boxplot':
        return [{
          type: 'box' as const,
          y: trendData.map(d => d.v),
          name: selectedCol,
          boxpoints: 'outliers' as const,
          jitter: 0.3,
          marker: { color: T.coral, size: 4, opacity: 0.7 },
          line: { color: T.coralHover, width: 2 },
          fillcolor: T.coralGlow,
          whiskerwidth: 0.7,
        } as any];

      case 'scatter': {
        // Scatter feature vs. itself shifted (proxy if no explicit target)
        const xs = trendData.slice(0, -1).map(d => d.v);
        const ys = trendData.slice(1).map(d => d.v);
        return [{
          type: 'scatter' as const,
          mode: 'markers' as const,
          x: xs,
          y: ys,
          name: `${selectedCol} [t] vs [t+1]`,
          marker: {
            color: xs.map(v => v),
            colorscale: [[0, T.eggplantMid], [0.5, T.coral], [1, '#fbbf24']] as any,
            size: 5,
            opacity: 0.70,
            showscale: true,
            colorbar: { thickness: 10, len: 0.7, tickfont: { size: 9 } },
          },
          hovertemplate: 'X: %{x:.3f}<br>Y: %{y:.3f}<extra></extra>',
        }];
      }

      default:
        return [];
    }
  }, [chartMode, activeCol, trendData, selectedCol]);

  const plotlyLayout = useMemo((): Partial<Plotly.Layout> => {
    const base = buildPlotlyLayout({
      xaxis: {
        title: chartMode === 'scatter' ? `${selectedCol} [t]` : chartMode === 'trend' ? 'Sample Index' : undefined,
        gridcolor: 'rgba(100,116,139,0.12)',
        zerolinecolor: 'rgba(100,116,139,0.20)',
        tickfont: { size: 10, family: "'JetBrains Mono', monospace" },
      } as any,
      yaxis: {
        title: chartMode === 'scatter' ? `${selectedCol} [t+1]` : selectedCol,
        gridcolor: 'rgba(100,116,139,0.12)',
        tickfont: { size: 10, family: "'JetBrains Mono', monospace" },
      } as any,
    });
    return base;
  }, [chartMode, selectedCol]);

  // ── Readiness colour ─────────────────────────────────────────
  const readinessColor = readiness >= 80 ? T.optimal : readiness >= 50 ? T.warning : T.critical;

  // ── Signal mini-chart renderer ───────────────────────────────
  const renderMiniChart = (sig: any) => {
    switch (sig.chart_type) {
      case 'missing_bars':   return <MissingBarsChart data={sig.chart_payload} />;
      case 'boxplot':        return <SvgBoxPlot data={sig.chart_payload} />;
      case 'skewness_gauge': return <SvgSkewnessGauge data={sig.chart_payload} />;
      case 'correlations':   return <SvgCorrelations data={sig.chart_payload} />;
      case 'schema_donut':   return <SvgSchemaDonut data={sig.chart_payload} />;
      default:               return null;
    }
  };

  // ─────────────────────────────────────────────────────────────
  return (
    <div className="page-container" style={{ gap: 20 }}>

      {/* ── STATUS BAR ─────────────────────────────────────────── */}
      <section className="status-action-bar">
        <div className="status-bar-info">
          <div className="status-bar-icon-block"><Workflow size={20} /></div>
          <div className="status-bar-details">
            <div className="status-bar-title-row">
              <span>{executionMode === 'EXPLORATION_ONLY' ? 'Dataset Exploration & Visual Profiling Hub' : 'Pipeline Stage 1 · Pre-Prepare Audit Hub'}</span>
              <span className="status-run-badge"><GitCommit size={10} />{effectiveRunId}</span>
              {executionMode === 'EXPLORATION_ONLY' && (
                <span className="text-[9px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 font-bold">
                  Standalone Visual Mode
                </span>
              )}
            </div>
            <div className="status-bar-parameters">
              <div className="param-item">{executionMode === 'EXPLORATION_ONLY' ? 'Engine:' : 'Pipeline:'} <strong style={{ color: T.coral }}>{executionMode === 'EXPLORATION_ONLY' ? 'Direct Fast-Track EDA' : effectiveDagId}</strong></div>
              <span style={{ color: T.textMuted }}>·</span>
              <div className="param-item">Family: <strong style={{ color: T.optimal }}>{executionMode === 'EXPLORATION_ONLY' ? (profile.qwen_semantics?.domain ? profile.qwen_semantics.domain.replace(/_/g, ' ').toUpperCase() : 'Visual Profiler') : effectiveFamily}</strong></div>
              <span style={{ color: T.textMuted }}>·</span>
              <div className="param-item">Channels: <strong style={{ fontFamily: 'var(--font-mono)' }}>{colsTotal} mapped</strong></div>
              {profile.qwen_semantics?.suggested_target && (
                <>
                  <span style={{ color: T.textMuted }}>·</span>
                  <div className="param-item">Target: <strong style={{ color: '#8b5cf6', fontFamily: 'var(--font-mono)' }}>{profile.qwen_semantics.suggested_target}</strong></div>
                </>
              )}
            </div>
          </div>
        </div>
        {executionMode === 'EXPLORATION_ONLY' ? (
          onOpenGraphicWalker && (
            <button className="proceed-cta-btn cursor-pointer bg-purple-700 hover:bg-purple-800 text-white" onClick={onOpenGraphicWalker}>
              <BarChart2 size={15} /> Open Graphic Walker
            </button>
          )
        ) : onProceed ? (
          <button className="proceed-cta-btn cursor-pointer" onClick={onProceed}>
            Proceed to Preparation <ArrowRight size={15} />
          </button>
        ) : null}
      </section>

      {/* ── PHI-4-MINI DYNAMIC NARRATIVE CARD ─────────────────── */}
      {(profile.phi4_story || profile.narrative) && (
        <section
          className="p-4 sm:p-5 rounded-2xl flex items-start gap-4 shadow-xs"
          style={{
            background: '#FFFFFF',
            border: '1px solid #E2E8F0',
            borderLeft: '4px solid #280B43',
          }}
        >
          <div
            style={{
              width: 38,
              height: 38,
              borderRadius: 10,
              background: '#F5F3FF',
              color: '#280B43',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              border: '1px solid #DDD6FE',
              marginTop: 2,
            }}
          >
            <Sparkles size={18} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <span style={{ fontSize: 13, fontWeight: 700, fontFamily: 'var(--font-mono)', color: '#0F172A', letterSpacing: '-0.01em' }}>
                🧠 Phi-4-mini Sensor Health & Operational Takeaways
              </span>
              <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', padding: '2px 8px', borderRadius: 99, background: '#F5F3FF', color: '#5B21B6', border: '1px solid #DDD6FE', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Dynamic AI Reasoning
              </span>
            </div>
            <div
              className="phi4-story-content"
              style={{ fontSize: 12, color: '#1E293B', lineHeight: 1.6 }}
              dangerouslySetInnerHTML={{
                __html: (profile.phi4_story_html || profile.narrative_html)
                  ? (profile.phi4_story_html || profile.narrative_html)
                  : (profile.phi4_story || profile.narrative || '')
                      .replace(/\*\*\[([^\]]+)\]\*\*/g, '<span style="display:inline-block; padding:2px 8px; border-radius:6px; background:#F5F3FF; color:#4C1D95; font-family:var(--font-mono); font-weight:700; font-size:11px; border:1px solid #DDD6FE; margin-right:6px;">$1</span>')
                      .replace(/(\d+)\.\s+\*\*([^*]+)\*\*:\s*/g, '<div style="margin-top:8px; display:flex; align-items:flex-start; gap:8px;"><span style="width:18px; height:18px; border-radius:50%; background:#280B43; color:#FFFFFF; font-family:var(--font-mono); font-weight:700; font-size:10px; display:flex; align-items:center; justify-content:center; flex-shrink:0; margin-top:2px;">$1</span><div style="flex:1;"><strong style="font-weight:700; color:#0F172A;">$2:</strong> ')
                      .replace(/\*\*([^*]+)\*\*/g, '<strong style="font-weight:700; color:#0F172A;">$1</strong>')
                      .replace(/`([^`]+)`/g, '<code style="padding:2px 6px; border-radius:4px; background:#F1F5F9; color:#E85520; font-family:var(--font-mono); font-size:11px; border:1px solid #CBD5E1;">$1</code>')
                      .replace(/➔|->/g, '➔')
              }}
            />
          </div>
        </section>
      )}

      {/* ── TOP: EXECUTIVE ASSESSMENT ──────────────────────────── */}
      <section style={{
        background: '#FFFFFF',
        border: '1px solid #E2E8F0',
        borderRadius: 16,
        padding: '20px 24px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
      }}>
        {/* Header row */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16,
                      borderBottom: '1px solid #E2E8F0', paddingBottom: 16, marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{ width: 42, height: 42, borderRadius: 12, background: 'rgba(255,107,53,0.12)', color: '#FF6B35', border: '1px solid rgba(255,107,53,0.25)', display: 'flex',
                          alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <ShieldCheck size={22} color="#FF6B35" />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ color: '#0F172A', fontWeight: 800, fontSize: 15 }}>Executive Dataset Assessment</span>
                <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', padding: '2px 8px', borderRadius: 99,
                               background: '#F1F5F9', color: '#475569',
                               border: '1px solid #E2E8F0', fontWeight: 600 }}>Automated Audit</span>
              </div>
              <p style={{ fontSize: 11.5, color: '#64748B', marginTop: 3 }}>
                Real-time diagnostic evaluation across ingestion integrity, telemetry risks, and model routing.
              </p>
            </div>
          </div>
          {/* Readiness Score */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: '#64748B',
                            textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>Readiness Score</div>
              <div style={{ fontSize: 24, fontWeight: 800, fontFamily: 'var(--font-mono)', color: readinessColor }}>
                {readiness}<span style={{ fontSize: 13, opacity: 0.6, color: '#64748B' }}>/100</span>
              </div>
            </div>
            <div style={{ width: 12, height: 12, borderRadius: '50%', background: readinessColor,
                          boxShadow: `0 0 8px ${readinessColor}` }} className="animate-pulse" />
          </div>
        </div>

        {/* 3 Pillars */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 12 }}>
          {[
            { icon: <Database size={14} />, label: '1. Ingestion & Schema Integrity', text: execAssess.ingestion_integrity, color: '#059669' },
            { icon: <Activity size={14} />, label: '2. Telemetry Risk Factors',       text: execAssess.critical_signals,    color: '#D97706' },
            { icon: <Layers size={14} />,   label: '3. Pipeline Strategy',             text: execAssess.pipeline_strategy,   color: '#E85520' },
          ].map((p, i) => (
            <div key={i} style={{ padding: '14px 16px', borderRadius: 12,
                                  background: '#F8FAFC',
                                  border: '1px solid #E2E8F0' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: p.color,
                            fontWeight: 700, fontSize: 11.5, marginBottom: 8 }}>
                {p.icon}{p.label}
              </div>
              <p style={{ fontSize: 11, color: '#334155', lineHeight: 1.6 }}>{p.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── KPI SCORECARD ROW ──────────────────────────────────── */}
      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
        {[
          { label: 'Total Ingested Rows', value: rowsTotal.toLocaleString(), color: 'var(--text-main)' },
          { label: 'Active Channels',     value: `${colsTotal} Columns`,       color: 'var(--text-main)' },
          { label: 'Row Duplication',     value: `${duplicatePct.toFixed(1)}%`, color: duplicatePct > 0 ? T.warning : T.optimal },
          { label: 'Outlier Variance',    value: `${outlierPct.toFixed(1)}%`,   color: outlierPct > 2 ? T.critical : T.optimal },
        ].map((kpi, i) => (
          <div key={i} className="dashboard-card" style={{ padding: '14px 18px', gap: 4, textAlign: 'center' }}>
            <span style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.07em',
                           color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{kpi.label}</span>
            <span style={{ fontSize: 20, fontWeight: 800, fontFamily: 'var(--font-mono)', color: kpi.color }}>
              {kpi.value}
            </span>
          </div>
        ))}
      </section>

      {/* ── MIDDLE: RANKED DIAGNOSTIC SIGNAL CARDS ─────────────── */}
      <section>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <BarChart2 size={18} color={T.coral} />
            <span style={{ fontWeight: 700, fontSize: 13.5, color: 'var(--text-main)' }}>
              Ranked Diagnostic Quality Signals & Actionable Treatments
            </span>
          </div>
          <span style={{ fontSize: 10.5, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
            {diagSignals.length} Active Audit Signals — sorted by severity
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
          {diagSignals.map((sig: any) => {
            const isCrit = sig.status === 'CRITICAL';
            const isWarn = sig.status === 'WARNING';
            const borderC = isCrit ? 'rgba(239,68,68,0.35)' : isWarn ? 'rgba(245,158,11,0.30)' : 'var(--border-light)';
            return (
              <div key={sig.id} className="dashboard-card" style={{
                gap: 12, padding: '16px',
                borderColor: borderC,
                background: isCrit ? 'rgba(239,68,68,0.04)' : isWarn ? 'rgba(245,158,11,0.03)' : 'var(--bg-card)',
              }}>
                {/* Card Header */}
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between',
                              borderBottom: '1px solid var(--border-light)', paddingBottom: 10, gap: 8 }}>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 12, color: 'var(--text-main)' }}>{sig.title}</div>
                    <div style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginTop: 2 }}>
                      Target: <strong style={{ color: 'var(--text-secondary)' }}>{sig.feature}</strong>
                    </div>
                  </div>
                  <StatusBadge status={sig.status} metric={sig.metric} />
                </div>

                {/* Mini Chart */}
                <div style={{ width: '100%', height: 100, borderRadius: 10, overflow: 'hidden',
                              background: 'rgba(100,116,139,0.05)', border: '1px solid var(--border-light)',
                              display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  {renderMiniChart(sig)}
                </div>

                {/* Operational Impact */}
                <div style={{ padding: '10px 12px', borderRadius: 10,
                              background: 'rgba(100,116,139,0.06)', border: '1px solid var(--border-light)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 10,
                                textTransform: 'uppercase', letterSpacing: '0.07em',
                                fontWeight: 700, color: '#3b82f6', marginBottom: 4 }}>
                    <Search size={11} />Operational Impact
                  </div>
                  <p style={{ fontSize: 10.5, color: 'var(--text-muted)', lineHeight: 1.5 }}>{sig.operational_impact}</p>
                </div>

                {/* Recommended Treatment */}
                <div style={{ padding: '10px 12px', borderRadius: 10,
                              background: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.20)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 10,
                                textTransform: 'uppercase', letterSpacing: '0.07em',
                                fontWeight: 700, color: '#b45309', marginBottom: 4 }}>
                    <Sliders size={11} />Recommended Treatment
                  </div>
                  <p style={{ fontSize: 10.5, color: '#92400e', lineHeight: 1.5, fontWeight: 500 }}>
                    {sig.recommended_treatment}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* ── BOTTOM: PLOTLY INTERACTIVE FEATURE INSPECTOR ─────────── */}
      <section className="dashboard-card" style={{ padding: '20px 24px', gap: 0 }}>
        {/* Inspector Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between',
                      gap: 16, flexWrap: 'wrap', borderBottom: '1px solid var(--border-light)',
                      paddingBottom: 16, marginBottom: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: T.coralGlow,
                          display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <TrendingUp size={17} color={T.coral} />
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: 13.5, color: 'var(--text-main)' }}>
                Interactive Feature Inspector & Visual Explorer
              </div>
              <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                Inspect any telemetry channel — distributions, drift, outlier bounds, and lag correlations.
              </p>
            </div>
          </div>

          {/* Controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            {/* Feature select */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '7px 12px',
                          borderRadius: 10, background: 'rgba(100,116,139,0.08)',
                          border: '1px solid var(--border-medium)' }}>
              <Filter size={13} color="var(--text-muted)" />
              <span style={{ fontSize: 10.5, fontWeight: 700, color: 'var(--text-muted)' }}>Feature:</span>
              <select
                value={selectedCol}
                onChange={e => setSelectedCol(e.target.value)}
                style={{ background: 'transparent', border: 'none', outline: 'none', cursor: 'pointer',
                         fontSize: 11, fontFamily: 'var(--font-mono)', fontWeight: 700,
                         color: T.coral, maxWidth: 180 }}
              >
                {allCols.map((col: any) => (
                  <option key={col.column} value={col.column}>
                    {col.column} ({col.dtype})
                  </option>
                ))}
              </select>
            </div>

            {/* Chart type tabs */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 2, padding: '4px',
                          borderRadius: 12, background: 'rgba(100,116,139,0.08)',
                          border: '1px solid var(--border-light)' }}>
              {([
                { key: 'histogram', icon: <BarChart2 size={13} />,       label: 'Histogram'   },
                { key: 'trend',     icon: <LineChartIcon size={13} />,    label: 'Time Trend'  },
                { key: 'boxplot',   icon: <Maximize2 size={13} />,        label: 'Boxplot'     },
                { key: 'scatter',   icon: <Activity size={13} />,         label: 'Lag Scatter' },
              ] as const).map(btn => (
                <button
                  key={btn.key}
                  onClick={() => setChartMode(btn.key)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 5, padding: '6px 12px', borderRadius: 8,
                    border: 'none', cursor: 'pointer', fontSize: 11, fontWeight: 600, transition: 'all 0.18s',
                    background: chartMode === btn.key ? T.coral : 'transparent',
                    color:      chartMode === btn.key ? '#fff' : 'var(--text-muted)',
                    boxShadow:  chartMode === btn.key ? `0 2px 8px ${T.coralGlow}` : 'none',
                  }}
                >
                  {btn.icon}{btn.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Chart + Sidebar Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 240px', gap: 20 }}>
          {/* Plotly Main Chart */}
          <div style={{ borderRadius: 14, overflow: 'hidden', border: '1px solid var(--border-light)',
                        background: 'rgba(100,116,139,0.04)', minHeight: 320 }}>
            <Plot
              data={plotlyData}
              layout={plotlyLayout}
              config={PLOTLY_CONFIG}
              style={{ width: '100%', height: 320 }}
              useResizeHandler
            />
          </div>

          {/* Metric Sidebar */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {/* Feature title */}
            <div>
              <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.07em',
                            color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginBottom: 4 }}>
                Feature Health Profile
              </div>
              <div style={{ fontSize: 12, fontWeight: 700, fontFamily: 'var(--font-mono)',
                            color: 'var(--text-main)', wordBreak: 'break-all' }}>
                {selectedCol}
              </div>
            </div>

            {/* Metric rows */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 0,
                          border: '1px solid var(--border-light)', borderRadius: 12, overflow: 'hidden' }}>
              {[
                { k: 'Data Type',       v: activeCol.dtype || 'float64',                   c: 'var(--text-main)' },
                { k: 'Missingness',     v: `${activeCol.missing_pct ?? 0}%`,                c: (activeCol.missing_pct ?? 0) > 0 ? T.critical : T.optimal },
                { k: 'Mean',            v: activeCol.mean   != null ? `${activeCol.mean}`   : 'N/A', c: 'var(--text-main)' },
                { k: 'Std Dev',         v: activeCol.std    != null ? `${activeCol.std}`    : 'N/A', c: 'var(--text-main)' },
                { k: 'Median',          v: activeCol.median != null ? `${activeCol.median}` : 'N/A', c: 'var(--text-main)' },
                { k: 'Skewness',        v: activeCol.skewness != null ? `${activeCol.skewness}` : 'N/A', c: Math.abs(activeCol.skewness ?? 0) > 1.5 ? T.warning : T.optimal },
                { k: 'IQR Outliers',    v: `${activeCol.outlier_pct ?? 0}%`,                c: (activeCol.outlier_pct ?? 0) > 2 ? T.warning : T.optimal },
              ].map((row, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                      padding: '7px 12px', fontSize: 10.5, fontFamily: 'var(--font-mono)',
                                      borderBottom: i < 6 ? '1px solid var(--border-light)' : 'none',
                                      background: i % 2 === 0 ? 'rgba(100,116,139,0.03)' : 'transparent' }}>
                  <span style={{ color: 'var(--text-muted)', fontWeight: 500 }}>{row.k}</span>
                  <span style={{ fontWeight: 700, color: row.c }}>{row.v}</span>
                </div>
              ))}
            </div>

            {/* Stage 2 action card */}
            <div style={{ padding: '12px 14px', borderRadius: 12,
                          background: 'rgba(245,158,11,0.07)', border: '1px solid rgba(245,158,11,0.22)' }}>
              <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.07em',
                            fontWeight: 700, color: '#92400e', marginBottom: 5 }}>
                Stage 2 Preparation Action
              </div>
              <p style={{ fontSize: 10.5, color: '#78350f', lineHeight: 1.55, fontWeight: 500 }}>
                {(activeCol.missing_pct ?? 0) > 0
                  ? 'Apply forward-fill temporal imputation to bridge null telemetry gap.'
                  : Math.abs(activeCol.skewness ?? 0) > 2.0
                    ? 'Apply Yeo-Johnson power transform to normalize distribution.'
                    : (activeCol.outlier_pct ?? 0) > 2.0
                      ? 'Apply RobustScaler (IQR bounds) to insulate loss gradients.'
                      : 'Feature is well-conditioned. Standard continuous scaling applied.'}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── CAUSAL RATIONALE CHAIN ─────────────────────────────── */}
      <section style={{
        padding: '20px 24px', borderRadius: 16,
        background: 'linear-gradient(135deg, rgba(99,102,241,0.06) 0%, rgba(100,116,139,0.04) 100%)',
        border: '1px solid rgba(99,102,241,0.20)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                      marginBottom: 16, flexWrap: 'wrap', gap: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Workflow size={18} color="#6366f1" />
            <span style={{ fontWeight: 700, fontSize: 13.5, color: 'var(--text-main)' }}>
              Model Selection & Pipeline Selection Rationale
            </span>
          </div>
          <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', fontWeight: 700,
                         padding: '4px 12px', borderRadius: 99, background: '#6366f1', color: '#fff' }}>
            Auto-Resolved: {dagId}
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
          {[
            { icon: <Cpu size={13} color="#3b82f6" />,       label: '1. Compiler Ingestion',  text: causal.step_1_compiler,     border: 'rgba(59,130,246,0.25)'  },
            { icon: <Sliders size={13} color="#14b8a6" />,   label: '2. Statistical Audit',   text: causal.step_2_profiler,     border: 'rgba(20,184,166,0.25)'  },
            { icon: <Workflow size={13} color={T.warning} />, label: '3. Topology Routing',   text: causal.step_3_orchestrator, border: `rgba(245,158,11,0.25)` },
            { icon: <CheckCircle size={13} color="#a855f7" />, label: '4. Recipe Locking',   text: causal.step_4_recipe,       border: 'rgba(168,85,247,0.25)' },
          ].map((step, i) => (
            <div key={i} className="dashboard-card" style={{ gap: 6, padding: '12px 14px', borderColor: step.border, borderWidth: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontWeight: 700, fontSize: 11, color: 'var(--text-main)' }}>
                {step.icon}{step.label}
              </div>
              <p style={{ fontSize: 10.5, color: 'var(--text-muted)', lineHeight: 1.55 }}>{step.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── HITL APPROVAL FOOTER ───────────────────────────────── */}
      <section style={{
        padding: '20px 28px',
        background: `linear-gradient(135deg, ${T.eggplantDeep} 0%, #4c1d95 60%, ${T.eggplant} 100%)`,
        borderRadius: 20,
        border: '1px solid rgba(255,255,255,0.08)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        gap: 20, flexWrap: 'wrap',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ width: 48, height: 48, borderRadius: 14, background: T.coral,
                        display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <Sparkles size={24} color="#fff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#fff', fontWeight: 700, fontSize: 14 }}>
              {executionMode === 'EXPLORATION_ONLY' ? 'Visual Exploration & Quality Audit Summary' : 'Preparation Deliverables Verification'}
              <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', padding: '2px 8px', borderRadius: 99,
                             background: 'rgba(16,185,129,0.18)', color: '#6ee7b7',
                             border: '1px solid rgba(16,185,129,0.30)' }}>
                {executionMode === 'EXPLORATION_ONLY' ? 'Exploration Active' : 'Audited & Ready'}
              </span>
            </div>
            <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.60)', fontFamily: 'var(--font-mono)', marginTop: 4 }}>
              {executionMode === 'EXPLORATION_ONLY'
                ? `Dynamic profiling complete for ${rowsTotal.toLocaleString()} rows across ${colsTotal} channels. AutoML training is gated in exploration mode.`
                : `Diagnostic audit complete for ${rowsTotal.toLocaleString()} rows. Pre-processing transforms locked for Stage 2.`}
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {executionMode === 'EXPLORATION_ONLY' ? (
            <>
              <button
                onClick={() => {
                  const blob = new Blob([JSON.stringify(profile, null, 2)], { type: 'application/json' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `data_profile_${runId}.json`;
                  a.click();
                }}
                style={{
                  padding: '12px 18px', background: 'rgba(255,255,255,0.12)', color: '#fff',
                  fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700,
                  borderRadius: 14, border: '1px solid rgba(255,255,255,0.20)', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', gap: 6,
                  transition: 'all 0.2s', flexShrink: 0,
                }}
                onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.20)')}
                onMouseLeave={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.12)')}
              >
                <Database size={15} />
                Export Profile JSON
              </button>

              {onOpenGraphicWalker && (
                <button
                  onClick={onOpenGraphicWalker}
                  style={{
                    padding: '12px 24px', background: T.coral, color: '#fff',
                    fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 700,
                    borderRadius: 14, border: 'none', cursor: 'pointer',
                    boxShadow: `0 4px 16px ${T.coralGlow}`,
                    display: 'flex', alignItems: 'center', gap: 8,
                    transition: 'all 0.2s', flexShrink: 0,
                  }}
                  onMouseEnter={e => (e.currentTarget.style.background = T.coralHover)}
                  onMouseLeave={e => (e.currentTarget.style.background = T.coral)}
                >
                  <BarChart2 size={16} />
                  Open Graphic Walker Visual Studio
                </button>
              )}
            </>
          ) : onApproveDeliverables && (
            <button
              onClick={onApproveDeliverables}
              style={{
                padding: '12px 24px', background: T.coral, color: '#fff',
                fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 700,
                borderRadius: 14, border: 'none', cursor: 'pointer',
                boxShadow: `0 4px 16px ${T.coralGlow}`,
                display: 'flex', alignItems: 'center', gap: 8,
                transition: 'all 0.2s', flexShrink: 0,
              }}
              onMouseEnter={e => (e.currentTarget.style.background = T.coralHover)}
              onMouseLeave={e => (e.currentTarget.style.background = T.coral)}
            >
              <CheckCircle size={16} />
              Approve & Dispatch Deliverables to ML Studio
            </button>
          )}
        </div>
      </section>

    </div>
  );
};

export default PrePrepare;
