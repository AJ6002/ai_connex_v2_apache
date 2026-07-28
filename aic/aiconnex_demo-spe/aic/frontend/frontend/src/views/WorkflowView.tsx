import React, { useState } from 'react';
import { ViewMode } from '../types';
import { DAG_FAMILY_NODES, RECIPE_STEPS_NODES } from '../data/initialData';

interface WorkflowViewProps {
  onRunDagPipeline: (familyLabel: string) => void;
  isJobRunning: boolean;
  activeNodeId?: string;
  onSelectView: (view: ViewMode) => void;
}

export const WorkflowView: React.FC<WorkflowViewProps> = ({
  onRunDagPipeline,
  isJobRunning,
  onSelectView,
}) => {
  const [selectedFamily, setSelectedFamily] = useState<string>('CLASSIFICATION FAMILY');
  const [selectedRecipeFilter, setSelectedRecipeFilter] = useState<string>('ALL');
  const [activeTab, setActiveTab] = useState<'diagram' | 'recipe_specs' | 'pipeline_logs'>('diagram');

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* View Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <nav className="flex items-center gap-2 text-slate-400 text-xs font-mono uppercase tracking-widest mb-1">
            <span>Workflow</span>
            <span className="material-symbols-outlined text-xs">chevron_right</span>
            <span className="text-tas-blue font-bold">DAG Recipe Orchestrator</span>
          </nav>
          <h1 className="font-headline text-2xl font-bold text-slate-900 tracking-tight">
            Total Automation Solution DAG Pipeline
          </h1>
          <p className="text-slate-600 text-xs mt-1 leading-relaxed">
            Visual recipe orchestrator mapping data profiler, model family classifiers, preprocessing pipelines, and VG_1/VG_2 validation gateways.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setActiveTab('diagram')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold font-mono transition-colors ${
              activeTab === 'diagram' ? 'bg-tas-blue text-white shadow-xs' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            Diagram Map
          </button>
          <button
            onClick={() => setActiveTab('recipe_specs')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold font-mono transition-colors ${
              activeTab === 'recipe_specs' ? 'bg-tas-blue text-white shadow-xs' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            Recipe Specs
          </button>
          <button
            onClick={() => onRunDagPipeline(selectedFamily)}
            disabled={isJobRunning}
            className="px-5 py-2 bg-tas-blue hover:bg-tas-blue-hover text-white font-bold text-xs rounded-lg shadow-sm transition-all flex items-center gap-2 active:scale-95 disabled:opacity-50"
          >
            <span className="material-symbols-outlined text-base">play_circle</span>
            <span>{isJobRunning ? 'Orchestrating...' : 'Execute Recipe DAG'}</span>
          </button>
        </div>
      </div>

      {/* Main Workflow Workspace */}
      {activeTab === 'diagram' && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm overflow-x-auto min-w-[1200px] relative">
          {/* Top Status Bar */}
          <div className="flex justify-between items-center mb-6 bg-slate-50 p-3.5 rounded-lg border border-slate-200 text-xs font-mono">
            <div className="flex items-center gap-3">
              <span className="text-slate-500 font-bold">ACTIVE FAMILY:</span>
              <span className="px-2.5 py-1 bg-tas-blue text-white font-bold rounded-md shadow-2xs">
                {selectedFamily}
              </span>
            </div>
            <div className="flex items-center gap-5 text-slate-600">
              <span>CLUSTER: US-EAST-1 GPU</span>
              <span>GATEWAYS: VG_1 (ACC &gt;= 90%) | VG_2 (LAT &lt;= 50ms)</span>
              <span className="flex items-center gap-1.5 text-emerald-600 font-bold">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
                READY
              </span>
            </div>
          </div>

          {/* Visual DAG Architecture Flow Chart */}
          <div className="grid grid-cols-12 gap-4 items-center py-8 relative">
            {/* Column 1: Data Profiler */}
            <div className="col-span-2 flex flex-col items-center justify-center space-y-4">
              <div onClick={() => onSelectView('node1')} className="p-4 bg-white border-2 border-tas-blue rounded-full shadow-md text-center hover:scale-105 transition-transform cursor-pointer w-36 h-36 flex flex-col items-center justify-center">
                <span className="material-symbols-outlined text-tas-blue text-2xl mb-1">analytics</span>
                <span className="font-mono text-xs font-bold text-tas-blue leading-tight">
                  DATA PROFILER
                </span>
                <span className="text-[9px] text-slate-500 mt-1">2.4M Meta Rows</span>
              </div>
              <div className="text-[10px] font-mono text-slate-600 bg-slate-50 px-2.5 py-1 rounded-md border border-slate-200">
                Profile Meta Report
              </div>
            </div>

            {/* Connecting Arrow 1 */}
            <div className="col-span-1 flex items-center justify-center">
              <svg className="w-full h-8 text-tas-blue" viewBox="0 0 100 20">
                <line x1="0" y1="10" x2="90" y2="10" stroke="currentColor" strokeWidth="2" className="animate-flow" />
                <polygon points="90,5 100,10 90,15" fill="currentColor" />
              </svg>
            </div>

            {/* Column 2: DAG Family Classifier Stack */}
            <div className="col-span-3 bg-slate-50/70 p-4 border border-slate-200 rounded-xl shadow-xs space-y-2 max-h-[500px] overflow-y-auto">
              <div className="text-[10px] font-mono font-bold uppercase text-slate-400 border-b border-slate-200 pb-1.5 mb-2">
                Select Model Family (DAG_ID_1..10)
              </div>
              {DAG_FAMILY_NODES.map((family) => {
                const isSelected = selectedFamily === family.label;
                return (
                  <button
                    key={family.id}
                    onClick={() => setSelectedFamily(family.label)}
                    className={`w-full text-left px-3 py-2.5 rounded-lg text-[11px] font-mono font-semibold transition-all border flex items-center justify-between ${
                      isSelected
                        ? 'bg-tas-blue text-white border-tas-blue shadow-xs'
                        : 'bg-white text-slate-700 border-slate-200 hover:border-tas-blue'
                    }`}
                  >
                    <span>{family.label}</span>
                    {isSelected && (
                      <span className="material-symbols-outlined text-xs text-white">check_circle</span>
                    )}
                  </button>
                );
              })}
            </div>

            {/* Connecting Arrow 2 */}
            <div className="col-span-1 flex items-center justify-center">
              <svg className="w-full h-8 text-tas-blue" viewBox="0 0 100 20">
                <line x1="0" y1="10" x2="90" y2="10" stroke="currentColor" strokeWidth="2" className="animate-flow" />
                <polygon points="90,5 100,10 90,15" fill="currentColor" />
              </svg>
            </div>

            {/* Column 3: Central Recipe Orchestrator */}
            <div className="col-span-2 flex flex-col items-center justify-center space-y-3">
              <div onClick={() => onSelectView('node3')} className="p-5 bg-white border-4 border-tas-blue text-tas-blue rounded-full shadow-lg text-center w-40 h-40 flex flex-col items-center justify-center relative cursor-pointer hover:scale-105 transition-transform">
                <span className="material-symbols-outlined text-3xl mb-1 text-tas-red">hub</span>
                <span className="font-headline text-xs font-bold tracking-tight text-tas-blue">
                  RECIPE ORCHESTRATOR
                </span>
                <span className="text-[9px] font-mono text-tas-red font-bold mt-1">DAG_ID Dispatcher</span>
              </div>

              {/* Recipe Cards Sub-stack */}
              <div className="w-full space-y-1.5 text-[10px] font-mono">
                <div className="p-1.5 bg-tas-red-light text-tas-red rounded-md border border-tas-red/30 text-center font-bold shadow-2xs">
                  DAG_ID PREPARING_RECIPE
                </div>
                <div className="p-1.5 bg-tas-red-light text-tas-red rounded-md border border-tas-red/30 text-center font-bold shadow-2xs">
                  DAG_ID SPLITTING_RECIPE
                </div>
                <div className="p-1.5 bg-tas-red-light text-tas-red rounded-md border border-tas-red/30 text-center font-bold shadow-2xs">
                  DAG_ID TRAINING_RECIPE
                </div>
              </div>
            </div>

            {/* Connecting Arrow 3 */}
            <div className="col-span-1 flex items-center justify-center">
              <svg className="w-full h-8 text-tas-blue" viewBox="0 0 100 20">
                <line x1="0" y1="10" x2="90" y2="10" stroke="currentColor" strokeWidth="2" className="animate-flow" />
                <polygon points="90,5 100,10 90,15" fill="currentColor" />
              </svg>
            </div>

            {/* Column 4: Pipeline Execution Sequence */}
            <div className="col-span-2 space-y-2 bg-slate-50/70 p-4 border border-slate-200 rounded-xl shadow-xs">
              <div className="text-[10px] font-mono font-bold uppercase text-slate-400 border-b border-slate-200 pb-1.5 mb-2">
                Pipeline Execution Steps
              </div>

              <div onClick={() => onSelectView('node4')} className="p-2 bg-white border border-slate-200 hover:border-tas-blue rounded-md flex justify-between items-center text-xs font-mono cursor-pointer transition-colors">
                <span className="font-bold text-tas-blue">1. PREPARE</span>
                <span className="text-[10px] bg-slate-100 px-1.5 py-0.5 rounded text-slate-600">IMPUTE</span>
              </div>

              <div onClick={() => onSelectView('node5')} className="p-2 bg-white border border-slate-200 hover:border-tas-blue rounded-md flex justify-between items-center text-xs font-mono cursor-pointer transition-colors">
                <span className="font-bold text-tas-blue">2. ENGINEER</span>
                <span className="text-[10px] bg-slate-100 px-1.5 py-0.5 rounded text-slate-600">ENCODE</span>
              </div>

              <div onClick={() => onSelectView('node6')} className="p-2 bg-white border border-slate-200 hover:border-tas-blue rounded-md flex justify-between items-center text-xs font-mono cursor-pointer transition-colors">
                <span className="font-bold text-tas-blue">3. SPLIT</span>
                <span className="text-[10px] bg-slate-100 px-1.5 py-0.5 rounded text-slate-600">SCALE</span>
              </div>

              <div onClick={() => onSelectView('node7')} className="p-2 bg-white border border-slate-200 hover:border-tas-blue rounded-md flex justify-between items-center text-xs font-mono cursor-pointer transition-colors">
                <span className="font-bold text-tas-blue">4. TRAIN</span>
                <span className="text-[10px] bg-slate-100 px-1.5 py-0.5 rounded text-slate-600">TUNING</span>
              </div>

              <div onClick={() => onSelectView('node9')} className="p-2 bg-white border border-slate-200 hover:border-tas-blue rounded-md flex justify-between items-center text-xs font-mono cursor-pointer transition-colors">
                <span className="font-bold text-tas-blue">5. DEPLOY</span>
                <span className="text-[10px] bg-emerald-100 text-emerald-800 px-1.5 py-0.5 rounded font-bold">ROLLOUT</span>
              </div>

              <div onClick={() => onSelectView('node9')} className="p-2 bg-tas-blue hover:bg-tas-blue-hover text-white rounded-md flex justify-between items-center text-xs font-mono shadow-2xs cursor-pointer transition-colors">
                <span className="font-bold">6. MONITOR</span>
                <span className="text-[10px] bg-tas-red text-white px-1.5 py-0.5 rounded font-bold">VG_1 &amp; VG_2</span>
              </div>
            </div>
          </div>

          {/* Detailed Gateway Legend & Feedback Loop */}
          <div className="mt-6 pt-4 border-t border-slate-200 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono">
              <span className="font-bold text-tas-blue block mb-1">VG_1 Validation Gateway</span>
              <p className="text-slate-600 text-[11px] leading-relaxed">
                Validates prepared dataset accuracy &gt;= 90%. If INVALID, routes back to PREPARE recipe loop.
              </p>
            </div>

            <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono">
              <span className="font-bold text-tas-blue block mb-1">VG_2 Validation Gateway</span>
              <p className="text-slate-600 text-[11px] leading-relaxed">
                Validates trained model latency &lt;= 50ms &amp; memory safety. If INVALID, routes back to TRAIN tuning loop.
              </p>
            </div>

            <div className="p-3.5 bg-tas-blue text-white rounded-lg text-xs font-mono">
              <span className="font-bold text-tas-red-light block mb-1">Final Model Output</span>
              <p className="text-slate-100 text-[11px] leading-relaxed">
                Generates signed model artifact binary and streams monitoring telemetry logs directly to Main Dashboard.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Recipe Specifications Tab */}
      {activeTab === 'recipe_specs' && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h3 className="font-headline text-xl font-bold text-slate-900 mb-4 tracking-tight">
            Recipe Processing Steps Specs
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {RECIPE_STEPS_NODES.map((step) => (
              <div key={step.id} className="p-4 border border-slate-200 rounded-lg bg-slate-50/50 space-y-2">
                <div className="flex justify-between items-center">
                  <span className="font-mono text-sm font-bold text-tas-blue">{step.label}</span>
                  <span className="text-[10px] font-mono bg-slate-200 text-slate-700 px-2 py-0.5 rounded uppercase font-semibold">
                    {step.type}
                  </span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">{step.description}</p>
                <div className="pt-2 border-t border-slate-200 flex justify-between items-center text-[11px] font-mono text-slate-400">
                  <span>Status: Operational</span>
                  <button className="text-tas-blue font-bold hover:underline">Config &gt;</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
