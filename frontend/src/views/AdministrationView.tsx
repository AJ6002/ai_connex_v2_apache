import React, { useState } from 'react';
import { EnvironmentVariable } from '../types';

interface AdministrationViewProps {
  envVars: EnvironmentVariable[];
  onAddVariable: (key: string, value: string, description: string, isSecret: boolean) => void;
  onToggleMaskSecret: (id: string) => void;
}

export const AdministrationView: React.FC<AdministrationViewProps> = ({
  envVars,
  onAddVariable,
  onToggleMaskSecret,
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newKey, setNewKey] = useState('');
  const [newValue, setNewValue] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [isSecret, setIsSecret] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKey.trim()) return;
    onAddVariable(newKey.trim(), newValue, newDesc, isSecret);
    setNewKey('');
    setNewValue('');
    setNewDesc('');
    setIsSecret(false);
    setIsModalOpen(false);
  };

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Header & New Variable CTA */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <nav className="flex items-center gap-2 text-slate-400 text-xs font-mono uppercase tracking-widest mb-1">
            <span>Administration</span>
            <span className="material-symbols-outlined text-xs">chevron_right</span>
            <span className="text-tas-blue font-bold">System Configurations</span>
          </nav>
          <h1 className="font-headline text-3xl font-bold text-slate-900 tracking-tight">Environment Variables</h1>
          <p className="text-slate-500 text-xs mt-1">
            Manage global application settings and secure connection strings for the AI-Connexx production cluster.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="bg-tas-blue hover:bg-tas-blue-hover text-white px-5 py-2.5 rounded-lg text-xs font-bold flex items-center gap-2 shadow-xs transition-all active:scale-95"
        >
          <span className="material-symbols-outlined text-base">add</span>
          <span>New Variable</span>
        </button>
      </div>

      {/* Stats Summary Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-sm">
          <p className="font-mono text-[11px] text-slate-400 uppercase tracking-wider font-semibold">
            TOTAL VARIABLES
          </p>
          <p className="font-mono text-3xl font-bold text-slate-900 mt-1">42</p>
        </div>
        <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-sm">
          <p className="font-mono text-[11px] text-slate-400 uppercase tracking-wider font-semibold">
            MASKED SECRETS
          </p>
          <p className="font-mono text-3xl font-bold text-tas-blue mt-1">12</p>
        </div>
        <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-sm">
          <p className="font-mono text-[11px] text-slate-400 uppercase tracking-wider font-semibold">
            LAST DEPLOYMENT
          </p>
          <p className="font-mono text-2xl font-bold text-slate-900 mt-2">14m ago</p>
        </div>
        <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-sm">
          <p className="font-mono text-[11px] text-slate-400 uppercase tracking-wider font-semibold">
            ACTIVE CLUSTER
          </p>
          <p className="font-mono text-2xl font-bold text-tas-blue mt-2">US-EAST-1</p>
        </div>
      </div>

      {/* Configuration List Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <div className="grid grid-cols-12 gap-4 px-6 py-3.5 bg-slate-100 text-slate-500 font-mono text-[11px] uppercase tracking-wider font-bold border-b border-slate-200">
          <div className="col-span-5">Key Identifier</div>
          <div className="col-span-5">Current Value</div>
          <div className="col-span-2 text-right">Actions</div>
        </div>

        <div className="divide-y divide-slate-100">
          {envVars.map((item) => (
            <div
              key={item.id}
              className="grid grid-cols-12 gap-4 px-6 py-4 items-center hover:bg-slate-50 transition-colors text-xs"
            >
              <div className="col-span-5 flex flex-col">
                <span className="font-mono font-bold text-slate-900">{item.key}</span>
                <span className="text-[11px] text-slate-500 mt-0.5">{item.description}</span>
              </div>

              <div className="col-span-5 flex items-center">
                {item.isSecret ? (
                  <div className="bg-slate-100 px-3 py-1.5 rounded-md border border-slate-200 flex items-center gap-3">
                    <button
                      onClick={() => onToggleMaskSecret(item.id)}
                      title={item.isMasked ? 'Reveal secret' : 'Mask secret'}
                      className="material-symbols-outlined text-slate-400 text-base hover:text-tas-blue transition-colors"
                    >
                      {item.isMasked ? 'lock' : 'lock_open'}
                    </button>
                    <span className="font-mono text-slate-600 tracking-widest">
                      {item.isMasked ? '•••••••••••••••••••••' : item.value}
                    </span>
                  </div>
                ) : (
                  <code className="bg-tas-blue-light text-tas-blue px-3 py-1.5 rounded-md border border-tas-blue/30 font-mono text-xs font-bold">
                    {item.value}
                  </code>
                )}
              </div>

              <div className="col-span-2 text-right flex justify-end gap-1">
                <button
                  onClick={() => onToggleMaskSecret(item.id)}
                  className="text-slate-400 hover:text-tas-blue p-2 rounded-md hover:bg-slate-100 transition-all"
                  title="Toggle Visibility"
                >
                  <span className="material-symbols-outlined text-base">
                    {item.isMasked ? 'visibility' : 'visibility_off'}
                  </span>
                </button>
                <button
                  className="text-slate-400 hover:text-slate-700 p-2 rounded-md hover:bg-slate-100 transition-all"
                  title="View History"
                >
                  <span className="material-symbols-outlined text-base">history</span>
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* List Footer */}
        <div className="bg-slate-50/50 px-6 py-3 flex justify-between items-center border-t border-slate-200">
          <span className="text-xs font-mono text-slate-500">Showing {envVars.length} of 42 configurations</span>
          <div className="flex gap-2 font-mono text-xs font-bold">
            <button className="px-3 py-1 border border-slate-200 rounded-md hover:bg-white text-slate-700">
              Previous
            </button>
            <button className="px-3 py-1 bg-tas-blue text-white rounded-md">Next</button>
          </div>
        </div>
      </div>

      {/* Deployment Warning Banner */}
      <div className="bg-tas-red-light border border-tas-red/30 p-5 rounded-xl flex items-start gap-4">
        <span className="material-symbols-outlined text-tas-red text-2xl">report</span>
        <div>
          <h3 className="font-sans font-bold text-sm text-tas-red">Warning: Cluster Propagation</h3>
          <p className="text-slate-700 text-xs mt-1 leading-relaxed">
            Changes to environment variables trigger an automated rolling restart of the AI-Connexx cluster. Expected downtime: <span className="font-bold font-mono">~0 seconds (Zero-Downtime)</span>.
          </p>
        </div>
      </div>

      {/* New Variable Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="bg-white border border-slate-200 rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex justify-between items-center border-b border-slate-200 pb-3">
              <h3 className="font-headline text-lg font-bold text-slate-900">Add Environment Variable</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <span className="material-symbols-outlined text-xl">close</span>
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-mono font-bold text-slate-600 mb-1">
                  KEY IDENTIFIER
                </label>
                <input
                  type="text"
                  required
                  value={newKey}
                  onChange={(e) => setNewKey(e.target.value.toUpperCase())}
                  placeholder="e.g. GEMINI_PRO_API_ENDPOINT"
                  className="w-full border border-slate-200 rounded-lg p-2.5 text-xs font-mono text-slate-900 focus:ring-2 focus:ring-tas-blue outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-mono font-bold text-slate-600 mb-1">
                  CURRENT VALUE
                </label>
                <input
                  type="text"
                  required
                  value={newValue}
                  onChange={(e) => setNewValue(e.target.value)}
                  placeholder="e.g. https://api.connexx.ai/v1"
                  className="w-full border border-slate-200 rounded-lg p-2.5 text-xs font-mono text-slate-900 focus:ring-2 focus:ring-tas-blue outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-mono font-bold text-slate-600 mb-1">
                  DESCRIPTION
                </label>
                <input
                  type="text"
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="Purpose of this configuration variable..."
                  className="w-full border border-slate-200 rounded-lg p-2.5 text-xs text-slate-900 focus:ring-2 focus:ring-tas-blue outline-none"
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="secret-check"
                  checked={isSecret}
                  onChange={(e) => setIsSecret(e.target.checked)}
                  className="rounded text-tas-blue focus:ring-tas-blue accent-tas-blue"
                />
                <label htmlFor="secret-check" className="text-xs font-mono font-bold text-slate-900">
                  Mask as Sensitive Secret credential
                </label>
              </div>

              <div className="pt-2 flex justify-end gap-3 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-tas-blue hover:bg-tas-blue-hover text-white text-xs font-bold rounded-lg shadow-xs"
                >
                  Save Configuration
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
