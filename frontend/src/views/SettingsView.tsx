import React, { useState } from 'react';
import { SidebarStyle } from '../types';

interface SettingsViewProps {
  sidebarStyle?: SidebarStyle;
  onSidebarStyleChange?: (style: SidebarStyle) => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  sidebarStyle = 'slim',
  onSidebarStyleChange,
}) => {
  const [clusterRegion, setClusterRegion] = useState('US-EAST-1 (N. Virginia)');
  const [maxBatchSize, setMaxBatchSize] = useState('512');
  const [autoScale, setAutoScale] = useState(true);
  const [selectedSidebarStyle, setSelectedSidebarStyle] = useState<SidebarStyle>(sidebarStyle);
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    if (onSidebarStyleChange) {
      onSidebarStyleChange(selectedSidebarStyle);
    }
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="space-y-6 pb-12 animate-fadeIn max-w-4xl">
      <div className="border-b border-slate-200 pb-4">
        <h1 className="font-headline text-3xl font-bold text-slate-900 tracking-tight">Platform Settings</h1>
        <p className="text-slate-500 text-xs mt-1">
          Cluster region defaults, zero-downtime deployment policies, and platform interface preferences.
        </p>
      </div>

      {saved && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg text-xs font-mono font-bold flex items-center gap-2 animate-fadeIn">
          <span className="material-symbols-outlined text-base">check_circle</span>
          <span>Settings saved successfully. Navigation layout and platform preferences synchronized.</span>
        </div>
      )}

      <form onSubmit={handleSave} className="bg-white border border-slate-200 p-6 rounded-xl shadow-sm space-y-8">
        {/* Navigation & Interface Aesthetics Section */}
        <div className="space-y-4">
          <div className="border-b border-slate-100 pb-2">
            <h3 className="font-headline text-base font-bold text-slate-900">
              Navigation &amp; Interface Aesthetics
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Choose your preferred sidebar layout. Toggle between the Slim Sleek Left Dock and the OrbitalARC Assistive Arc.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            {/* Slim Sleek Floating Icons Option */}
            <div
              onClick={() => setSelectedSidebarStyle('slim')}
              className={`cursor-pointer rounded-2xl border-2 p-4 transition-all duration-200 relative flex flex-col justify-between ${
                selectedSidebarStyle === 'slim'
                  ? 'border-tas-blue bg-blue-50/40 shadow-md ring-2 ring-tas-blue/20'
                  : 'border-slate-200 hover:border-slate-300 bg-white hover:bg-slate-50/50'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-9 h-9 rounded-xl bg-slate-900 text-cyan-400 flex items-center justify-center shadow-xs">
                      <span className="material-symbols-outlined text-lg">view_sidebar</span>
                    </div>
                    <div>
                      <h4 className="font-bold text-xs text-slate-900">Slim Sleek Left Dock</h4>
                      <span className="text-[10px] font-mono text-cyan-600 font-semibold">Floating Left Icons</span>
                    </div>
                  </div>
                  <input
                    type="radio"
                    name="sidebarStyle"
                    checked={selectedSidebarStyle === 'slim'}
                    onChange={() => setSelectedSidebarStyle('slim')}
                    className="w-4 h-4 text-tas-blue focus:ring-tas-blue"
                  />
                </div>
                <p className="text-slate-600 text-xs leading-relaxed">
                  Unique, lightweight floating icon sidebar anchored on the left side of the screen. Hover cursor over icons for instant name tooltips.
                </p>
              </div>

              {/* Feature Pills */}
              <div className="mt-4 pt-3 border-t border-slate-200/60 flex items-center gap-2">
                <span className="px-2 py-0.5 bg-cyan-100 text-cyan-800 text-[10px] font-mono font-bold rounded-md">
                  Hover Name Tooltips
                </span>
                <span className="px-2 py-0.5 bg-slate-100 text-slate-700 text-[10px] font-mono font-bold rounded-md">
                  Left Floating
                </span>
              </div>
            </div>

            {/* OrbitalARC Sidebar Option */}
            <div
              onClick={() => setSelectedSidebarStyle('orbital')}
              className={`cursor-pointer rounded-2xl border-2 p-4 transition-all duration-200 relative flex flex-col justify-between ${
                selectedSidebarStyle === 'orbital'
                  ? 'border-tas-blue bg-blue-50/40 shadow-md ring-2 ring-tas-blue/20'
                  : 'border-slate-200 hover:border-slate-300 bg-white hover:bg-slate-50/50'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-9 h-9 rounded-xl bg-slate-900 text-purple-400 flex items-center justify-center shadow-xs">
                      <span className="material-symbols-outlined text-lg">motion_photos_paused</span>
                    </div>
                    <div>
                      <h4 className="font-bold text-xs text-slate-900">OrbitalARC Sidebar</h4>
                      <span className="text-[10px] font-mono text-purple-600 font-semibold">Assistive Arc</span>
                    </div>
                  </div>
                  <input
                    type="radio"
                    name="sidebarStyle"
                    checked={selectedSidebarStyle === 'orbital'}
                    onChange={() => setSelectedSidebarStyle('orbital')}
                    className="w-4 h-4 text-tas-blue focus:ring-tas-blue"
                  />
                </div>
                <p className="text-slate-600 text-xs leading-relaxed">
                  Interactive floating arc menu with smooth cursor magnetics, radial physics, and dual concentric inner/outer wheels.
                </p>
              </div>

              {/* Feature Pills */}
              <div className="mt-4 pt-3 border-t border-slate-200/60 flex items-center gap-2">
                <span className="px-2 py-0.5 bg-purple-100 text-purple-800 text-[10px] font-mono font-bold rounded-md">
                  Physics Cursor Arc
                </span>
                <span className="px-2 py-0.5 bg-slate-100 text-slate-700 text-[10px] font-mono font-bold rounded-md">
                  Dual concentric
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Compute & Region Configuration */}
        <div className="space-y-4 pt-4 border-t border-slate-100">
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
            className="px-6 py-2.5 bg-tas-blue hover:bg-tas-blue-hover text-white font-bold text-xs rounded-lg shadow-xs transition-all active:scale-95 flex items-center gap-2"
          >
            <span className="material-symbols-outlined text-sm">save</span>
            <span>Save Platform Settings</span>
          </button>
        </div>
      </form>
    </div>
  );
};
