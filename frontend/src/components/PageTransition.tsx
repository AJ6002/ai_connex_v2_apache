import React, { useEffect, useState } from 'react';
import { ViewMode } from '../types';

interface PageTransitionProps {
  from: ViewMode;
  to: ViewMode;
  onComplete: () => void;
}

const TRANSITION_STEPS: Record<string, { label: string; steps: string[] }> = {
  compiler: {
    label: 'Home / Upload',
    steps: ['Initialising Workspace…', 'Loading Archive Engine…', 'Ready'],
  },
  node4: {
    label: 'Prepare Node',
    steps: ['Validating Pre-processed Data…', 'Loading Data Visualizations…', 'Rendering Before / After Views…'],
  },
  vg1: {
    label: 'Validation Gate 1',
    steps: ['Running Validation Checklist…', 'Generating Quality Report…', 'Building Visualizations…'],
  },
  node5: {
    label: 'Feature Engineer Node',
    steps: ['Loading Engineered Features…', 'Computing Feature Importance…', 'Ready for Custom Formulas…'],
  },
  node7: {
    label: 'Train Node',
    steps: ['Connecting to Training API…', 'Loading Model Registry…', 'Preparing Hyperparameter Grid…'],
  },
  vg2: {
    label: 'Validation Gate 2',
    steps: ['Running Post-Train Validation…', 'Scoring Model Metrics…', 'Finalising Evaluation Report…'],
  },
  node9: {
    label: 'Deploy Node',
    steps: ['Connecting to Deploy API…', 'Verifying Deployment Target…', 'Loading Deployment Matrix…'],
  },
  pipeline_studio: {
    label: 'Monitor Node',
    steps: ['Starting Health Monitors…', 'Fetching Node Heartbeats…', 'Loading Drift Metrics…'],
  },
  master_data: {
    label: 'Master Data',
    steps: ['Loading Recipe Library…', 'Indexing DAG Catalogue…', 'Connecting to Recipe Orchestrator…'],
  },
  templates: {
    label: 'Templates',
    steps: ['Loading Template Library…', 'Scanning Template Schemas…', 'Ready'],
  },
  administration: {
    label: 'Administration',
    steps: ['Loading Environment Variables…', 'Fetching Cluster Config…', 'Ready'],
  },
  developer_studio: {
    label: 'Developer Studio',
    steps: ['Opening Stdout Stream…', 'Connecting to Log Aggregator…', 'Ready'],
  },
  settings: {
    label: 'Settings',
    steps: ['Loading Platform Settings…', 'Ready'],
  },
  support: {
    label: 'Support & Specs',
    steps: ['Loading Documentation…', 'Ready'],
  },
  default: {
    label: 'Page',
    steps: ['Loading…', 'Preparing View…', 'Ready'],
  },
};

export const PageTransition: React.FC<PageTransitionProps> = ({ to, onComplete }) => {
  const config = TRANSITION_STEPS[to] ?? TRANSITION_STEPS.default;
  const [stepIndex, setStepIndex] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const total = config.steps.length;
    let current = 0;

    const interval = setInterval(() => {
      current++;
      setStepIndex(Math.min(current, total - 1));
      setProgress(Math.round((current / total) * 100));

      if (current >= total) {
        clearInterval(interval);
        setTimeout(onComplete, 300);
      }
    }, 350);

    return () => clearInterval(interval);
  }, [config.steps.length, onComplete]);

  return (
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center"
      style={{ background: 'var(--bg-page)' }}
    >
      {/* Animated background blobs */}
      <div
        className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full blur-3xl opacity-20 pointer-events-none"
        style={{ background: 'radial-gradient(circle, #C8102E 0%, transparent 70%)' }}
      />
      <div
        className="absolute bottom-1/4 right-1/4 w-80 h-80 rounded-full blur-3xl opacity-15 pointer-events-none"
        style={{ background: 'radial-gradient(circle, #1E47C8 0%, transparent 70%)' }}
      />

      <div className="relative z-10 flex flex-col items-center gap-8 w-full max-w-md px-8">
        {/* Spinning ring logo */}
        <div className="relative w-20 h-20">
          <svg className="absolute inset-0 animate-spin" viewBox="0 0 80 80" fill="none">
            <circle cx="40" cy="40" r="36" stroke="rgba(200,16,46,0.15)" strokeWidth="4" />
            <path
              d="M40 4 A36 36 0 0 1 76 40"
              stroke="#C8102E"
              strokeWidth="4"
              strokeLinecap="round"
            />
          </svg>
          <div
            className="absolute inset-3 rounded-full flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg,rgba(200,16,46,0.18) 0%,rgba(30,71,200,0.18) 100%)' }}
          >
            <span className="material-symbols-outlined text-2xl" style={{ color: '#C8102E' }}>
              hub
            </span>
          </div>
        </div>

        {/* Destination label */}
        <div className="text-center">
          <p className="text-xs font-mono uppercase tracking-widest mb-1" style={{ color: 'rgba(200,16,46,0.7)' }}>
            Navigating to
          </p>
          <h2 className="text-xl font-bold font-headline" style={{ color: 'var(--text-primary)' }}>
            {config.label}
          </h2>
        </div>

        {/* Steps list */}
        <div className="w-full space-y-2">
          {config.steps.map((step, i) => {
            const done = i < stepIndex;
            const active = i === stepIndex;
            return (
              <div
                key={i}
                className="flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all duration-300"
                style={{
                  background: active
                    ? 'rgba(200,16,46,0.10)'
                    : done
                    ? 'rgba(74,222,128,0.06)'
                    : 'rgba(255,255,255,0.03)',
                  border: active
                    ? '1px solid rgba(200,16,46,0.30)'
                    : done
                    ? '1px solid rgba(74,222,128,0.20)'
                    : '1px solid rgba(255,255,255,0.06)',
                  opacity: i > stepIndex ? 0.35 : 1,
                }}
              >
                <span
                  className="material-symbols-outlined text-base flex-shrink-0"
                  style={{
                    color: done ? '#4ade80' : active ? '#C8102E' : 'rgba(255,255,255,0.25)',
                  }}
                >
                  {done ? 'check_circle' : active ? 'radio_button_checked' : 'radio_button_unchecked'}
                </span>
                <span
                  className="text-sm font-mono"
                  style={{ color: active ? 'var(--text-primary)' : done ? '#4ade80' : 'var(--text-muted)' }}
                >
                  {step}
                </span>
                {active && (
                  <span className="ml-auto flex gap-0.5">
                    {[0, 1, 2].map((d) => (
                      <span
                        key={d}
                        className="w-1 h-1 rounded-full animate-bounce"
                        style={{
                          background: '#C8102E',
                          animationDelay: `${d * 150}ms`,
                        }}
                      />
                    ))}
                  </span>
                )}
              </div>
            );
          })}
        </div>

        {/* Progress bar */}
        <div className="w-full h-1 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.08)' }}>
          <div
            className="h-full rounded-full transition-all duration-500 ease-out"
            style={{
              width: `${progress}%`,
              background: 'linear-gradient(90deg,#C8102E 0%,#E8405A 100%)',
            }}
          />
        </div>

        <p className="text-xs font-mono" style={{ color: 'var(--text-muted)' }}>
          {progress}% complete
        </p>
      </div>
    </div>
  );
};
