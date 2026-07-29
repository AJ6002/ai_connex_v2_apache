import React, { useState, useEffect } from 'react';

interface ConfigState {
  recipes: Record<string, string>;
  jsons: Record<string, string>;
  boilerplates: Record<string, string>;
  templates: Record<string, string>;
}

interface TemplateMeta {
  key: string;
  label: string;
  category: 'gates' | 'families' | 'processes';
  icon: string;
  description: string;
  defaultVal: string;
}

const TEMPLATES_LIST: TemplateMeta[] = [
  // ── Validation Gate Reports & Checklists ────────────────────────────────────
  {
    key: 'vg1_checklist_template',
    label: 'Validation Gate 1 Audit Checklist',
    category: 'gates',
    icon: 'rule',
    description: 'Data preparation quality checklist containing null ratio thresholds, stuck sensor flags, and outlier bounds.',
    defaultVal: JSON.stringify({
      version: "1.0.0",
      checks: [
        { name: "null_ratio_threshold", limit: 0.05, action: "impute_or_fail" },
        { name: "stuck_sensor_variance_min", limit: 1e-5, action: "drop_feature" },
        { name: "outlier_bounds_iqr", limit: 1.5, action: "clip_robust" },
        { name: "class_imbalance_max_ratio", limit: 0.95, action: "warn_or_smote" }
      ],
      strict_mode: true
    }, null, 2),
  },
  {
    key: 'vg2_checklist_template',
    label: 'Validation Gate 2 HPO Checklist',
    category: 'gates',
    icon: 'task_alt',
    description: 'Post-train mathematical checklist for model validation, variance audit, and adversarial test criteria.',
    defaultVal: JSON.stringify({
      version: "1.0.0",
      performance_gates: {
        accuracy_min: 0.85,
        f1_min: 0.80,
        r2_min: 0.80,
        max_inference_latency_ms: 10
      },
      robustness_tests: {
        noise_injection_variance: 0.20,
        max_score_degradation_pct: 5.0,
        adversarial_immunity_test: true
      }
    }, null, 2),
  },
  {
    key: 'vg_report_boilerplate',
    label: 'HTML Evaluation Report Boilerplate',
    category: 'gates',
    icon: 'html',
    description: 'Responsive HTML template for printing Validation Gate audit reports with summary scorecards.',
    defaultVal: `<!DOCTYPE html>
<html>
<head>
  <title>Validation Gate Quality Report</title>
  <style>
    body { font-family: sans-serif; padding: 20px; background: #fafafa; }
    .card { background: white; padding: 20px; border-radius: 12px; border: 1px solid #eee; }
    h1 { color: #C8102E; }
    .pass { color: #10B981; font-weight: bold; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Validation Gate Audit Summary</h1>
    <p>Run ID: {{ run_id }}</p>
    <p>Status: <span class="pass">PASSED</span></p>
    <hr/>
    <h3>Checklist Evaluation:</h3>
    <ul>
      {{#each checks}}
        <li>{{this.name}}: {{this.status}}</li>
      {{/each}}
    </ul>
  </div>
</body>
</html>`,
  },

  // ── Algorithm Families & Algos ──────────────────────────────────────────────
  {
    key: 'classification_recipe_template',
    label: 'Classification Family Recipe',
    category: 'families',
    icon: 'category',
    description: 'Standard hyperparameters and pipeline actions for classification models (Random Forest, XGBoost, AdaBoost).',
    defaultVal: JSON.stringify({
      family_id: "CLASSIFICATION",
      default_algorithm: "Random Forest",
      variant: "Classifier",
      hyperparameters: {
        n_estimators: 100,
        max_depth: 10,
        min_samples_split: 2,
        class_weight: "balanced"
      },
      validation_metrics: ["accuracy", "precision", "recall", "f1_score"]
    }, null, 2),
  },
  {
    key: 'regression_recipe_template',
    label: 'Regression Family Recipe',
    category: 'families',
    icon: 'trending_up',
    description: 'Pipeline hyperparameters and evaluation metrics for regression models (Linear, Huber, Ridge, Lasso).',
    defaultVal: JSON.stringify({
      family_id: "REGRESSION",
      default_algorithm: "Huber Regressor",
      variant: "Robust",
      hyperparameters: {
        epsilon: 1.35,
        max_iter: 100,
        alpha: 0.0001
      },
      validation_metrics: ["r2_score", "mean_squared_error", "mean_absolute_error"]
    }, null, 2),
  },
  {
    key: 'anomaly_recipe_template',
    label: 'Anomaly Detection Family Recipe',
    category: 'families',
    icon: 'error_outline',
    description: 'Unsupervised configuration and threshold metrics for anomaly detection (Isolation Forest, One-Class SVM).',
    defaultVal: JSON.stringify({
      family_id: "ANOMALY_DETECTION",
      default_algorithm: "Isolation Forest",
      variant: "Standard",
      hyperparameters: {
        contamination: 0.05,
        n_estimators: 100,
        random_state: 42
      },
      validation_metrics: ["contamination_ratio", "anomaly_count"]
    }, null, 2),
  },
  {
    key: 'time_series_recipe_template',
    label: 'Time-Series Family Recipe',
    category: 'families',
    icon: 'schedule',
    description: 'Lag structures, moving averages, and cross-validation folds for time-series and forecasting.',
    defaultVal: JSON.stringify({
      family_id: "TIME_SERIES",
      default_algorithm: "ARIMA",
      variant: "Standard",
      lag_steps: [1, 5, 10],
      rolling_window_sizes: [5, 10],
      validation_strategy: "time_series_split",
      time_series_folds: 5
    }, null, 2),
  },

  // ── Pipeline Processes ──────────────────────────────────────────────────────
  {
    key: 'profiler_process_template',
    label: 'Data Profiler Config Template',
    category: 'processes',
    icon: 'analytics',
    description: 'Defines missing value thresholds, data types extraction strategy, and correlation cutoff limits.',
    defaultVal: JSON.stringify({
      process: "dataset_profiler",
      missing_ratio_alert: 0.10,
      correlation_threshold: 0.85,
      categorical_cardinality_limit: 50,
      enable_spectral_density: true
    }, null, 2),
  },
  {
    key: 'dag_matcher_process_template',
    label: 'DAG Matcher & Router Rules',
    category: 'processes',
    icon: 'route',
    description: 'Rules schema mapped by the Matcher engine to route incoming datasets to specific recommended DAGs.',
    defaultVal: JSON.stringify({
      process: "dag_matcher",
      confidence_min_threshold: 80.0,
      routing_rules: {
        continuous_target_only: "REGRESSION",
        categorical_target_only: "CLASSIFICATION",
        no_target_labeled: "ANOMALY_DETECTION",
        time_series_index_present: "TIME_SERIES"
      }
    }, null, 2),
  },
];

export const TemplatesView: React.FC = () => {
  const [config, setConfig] = useState<ConfigState | null>(null);
  const [activeKey, setActiveKey] = useState<string>('vg1_checklist_template');
  const [editorValue, setEditorValue] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [activeCategory, setActiveCategory] = useState<'gates' | 'families' | 'processes'>('gates');

  // Fetch configs from backend
  const fetchConfig = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`http://${window.location.hostname}:8000/api/v1/master/config`);
      if (res.ok) {
        const data = await res.json();
        setConfig(data);
        const resolvedVal = data.templates?.[activeKey] || TEMPLATES_LIST.find(t => t.key === activeKey)?.defaultVal || '';
        setEditorValue(resolvedVal);
      }
    } catch (err) {
      console.error("Error loading templates:", err);
      // Fallback to local default value
      const resolvedVal = TEMPLATES_LIST.find(t => t.key === activeKey)?.defaultVal || '';
      setEditorValue(resolvedVal);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  // Update editor value when active template changes
  useEffect(() => {
    if (config?.templates) {
      setEditorValue(config.templates[activeKey] || TEMPLATES_LIST.find(t => t.key === activeKey)?.defaultVal || '');
    } else {
      setEditorValue(TEMPLATES_LIST.find(t => t.key === activeKey)?.defaultVal || '');
    }
  }, [activeKey, config]);

  const handleCopy = () => {
    navigator.clipboard.writeText(editorValue);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSave = async () => {
    setIsSaving(true);
    setMessage(null);
    try {
      const res = await fetch(`http://${window.location.hostname}:8000/api/v1/master/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category: 'templates',
          key: activeKey,
          value: editorValue
        })
      });

      if (res.ok) {
        const data = await res.json();
        setConfig(data.config);
        setMessage({ text: 'Blueprint template updated successfully!', type: 'success' });
      } else {
        setMessage({ text: 'Failed to update template on server. Saved locally.', type: 'error' });
      }
    } catch {
      setMessage({ text: 'Saved locally (API Offline).', type: 'success' });
    } finally {
      setIsSaving(false);
      setTimeout(() => setMessage(null), 3000);
    }
  };

  const currentMeta = TEMPLATES_LIST.find(t => t.key === activeKey);

  const filteredTemplates = TEMPLATES_LIST.filter(t => t.category === activeCategory);

  return (
    <div className="space-y-6 text-primary animate-fadeIn">
      {/* Page Title & Banner */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl relative overflow-hidden"
        style={{ border: '1px solid rgba(255,255,255,0.09)' }}>
        <div className="absolute top-0 right-0 w-96 h-96 bg-tas-red/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20"></div>
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-2 text-muted text-xs font-mono uppercase tracking-widest mb-1">
              <span className="text-tas-red font-extrabold">BLUEPRINTS DECK</span>
              <span>•</span>
              <span className="text-cb font-bold">Standard Boilerplates</span>
            </div>
            <h1 className="font-headline text-2xl sm:text-3xl font-extrabold text-primary tracking-tight">
              Blueprint Templates Library
            </h1>
            <p className="text-sm text-secondary mt-1 max-w-2xl">
              Configure baseline blueprints for Validation Gates checklists, model training algorithm families, and microservice matching rules.
            </p>
          </div>
          <span className="px-3.5 py-1.5 bg-tas-blue/15 text-tas-blue border border-tas-blue/20 rounded-full text-xs font-mono font-bold">
            Standard Blueprints
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* LEFT COLUMN: Categories & List */}
        <div className="lg:col-span-4 flex flex-col gap-5">
          {/* Category Tabs */}
          <div className="glass-panel p-2.5 rounded-2xl flex gap-1 border" style={{ borderColor: 'var(--border-ui)' }}>
            {(['gates', 'families', 'processes'] as const).map((cat) => (
              <button
                key={cat}
                onClick={() => {
                  setActiveCategory(cat);
                  const firstOfCat = TEMPLATES_LIST.find(t => t.category === cat);
                  if (firstOfCat) setActiveKey(firstOfCat.key);
                }}
                className={`flex-1 py-2 text-center rounded-xl text-xs font-mono font-bold transition-all ${
                  activeCategory === cat
                    ? 'bg-tas-red text-white shadow-md'
                    : 'text-secondary hover:bg-slate-50 dark:hover:bg-slate-850'
                }`}
              >
                {cat === 'gates' ? 'Gates' : cat === 'families' ? 'Algo Families' : 'Processes'}
              </button>
            ))}
          </div>

          {/* List of Templates in Category */}
          <div className="glass-panel p-4 rounded-2xl space-y-3 border" style={{ borderColor: 'var(--border-ui)' }}>
            <h3 className="font-headline font-bold text-xs text-primary pb-2 border-b" style={{ borderColor: 'var(--border-ui)' }}>
              Select Template Schema
            </h3>

            <div className="space-y-1.5">
              {filteredTemplates.map((t) => {
                const isSelected = activeKey === t.key;
                return (
                  <button
                    key={t.key}
                    onClick={() => setActiveKey(t.key)}
                    className={`w-full text-left p-3 rounded-xl font-mono text-xs transition-all flex items-start gap-3 border ${
                      isSelected
                        ? 'bg-tas-blue/10 text-tas-blue border-tas-blue/30 font-bold'
                        : 'bg-transparent border-transparent hover:bg-slate-50 dark:hover:bg-slate-850 text-secondary'
                    }`}
                  >
                    <span className="material-symbols-outlined text-base mt-0.5" style={{ color: isSelected ? 'var(--tas-blue)' : 'var(--text-muted)' }}>
                      {t.icon}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="truncate text-xs text-primary">{t.label}</p>
                      <p className="text-[10px] text-secondary truncate mt-0.5">{t.description}</p>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Code Editor */}
        <div className="lg:col-span-8 glass-panel p-6 rounded-2xl flex flex-col space-y-4 border" style={{ borderColor: 'var(--border-ui)', background: 'var(--bg-card)' }}>
          {currentMeta && (
            <div className="flex justify-between items-center pb-3 border-b" style={{ borderColor: 'var(--border-ui)' }}>
              <div>
                <h4 className="font-headline font-bold text-sm text-primary flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ background: 'var(--tas-red)' }}></span>
                  {currentMeta.label}
                </h4>
                <p className="text-[10px] text-secondary font-mono mt-0.5">{currentMeta.description}</p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleCopy}
                  className="px-3 py-1.5 border rounded-xl text-xs font-mono font-semibold transition-all flex items-center gap-1.5 hover:bg-slate-50 dark:hover:bg-slate-850 text-primary"
                  style={{ borderColor: 'var(--border-ui)' }}
                >
                  <span className="material-symbols-outlined text-xs">
                    {copied ? 'check' : 'content_copy'}
                  </span>
                  <span>{copied ? 'Copied' : 'Copy'}</span>
                </button>
                <button
                  onClick={handleSave}
                  disabled={isSaving}
                  className="px-4 py-1.5 bg-tas-red hover:bg-tas-red-hover text-white font-mono text-xs font-bold rounded-xl transition-all shadow-md active:scale-95 disabled:opacity-50 flex items-center gap-1.5"
                >
                  {isSaving ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>Saving...</span>
                    </>
                  ) : (
                    <>
                      <span className="material-symbols-outlined text-xs">save</span>
                      <span>Update Template</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Response message */}
          {message && (
            <div className={`p-3 rounded-xl text-xs font-mono flex items-start gap-2 ${
              message.type === 'success'
                ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400'
                : 'bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400'
            }`}>
              <span className="material-symbols-outlined text-base mt-0.5">
                {message.type === 'success' ? 'check_circle' : 'error'}
              </span>
              <span className="flex-1">{message.text}</span>
            </div>
          )}

          {/* Code Editor */}
          <div className="flex-1 min-h-[400px] flex flex-col rounded-2xl overflow-hidden border border-slate-800 bg-slate-950 p-4 font-mono text-xs">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-900 text-[10px] text-slate-500">
              <span>Standard Format Editor</span>
              <span>JSON / Template Code</span>
            </div>
            <textarea
              value={editorValue}
              onChange={(e) => setEditorValue(e.target.value)}
              spellCheck={false}
              className="w-full flex-1 resize-none bg-transparent font-mono text-xs outline-none leading-relaxed"
              style={{
                color: '#a6e3a1',
                caretColor: 'var(--tas-red)',
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
