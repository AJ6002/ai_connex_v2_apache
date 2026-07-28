import React from 'react';
import { AsyncJobProgress } from '../types';

interface AsyncLoadingModalProps {
  job: AsyncJobProgress | null;
  onDismissToBackground: () => void;
  onCancelJob?: () => void;
}

export const AsyncLoadingModal: React.FC<AsyncLoadingModalProps> = ({
  job,
  onDismissToBackground,
  onCancelJob,
}) => {
  if (!job) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 animate-fadeIn">
      <div className="bg-white border border-slate-200 rounded-xl shadow-2xl max-w-2xl w-full overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="bg-[#0F172A] text-white p-6 flex justify-between items-start">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 bg-tas-blue text-white text-[10px] font-mono font-bold uppercase rounded tracking-wider">
                ASYNC TASK RUNNING
              </span>
              <span className="text-slate-400 font-mono text-xs">ID: {job.jobId}</span>
            </div>
            <h3 className="font-headline text-xl font-bold mt-2 text-white leading-tight">
              {job.title}
            </h3>
            <p className="text-slate-300 text-xs font-sans mt-1 leading-relaxed">
              {job.subtitle}
            </p>
          </div>

          <div className="text-right">
            <span className="font-mono text-3xl font-black text-tas-blue">
              {Math.round(job.overallPercent)}%
            </span>
            <p className="text-[10px] font-mono text-slate-400 uppercase">Progress</p>
          </div>
        </div>

        {/* Overall Progress Bar */}
        <div className="w-full bg-slate-100 h-2 relative">
          <div
            className="bg-tas-blue h-full transition-all duration-300 ease-out"
            style={{ width: `${job.overallPercent}%` }}
          />
        </div>

        {/* Modal Content - Steps & Detailed Explanation */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 bg-slate-50/50">
          {/* Detailed Sequential Steps */}
          <div>
            <h4 className="text-xs font-mono font-bold text-slate-500 uppercase tracking-wider mb-3">
              Background Processing Stages ({job.currentStepIndex + 1}/{job.totalSteps})
            </h4>

            <div className="space-y-2.5">
              {job.steps.map((step, idx) => {
                const isCurrent = idx === job.currentStepIndex;
                const isDone = step.status === 'completed';

                return (
                  <div
                    key={step.id}
                    className={`p-3.5 rounded-lg border transition-all ${
                      isCurrent
                        ? 'border-tas-blue bg-tas-blue-light ring-1 ring-tas-blue/30'
                        : isDone
                        ? 'border-emerald-200 bg-emerald-50/50'
                        : 'border-slate-200 bg-white opacity-60'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="mt-0.5 flex-shrink-0">
                        {isDone ? (
                          <span className="material-symbols-outlined text-emerald-600 text-lg">
                            check_circle
                          </span>
                        ) : isCurrent ? (
                          <span className="material-symbols-outlined text-tas-blue text-lg animate-spin">
                            sync
                          </span>
                        ) : (
                          <span className="material-symbols-outlined text-slate-400 text-lg">
                            radio_button_unchecked
                          </span>
                        )}
                      </div>

                      <div className="flex-1">
                        <div className="flex justify-between items-center">
                          <h5
                            className={`text-sm font-semibold ${
                              isCurrent
                                ? 'text-tas-blue font-bold'
                                : isDone
                                ? 'text-emerald-900'
                                : 'text-slate-700'
                            }`}
                          >
                            {step.title}
                          </h5>
                          <span
                            className={`text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded ${
                              isDone
                                ? 'bg-emerald-100 text-emerald-800'
                                : isCurrent
                                ? 'bg-tas-blue text-white animate-pulse'
                                : 'bg-slate-200 text-slate-600'
                            }`}
                          >
                            {step.status}
                          </span>
                        </div>

                        <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                          {step.description}
                        </p>

                        {step.detail && isCurrent && (
                          <div className="mt-2 text-[11px] font-mono bg-white p-2 rounded-md border border-tas-blue/30 text-tas-blue font-bold shadow-2xs">
                            👉 {step.detail}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Real-time Streaming Logs Preview */}
          <div>
            <div className="flex justify-between items-center mb-1.5">
              <h4 className="text-xs font-mono font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
                Live Execution Output Log
              </h4>
              <span className="text-[10px] font-mono text-slate-400">Streaming...</span>
            </div>

            <div className="bg-slate-900 text-emerald-400 font-mono text-[11px] p-3 rounded-lg h-28 overflow-y-auto space-y-1 border border-slate-800 shadow-inner">
              {job.logs.length === 0 ? (
                <div className="text-slate-500 italic">Initializing stream logger...</div>
              ) : (
                job.logs.map((log, i) => (
                  <div key={i} className="leading-snug">
                    {log}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Modal Footer Actions */}
        <div className="p-4 bg-white border-t border-slate-200 flex justify-between items-center">
          <button
            onClick={onCancelJob}
            className="px-4 py-2 border border-tas-red/30 text-tas-red hover:bg-tas-red-light font-semibold text-xs rounded-lg transition-all"
          >
            Cancel Job
          </button>

          <button
            onClick={onDismissToBackground}
            className="px-5 py-2 bg-tas-blue hover:bg-tas-blue-hover text-white font-bold text-xs rounded-lg shadow-sm transition-all flex items-center gap-2"
          >
            <span>Run in Background & Dismiss</span>
            <span className="material-symbols-outlined text-sm">visibility_off</span>
          </button>
        </div>
      </div>
    </div>
  );
};
