import React, { useState } from 'react';

interface DagInspectorViewProps {
  onSelectDagForPipeline?: (dagId: string) => void;
}

export const DagInspectorView: React.FC<DagInspectorViewProps> = ({ onSelectDagForPipeline }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFamily, setSelectedFamily] = useState('ALL');
  const [selectedTopology, setSelectedTopology] = useState('ALL');
  const [inspectingDag, setInspectingDag] = useState<string | null>('DAG_906');

  // Sample Master DAG items representing the 1,993 Master DAG registry
  const masterDags = [
    {
      id: 'DAG_906',
      name: 'Time-Series RUL Multi-Sensor Degradation Model',
      family: 'Time-Series Regression',
      topology: 'time_series',
      complexity: 'High',
      inputs: 21,
      matchConfidence: 98.4,
      rules: [
        'data_type == time_series',
        'sampling_rate_hz >= 1.0',
        'target_type == continuous_rul',
        'missing_value_ratio <= 0.05',
      ],
      stages: ['Prep (FFill/Scaling)', 'Lag Generator (t-1..t-10)', 'Zero-Leakage Split (70/15/15)', 'LightGBM / PyTorch LSTM HPO'],
      description: 'Optimized for turbofan & turbine engine degradation with sliding lag features and zero random shuffle leakage protection.',
    },
    {
      id: 'DAG_102',
      name: 'High-Frequency Vibration Fault Classifier',
      family: 'Fault Classification',
      topology: 'multi_sensor',
      complexity: 'Very High',
      inputs: 14,
      matchConfidence: 94.1,
      rules: [
        'data_type == multi_sensor_vibration',
        'spectral_fft_required == true',
        'class_count >= 3',
      ],
      stages: ['FFT Spectral Filtering', 'Wavelet Transform', 'Random Forest Classifier', 'VG_1 Accuracy Gate'],
      description: 'Used in SCADA gearbox bearing telemetry to detect outer/inner race defects across multi-channel accelerometers.',
    },
    {
      id: 'DAG_405',
      name: 'IGBT Power Semiconductor Aging Anomaly Detector',
      family: 'Anomaly Detection',
      topology: 'time_series',
      complexity: 'Medium',
      inputs: 8,
      matchConfidence: 91.2,
      rules: [
        'thermal_resistance_delta >= 0.02',
        'target_type == anomaly_score',
        'group_by == unit_id',
      ],
      stages: ['Outlier Isolation Forest', 'Rolling Mean (w=10)', 'Chronological Split', 'XGBoost One-Class'],
      description: 'Semiconductor junction temperature profiling for power inverter thermal stress analysis.',
    },
    {
      id: 'DAG_812',
      name: 'Tabular SCADA Multi-Fleet Feature Engine',
      family: 'Tabular Regression',
      topology: 'tabular',
      complexity: 'Medium',
      inputs: 32,
      matchConfidence: 89.6,
      rules: [
        'data_type == tabular',
        'entity_join_keys >= 1',
        'pca_components == 12',
      ],
      stages: ['K-Best Feature Selector', 'RobustScaler', 'CatBoost Regressor', 'VG_2 Latency Gate'],
      description: 'Fast tabular pipeline designed for multi-site SCADA telemetry dumps.',
    },
  ];

  const filteredDags = masterDags.filter((dag) => {
    const matchesSearch =
      dag.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      dag.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      dag.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFamily = selectedFamily === 'ALL' || dag.family === selectedFamily;
    const matchesTopology = selectedTopology === 'ALL' || dag.topology === selectedTopology;
    return matchesSearch && matchesFamily && matchesTopology;
  });

  const activeDagDetail = masterDags.find((d) => d.id === inspectingDag) || masterDags[0];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
        <div>
          <nav className="flex items-center gap-2 text-slate-400 text-xs font-mono uppercase tracking-widest mb-1">
            <span>Core Registry</span>
            <span className="material-symbols-outlined text-xs">chevron_right</span>
            <span className="text-tas-blue font-bold">Profiler & Master DAG Inspector</span>
          </nav>
          <h1 className="font-headline text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-3">
            <span>1,993 Master DAGs Catalog</span>
            <span className="px-3 py-1 bg-tas-blue-light text-tas-blue border border-tas-blue/30 rounded-full text-xs font-mono font-bold">
              1.1 MB Rule Matrix
            </span>
          </h1>
          <p className="text-slate-500 text-xs mt-1">
            Inspect condition evaluation rules, family matchers, and recipe DAG topologies derived from <code className="font-mono text-slate-700">algorithm_families_complete-2.xlsx</code>.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl font-mono text-xs text-right">
            <span className="text-slate-400 uppercase text-[10px] block">TOTAL DAGS MATCHED</span>
            <span className="text-xl font-bold text-tas-blue">1,993 Master Rules</span>
          </div>
        </div>
      </div>

      {/* Filter & Search Toolbar */}
      <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-xs flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-96">
          <span className="material-symbols-outlined absolute left-3 top-2.5 text-slate-400 text-base">search</span>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search 1,993 Master DAGs (e.g. DAG_906, vibration)..."
            className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-9 pr-3 py-2 text-xs font-mono text-slate-900 outline-none focus:ring-2 focus:ring-tas-blue"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          <select
            value={selectedFamily}
            onChange={(e) => setSelectedFamily(e.target.value)}
            className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-mono text-slate-800 outline-none focus:ring-2 focus:ring-tas-blue"
          >
            <option value="ALL">ALL FAMILIES</option>
            <option value="Time-Series Regression">Time-Series Regression</option>
            <option value="Fault Classification">Fault Classification</option>
            <option value="Anomaly Detection">Anomaly Detection</option>
            <option value="Tabular Regression">Tabular Regression</option>
          </select>

          <select
            value={selectedTopology}
            onChange={(e) => setSelectedTopology(e.target.value)}
            className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-mono text-slate-800 outline-none focus:ring-2 focus:ring-tas-blue"
          >
            <option value="ALL">ALL TOPOLOGIES</option>
            <option value="time_series">[time_series]</option>
            <option value="multi_sensor">[multi_sensor]</option>
            <option value="tabular">[tabular]</option>
          </select>
        </div>
      </div>

      {/* Main Grid: DAG List & Condition Rule Inspector Drawer */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Master DAG List */}
        <div className="lg:col-span-2 space-y-3">
          {filteredDags.map((dag) => {
            const isSelected = inspectingDag === dag.id;
            return (
              <div
                key={dag.id}
                onClick={() => setInspectingDag(dag.id)}
                className={`p-5 rounded-2xl border transition-all cursor-pointer ${
                  isSelected
                    ? 'border-tas-blue bg-tas-blue-light/40 shadow-sm ring-1 ring-tas-blue/30'
                    : 'border-slate-200 bg-white hover:border-slate-300'
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-1 bg-slate-900 text-white font-mono text-xs font-bold rounded-lg">
                      {dag.id}
                    </span>
                    <span className="px-2 py-0.5 bg-tas-blue-light text-tas-blue border border-tas-blue/30 font-mono text-[10px] font-bold rounded">
                      [{dag.topology}]
                    </span>
                    <span className="px-2 py-0.5 bg-slate-100 text-slate-700 font-mono text-[10px] rounded">
                      {dag.family}
                    </span>
                  </div>

                  <span className="font-mono text-xs font-bold text-[#FF6B35] bg-[#FF6B35]/08 border border-[#FF6B35]/20 px-2.5 py-1 rounded-full">
                    Match: {dag.matchConfidence}%
                  </span>
                </div>

                <h3 className="font-headline font-bold text-base text-slate-900 mb-1">{dag.name}</h3>
                <p className="text-xs text-slate-600 line-clamp-2">{dag.description}</p>

                <div className="mt-3 pt-3 border-t border-slate-200/80 flex items-center justify-between text-[11px] font-mono text-slate-500">
                  <span>Input Sensors: <strong>{dag.inputs} Channels</strong></span>
                  <span>Complexity: <strong>{dag.complexity}</strong></span>
                  <span className="text-tas-blue font-bold flex items-center gap-1">
                    Inspect Condition Rules &rarr;
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Selected DAG Rule Inspector Detail */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-5 h-fit sticky top-24">
          <div className="flex justify-between items-start pb-3 border-b border-slate-200">
            <div>
              <span className="text-[10px] font-mono font-bold uppercase text-tas-blue">Condition Evaluator Rule Inspector</span>
              <h3 className="font-headline font-bold text-xl text-slate-900 mt-0.5">{activeDagDetail.id}</h3>
            </div>
            <span className="px-3 py-1 bg-[#FF6B35]/12 text-[#FF6B35] text-xs font-mono font-bold rounded-full">
              Matched DAG_906
            </span>
          </div>

          <div>
            <h4 className="font-bold text-xs text-slate-900 mb-1">{activeDagDetail.name}</h4>
            <p className="text-xs text-slate-600 leading-relaxed">{activeDagDetail.description}</p>
          </div>

          {/* Condition Rules List */}
          <div>
            <span className="text-[11px] font-mono font-bold uppercase text-slate-400 block mb-2">
              1.1 MB Rule Evaluation Logic
            </span>
            <div className="p-3 bg-slate-900 text-[#FF6B35] rounded-xl font-mono text-xs space-y-1.5 shadow-inner">
              {activeDagDetail.rules.map((rule, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <span className="text-slate-500">IF</span>
                  <span className="text-white font-bold">{rule}</span>
                  <span className="material-symbols-outlined text-xs text-[#FF6B35] ml-auto">check</span>
                </div>
              ))}
            </div>
          </div>

          {/* Pipeline Stage Sequence */}
          <div>
            <span className="text-[11px] font-mono font-bold uppercase text-slate-400 block mb-2">
              Recipe Orchestrator Stages
            </span>
            <div className="space-y-2">
              {activeDagDetail.stages.map((stage, idx) => (
                <div key={idx} className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono text-slate-800 flex items-center gap-2">
                  <span className="w-5 h-5 rounded-full bg-tas-blue text-white text-[10px] font-bold flex items-center justify-center">
                    {idx + 1}
                  </span>
                  <span>{stage}</span>
                </div>
              ))}
            </div>
          </div>

          <button
            onClick={() => onSelectDagForPipeline && onSelectDagForPipeline(activeDagDetail.id)}
            className="w-full py-3 bg-tas-blue hover:bg-tas-blue-hover text-white font-mono text-xs font-bold rounded-xl shadow-md transition-all active:scale-95 flex items-center justify-center gap-2"
          >
            <span>Dispatch Recipe with {activeDagDetail.id}</span>
            <span className="material-symbols-outlined text-base">play_circle</span>
          </button>
        </div>
      </div>
    </div>
  );
};
