import React, { useState } from 'react';

interface CompilerViewProps {
  onSendToMLOps: () => void;
}

export const CompilerView: React.FC<CompilerViewProps> = ({ onSendToMLOps }) => {
  // Compiler UI States
  const [activeTab, setActiveTab] = useState<'upload' | 'inspector' | 'pipeline' | 'audit'>('upload');
  const [queryInput, setQueryInput] = useState('');
  const [queryResponse, setQueryResponse] = useState<string | null>(null);
  const [isInspectionDrawerOpen, setIsInspectionDrawerOpen] = useState(false);
  const [showRejectionShield, setShowRejectionShield] = useState(false);
  const [compilationLayer, setCompilationLayer] = useState<number>(4); // 1 to 4
  const [isCompiling, setIsCompiling] = useState(false);

  // Sample extracted archive tree
  const archiveFiles = [
    { name: 'C-MAPSS_FD001_train.csv', size: '14.2 MB', encoding: 'utf-8', type: 'SCADA Table', cols: 26 },
    { name: 'unit_metadata_v2.json', size: '420 KB', encoding: 'utf-8', type: 'Entity Index', cols: 6 },
    { name: 'high_freq_vibration_ch1.mat', size: '38.5 MB', encoding: 'binary/mat', type: 'High-Freq Signal', cols: 1 },
    { name: 'thermal_sensor_log.txt', size: '2.8 MB', encoding: 'latin-1', type: 'Raw Text Dump', cols: 14 },
    { name: 'operational_settings.xlsx', size: '1.1 MB', encoding: 'ooxml', type: 'Spreadsheet', cols: 8 },
  ];

  // Sample preview columns
  const previewColumns = [
    { name: 'unit_id', type: 'int64', badge: 'bg-blue-100 text-blue-800' },
    { name: 'time_cycle', type: 'int64', badge: 'bg-blue-100 text-blue-800' },
    { name: 'setting_1', type: 'float64', badge: 'bg-emerald-100 text-emerald-800' },
    { name: 'setting_2', type: 'float64', badge: 'bg-emerald-100 text-emerald-800' },
    { name: 'setting_3', type: 'float64', badge: 'bg-emerald-100 text-emerald-800' },
    { name: 'fan_inlet_temp', type: 'float64', badge: 'bg-emerald-100 text-emerald-800' },
    { name: 'lpc_outlet_temp', type: 'float64', badge: 'bg-emerald-100 text-emerald-800' },
    { name: 'hpc_outlet_temp', type: 'float64', badge: 'bg-emerald-100 text-emerald-800' },
    { name: 'lpt_outlet_temp', type: 'float64', badge: 'bg-emerald-100 text-emerald-800' },
    { name: 'fan_speed_rpm', type: 'float64', badge: 'bg-emerald-100 text-emerald-800' },
  ];

  // Sample data preview rows
  const previewRows = Array.from({ length: 8 }).map((_, i) => ({
    unit_id: 1,
    time_cycle: i + 1,
    setting_1: (0.0023 + i * 0.0001).toFixed(4),
    setting_2: (0.0003 - i * 0.00005).toFixed(4),
    setting_3: '100.0',
    fan_inlet_temp: (518.67 + Math.sin(i) * 0.4).toFixed(2),
    lpc_outlet_temp: (641.82 + i * 0.15).toFixed(2),
    hpc_outlet_temp: (1589.7 + i * 0.8).toFixed(2),
    lpt_outlet_temp: (1400.6 + i * 0.5).toFixed(2),
    fan_speed_rpm: (14.62 + i * 0.02).toFixed(2),
  }));

  const handleQuerySubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!queryInput.trim()) return;
    setQueryResponse(
      `AI Agent scanned archive files across C-MAPSS_FD001. Found 21 continuous sensor signals (temperature, pressure, vibration) sampled at 1Hz. Auto-aligned on timestamp axis 'time_cycle' and entity key 'unit_id'. Missing values: 0.00%.`
    );
  };

  const handleRunCompilation = () => {
    setIsCompiling(true);
    setCompilationLayer(1);
    setTimeout(() => setCompilationLayer(2), 800);
    setTimeout(() => setCompilationLayer(3), 1600);
    setTimeout(() => {
      setCompilationLayer(4);
      setIsCompiling(false);
    }, 2400);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/75 backdrop-blur-2xl p-6 rounded-3xl border border-white/15 shadow-2xl">
        <div>
          <nav className="flex items-center gap-2 text-slate-400 text-xs font-mono uppercase tracking-widest mb-1">
            <span>Isolated Module</span>
            <span className="material-symbols-outlined text-xs">chevron_right</span>
            <span className="text-tas-red font-bold">Relational Compiler Suite</span>
          </nav>
          <h1 className="font-headline text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
            <span>Universal ZIP & SCADA Compiler</span>
            <span className="px-3 py-1 bg-tas-red/20 text-tas-red border border-tas-red/40 rounded-full text-xs font-mono font-bold">
              v2.4 Live
            </span>
          </h1>
          <p className="text-slate-300 text-xs mt-1">
            Ingest multi-table SCADA archives (.zip, .mat, .csv, .xlsx), autodetect time axes, and compile unified 27-column feature sets for the 9-Node MLOps Cascade.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsInspectionDrawerOpen(!isInspectionDrawerOpen)}
            className="px-4 py-2.5 bg-white/10 hover:bg-white/20 text-white font-mono text-xs font-bold rounded-2xl transition-all flex items-center gap-2 border border-white/20"
          >
            <span className="material-symbols-outlined text-base text-tas-red">folder_zip</span>
            <span>Archive Drawer ({archiveFiles.length} files)</span>
          </button>

          <button
            onClick={onSendToMLOps}
            className="px-5 py-2.5 bg-gradient-to-r from-tas-red to-tas-red-hover hover:scale-105 text-white font-mono text-xs font-bold rounded-2xl shadow-xl transition-all active:scale-95 flex items-center gap-2"
          >
            <span>Send to MLOps Cascade</span>
            <span className="material-symbols-outlined text-base">east</span>
          </button>
        </div>
      </div>

      {/* Main Grid: Dropzone & Data Agent Bar */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Archive Dropzone & 4-Layer Tracker */}
        <div className="lg:col-span-2 space-y-6">
          {/* Section 1: Industrial Archive Dropzone */}
          <div className="bg-slate-900/75 backdrop-blur-2xl border border-white/15 rounded-3xl p-6 shadow-2xl relative overflow-hidden">
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-tas-red text-xl">upload_file</span>
                <h2 className="font-headline font-bold text-base text-white">
                  1. Multi-Format Industrial Archive Dropzone
                </h2>
              </div>
              <span className="text-[11px] font-mono text-slate-400">
                Supports .zip, .csv, .txt, .mat, .xlsx (Max 5GB)
              </span>
            </div>

            {/* Drop Area */}
            <div className="border-2 border-dashed border-tas-red/40 hover:border-tas-red bg-slate-950/40 hover:bg-slate-950/70 transition-all rounded-2xl p-8 text-center cursor-pointer group">
              <div className="w-14 h-14 bg-slate-900/80 rounded-2xl border border-white/20 flex items-center justify-center mx-auto mb-3 shadow-lg group-hover:scale-110 transition-transform">
                <span className="material-symbols-outlined text-tas-red text-3xl">cloud_upload</span>
              </div>
              <p className="font-headline font-bold text-sm text-white">
                Drag & Drop Industrial Telemetry Archives Here
              </p>
              <p className="text-slate-400 text-xs mt-1">
                or <span className="text-tas-red font-bold underline">browse local storage</span> to select multi-table SCADA dataset
              </p>
              <div className="flex items-center justify-center gap-3 mt-4 text-[10px] font-mono text-slate-300">
                <span className="px-2 py-0.5 bg-slate-950/80 border border-white/15 rounded-lg">C-MAPSS Turbofan</span>
                <span className="px-2 py-0.5 bg-slate-950/80 border border-white/15 rounded-lg">Wind Turbine SCADA</span>
                <span className="px-2 py-0.5 bg-slate-950/80 border border-white/15 rounded-lg">IGBT Semiconductor</span>
              </div>
            </div>

            {/* Active Archive Card */}
            <div className="mt-4 p-4 bg-slate-950/60 border border-white/15 rounded-2xl flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-emerald-500/20 text-emerald-300 rounded-xl">
                  <span className="material-symbols-outlined text-lg">check_circle</span>
                </div>
                <div>
                  <p className="font-mono text-xs font-bold text-white">C-MAPSS_FD001_Industrial_Telemetry.zip</p>
                  <p className="text-[11px] text-slate-400 font-mono">Size: 58.4 MB • 5 Extracted Tables • Encoding: UTF-8</p>
                </div>
              </div>
              <button
                onClick={handleRunCompilation}
                disabled={isCompiling}
                className="px-4 py-2 bg-gradient-to-r from-tas-red to-tas-red-hover text-white font-mono text-xs font-bold rounded-xl transition-all flex items-center gap-2 shadow-lg hover:scale-105"
              >
                {isCompiling ? (
                  <>
                    <span className="material-symbols-outlined text-sm animate-spin">sync</span>
                    <span>Compiling...</span>
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined text-sm">play_arrow</span>
                    <span>Re-Run 4-Layer Compile</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Section 3: Live 4-Layer Compilation Pipeline Tracker */}
          <div className="bg-slate-900/75 backdrop-blur-2xl border border-white/15 rounded-3xl p-6 shadow-2xl">
            <div className="flex justify-between items-center mb-6">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-tas-red text-xl">layers</span>
                <h2 className="font-headline font-bold text-base text-white">
                  3. Live 4-Layer Compilation Pipeline Tracker
                </h2>
              </div>
              <span className="px-3 py-1 bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 rounded-full text-xs font-mono font-bold flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                Status: Handoff Ready
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 relative">
              {/* Layer 1 */}
              <div
                className={`p-4 rounded-xl border transition-all ${
                  compilationLayer >= 1
                    ? 'border-emerald-300 bg-emerald-50/50'
                    : 'border-slate-200 bg-slate-50 opacity-60'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-mono font-bold uppercase text-slate-500">Layer 1</span>
                  <span className="material-symbols-outlined text-base text-emerald-600">check_circle</span>
                </div>
                <h4 className="font-sans font-bold text-xs text-slate-900">Discovery</h4>
                <p className="text-[11px] text-slate-500 mt-1 leading-tight">
                  File tree parsing & encoding normalization.
                </p>
              </div>

              {/* Layer 2 */}
              <div
                className={`p-4 rounded-xl border transition-all ${
                  compilationLayer >= 2
                    ? 'border-emerald-300 bg-emerald-50/50'
                    : 'border-slate-200 bg-slate-50 opacity-60'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-mono font-bold uppercase text-slate-500">Layer 2</span>
                  <span className="material-symbols-outlined text-base text-emerald-600">check_circle</span>
                </div>
                <h4 className="font-sans font-bold text-xs text-slate-900">Schema Mapper</h4>
                <p className="text-[11px] text-slate-500 mt-1 leading-tight">
                  Snake_case header alignment & time axis pairing.
                </p>
              </div>

              {/* Layer 3 */}
              <div
                className={`p-4 rounded-xl border transition-all ${
                  compilationLayer >= 3
                    ? 'border-emerald-300 bg-emerald-50/50'
                    : 'border-slate-200 bg-slate-50 opacity-60'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-mono font-bold uppercase text-slate-500">Layer 3</span>
                  <span className="material-symbols-outlined text-base text-emerald-600">check_circle</span>
                </div>
                <h4 className="font-sans font-bold text-xs text-slate-900">Relational Joiner</h4>
                <p className="text-[11px] text-slate-500 mt-1 leading-tight">
                  Side-by-side index join on parallel sensor channels.
                </p>
              </div>

              {/* Layer 4 */}
              <div
                className={`p-4 rounded-xl border transition-all ${
                  compilationLayer >= 4
                    ? 'border-tas-red bg-tas-red/20 ring-2 ring-tas-red/40 backdrop-blur-md'
                    : 'border-white/10 bg-slate-950/40 opacity-60'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-mono font-bold uppercase text-tas-red">Layer 4</span>
                  <span className="material-symbols-outlined text-base text-tas-red">verified</span>
                </div>
                <h4 className="font-sans font-bold text-xs text-tas-red">Handoff</h4>
                <p className="text-[11px] text-slate-300 mt-1 leading-tight">
                  Fleet vertical concatenation into clean 27-col table.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Col: Intelligent AI Data Agent & Health Shield */}
        <div className="space-y-6">
          {/* Section 2: Intelligent Data Agent & Query Inspector */}
          <div className="bg-slate-900/75 backdrop-blur-2xl border border-white/15 rounded-3xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-tas-red text-xl">psychology</span>
              <h2 className="font-headline font-bold text-base text-white">
                2. AI Data Agent & Inspector
              </h2>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              Ask the Schema Agent to query sensor columns, check sampling rates, or verify entity join keys.
            </p>

            <form onSubmit={handleQuerySubmit} className="space-y-2">
              <div className="relative">
                <input
                  type="text"
                  value={queryInput}
                  onChange={(e) => setQueryInput(e.target.value)}
                  placeholder="e.g. Find temperature sensors across set 1 & set 2..."
                  className="w-full bg-slate-950/60 border border-white/20 rounded-xl px-3.5 py-2.5 text-xs font-mono text-white placeholder-slate-400 focus:ring-2 focus:ring-tas-red outline-none"
                />
                <button
                  type="submit"
                  className="absolute right-1.5 top-1.5 p-1.5 bg-gradient-to-r from-tas-red to-tas-red-hover text-white rounded-lg transition-all shadow-md"
                >
                  <span className="material-symbols-outlined text-sm">search</span>
                </button>
              </div>
            </form>

            {/* Prompt Chips */}
            <div className="flex flex-wrap gap-1.5">
              <button
                type="button"
                onClick={() =>
                  setQueryInput('Find temperature sensors across set 1 and set 2 and check sampling rate')
                }
                className="px-2.5 py-1 bg-white/10 hover:bg-white/20 text-slate-200 text-[10px] font-mono rounded-lg border border-white/10 text-left"
              >
                ⚡ "Check temperature sensor sampling rate"
              </button>
              <button
                type="button"
                onClick={() => setQueryInput('Identify primary timestamp column and entity join keys')}
                className="px-2.5 py-1 bg-white/10 hover:bg-white/20 text-slate-200 text-[10px] font-mono rounded-lg border border-white/10 text-left"
              >
                ⚡ "Identify primary entity join keys"
              </button>
            </div>

            {/* AI Agent Response Box */}
            {queryResponse && (
              <div className="p-3.5 bg-tas-red/15 border border-tas-red/30 rounded-xl text-xs font-mono text-white leading-relaxed animate-fadeIn backdrop-blur-md">
                <div className="flex items-center gap-1.5 text-tas-red font-bold mb-1">
                  <span className="material-symbols-outlined text-sm">smart_toy</span>
                  <span>Schema Agent Diagnostic Result:</span>
                </div>
                {queryResponse}
              </div>
            )}

            {/* Schema Autodetect Cards */}
            <div className="pt-3 border-t border-white/10 space-y-2">
              <span className="text-[10px] font-mono font-bold uppercase text-slate-400">
                Autodetected Schema Badges
              </span>
              <div className="grid grid-cols-2 gap-2">
                <div className="p-2.5 bg-slate-950/60 border border-white/15 rounded-xl">
                  <p className="text-[10px] font-mono text-slate-400 uppercase">Time Axis</p>
                  <p className="text-xs font-mono font-bold text-white mt-0.5">time_cycle / timestamp</p>
                </div>
                <div className="p-2.5 bg-slate-950/60 border border-white/15 rounded-xl">
                  <p className="text-[10px] font-mono text-slate-400 uppercase">Entity Join Key</p>
                  <p className="text-xs font-mono font-bold text-white mt-0.5">unit_id (Turbofan Engine)</p>
                </div>
              </div>
            </div>
          </div>

          {/* Section 5: Dataset Health & Rejection Shield */}
          <div className="bg-slate-900/75 backdrop-blur-2xl border border-white/15 rounded-3xl p-6 shadow-2xl space-y-3">
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-tas-red text-xl">shield</span>
                <h2 className="font-headline font-bold text-base text-white">
                  5. Rejection Shield
                </h2>
              </div>
              <button
                onClick={() => setShowRejectionShield(!showRejectionShield)}
                className="text-xs font-mono font-bold text-tas-red hover:underline"
              >
                {showRejectionShield ? 'Hide Diagnostic' : 'Test Rejection Shield'}
              </button>
            </div>

            {showRejectionShield ? (
              <div className="p-4 bg-tas-red-light border border-tas-red/30 rounded-xl space-y-3 animate-fadeIn">
                <div className="flex items-start gap-2 text-tas-red">
                  <span className="material-symbols-outlined text-xl">gpp_maybe</span>
                  <div>
                    <h4 className="font-bold text-xs uppercase font-mono">
                      RED REJECTION SHIELD TRIGGERED
                    </h4>
                    <p className="text-xs text-slate-800 mt-0.5">
                      Row explosion delta check: Cartesian join mismatch detected (&gt;5.2%).
                    </p>
                  </div>
                </div>

                <div className="bg-white p-3 rounded-lg border border-tas-red/20 text-[11px] font-mono text-slate-700 space-y-1">
                  <p>• Sensor_A (20,631 rows) vs Sensor_B (21,705 rows)</p>
                  <p>• Missing timestamp indices in cycle range [140..152]</p>
                </div>

                <div className="text-[11px] text-slate-800">
                  <p className="font-bold text-slate-900 mb-1">Actionable Resolution Suggestions:</p>
                  <ul className="list-disc pl-4 space-y-0.5 font-mono text-[10px]">
                    <li>Enable strict index alignment on unit_id</li>
                    <li>Apply forward-fill (ffill) on missing time steps</li>
                  </ul>
                </div>
              </div>
            ) : (
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-3">
                <span className="material-symbols-outlined text-emerald-600 text-xl">verified_user</span>
                <div>
                  <p className="font-mono text-xs font-bold text-emerald-900">Shield Status: PASSING</p>
                  <p className="text-[11px] text-emerald-700 font-mono">
                    Zero Cartesian row explosion. 100% clean schema join.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Section 4: Data Summary & Transformation Audit Card + Preview Table */}
      <div className="bg-slate-900/75 backdrop-blur-2xl border border-white/15 rounded-3xl p-6 shadow-2xl space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/10">
          <div>
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-tas-red text-xl">summarize</span>
              <h2 className="font-headline font-bold text-lg text-white">
                4. Data Summary & Transformation Audit Card
              </h2>
            </div>
            <p className="text-xs text-slate-300 mt-0.5">
              Automated compilation summary pre- and post-transformation.
            </p>
          </div>

          <div className="px-4 py-2.5 bg-tas-red/15 border border-tas-red/30 rounded-2xl font-mono text-xs font-bold text-white flex items-center gap-2 backdrop-blur-md">
            <span className="material-symbols-outlined text-sm text-tas-red">transform</span>
            <span>Your Data: 12 Raw Text Files → Converted to: 27 Clean Columns (20,631 Rows)</span>
          </div>
        </div>

        {/* Column Types Header Pills */}
        <div>
          <div className="flex justify-between items-center mb-3">
            <span className="text-xs font-mono font-bold text-slate-300 uppercase tracking-wider">
              Compiled Data Schema Preview (First 10 Columns)
            </span>
            <span className="text-xs font-mono text-slate-400">Total Rows: 20,631 • Memory: 4.8 MB</span>
          </div>

          <div className="overflow-x-auto border border-white/15 rounded-2xl bg-slate-950/60">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-900/80 border-b border-white/15 text-[11px] font-mono text-slate-300">
                  {previewColumns.map((col) => (
                    <th key={col.name} className="px-4 py-3 font-semibold whitespace-nowrap">
                      <div className="flex flex-col gap-0.5">
                        <span className="text-white font-bold">{col.name}</span>
                        <span className="inline-block text-[9px] px-1.5 py-0.5 rounded font-mono bg-white/10 text-slate-200 border border-white/10">
                          {col.type}
                        </span>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10 text-xs font-mono text-slate-200">
                {previewRows.map((row, idx) => (
                  <tr key={idx} className="hover:bg-white/5 transition-colors">
                    <td className="px-4 py-2.5 text-white font-bold">{row.unit_id}</td>
                    <td className="px-4 py-2.5 text-slate-300">{row.time_cycle}</td>
                    <td className="px-4 py-2.5 text-slate-300">{row.setting_1}</td>
                    <td className="px-4 py-2.5 text-slate-300">{row.setting_2}</td>
                    <td className="px-4 py-2.5 text-slate-300">{row.setting_3}</td>
                    <td className="px-4 py-2.5 text-white font-semibold">{row.fan_inlet_temp}</td>
                    <td className="px-4 py-2.5 text-white font-semibold">{row.lpc_outlet_temp}</td>
                    <td className="px-4 py-2.5 text-white font-semibold">{row.hpc_outlet_temp}</td>
                    <td className="px-4 py-2.5 text-white font-semibold">{row.lpt_outlet_temp}</td>
                    <td className="px-4 py-2.5 text-white font-semibold">{row.fan_speed_rpm}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Action Bar */}
        <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-xs text-slate-300 font-mono">
            <span className="material-symbols-outlined text-emerald-400 text-base">check_circle</span>
            <span>Target Column Synthesized: <strong className="text-white font-mono">RUL (Remaining Useful Life)</strong></span>
          </div>

          <button
            onClick={onSendToMLOps}
            className="w-full sm:w-auto px-6 py-3 bg-gradient-to-r from-tas-red to-tas-red-hover hover:scale-105 text-white font-mono text-xs font-bold rounded-2xl shadow-xl transition-all active:scale-95 flex items-center justify-center gap-2"
          >
            <span>Direct MLOps Handoff: Trigger Node 1 Dataset Profiler</span>
            <span className="material-symbols-outlined text-base">arrow_forward</span>
          </button>
        </div>
      </div>

      {/* Archive Inspection Drawer (Overlay Slide-over) */}
      {isInspectionDrawerOpen && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-md z-50 flex justify-end animate-fadeIn">
          <div className="w-full max-w-md bg-slate-900/90 border-l border-white/15 h-full shadow-2xl p-6 flex flex-col justify-between overflow-y-auto backdrop-blur-2xl text-white">
            <div>
              <div className="flex justify-between items-center pb-4 border-b border-white/10 mb-4">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-tas-red text-xl">folder_open</span>
                  <h3 className="font-headline font-bold text-base text-white">Archive Inspection Drawer</h3>
                </div>
                <button
                  onClick={() => setIsInspectionDrawerOpen(false)}
                  className="p-1 hover:bg-white/10 rounded-lg text-slate-400 hover:text-white"
                >
                  <span className="material-symbols-outlined">close</span>
                </button>
              </div>

              <p className="text-xs text-slate-300 mb-4">
                Extracted subfolder tree with detected character encodings and size breakdown.
              </p>

              <div className="space-y-3 font-mono text-xs">
                {archiveFiles.map((file, i) => (
                  <div key={i} className="p-3 bg-slate-950/60 border border-white/15 rounded-2xl space-y-1">
                    <div className="flex justify-between items-center font-bold text-white">
                      <span className="truncate">{file.name}</span>
                      <span className="px-2 py-0.5 bg-white/10 text-slate-200 text-[10px] rounded-lg">{file.size}</span>
                    </div>
                    <div className="flex justify-between text-[11px] text-slate-400">
                      <span>Type: {file.type}</span>
                      <span>Encoding: <strong className="text-tas-red">{file.encoding}</strong></span>
                    </div>
                    <div className="text-[10px] text-slate-400">
                      Columns: {file.cols} detected
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-4 border-t border-white/10">
              <button
                onClick={() => setIsInspectionDrawerOpen(false)}
                className="w-full py-2.5 bg-gradient-to-r from-tas-red to-tas-red-hover hover:scale-105 text-white font-mono text-xs font-bold rounded-2xl shadow-lg transition-all"
              >
                Close Inspection Drawer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
