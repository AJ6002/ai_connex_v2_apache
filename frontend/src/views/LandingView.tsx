import React, { useState } from 'react';
import { TasLogo } from '../components/TasLogo';
import { ChatView } from './ChatView';

interface LandingViewProps {
  onNavigateToUpload: (prompt: string, initialInputs?: {
    targetColumn?: string;
    problemType?: string;
    timestampColumn?: string;
    entityColumn?: string;
  }) => void;
  onDatasetCompiled?: (sessionId: string, compiledCsvPath: string) => void;
}

export const LandingView: React.FC<LandingViewProps> = ({
  onNavigateToUpload,
  onDatasetCompiled,
}) => {
  const [activeInitialPrompt, setActiveInitialPrompt] = useState<string | undefined>(undefined);

  const samplePrompts = [
    { text: 'Train a Remaining Useful Life (RUL) predictor for C-MAPSS turbofan engine SCADA logs.', icon: 'speed',    color: '#C8102E', label: 'Regression · RUL' },
    { text: 'Detect anomalies and drifts in multivariate industrial sensor streams.',                icon: 'insights', color: '#1E47C8', label: 'Anomaly Detection' },
    { text: 'Build a failure classification pipeline with custom outlier thresholds.',              icon: 'warning',  color: '#d97706', label: 'Classification' },
  ];

  return (
    <div className="min-h-[85vh] flex flex-col items-center justify-center p-4 relative overflow-hidden bg-slate-900/50 backdrop-blur-xl rounded-3xl border border-slate-800 shadow-2xl">
      {/* Background ambience */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-tas-red/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-tas-blue/5 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-3xl w-full space-y-6 relative z-10">

        {/* HEADER */}
        <div className="flex flex-col items-center gap-2 text-center">
          <TasLogo className="h-14 animate-pulse" showSubtitle={false} />
          <h1 className="font-headline text-3xl sm:text-4xl font-black tracking-tight text-white">
            <span className="inline-flex items-center gap-1">
              AI&nbsp;<img src="/connexx-dark.png" alt="Connexx" className="h-8 w-auto object-contain inline-block align-middle invert" />
            </span>
          </h1>
          <p className="text-xs font-mono text-slate-400 max-w-xl">
            Single LangGraph Conversational Compiler — Intent gathering, Scout profiling, Strategy choice, and in-app Data Explorer handoff.
          </p>
        </div>

        {/* STARTER PROMPT CARDS (before prompt is selected) */}
        {!activeInitialPrompt && (
          <div className="space-y-2">
            <p className="text-[10px] font-mono font-bold uppercase tracking-widest text-slate-400 text-center">
              Select a starter configuration or type below
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {samplePrompts.map((sample, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setActiveInitialPrompt(sample.text)}
                  className="group flex flex-col gap-2 rounded-xl border border-slate-800 bg-slate-950/80 p-4 text-left shadow-sm hover:border-blue-500 hover:shadow-md transition-all active:scale-95 cursor-pointer"
                >
                  <div className="flex items-center gap-2">
                    <span
                      className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-white text-sm"
                      style={{ background: sample.color }}
                    >
                      <span className="material-symbols-outlined text-base">{sample.icon}</span>
                    </span>
                    <span className="text-[10px] font-mono font-semibold text-slate-400 bg-slate-800 px-2 py-0.5 rounded-full transition-colors group-hover:text-blue-300">
                      {sample.label}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 font-sans leading-relaxed group-hover:text-white transition-colors">
                    {sample.text}
                  </p>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* CHATVIEW CONTAINER — assistant-ui single brain */}
        <div className="rounded-2xl border border-slate-800 bg-slate-950/90 shadow-2xl overflow-hidden flex flex-col min-h-[420px]">
          <ChatView
            key={activeInitialPrompt || 'default'}
            initialMessage={activeInitialPrompt}
            onDatasetCompiled={onDatasetCompiled}
          />
        </div>

      </div>
    </div>
  );
};

export default LandingView;
