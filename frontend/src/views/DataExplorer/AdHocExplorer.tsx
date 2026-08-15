import React, { Suspense, lazy, useState, useEffect, useMemo } from 'react';
import { BarChart2, Loader2, AlertCircle, Info, Sliders, TableIcon, TrendingUp } from 'lucide-react';

// Lazy-load Graphic Walker only when this tab is first rendered
// This prevents the ~3.5MB bundle from loading until the user requests it
const GraphicWalker = lazy(() =>
  import('@kanaries/graphic-walker').then((mod) => ({ default: mod.GraphicWalker }))
);

interface AdHocExplorerProps {
  compiledCsvPath?: string;
  runId?: string;
  dagId?: string;
  algorithmFamily?: string;
}

// ── Lightweight CSV → IDataSet converter ──────────────────────────────────────
// Parses a small CSV string (first 5000 rows) into the FieldSpec + rows format
// required by Graphic Walker's `dataSource` prop.
function parseCSVtoGWDataset(csvText: string): {
  fields: { fid: string; name: string; semanticType: 'quantitative' | 'nominal'; analyticType: 'measure' | 'dimension' }[];
  dataSource: Record<string, any>[];
} {
  const lines = csvText.trim().split('\n');
  const headers = lines[0].split(',').map((h) => h.trim().replace(/"/g, ''));

  const sampleLines = lines.slice(1, 5001); // cap at 5000 rows
  const dataSource = sampleLines.map((line) => {
    const vals = line.split(',');
    const row: Record<string, any> = {};
    headers.forEach((h, i) => {
      const raw = (vals[i] ?? '').trim().replace(/"/g, '');
      const num = parseFloat(raw);
      row[h] = isNaN(num) ? raw : num;
    });
    return row;
  });

  const fields = headers.map((h) => {
    const firstVal = dataSource[0]?.[h];
    const isNumeric = typeof firstVal === 'number';
    return {
      fid: h,
      name: h,
      semanticType: (isNumeric ? 'quantitative' : 'nominal') as 'quantitative' | 'nominal',
      analyticType: (isNumeric ? 'measure' : 'dimension') as 'measure' | 'dimension',
    };
  });

  return { fields, dataSource };
}

// ── Demo dataset (industrial telemetry) used when no real CSV is available ───
const DEMO_FIELDS = [
  { fid: 'cycle', name: 'Cycle', semanticType: 'quantitative' as const, analyticType: 'dimension' as const },
  { fid: 'temp_celsius', name: 'Temp (°C)', semanticType: 'quantitative' as const, analyticType: 'measure' as const },
  { fid: 'vibration_index', name: 'Vibration', semanticType: 'quantitative' as const, analyticType: 'measure' as const },
  { fid: 'pressure_bar', name: 'Pressure (bar)', semanticType: 'quantitative' as const, analyticType: 'measure' as const },
  { fid: 'rpm', name: 'RPM', semanticType: 'quantitative' as const, analyticType: 'measure' as const },
  { fid: 'sensor_id', name: 'Sensor ID', semanticType: 'nominal' as const, analyticType: 'dimension' as const },
  { fid: 'anomaly_flag', name: 'Anomaly Flag', semanticType: 'nominal' as const, analyticType: 'dimension' as const },
];

const DEMO_DATA = Array.from({ length: 200 }, (_, i) => ({
  cycle: i + 1,
  temp_celsius: 85 + Math.sin(i / 10) * 12 + Math.random() * 4,
  vibration_index: 0.03 + Math.cos(i / 15) * 0.025 + Math.random() * 0.01,
  pressure_bar: 14.5 + Math.sin(i / 8) * 2 + Math.random() * 0.5,
  rpm: 3000 + Math.cos(i / 12) * 400 + Math.random() * 100,
  sensor_id: `S-${(i % 5) + 1}`,
  anomaly_flag: i % 30 === 0 ? 'ANOMALY' : 'NOMINAL',
}));


export const AdHocExplorer: React.FC<AdHocExplorerProps> = ({
  compiledCsvPath,
  runId = 'run_20250115_143022',
  dagId = 'DAG_201',
  algorithmFamily = 'Anomaly Detection',
}) => {
  const [gwData, setGwData] = useState<{ fields: any[]; dataSource: any[] } | null>(null);
  const [loadState, setLoadState] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');
  const [rowCount, setRowCount] = useState(0);

  // Attempt to fetch real CSV from backend and parse it
  useEffect(() => {
    if (!compiledCsvPath) {
      // Fallback to demo data immediately
      setGwData({ fields: DEMO_FIELDS, dataSource: DEMO_DATA });
      setRowCount(DEMO_DATA.length);
      setLoadState('ready');
      return;
    }

    setLoadState('loading');
    // Try fetching the CSV via the backend profiler endpoint as raw CSV
    fetch(`http://localhost:8000/api/v1/dataset?path=${encodeURIComponent(compiledCsvPath)}&rows=5000`)
      .then((res) => (res.ok ? res.text() : Promise.reject('backend unavailable')))
      .then((csvText) => {
        const parsed = parseCSVtoGWDataset(csvText);
        setGwData(parsed);
        setRowCount(parsed.dataSource.length);
        setLoadState('ready');
      })
      .catch(() => {
        // Graceful fallback to demo data if backend isn't running
        setGwData({ fields: DEMO_FIELDS, dataSource: DEMO_DATA });
        setRowCount(DEMO_DATA.length);
        setLoadState('ready');
      });
  }, [compiledCsvPath]);

  // ── Pre-load spinner state ─────────────────────────────────────────────────
  if (loadState === 'idle' || loadState === 'loading') {
    return (
      <div className="page-container font-sans flex flex-col items-center justify-center min-h-[400px] gap-4">
        <Loader2 className="animate-spin text-blue-600" size={36} />
        <p className="text-slate-600 text-sm font-medium">Loading dataset for Ad-Hoc Exploration...</p>
      </div>
    );
  }

  return (
    <div className="page-container font-sans text-xs">

      {/* ── Header Status Bar ────────────────────────────────────────────────── */}
      <section className="status-action-bar">
        <div className="status-bar-info">
          <div className="status-bar-icon-block">
            <Sliders size={20} />
          </div>
          <div className="status-bar-details">
            <div className="status-bar-title-row">
              <span>Ad-Hoc Visual Explorer — Drag & Drop Pivot Builder</span>
              <span className="status-run-badge">
                <BarChart2 size={10} /> {runId}
              </span>
            </div>
            <div className="status-bar-parameters">
              <div className="param-item">
                <span>DAG:</span>
                <span className="highlight-orange font-bold font-mono">{dagId}</span>
              </div>
              <span>•</span>
              <div className="param-item">
                <span>Family:</span>
                <span className="highlight-green font-bold">{algorithmFamily}</span>
              </div>
              <span>•</span>
              <div className="param-item">
                <span>Rows Loaded:</span>
                <span className="highlight-blue font-bold font-mono">
                  {rowCount.toLocaleString()}
                  {!compiledCsvPath && <span className="text-amber-600 ml-1">(demo)</span>}
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Info Callout ─────────────────────────────────────────────────────── */}
      <section className="info-callout-banner">
        <Info size={18} className="info-banner-icon" />
        <div className="info-banner-text">
          <strong>Ad-Hoc Visual Explorer:</strong> Drag fields from the left panel onto X/Y axes to build scatter plots, bar
          charts, heatmaps, and pivot tables dynamically. No code required.
          {!compiledCsvPath && (
            <span className="text-amber-700 ml-1 font-medium">
              — Showing demo industrial telemetry dataset (200 rows). Upload a CSV to explore your own data.
            </span>
          )}
        </div>
      </section>

      {/* ── Quick Tips Bar ───────────────────────────────────────────────────── */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="p-3 bg-white rounded-xl border border-blue-200 shadow-sm flex items-start gap-2">
          <TableIcon size={14} className="text-blue-600 mt-0.5 flex-shrink-0" />
          <div>
            <div className="font-bold text-slate-700 text-[11px]">Drag Fields</div>
            <div className="text-slate-500 text-[10px]">Drag dimensions or measures from the sidebar onto chart axes.</div>
          </div>
        </div>
        <div className="p-3 bg-white/5 rounded-xl border border-[#FF6B35]/20 shadow-sm flex items-start gap-2">
          <TrendingUp size={14} className="text-[#FF6B35] mt-0.5 flex-shrink-0" />
          <div>
            <div className="font-bold text-slate-700 text-[11px]">Switch Chart Types</div>
            <div className="text-slate-500 text-[10px]">Use the chart type selector to switch between bar, scatter, line, heatmap.</div>
          </div>
        </div>
        <div className="p-3 bg-white rounded-xl border border-purple-200 shadow-sm flex items-start gap-2">
          <Sliders size={14} className="text-purple-600 mt-0.5 flex-shrink-0" />
          <div>
            <div className="font-bold text-slate-700 text-[11px]">Pivot Tables</div>
            <div className="text-slate-500 text-[10px]">Drop dimensions onto rows/columns in the table view to build pivot tables.</div>
          </div>
        </div>
      </div>

      {/* ── Graphic Walker Canvas ─────────────────────────────────────────────── */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden" style={{ minHeight: '600px' }}>
        <Suspense
          fallback={
            <div className="flex items-center justify-center h-[600px] gap-3">
              <Loader2 className="animate-spin text-blue-500" size={28} />
              <span className="text-slate-500 text-sm">Initializing Visual Explorer...</span>
            </div>
          }
        >
          {gwData && (
            <GraphicWalker
              dataSource={gwData.dataSource}
              fields={gwData.fields}
              appearance="light"
            />
          )}
        </Suspense>
      </div>

    </div>
  );
};

export default AdHocExplorer;
