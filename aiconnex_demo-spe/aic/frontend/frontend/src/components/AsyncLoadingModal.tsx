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
    <div className="fixed inset-0 z-50 flex items-center justify-center backdrop-blur-md p-4 animate-fadeIn"
      style={{background:'rgba(255,255,255,0.60)'}}>
      <div className="rounded-3xl shadow-2xl max-w-2xl w-full overflow-hidden flex flex-col max-h-[90vh] text-white"
        style={{background:'rgba(13,21,51,0.92)', border:'1px solid rgba(255,255,255,0.16)'}}>
        {/* Modal Header */}
        <div className="p-6 flex justify-between items-start" style={{background:'rgba(6,9,20,0.70)', borderBottom:'1px solid rgba(255,255,255,0.08)'}}>
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 bg-tas-red text-white text-[10px] font-mono font-bold uppercase rounded-lg tracking-wider">
                CASCADE RUNNING
              </span>
              <span className="text-slate-400 font-mono text-xs">ID: {job.jobId}</span>
            </div>
            <h3 className="font-headline text-xl font-extrabold mt-2 text-white leading-tight">
              {job.title}
            </h3>
            <p className="text-slate-300 text-xs font-sans mt-1 leading-relaxed">
              {job.subtitle}
            </p>
          </div>

          <div className="text-right">
            <span className="font-mono text-3xl font-black text-tas-red">
              {Math.round(job.overallPercent)}%
            </span>
            <p className="text-[10px] font-mono text-slate-400 uppercase">Progress</p>
          </div>
        </div>

        {/* Overall Progress Bar */}
        <div className="w-full h-1.5 relative" style={{background:'rgba(255,255,255,0.06)'}}>
          <div
            className="h-full transition-all duration-300 ease-out rounded-full"
            style={{ width: `${job.overallPercent}%`, background:'linear-gradient(90deg,#C8102E 0%,#E8405A 100%)' }}
          />
        </div>

        {/* Modal Content - Steps & Detailed Explanation */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1" style={{background:'rgba(6,9,20,0.30)'}}>
          {/* Detailed Sequential Steps */}
          <div>
            <h4 className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider mb-3">
              Flowchart Stage Progress ({job.currentStepIndex + 1}/{job.totalSteps})
            </h4>

            <div className="space-y-2.5">
              {job.steps.map((step, idx) => {
                const isCurrent = idx === job.currentStepIndex;
                const isDone = step.status === 'completed';

                return (
                  <div
                    key={step.id}
                    className={`p-3.5 rounded-2xl border transition-all ${
                      isCurrent
                        ? 'border-[rgba(200,16,46,0.50)]'
                        : isDone
                        ? 'border-[rgba(34,197,94,0.25)]'
                        : 'border-[rgba(255,255,255,0.08)] opacity-60'
                    }`}
                    style={isCurrent ? {background:'rgba(200,16,46,0.10)', boxShadow:'0 0 0 1px rgba(200,16,46,0.30)'} : isDone ? {background:'rgba(34,197,94,0.08)'} : {background:'rgba(6,9,20,0.30)'}}
                  >
                    <div className="flex items-start gap-3">
                      <div className="mt-0.5 flex-shrink-0">
                        {isDone ? (
                          <span className="material-symbols-outlined text-emerald-400 text-lg">
                            check_circle
                          </span>
                        ) : isCurrent ? (
                          <span className="material-symbols-outlined text-tas-red text-lg animate-spin">
                            sync
                          </span>
                        ) : (
                          <span className="material-symbols-outlined text-slate-500 text-lg">
                            radio_button_unchecked
                          </span>
                        )}
                      </div>

                      <div className="flex-1">
                        <div className="flex justify-between items-center">
                          <h5
                            className={`text-xs font-mono font-bold ${
                              isCurrent
                                ? 'text-white'
                                : isDone
                                ? 'text-emerald-300'
                                : 'text-slate-400'
                            }`}
                          >
                            {step.title}
                          </h5>
                          <span
                            className={`text-[9px] font-mono font-bold uppercase px-2 py-0.5 rounded-lg ${
                              isDone
                                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                                : isCurrent
                                ? 'bg-tas-red text-white animate-pulse'
                                : 'bg-white/10 text-slate-400'
                            }`}
                          >
                            {step.status}
                          </span>
                        </div>

                        <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                          {step.description}
                        </p>

                        {step.detail && isCurrent && (
                          <div className="mt-2 text-[11px] font-mono p-2 rounded-xl flex items-center gap-1.5"
                            style={{background:'rgba(6,9,20,0.70)', border:'1px solid rgba(200,16,46,0.35)', color:'#E8405A'}}>
                            <span className="material-symbols-outlined text-xs">info</span>
                            <span>{step.detail}</span>
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
              <h4 className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
                Live Microservices Telemetry Log
              </h4>
              <span className="text-[10px] font-mono text-slate-400">Streaming...</span>
            </div>

            <div className="font-mono text-[11px] p-3 rounded-2xl h-28 overflow-y-auto space-y-1 border"
              style={{background:'rgba(6,9,20,0.80)', color:'rgba(74,222,128,0.90)', borderColor:'rgba(255,255,255,0.10)'}}>
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
        <div className="p-4 flex justify-between items-center" style={{background:'rgba(6,9,20,0.60)', borderTop:'1px solid rgba(255,255,255,0.08)'}}>
          <button
            onClick={onCancelJob}
            className="px-4 py-2 font-mono font-bold text-xs rounded-xl transition-all"
            style={{border:'1px solid rgba(200,16,46,0.40)', color:'#E8405A', background:'transparent'}}
            onMouseEnter={e => (e.currentTarget.style.background='rgba(200,16,46,0.12)')}
            onMouseLeave={e => (e.currentTarget.style.background='transparent')}
          >
            Cancel Pipeline
          </button>

          <button
            onClick={onDismissToBackground}
            className="px-5 py-2 btn-primary font-mono font-bold text-xs rounded-xl shadow-lg transition-all flex items-center gap-2"
          >
            <span>Run in Background</span>
            <span className="material-symbols-outlined text-sm">visibility_off</span>
          </button>
        </div>
      </div>
    </div>
  );
};
