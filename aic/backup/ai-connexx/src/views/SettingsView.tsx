import React, { useState } from 'react';

export const SettingsView: React.FC = () => {
  const [clusterRegion, setClusterRegion] = useState('US-EAST-1 (N. Virginia)');
  const [maxBatchSize, setMaxBatchSize] = useState('512');
  const [autoScale, setAutoScale] = useState(true);
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="space-y-6 pb-12 animate-fadeIn max-w-4xl">
      <div className="border-b border-slate-200 pb-4">
        <h1 className="font-headline text-3xl font-bold text-slate-900 tracking-tight">Platform Settings</h1>
        <p className="text-slate-500 text-xs mt-1">
          Cluster region defaults, zero-downtime deployment policies, and platform preferences.
        </p>
      </div>

      {saved && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg text-xs font-mono font-bold flex items-center gap-2">
          <span className="material-symbols-outlined text-base">check_circle</span>
          <span>Settings saved successfully. Cluster configuration synchronized.</span>
        </div>
      )}

      <form onSubmit={handleSave} className="bg-white border border-slate-200 p-6 rounded-xl shadow-sm space-y-6">
        <div className="space-y-4">
          <h3 className="font-headline text-base font-bold text-slate-900 border-b border-slate-100 pb-2">
            Compute &amp; Region Configuration
          </h3>

          <div>
            <label className="block text-xs font-mono font-bold text-slate-600 mb-1">
              PRIMARY CLUSTER REGION
            </label>
            <select
              value={clusterRegion}
              onChange={(e) => setClusterRegion(e.target.value)}
              className="w-full border border-slate-200 rounded-lg p-2.5 text-xs font-mono text-slate-900 focus:ring-2 focus:ring-tas-blue outline-none"
            >
              <option value="US-EAST-1 (N. Virginia)">US-EAST-1 (N. Virginia)</option>
              <option value="EU-WEST-1 (Ireland)">EU-WEST-1 (Ireland)</option>
              <option value="AP-SOUTHEAST-1 (Singapore)">AP-SOUTHEAST-1 (Singapore)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-mono font-bold text-slate-600 mb-1">
              MAX CONCURRENT BATCH SIZE
            </label>
            <input
              type="number"
              value={maxBatchSize}
              onChange={(e) => setMaxBatchSize(e.target.value)}
              className="w-full border border-slate-200 rounded-lg p-2.5 text-xs font-mono text-slate-900 focus:ring-2 focus:ring-tas-blue outline-none"
            />
          </div>

          <div className="flex items-center gap-2 pt-2">
            <input
              type="checkbox"
              id="autoscale-check"
              checked={autoScale}
              onChange={(e) => setAutoScale(e.target.checked)}
              className="rounded text-tas-blue focus:ring-tas-blue accent-tas-blue"
            />
            <label htmlFor="autoscale-check" className="text-xs font-mono font-bold text-slate-900">
              Enable Automatic GPU Node Auto-Scaling (0 to 128 nodes)
            </label>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-200 flex justify-end">
          <button
            type="submit"
            className="px-6 py-2.5 bg-tas-blue hover:bg-tas-blue-hover text-white font-bold text-xs rounded-lg shadow-xs transition-all active:scale-95"
          >
            Save Platform Settings
          </button>
        </div>
      </form>
    </div>
  );
};
