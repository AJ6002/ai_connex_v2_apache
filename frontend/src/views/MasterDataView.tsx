import React, { useState, useEffect, useCallback } from 'react';

// ─── Types ───────────────────────────────────────────────────────────────────

type Category = 'preparing' | 'feature_engineering' | 'splitting' | 'training' | 'evaluating';

interface CategoryMeta {
  id: Category;
  label: string;
  icon: string;
  color: string;
  accent: string;
  description: string;
  serviceFolder: string;
  port: number;
  fields: string[];
}

const CATEGORIES: CategoryMeta[] = [
  {
    id: 'preparing',
    label: 'Data Preparation',
    icon: 'cleaning_services',
    color: 'rgba(200,16,46,0.12)',
    accent: '#C8102E',
    description: 'Imputation, outlier handling, scaling and encoding recipes · services/4_prepare/recipe/',
    serviceFolder: '4_prepare',
    port: 8003,
    fields: ['impute_strategy', 'outlier_method', 'scale_method', 'encode_strategy', 'text_clean', 'time_align'],
  },
  {
    id: 'feature_engineering',
    label: 'Feature Engineering',
    icon: 'science',
    color: 'rgba(30,71,200,0.12)',
    accent: '#1E47C8',
    description: 'Polynomial degrees, lag steps, PCA and custom formula recipes · services/5_feature_engineering/recipe/',
    serviceFolder: '5_feature_engineering',
    port: 8004,
    fields: ['polynomial_degree', 'lag_steps', 'pca_components', 'feature_selection_method', 'custom_formulas'],
  },
  {
    id: 'splitting',
    label: 'Data Splitting',
    icon: 'call_split',
    color: 'rgba(16,185,129,0.12)',
    accent: '#10B981',
    description: 'Test size, group / time column and stratification recipes · services/6_split/recipe/',
    serviceFolder: '6_split',
    port: 8005,
    fields: ['test_size', 'group_column', 'time_column', 'stratify'],
  },
  {
    id: 'training',
    label: 'Model Training',
    icon: 'model_training',
    color: 'rgba(139,92,246,0.12)',
    accent: '#8B5CF6',
    description: 'Algorithm, hyperparameters and metric recipes · services/7_train/recipe/',
    serviceFolder: '7_train',
    port: 8006,
    fields: ['algorithm', 'variant', 'validation_metrics', 'hyperparameters'],
  },
  {
    id: 'evaluating',
    label: 'Evaluation / Gates',
    icon: 'verified',
    color: 'rgba(245,158,11,0.12)',
    accent: '#F59E0B',
    description: 'Gate thresholds, noise injection, score cutoff recipes · services/8_evaluate/recipe/',
    serviceFolder: '8_evaluate',
    port: 8007,
    fields: ['gate_threshold', 'noise_variance', 'score_cutoff', 'metrics_required'],
  },
];

// ─── Helpers ──────────────────────────────────────────────────────────────────

const RECIPE_API = typeof window !== 'undefined' ? `http://${window.location.hostname}:8002` : 'http://localhost:8002';

async function fetchDagList(category: Category): Promise<string[]> {
  try {
    const res = await fetch(`${RECIPE_API}/api/v1/service-recipes/all`);
    if (!res.ok) throw new Error();
    const data = await res.json();
    const ids = Object.keys(data.recipes?.[category] ?? {});
    return ids.sort((a, b) => {
      const numA = parseInt(a.replace('DAG_', ''));
      const numB = parseInt(b.replace('DAG_', ''));
      return numA - numB;
    });
  } catch {
    return Array.from({ length: 5 }, (_, i) => `DAG_${String(i + 1).padStart(3, '0')}`);
  }
}

async function fetchRecipe(category: Category, dagId: string): Promise<Record<string, any> | null> {
  try {
    const res = await fetch(`${RECIPE_API}/api/v1/service-recipes/${category}/${dagId}`);
    if (!res.ok) return null;
    const data = await res.json();
    return data.content ?? null;
  } catch {
    return null;
  }
}

async function saveRecipe(category: Category, dagId: string, content: Record<string, any>): Promise<{ ok: boolean; message: string }> {
  try {
    const res = await fetch(`${RECIPE_API}/api/v1/service-recipes/save`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category, dag_id: dagId, content }),
    });
    const data = await res.json();
    return { ok: res.ok, message: data.message ?? (res.ok ? 'Saved' : 'Save failed') };
  } catch {
    return { ok: false, message: 'Network error — saved locally only' };
  }
}

async function deleteRecipe(category: Category, dagId: string): Promise<boolean> {
  try {
    const res = await fetch(`${RECIPE_API}/api/v1/service-recipes/delete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category, dag_id: dagId }),
    });
    return res.ok;
  } catch {
    return false;
  }
}

// ─── Sub-components ───────────────────────────────────────────────────────────

const CategoryCard: React.FC<{
  meta: CategoryMeta;
  dagCount: number;
  onClick: () => void;
}> = ({ meta, dagCount, onClick }) => (
  <button
    onClick={onClick}
    className="group relative rounded-2xl p-6 text-left transition-all duration-300 hover:scale-[1.02] active:scale-[0.99] overflow-hidden"
    style={{
      background: meta.color,
      border: `1.5px solid ${meta.accent}40`,
      boxShadow: `0 4px 24px ${meta.accent}18`,
    }}
  >
    {/* Glow on hover */}
    <div
      className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none rounded-2xl"
      style={{ background: `radial-gradient(circle at 30% 50%, ${meta.accent}22 0%, transparent 70%)` }}
    />

    <div className="relative z-10">
      {/* Icon + badge */}
      <div className="flex items-start justify-between mb-4">
        <div
          className="w-12 h-12 rounded-xl flex items-center justify-center"
          style={{ background: `${meta.accent}22`, border: `1px solid ${meta.accent}40` }}
        >
          <span className="material-symbols-outlined text-2xl" style={{ color: meta.accent }}>
            {meta.icon}
          </span>
        </div>
        <span
          className="px-2.5 py-1 text-xs font-mono font-bold rounded-lg"
          style={{ background: `${meta.accent}18`, color: meta.accent, border: `1px solid ${meta.accent}30` }}
        >
          {dagCount.toLocaleString()} DAGs
        </span>
      </div>

      <h3 className="font-headline font-bold text-lg mb-1" style={{ color: 'var(--text-primary)' }}>
        {meta.label}
      </h3>
      <p className="text-sm leading-relaxed" style={{ color: 'var(--text-muted)' }}>
        {meta.description}
      </p>

      {/* Arrow hint */}
      <div
        className="mt-4 flex items-center gap-1.5 text-xs font-mono font-semibold group-hover:gap-2.5 transition-all"
        style={{ color: meta.accent }}
      >
        <span>Open Editor</span>
        <span className="material-symbols-outlined text-sm">arrow_forward</span>
      </div>
    </div>
  </button>
);

// ─── Main Editor Panel ────────────────────────────────────────────────────────

const EditorPanel: React.FC<{
  meta: CategoryMeta;
  dagList: string[];
  onBack: () => void;
}> = ({ meta, dagList, onBack }) => {
  const [search, setSearch] = useState('');
  const [selectedDag, setSelectedDag] = useState<string | null>(null);
  const [recipe, setRecipe] = useState<Record<string, any> | null>(null);
  const [rawJson, setRawJson] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [isNewDagMode, setIsNewDagMode] = useState(false);
  const [newDagId, setNewDagId] = useState('');
  const [localDagList, setLocalDagList] = useState(dagList);

  const filtered = localDagList.filter((id) =>
    id.toLowerCase().includes(search.toLowerCase())
  );

  const loadRecipe = useCallback(async (dagId: string) => {
    setLoading(true);
    setRecipe(null);
    setRawJson('');
    const data = await fetchRecipe(meta.id, dagId);
    if (data) {
      setRecipe(data);
      setRawJson(JSON.stringify(data, null, 2));
    } else {
      // Template defaults
      const defaults: Record<string, any> = {};
      meta.fields.forEach((f) => { defaults[f] = ''; });
      setRecipe(defaults);
      setRawJson(JSON.stringify(defaults, null, 2));
    }
    setLoading(false);
  }, [meta]);

  const handleSelectDag = (id: string) => {
    setSelectedDag(id);
    setIsNewDagMode(false);
    loadRecipe(id);
  };

  const handleSave = async () => {
    if (!selectedDag) return;
    setSaving(true);
    try {
      const parsed = JSON.parse(rawJson);
      const ok = await saveRecipe(meta.id, selectedDag, parsed);
      setRecipe(parsed);
      setMessage({ text: ok ? `Saved ${selectedDag} successfully` : 'Saved locally (API offline)', type: 'success' });
    } catch {
      setMessage({ text: 'Invalid JSON — fix syntax errors before saving', type: 'error' });
    }
    setSaving(false);
    setTimeout(() => setMessage(null), 3000);
  };

  const handleDelete = async () => {
    if (!selectedDag) return;
    if (!confirm(`Delete ${selectedDag} from ${meta.label}?`)) return;
    const ok = await deleteRecipe(meta.id, selectedDag);
    if (ok) {
      setLocalDagList((prev) => prev.filter((d) => d !== selectedDag));
      setSelectedDag(null);
      setRecipe(null);
      setRawJson('');
      setMessage({ text: `${selectedDag} deleted`, type: 'success' });
    } else {
      setMessage({ text: 'Delete failed or API offline', type: 'error' });
    }
    setTimeout(() => setMessage(null), 3000);
  };

  const handleCreateNew = async () => {
    if (!newDagId.trim()) return;
    const id = newDagId.trim().toUpperCase();
    const defaults: Record<string, any> = {};
    meta.fields.forEach((f) => { defaults[f] = ''; });
    const ok = await saveRecipe(meta.id, id, defaults);
    setLocalDagList((prev) => [...prev, id].sort());
    setSelectedDag(id);
    setRecipe(defaults);
    setRawJson(JSON.stringify(defaults, null, 2));
    setIsNewDagMode(false);
    setNewDagId('');
    setMessage({ text: ok ? `Created ${id}` : `Created ${id} locally`, type: 'success' });
    setTimeout(() => setMessage(null), 3000);
  };

  return (
    <div className="flex flex-col gap-0 h-full animate-fadeIn">
      {/* Header bar */}
      <div
        className="flex items-center gap-4 px-6 py-4 rounded-2xl mb-5"
        style={{ background: meta.color, border: `1px solid ${meta.accent}35` }}
      >
        <button
          onClick={onBack}
          className="w-9 h-9 rounded-xl flex items-center justify-center transition-all hover:scale-105 active:scale-95"
          style={{ background: `${meta.accent}22`, border: `1px solid ${meta.accent}40`, color: meta.accent }}
        >
          <span className="material-symbols-outlined text-lg">arrow_back</span>
        </button>
        <div
          className="w-9 h-9 rounded-xl flex items-center justify-center"
          style={{ background: `${meta.accent}22`, border: `1px solid ${meta.accent}40` }}
        >
          <span className="material-symbols-outlined text-lg" style={{ color: meta.accent }}>
            {meta.icon}
          </span>
        </div>
        <div className="flex-1">
          <p className="text-xs font-mono uppercase tracking-widest" style={{ color: meta.accent }}>
            Recipe Editor
          </p>
          <h2 className="font-headline font-bold text-lg" style={{ color: 'var(--text-primary)' }}>
            {meta.label}
          </h2>
        </div>

        {/* Port badge */}
        <span
          className="px-2.5 py-1 text-[11px] font-mono font-bold rounded-lg"
          style={{ background: 'rgba(255,255,255,0.06)', color: 'var(--text-muted)', border: '1px solid rgba(255,255,255,0.10)' }}
        >
          Port :{meta.port}
        </span>

        {/* Toast message */}
        {message && (
          <span
            className="px-3 py-1.5 text-xs font-mono rounded-xl animate-bounce"
            style={{
              background: message.type === 'success' ? 'rgba(74,222,128,0.15)' : 'rgba(239,68,68,0.15)',
              color: message.type === 'success' ? '#4ade80' : '#f87171',
              border: `1px solid ${message.type === 'success' ? 'rgba(74,222,128,0.30)' : 'rgba(239,68,68,0.30)'}`,
            }}
          >
            {message.text}
          </span>
        )}
      </div>

      {/* Main 2-column layout */}
      <div className="grid grid-cols-[280px_1fr] gap-5 flex-1 min-h-0">
        {/* LEFT: DAG selector */}
        <div
          className="rounded-2xl flex flex-col overflow-hidden"
          style={{ border: '1px solid rgba(255,255,255,0.09)', background: 'var(--bg-card)' }}
        >
          {/* Search */}
          <div className="p-3 border-b" style={{ borderColor: 'rgba(255,255,255,0.07)' }}>
            <div className="relative">
              <span
                className="material-symbols-outlined text-sm absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none"
                style={{ color: 'var(--text-muted)' }}
              >
                search
              </span>
              <input
                type="text"
                placeholder="Search DAG-ID…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-8 pr-3 py-2 text-xs font-mono rounded-xl outline-none"
                style={{
                  background: 'var(--bg-input)',
                  border: '1px solid rgba(255,255,255,0.09)',
                  color: 'var(--text-primary)',
                }}
              />
            </div>
          </div>

          {/* DAG list */}
          <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
            {filtered.length === 0 && (
              <p className="text-xs font-mono text-center py-6" style={{ color: 'var(--text-muted)' }}>
                No DAGs found
              </p>
            )}
            {filtered.map((id) => {
              const active = id === selectedDag;
              return (
                <button
                  key={id}
                  onClick={() => handleSelectDag(id)}
                  className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-left text-xs font-mono transition-all"
                  style={{
                    background: active ? `${meta.accent}18` : 'transparent',
                    border: active ? `1px solid ${meta.accent}40` : '1px solid transparent',
                    color: active ? meta.accent : 'var(--text-muted)',
                    fontWeight: active ? 700 : 400,
                  }}
                >
                  <span
                    className="material-symbols-outlined text-xs flex-shrink-0"
                    style={{ color: active ? meta.accent : 'rgba(255,255,255,0.25)' }}
                  >
                    {active ? 'folder_open' : 'description'}
                  </span>
                  <span className="truncate">{id}</span>
                  {active && (
                    <span className="ml-auto">
                      <span className="material-symbols-outlined text-xs" style={{ color: meta.accent }}>
                        chevron_right
                      </span>
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Add New */}
          <div className="p-3 border-t" style={{ borderColor: 'rgba(255,255,255,0.07)' }}>
            {isNewDagMode ? (
              <div className="space-y-2">
                <input
                  type="text"
                  placeholder="e.g. DAG_9999"
                  value={newDagId}
                  onChange={(e) => setNewDagId(e.target.value)}
                  className="w-full px-3 py-2 text-xs font-mono rounded-xl outline-none"
                  style={{
                    background: 'var(--bg-input)',
                    border: `1px solid ${meta.accent}40`,
                    color: 'var(--text-primary)',
                  }}
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleCreateNew}
                    className="flex-1 py-1.5 rounded-lg text-xs font-mono font-bold transition-all"
                    style={{ background: meta.accent, color: '#fff' }}
                  >
                    Create
                  </button>
                  <button
                    onClick={() => { setIsNewDagMode(false); setNewDagId(''); }}
                    className="px-3 py-1.5 rounded-lg text-xs font-mono transition-all"
                    style={{ background: 'rgba(255,255,255,0.08)', color: 'var(--text-muted)' }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => setIsNewDagMode(true)}
                className="w-full flex items-center justify-center gap-2 py-2 rounded-xl text-xs font-mono font-semibold transition-all hover:scale-[1.02]"
                style={{
                  background: `${meta.accent}14`,
                  border: `1px dashed ${meta.accent}50`,
                  color: meta.accent,
                }}
              >
                <span className="material-symbols-outlined text-sm">add</span>
                New DAG Recipe
              </button>
            )}
          </div>
        </div>

        {/* RIGHT: JSON Editor */}
        <div
          className="rounded-2xl flex flex-col overflow-hidden"
          style={{ border: '1px solid rgba(255,255,255,0.09)', background: 'var(--bg-card)' }}
        >
          {!selectedDag ? (
            /* Empty state */
            <div className="flex-1 flex flex-col items-center justify-center gap-4 p-10 text-center">
              <div
                className="w-16 h-16 rounded-2xl flex items-center justify-center"
                style={{ background: meta.color, border: `1px solid ${meta.accent}30` }}
              >
                <span className="material-symbols-outlined text-3xl" style={{ color: meta.accent }}>
                  {meta.icon}
                </span>
              </div>
              <div>
                <h3 className="font-bold text-base mb-1" style={{ color: 'var(--text-primary)' }}>
                  Select a DAG-ID
                </h3>
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                  Choose a recipe from the left panel to open and edit its JSON configuration.
                </p>
              </div>
              <div
                className="grid grid-cols-2 gap-2 w-full max-w-xs mt-2"
              >
                {meta.fields.map((f) => (
                  <div
                    key={f}
                    className="px-3 py-1.5 rounded-lg text-[11px] font-mono text-center"
                    style={{
                      background: `${meta.accent}10`,
                      border: `1px solid ${meta.accent}25`,
                      color: meta.accent,
                    }}
                  >
                    {f}
                  </div>
                ))}
              </div>
            </div>
          ) : loading ? (
            /* Loading state */
            <div className="flex-1 flex flex-col items-center justify-center gap-3">
              <div className="w-8 h-8 border-2 border-t-transparent rounded-full animate-spin" style={{ borderColor: meta.accent }} />
              <p className="text-sm font-mono" style={{ color: 'var(--text-muted)' }}>
                Loading {selectedDag}…
              </p>
            </div>
          ) : (
            /* Editor */
            <>
              {/* Editor header */}
              <div
                className="flex items-center gap-3 px-4 py-3 border-b"
                style={{ borderColor: 'rgba(255,255,255,0.07)' }}
              >
                <span
                  className="px-2.5 py-1 rounded-lg text-xs font-mono font-bold"
                  style={{ background: `${meta.accent}20`, color: meta.accent, border: `1px solid ${meta.accent}40` }}
                >
                  {selectedDag}
                </span>
                <span className="text-xs font-mono" style={{ color: 'var(--text-muted)' }}>
                  {meta.label} Recipe
                </span>
                <div className="ml-auto flex items-center gap-2">
                  {/* Field pills */}
                  <span className="text-[10px] font-mono" style={{ color: 'rgba(255,255,255,0.25)' }}>
                    {Object.keys(recipe ?? {}).length} fields
                  </span>
                  <button
                    onClick={handleDelete}
                    className="px-3 py-1.5 text-xs font-mono rounded-lg transition-all hover:scale-105"
                    style={{
                      background: 'rgba(239,68,68,0.12)',
                      border: '1px solid rgba(239,68,68,0.30)',
                      color: '#f87171',
                    }}
                  >
                    <span className="material-symbols-outlined text-xs align-middle mr-1">delete</span>
                    Delete
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="px-4 py-1.5 text-xs font-mono font-bold rounded-lg transition-all hover:scale-105 disabled:opacity-50"
                    style={{ background: meta.accent, color: '#fff' }}
                  >
                    {saving ? 'Saving…' : '💾 Save Recipe'}
                  </button>
                </div>
              </div>

              {/* Field grid at top */}
              <div className="px-4 py-3 border-b flex flex-wrap gap-2" style={{ borderColor: 'rgba(255,255,255,0.07)' }}>
                {recipe && Object.entries(recipe).map(([key, val]) => {
                  const displayVal = Array.isArray(val)
                    ? `[${val.join(', ')}]`
                    : typeof val === 'object' && val !== null
                    ? '{…}'
                    : String(val);
                  return (
                    <div
                      key={key}
                      className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-mono"
                      style={{
                        background: 'rgba(255,255,255,0.04)',
                        border: '1px solid rgba(255,255,255,0.09)',
                      }}
                    >
                      <span style={{ color: meta.accent }}>{key}</span>
                      <span style={{ color: 'rgba(255,255,255,0.30)' }}>:</span>
                      <span style={{ color: 'var(--text-primary)' }}>{displayVal}</span>
                    </div>
                  );
                })}
              </div>

              {/* Raw JSON editor */}
              <div className="flex-1 relative p-4 overflow-hidden">
                <div
                  className="absolute top-4 left-4 flex items-center gap-2 z-10"
                  style={{ pointerEvents: 'none' }}
                >
                  <span
                    className="px-2 py-0.5 text-[10px] font-mono rounded"
                    style={{ background: 'rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.35)' }}
                  >
                    JSON
                  </span>
                </div>
                <textarea
                  value={rawJson}
                  onChange={(e) => setRawJson(e.target.value)}
                  spellCheck={false}
                  className="w-full h-full resize-none rounded-xl p-4 pt-8 font-mono text-xs outline-none leading-relaxed"
                  style={{
                    background: 'rgba(0,0,0,0.35)',
                    border: '1px solid rgba(255,255,255,0.09)',
                    color: '#a6e3a1',
                    caretColor: meta.accent,
                  }}
                />
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

// ─── Main View ────────────────────────────────────────────────────────────────

export const MasterDataView: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null);
  const [dagCounts, setDagCounts] = useState<Record<Category, number>>({
    preparing: 0,
    feature_engineering: 0,
    splitting: 0,
    training: 0,
    evaluating: 0,
  });
  const [dagLists, setDagLists] = useState<Record<Category, string[]>>({
    preparing: [],
    feature_engineering: [],
    splitting: [],
    training: [],
    evaluating: [],
  });
  const [loadingCounts, setLoadingCounts] = useState(true);

  // Load counts on mount
  useEffect(() => {
    const loadAll = async () => {
      setLoadingCounts(true);
      try {
        const res = await fetch(`${RECIPE_API}/api/v1/service-recipes/all`);
        if (res.ok) {
          const data = await res.json();
          const counts: Record<Category, number> = {
            preparing: 0,
            feature_engineering: 0,
            splitting: 0,
            training: 0,
            evaluating: 0,
          };
          const lists: Record<Category, string[]> = {
            preparing: [],
            feature_engineering: [],
            splitting: [],
            training: [],
            evaluating: [],
          };
          for (const cat of Object.keys(counts) as Category[]) {
            const ids = Object.keys(data.recipes?.[cat] ?? {}).sort((a, b) => {
              const numA = parseInt(a.replace('DAG_', '')) || 0;
              const numB = parseInt(b.replace('DAG_', '')) || 0;
              return numA - numB;
            });
            counts[cat] = ids.length;
            lists[cat] = ids;
          }
          setDagCounts(counts);
          setDagLists(lists);
        }
      } catch {
        // API offline: use fallback counts
        setDagCounts({
          preparing: 24,
          feature_engineering: 24,
          splitting: 100,
          training: 10,
          evaluating: 5,
        });
      } finally {
        setLoadingCounts(false);
      }
    };
    loadAll();
  }, []);

  const activeMeta = CATEGORIES.find((c) => c.id === selectedCategory);

  return (
    <div className="space-y-6 text-primary">
      {/* Page Header */}
      <div
        className="glass-panel p-6 rounded-2xl flex items-center gap-5 relative overflow-hidden"
        style={{ border: '1px solid rgba(255,255,255,0.09)' }}
      >
        <div className="absolute right-0 top-0 w-64 h-64 pointer-events-none"
          style={{ background: 'radial-gradient(circle, rgba(200,16,46,0.08) 0%, transparent 70%)' }} />
        <div
          className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
          style={{ background: 'rgba(200,16,46,0.15)', border: '1px solid rgba(200,16,46,0.35)' }}
        >
          <span className="material-symbols-outlined text-2xl" style={{ color: '#C8102E' }}>database</span>
        </div>
        <div>
          <div className="text-xs font-mono uppercase tracking-widest mb-0.5" style={{ color: '#C8102E' }}>
            Administration › Master Data
          </div>
          <h1 className="font-headline font-extrabold text-2xl" style={{ color: 'var(--text-primary)' }}>
            Recipe Library
          </h1>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            Browse, edit and manage DAG recipes for each pipeline node. Click a category block to open its editor.
          </p>
        </div>

        {!loadingCounts && (
          <div className="ml-auto flex items-center gap-2 flex-shrink-0">
            <span className="text-xs font-mono" style={{ color: 'var(--text-muted)' }}>
              Total:
            </span>
            <span
              className="px-3 py-1.5 rounded-xl text-sm font-mono font-bold"
              style={{ background: 'rgba(200,16,46,0.15)', color: '#C8102E', border: '1px solid rgba(200,16,46,0.30)' }}
            >
              {(Object.values(dagCounts) as number[]).reduce((a, b) => a + b, 0).toLocaleString()} Recipes
            </span>
          </div>
        )}
      </div>

      {/* Content */}
      {!selectedCategory ? (
        /* Category Grid */
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {CATEGORIES.map((cat) => (
            <CategoryCard
              key={cat.id}
              meta={cat}
              dagCount={dagCounts[cat.id]}
              onClick={() => setSelectedCategory(cat.id)}
            />
          ))}
        </div>
      ) : activeMeta ? (
        /* Editor Panel */
        <div style={{ minHeight: 'calc(100vh - 260px)' }}>
          <EditorPanel
            meta={activeMeta}
            dagList={dagLists[selectedCategory]}
            onBack={() => setSelectedCategory(null)}
          />
        </div>
      ) : null}
    </div>
  );
};
