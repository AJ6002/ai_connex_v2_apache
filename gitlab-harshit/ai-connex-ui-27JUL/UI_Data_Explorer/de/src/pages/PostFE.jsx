import React from 'react';
import { 
  CheckCircle, 
  Workflow, 
  ArrowRight, 
  Info, 
  AlertTriangle,
  Sliders,
  Cpu
} from 'lucide-react';

// Reusable SVG Chart Renderer for Post-F.E visualizations (140px uniform height)
function PostFEChartRenderer({ type, id, flagged }) {
  const primaryColor = '#8b5cf6'; // Purple for F.E accent
  const beforeColor = '#94a3b8'; // Grey
  const blueColor = '#1d4ed8'; // Blue
  const greenColor = '#10b981'; // Green
  
  switch (type) {
    case 'branch-flow':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Flow nodes and pathways */}
          <rect x="20" y="45" width="60" height="25" rx="3" fill="#e0e7ff" stroke="#818cf8" strokeWidth="1" />
          <text x="50" y="60" fill="#3730a3" fontSize="8" fontWeight="bold" textAnchor="middle">entity_column</text>
          
          <line x1="80" y1="57" x2="110" y2="57" stroke="var(--border-medium)" strokeWidth="1.5" />
          <polygon points="110,54 116,57 110,60" fill="var(--text-muted)" />
          
          <rect x="116" y="45" width="65" height="25" rx="3" fill="#e0e7ff" stroke="#818cf8" strokeWidth="1" />
          <text x="148" y="60" fill="#3730a3" fontSize="7" fontWeight="bold" textAnchor="middle">timestamp_column</text>
          
          <line x1="181" y1="57" x2="210" y2="57" stroke="var(--border-medium)" strokeWidth="1.5" />
          <polygon points="210,54 216,57 210,60" fill="var(--text-muted)" />
          
          <rect x="216" y="35" width="68" height="45" rx="4" fill="#dcfce7" stroke="#4ade80" strokeWidth="1.5" />
          <text x="250" y="55" fill="#166534" fontSize="8" fontWeight="bold" textAnchor="middle">TEMPORAL</text>
          <text x="250" y="67" fill="#166534" fontSize="7" textAnchor="middle">Branch Active</text>
        </svg>
      );

    case 'count-evol':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Stacked count bars */}
          <rect x="40" y="50" width="45" height="60" rx="3" fill={beforeColor} opacity="0.6" />
          <text x="62" y="42" fill="var(--text-muted)" fontSize="9" fontWeight="bold" textAnchor="middle">Raw: 47</text>
          
          <rect x="125" y="50" width="45" height="60" rx="3" fill={beforeColor} opacity="0.8" />
          <text x="147" y="42" fill="var(--text-muted)" fontSize="9" fontWeight="bold" textAnchor="middle">Prep: 47</text>
          
          <rect x="210" y="35" width="45" height="75" rx="3" fill="#8b5cf6" />
          <text x="232" y="27" fill="#8b5cf6" fontSize="9" fontWeight="bold" textAnchor="middle">Eng: 58</text>
        </svg>
      );

    case 'temp-create':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Show lagged series values shifting right */}
          <line x1="20" y1="90" x2="280" y2="90" stroke="var(--border-medium)" strokeWidth="1" />
          
          {/* Original dot series */}
          <circle cx="50" cy="50" r="3.5" fill="#94a3b8" />
          <circle cx="100" cy="40" r="3.5" fill="#94a3b8" />
          <circle cx="150" cy="65" r="3.5" fill="#94a3b8" />
          <circle cx="200" cy="30" r="3.5" fill="#94a3b8" />
          
          {/* Lagged dot series */}
          <path d="M 50 50 Q 80 50 100 50" fill="none" stroke="#8b5cf6" strokeWidth="1.5" strokeDasharray="3" />
          <circle cx="100" cy="50" r="3.5" fill="#8b5cf6" />
          
          <path d="M 100 40 Q 130 40 150 40" fill="none" stroke="#8b5cf6" strokeWidth="1.5" strokeDasharray="3" />
          <circle cx="150" cy="40" r="3.5" fill="#8b5cf6" />
          
          <path d="M 150 65 Q 180 65 200 65" fill="none" stroke="#8b5cf6" strokeWidth="1.5" strokeDasharray="3" />
          <circle cx="200" cy="65" r="3.5" fill="#8b5cf6" />
          
          <text x="260" y="35" fill="#8b5cf6" fontSize="8" fontWeight="bold">Lagged (t-1)</text>
        </svg>
      );

    case 'tab-create':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Interaction polynomial blocks */}
          <rect x="25" y="20" width="60" height="35" rx="3" fill="#eff6ff" stroke="#3b82f6" strokeWidth="1" />
          <text x="55" y="41" fill="#1d4ed8" fontSize="8" fontWeight="bold" textAnchor="middle">voltage * temp</text>
          
          <rect x="105" y="20" width="85" height="35" rx="3" fill="#eff6ff" stroke="#3b82f6" strokeWidth="1" />
          <text x="147" y="41" fill="#1d4ed8" fontSize="8" fontWeight="bold" textAnchor="middle">current * voltage</text>
          
          <rect x="205" y="20" width="65" height="35" rx="3" fill="#eff6ff" stroke="#3b82f6" strokeWidth="1" />
          <text x="237" y="41" fill="#1d4ed8" fontSize="8" fontWeight="bold" textAnchor="middle">voltage^2</text>
          
          {/* PCA variances */}
          <line x1="20" y1="85" x2="280" y2="85" stroke="var(--border-medium)" strokeWidth="1" />
          <circle cx="60" cy="85" r="4.5" fill="#8b5cf6" />
          <text x="60" y="102" fill="var(--text-muted)" fontSize="8" textAnchor="middle">PC1 (45%)</text>
          <circle cx="140" cy="85" r="4.5" fill="#8b5cf6" />
          <text x="140" y="102" fill="var(--text-muted)" fontSize="8" textAnchor="middle">PC2 (22%)</text>
          <circle cx="220" cy="85" r="4.5" fill="#8b5cf6" />
          <text x="220" y="102" fill="var(--text-muted)" fontSize="8" textAnchor="middle">PC3 (15%)</text>
        </svg>
      );

    case 'lag-opt':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Autocorrelation drop curve */}
          <line x1="30" y1="90" x2="270" y2="90" stroke="var(--border-medium)" strokeWidth="1" />
          <line x1="30" y1="40" x2="270" y2="40" stroke="#ef4444" strokeWidth="1" strokeDasharray="3" />
          <text x="230" y="32" fill="#ef4444" fontSize="8">Threshold: 0.2</text>
          
          {/* ACF plot */}
          <path d="M 30 20 L 60 25 L 90 35 L 120 50 L 150 72 L 180 85 L 210 90 L 240 90" fill="none" stroke="#8b5cf6" strokeWidth="2.5" />
          <circle cx="30" cy="20" r="3.5" fill="#8b5cf6" />
          <circle cx="60" cy="25" r="3.5" fill="#8b5cf6" />
          <circle cx="90" cy="35" r="3.5" fill="#8b5cf6" />
          <circle cx="120" cy="50" r="3.5" fill="#8b5cf6" />
          <circle cx="150" cy="72" r="3.5" fill="#8b5cf6" />
          <circle cx="180" cy="85" r="3.5" fill="#8b5cf6" />
        </svg>
      );

    case 'roll-impact':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Noisy baseline */}
          <path d="M 20 80 L 50 20 L 80 90 L 110 30 L 140 85 L 170 25 L 200 70 L 230 40 L 260 80" fill="none" stroke={beforeColor} strokeWidth="1.5" opacity="0.4" />
          {/* Smoothed curve */}
          <path d="M 20 72 Q 80 50 140 60 T 260 55" fill="none" stroke="#8b5cf6" strokeWidth="2.5" />
          <circle cx="140" cy="60" r="4.5" fill="#8b5cf6" />
        </svg>
      );

    case 'pca-explain':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Scree bars */}
          <rect x="25" y="40" width="18" height="70" fill="#8b5cf6" rx="2" />
          <text x="34" y="32" fill="var(--text-muted)" fontSize="7" textAnchor="middle">PC1</text>
          
          <rect x="60" y="65" width="18" height="45" fill="#8b5cf6" rx="2" />
          <text x="69" y="57" fill="var(--text-muted)" fontSize="7" textAnchor="middle">PC2</text>
          
          <rect x="95" y="80" width="18" height="30" fill="#8b5cf6" rx="2" />
          <text x="104" y="72" fill="var(--text-muted)" fontSize="7" textAnchor="middle">PC3</text>
          
          <rect x="130" y="95" width="18" height="15" fill="#8b5cf6" rx="2" />
          <text x="139" y="87" fill="var(--text-muted)" fontSize="7" textAnchor="middle">PC4</text>
          
          {/* Cumulative line */}
          <path d="M 34 85 L 69 60 L 104 35 L 139 20 L 174 15 L 209 15" fill="none" stroke="#3b82f6" strokeWidth="2" />
          <circle cx="139" cy="20" r="3.5" fill="#3b82f6" />
          <text x="180" y="24" fill="#3b82f6" fontSize="7" fontWeight="bold">90% Cumulative</text>
        </svg>
      );

    case 'importance-rank':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Horizontal importance bars */}
          <text x="20" y="30" fill="var(--text-muted)" fontSize="8" fontWeight="bold" fontFamily="var(--font-mono)">voltage_lag_1</text>
          <rect x="110" y="22" width="115" height="10" rx="2" fill="#10b981" />
          
          <text x="20" y="55" fill="var(--text-muted)" fontSize="8" fontWeight="bold" fontFamily="var(--font-mono)">temp_mean_5</text>
          <rect x="110" y="47" width="95" height="10" rx="2" fill="#10b981" />
          
          <text x="20" y="80" fill="var(--text-muted)" fontSize="8" fontWeight="bold" fontFamily="var(--font-mono)">voltage_diff_1</text>
          <rect x="110" y="72" width="85" height="10" rx="2" fill="#10b981" />
          
          <text x="20" y="105" fill="var(--text-muted)" fontSize="8" fontWeight="bold" fontFamily="var(--font-mono)">voltage_raw</text>
          <rect x="110" y="97" width="55" height="10" rx="2" fill="#3b82f6" />
        </svg>
      );

    case 'select-filter':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Filter boundary bars */}
          <line x1="140" y1="15" x2="140" y2="105" stroke="#ef4444" strokeWidth="1.5" strokeDasharray="3" />
          <text x="145" y="24" fill="#ef4444" fontSize="8" fontWeight="bold">Cutoff Limit</text>
          
          {/* Kept bars */}
          <rect x="25" y="35" width="100" height="12" rx="2" fill="#10b981" />
          <text x="35" y="44" fill="white" fontSize="7" fontWeight="bold">Kept (Top 34)</text>
          
          {/* Discarded bars */}
          <rect x="155" y="70" width="110" height="12" rx="2" fill="#ef4444" opacity="0.4" />
          <text x="165" y="79" fill="var(--text-main)" fontSize="7" fontWeight="bold">Omitted (23)</text>
        </svg>
      );

    case 'leakage-check':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Safety check validation blocks */}
          <g transform="translate(45, 25)">
            <circle cx="20" cy="20" r="14" fill="#dcfce7" stroke="#22c55e" strokeWidth="2" />
            <text x="20" y="24" textAnchor="middle" fill="#166534" fontSize="12" fontWeight="bold">✓</text>
            <text x="20" y="48" textAnchor="middle" fill="var(--text-muted)" fontSize="8">Sorted</text>
          </g>
          <g transform="translate(130, 25)">
            <circle cx="20" cy="20" r="14" fill="#dcfce7" stroke="#22c55e" strokeWidth="2" />
            <text x="20" y="24" textAnchor="middle" fill="#166534" fontSize="12" fontWeight="bold">✓</text>
            <text x="20" y="48" textAnchor="middle" fill="var(--text-muted)" fontSize="8">No Leakage</text>
          </g>
          <g transform="translate(215, 25)">
            <circle cx="20" cy="20" r="14" fill="#dcfce7" stroke="#22c55e" strokeWidth="2" />
            <text x="20" y="24" textAnchor="middle" fill="#166534" fontSize="12" fontWeight="bold">✓</text>
            <text x="20" y="48" textAnchor="middle" fill="var(--text-muted)" fontSize="8">Valid bounds</text>
          </g>
        </svg>
      );

    case 'pipeline-timeline':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Gantt chart timeline for feature engineering steps */}
          <rect x="20" y="15" width="40" height="8" rx="2" fill="#3b82f6" />
          <text x="70" y="22" fill="var(--text-muted)" fontSize="8">Lag Gen (4.8s)</text>
          
          <rect x="50" y="32" width="60" height="8" rx="2" fill="#8b5cf6" />
          <text x="120" y="39" fill="var(--text-muted)" fontSize="8">Rolling Windows (5.2s)</text>
          
          <rect x="100" y="49" width="30" height="8" rx="2" fill="#10b981" />
          <text x="140" y="56" fill="var(--text-muted)" fontSize="8">Diff (3.4s)</text>
          
          <rect x="120" y="66" width="90" height="8" rx="2" fill="#ec4899" />
          <text x="20" y="90" fill="var(--text-muted)" fontSize="8">Backfilling (2.6s)</text>
          <text x="110" y="90" fill="var(--text-muted)" fontSize="8">Save CSV (6.8s)</text>
        </svg>
      );

    case 'type-dist':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Type distribution donut */}
          <circle cx="150" cy="60" r="32" fill="none" stroke="#eff6ff" strokeWidth="8" />
          {/* Engineered part (59%) */}
          <circle 
            cx="150" 
            cy="60" 
            r="32" 
            fill="none" 
            stroke="#8b5cf6" 
            strokeWidth="8" 
            strokeDasharray={`${2 * Math.PI * 32}`}
            strokeDashoffset={`${(1 - 0.59) * (2 * Math.PI * 32)}`}
            transform="rotate(-90 150 60)"
          />
          {/* Original part (41%) */}
          <circle 
            cx="150" 
            cy="60" 
            r="32" 
            fill="none" 
            stroke="#3b82f6" 
            strokeWidth="8" 
            strokeDasharray={`${2 * Math.PI * 32}`}
            strokeDashoffset={`${(1 - 0.41) * (2 * Math.PI * 32)}`}
            transform="rotate(122 150 60)"
          />
          <text x="150" y="64" textAnchor="middle" fill="var(--text-main)" fontSize="9" fontWeight="bold">
            58 Features
          </text>
        </svg>
      );

    case 'backfill-effect':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* NaN counts comparison before and after */}
          <rect x="60" y="30" width="40" height="70" fill={beforeColor} rx="3" />
          <text x="80" y="24" fill="var(--text-muted)" fontSize="9" fontWeight="bold" textAnchor="middle">Before NaNs</text>
          
          <rect x="180" y="99" width="40" height="1" fill="#10b981" rx="1" />
          <text x="200" y="92" fill="#10b981" fontSize="9" fontWeight="bold" textAnchor="middle">After (0)</text>
        </svg>
      );

    default:
      return (
        <div style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
          Chart View ({type})
        </div>
      );
  }
}

export default function PostFE({ onProceed }) {
  // 13 core Feature engineering visualizations
  const visualizations = [
    { 
      id: 'FE1', 
      title: 'Topology Detection & Branch Visualization', 
      type: 'branch-flow', 
      check: 'Branch selection logic based on columns', 
      metric: 'entity_column OR timestamp_column present', 
      decision: 'Identifies which feature engineering path was taken. Both device_id and timestamp were present, routing to Temporal Branch (A).',
      flagged: false
    },
    { 
      id: 'FE2', 
      title: 'Feature Count Evolution', 
      type: 'count-evol', 
      check: 'Feature expansion counts per stage', 
      metric: 'Raw: 47 → Prepared: 47 → Engineered: 58', 
      decision: 'Tracks feature growth. Created 34 new features and filtered out 23, resulting in 58 engineered features.' 
    },
    { 
      id: 'FE3', 
      title: 'Temporal Feature Creation (Branch A)', 
      type: 'temp-create', 
      check: 'Original vs. Lagged vs. Rolling values', 
      metric: 'Chronological time step shift logic', 
      decision: 'Visually traces lags. Confirms values correctly shift chronologically for lag creations (e.g. lag_1).' 
    },
    { 
      id: 'FE4', 
      title: 'Tabular Feature Creation (Branch B)', 
      type: 'tab-create', 
      check: 'Row aggregations, interaction products, and PCA projections', 
      metric: 'Explained variance threshold matching (PC4 explain 90%)', 
      decision: 'Validates tabular metrics. PCA projections explain 90% variance in 4 components.' 
    },
    { 
      id: 'FE5', 
      title: 'Lag Optimization Analysis', 
      type: 'lag-opt', 
      check: 'Correlation vs. Lag step duration decay', 
      metric: 'Autocorrelation (ACF) threshold drops below 0.2', 
      decision: 'Decides optimal lag sizes. Correlation drops below 0.2 after lag step 5. Optimal lags selected: [1, 2, 3, 5].' 
    },
    { 
      id: 'FE6', 
      title: 'Rolling Window Impact', 
      type: 'roll-impact', 
      check: 'Original vs. window-size smoothings', 
      metric: 'Smoothing impact variance reduction ratio', 
      decision: 'Optimizes smoothing metrics. Rolling window of 3 was selected as it balances noise reduction and signal loss.' 
    },
    { 
      id: 'FE7', 
      title: 'PCA Variance Explanation', 
      type: 'pca-explain', 
      check: 'Explained variance per principal component', 
      metric: '95% cumulative explained threshold', 
      decision: 'Tracks PCA contributions. Cumulative variance matches target thresholds in the first 4 components.' 
    },
    { 
      id: 'FE8', 
      title: 'Feature Importance Ranking', 
      type: 'importance-rank', 
      check: 'Feature correlations with targets', 
      metric: 'Top 15 features rank checks', 
      decision: 'Identifies predictive columns. The top 3 features are all engineered, validating feature engineering value.', 
      flagged: true 
    },
    { 
      id: 'FE9', 
      title: 'Feature Selection Filtering', 
      type: 'select-filter', 
      check: 'Kept vs. Discarded variables', 
      metric: 'SelectKBest F-score thresholds', 
      decision: 'Filters features to reduce size. Kept top 34 predictive features and dropped 23 low-scoring elements.' 
    },
    { 
      id: 'FE10', 
      title: 'Data Leakage Safety Check', 
      type: 'leakage-check', 
      check: 'Verification of leakage paths', 
      metric: 'NaN indices only at group starts', 
      decision: 'Ensures no future data was leaked during feature creation. Validates that NaNs only appear at group starts.', 
      flagged: true 
    },
    { 
      id: 'FE11', 
      title: 'Feature Engineering Pipeline Timeline', 
      type: 'pipeline-timeline', 
      check: 'Running duration per engineering step', 
      metric: 'Any step duration >30% of total time', 
      decision: 'Identifies computation bottlenecks. Generating rolling windows took 19% of total running time.' 
    },
    { 
      id: 'FE12', 
      title: 'Feature Type Distribution', 
      type: 'type-dist', 
      check: 'Ratio of original vs. engineered features', 
      metric: 'Engineered ratio >50% target', 
      decision: 'Visualizes final dataset composition. Engineered variables represent 59% of total features (34 out of 58).' 
    },
    { 
      id: 'FE13', 
      title: 'Backfilling Effect Visualization', 
      type: 'backfill-effect', 
      check: 'NaN recovery and fill rates', 
      metric: 'NaN count delta post-backfilling', 
      decision: 'Confirms proper NaN resolution. All missing indices caused by lags were successfully backfilled.' 
    }
  ];

  return (
    <div className="page-container">
      {/* Parameters Row */}
      <div className="status-action-bar">
        <div className="status-bar-info">
          <div className="status-bar-icon-block" style={{ color: '#8b5cf6', backgroundColor: 'rgba(139, 92, 246, 0.1)' }}>
            <Sliders size={20} />
          </div>
          <div className="status-bar-details">
            <div className="status-bar-title-row">
              <span>feature_engineering</span>
              <span className="status-run-badge">
                <CheckCircle size={12} style={{ color: '#10b981' }} /> Store Synced
              </span>
            </div>
            
            <div className="status-bar-parameters">
              <div className="param-item">
                <span>🧬 Total Features: </span>
                <span className="highlight-orange">58 (34 Generated)</span>
              </div>
              <span className="bullet-dot">•</span>
              <div className="param-item">
                <span>🎯 Selected: </span>
                <span className="highlight-green">34 Features</span>
              </div>
              <span className="bullet-dot">•</span>
              <div className="param-item">
                <span>📊 Selection Method: </span>
                <span className="highlight-blue">SelectKBest (F-Score)</span>
              </div>
            </div>
          </div>
        </div>
        
        <button className="proceed-cta-btn" onClick={onProceed}>
          Proceed to Model Training <ArrowRight size={16} />
        </button>
      </div>

      {/* Info Callout */}
      <div className="info-callout-banner" style={{ backgroundColor: '#f5f3ff', borderColor: '#ddd6fe', color: '#5b21b6' }}>
        <Info size={16} className="info-banner-icon" />
        <div className="info-banner-text">
          <strong>Post-F.E [Feature Engineered] Dataset Explorer:</strong> Visualizes temporal and tabular transformations, optimal lags, principal components, and final feature selections.
        </div>
      </div>

      {/* Visualizations Uniform Cards Grid */}
      <div className="viz-grid">
        {visualizations.map((card) => (
          <div key={card.id} className="viz-card" style={{ borderTop: card.flagged ? '3px solid #ef4444' : '1px solid var(--border-light)' }}>
            
            {/* Header */}
            <div className="viz-card-header">
              <div className="viz-card-title-group">
                <div className="viz-card-title-row">
                  {card.flagged ? (
                    <AlertTriangle size={15} style={{ color: '#ef4444' }} className="animate-bounce" />
                  ) : (
                    <CheckCircle size={15} style={{ color: '#10b981' }} />
                  )}
                  <span>{card.title}</span>
                </div>
                <div className="viz-card-checked">
                  <strong>Checks:</strong> {card.check}
                </div>
              </div>
              <span className="viz-card-id">{card.id}</span>
            </div>

            {/* Visual Canvas (Uniform 140px size) */}
            <div className="viz-chart-box">
              <PostFEChartRenderer type={card.type} id={card.id} flagged={card.flagged} />
            </div>

            {/* Decision Rule Alert Box */}
            <div className={`viz-card-decision-box ${card.flagged ? 'flagged' : ''}`}>
              <div style={{ fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-muted)', marginBottom: '2px', fontWeight: 'bold' }}>
                {card.flagged ? '⚠️ Warning Action Rule' : '⚙️ Standard Action Rule'}
              </div>
              <div>
                <strong>Metric Goal:</strong> {card.metric}. <br />
                <strong>Decision Logic:</strong> {card.decision}
              </div>
            </div>

          </div>
        ))}
      </div>
    </div>
  );
}
