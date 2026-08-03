import React, { useState } from 'react';
import { 
  Workflow, 
  GitCommit, 
  ArrowRight, 
  Info, 
  AlertCircle,
  FileText,
  Sliders,
  Cpu,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';

// Reusable SVG Chart Renderer for Post-Prepare visualizations (140px uniform height)
function PostPrepareChartRenderer({ type, id, flagged }) {
  const primaryColor = flagged ? '#ef4444' : '#10b981'; // Green for normal prepared, Red for alerts
  const beforeColor = '#94a3b8'; // Grey for raw baseline data
  const accentColor = '#8b5cf6'; // Purple for transforms
  const blueColor = '#1d4ed8'; // Blue for scaling checks
  
  switch (type) {
    case 'overlay-hist':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Baseline Raw */}
          <path d="M 20 100 Q 80 100 120 40 T 220 100 L 280 100" fill="none" stroke={beforeColor} strokeWidth="1.5" strokeDasharray="3" />
          <text x="50" y="55" fill={beforeColor} fontSize="8" fontWeight="bold">Raw (Before)</text>
          
          {/* Prepared curve */}
          <path d="M 20 100 Q 110 100 150 20 T 260 100" fill="none" stroke="#10b981" strokeWidth="2.5" />
          <text x="180" y="35" fill="#10b981" fontSize="8" fontWeight="bold">Prepared (After)</text>
          <circle cx="150" cy="20" r="4.5" fill="#10b981" />
        </svg>
      );

    case 'waterfall-missing':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Column labels on left, bars showing recovery */}
          <text x="20" y="32" fill="var(--text-muted)" fontSize="9" fontWeight="bold" fontFamily="var(--font-mono)">sensor_1 (142 nulls)</text>
          <rect x="130" y="24" width="90" height="10" rx="2" fill={beforeColor} opacity="0.3" />
          <rect x="130" y="24" width="90" height="10" rx="2" fill="#10b981" />
          <text x="230" y="32" fill="#10b981" fontSize="8" fontWeight="bold">✓ Fixed (100%)</text>
          
          <text x="20" y="62" fill="var(--text-muted)" fontSize="9" fontWeight="bold" fontFamily="var(--font-mono)">sensor_2 (98 nulls)</text>
          <rect x="130" y="54" width="90" height="10" rx="2" fill={beforeColor} opacity="0.3" />
          <rect x="130" y="54" width="90" height="10" rx="2" fill="#10b981" />
          <text x="230" y="62" fill="#10b981" fontSize="8" fontWeight="bold">✓ Fixed (100%)</text>
          
          <text x="20" y="92" fill="var(--text-muted)" fontSize="9" fontWeight="bold" fontFamily="var(--font-mono)">sensor_3 (56 nulls)</text>
          <rect x="130" y="84" width="90" height="10" rx="2" fill={beforeColor} opacity="0.3" />
          <rect x="130" y="84" width="90" height="10" rx="2" fill="#10b981" />
          <text x="230" y="92" fill="#10b981" fontSize="8" fontWeight="bold">✓ Fixed (100%)</text>
        </svg>
      );

    case 'clipping-box':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Before: box plot showing outliers outside upper bound */}
          <text x="20" y="28" fill={beforeColor} fontSize="8" fontWeight="bold">Before (Raw):</text>
          <line x1="120" y1="24" x2="220" y2="24" stroke={beforeColor} strokeWidth="1" />
          <rect x="140" y="14" width="50" height="20" rx="2" fill="none" stroke={beforeColor} strokeWidth="1" />
          <line x1="165" y1="14" x2="165" y2="34" stroke={beforeColor} strokeWidth="1.5" />
          {/* Outliers */}
          <circle cx="250" cy="24" r="3" fill="#ef4444" />
          <circle cx="270" cy="24" r="3" fill="#ef4444" />
          <text x="250" y="14" fill="#ef4444" fontSize="7">Outliers (24k)</text>
          
          {/* After: outliers clipped within upper bounds */}
          <text x="20" y="78" fill="#10b981" fontSize="8" fontWeight="bold">After (Clipped):</text>
          <line x1="120" y1="74" x2="220" y2="74" stroke="#10b981" strokeWidth="1" />
          <rect x="140" y="64" width="50" height="20" rx="2" fill="none" stroke="#10b981" strokeWidth="1.5" />
          <line x1="165" y1="64" x2="165" y2="84" stroke="#10b981" strokeWidth="2.5" />
          {/* Bounded marker */}
          <line x1="220" y1="64" x2="220" y2="84" stroke="#ef4444" strokeWidth="2" />
          <text x="225" y="60" fill="#ef4444" fontSize="7">Clipped to upper bound (1,450)</text>
        </svg>
      );

    case 'qq-plot':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Diagonal target line */}
          <line x1="40" y1="100" x2="260" y2="20" stroke="var(--border-medium)" strokeWidth="1.5" strokeDasharray="3" />
          {/* Points aligning to diagonal */}
          <circle cx="60" cy="92" r="3" fill={blueColor} />
          <circle cx="100" cy="78" r="3" fill={blueColor} />
          <circle cx="150" cy="58" r="3" fill={blueColor} />
          <circle cx="200" cy="40" r="3" fill={blueColor} />
          <circle cx="240" cy="26" r="3" fill={blueColor} />
          <text x="140" y="112" fill="var(--text-muted)" fontSize="8" textAnchor="middle">Theoretical Quantiles</text>
        </svg>
      );

    case 'category-encode':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Category columns frequency */}
          <rect x="25" y="30" width="36" height="70" fill={accentColor} opacity="0.9" rx="2" />
          <text x="43" y="112" fill="var(--text-muted)" fontSize="8" textAnchor="middle">OK (0)</text>
          
          <rect x="85" y="55" width="36" height="45" fill={accentColor} opacity="0.75" rx="2" />
          <text x="103" y="112" fill="var(--text-muted)" fontSize="8" textAnchor="middle">WARN (1)</text>
          
          <rect x="145" y="85" width="36" height="15" fill={accentColor} opacity="0.6" rx="2" />
          <text x="163" y="112" fill="var(--text-muted)" fontSize="8" textAnchor="middle">ERR (2)</text>
          
          <rect x="205" y="96" width="36" height="4" fill={accentColor} opacity="0.3" rx="2" />
          <text x="223" y="112" fill="var(--text-muted)" fontSize="8" textAnchor="middle">UNK (3)</text>
        </svg>
      );

    case 'type-class':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Classification donut */}
          <circle cx="150" cy="60" r="32" fill="none" stroke="#eff6ff" strokeWidth="8" />
          {/* Categorical part (35%) */}
          <circle 
            cx="150" 
            cy="60" 
            r="32" 
            fill="none" 
            stroke={accentColor} 
            strokeWidth="8" 
            strokeDasharray={`${2 * Math.PI * 32}`}
            strokeDashoffset={`${(1 - 0.35) * (2 * Math.PI * 32)}`}
            transform="rotate(-90 150 60)"
          />
          {/* Numeric part (65%) */}
          <circle 
            cx="150" 
            cy="60" 
            r="32" 
            fill="none" 
            stroke={blueColor} 
            strokeWidth="8" 
            strokeDasharray={`${2 * Math.PI * 32}`}
            strokeDashoffset={`${(1 - 0.65) * (2 * Math.PI * 32)}`}
            transform="rotate(36 150 60)"
          />
          <text x="150" y="64" textAnchor="middle" fill="var(--text-main)" fontSize="10" fontWeight="bold">
            9 Columns
          </text>
        </svg>
      );

    case 'pipeline-gantt':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Horizontal Gantt timeline */}
          <rect x="20" y="15" width="50" height="8" rx="2" fill="#3b82f6" />
          <text x="80" y="22" fill="var(--text-muted)" fontSize="8">1. Load (2.3s)</text>
          
          <rect x="60" y="30" width="70" height="8" rx="2" fill="#8b5cf6" />
          <text x="140" y="37" fill="var(--text-muted)" fontSize="8">2. Impute (4.1s)</text>
          
          <rect x="120" y="45" width="60" height="8" rx="2" fill="#ec4899" />
          <text x="190" y="52" fill="var(--text-muted)" fontSize="8">3. Clip (3.8s)</text>
          
          <rect x="170" y="60" width="90" height="8" rx="2" fill="#10b981" />
          <text x="20" y="85" fill="var(--text-muted)" fontSize="8">4. Scale (5.2s)</text>
          <text x="110" y="85" fill="var(--text-muted)" fontSize="8">5. Encode (2.9s)</text>
          <text x="200" y="85" fill="var(--text-muted)" fontSize="8">6. Save CSV (6.7s)</text>
        </svg>
      );

    case 'impute-compare':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Show strategy differences (Actual vs Imputed distributions) */}
          <path d="M 30 100 C 60 100, 80 15, 110 15 C 140 15, 160 100, 190 100" fill="none" stroke={beforeColor} strokeWidth="1.5" strokeDasharray="3" />
          <text x="90" y="55" fill={beforeColor} fontSize="8">Actual</text>
          
          <path d="M 90 100 C 120 100, 140 30, 170 30 C 200 30, 220 100, 250 100" fill="none" stroke="#10b981" strokeWidth="2.5" />
          <text x="190" y="45" fill="#10b981" fontSize="8" fontWeight="bold">Imputed (Median)</text>
        </svg>
      );

    case 'scale-compare':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Display StandardScaler vs RobustScaler vs MinMaxScaler */}
          <path d="M 20 80 Q 75 10 130 80 T 240 80" fill="none" stroke="#3b82f6" strokeWidth="1.5" />
          <text x="60" y="50" fill="#3b82f6" fontSize="7" fontWeight="bold">MinMax</text>
          
          <path d="M 40 80 Q 95 30 150 80 T 260 80" fill="none" stroke="#8b5cf6" strokeWidth="1.5" strokeDasharray="2" />
          <text x="140" y="45" fill="#8b5cf6" fontSize="7">Standard</text>
          
          <path d="M 60 80 Q 115 20 170 80 T 280 80" fill="none" stroke="#10b981" strokeWidth="2" />
          <text x="210" y="40" fill="#10b981" fontSize="7" fontWeight="bold">RobustScaler</text>
        </svg>
      );

    case 'quality-radar':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          <g transform="translate(150, 60)">
            {/* Hexagon backing */}
            <polygon points="0,-40 35,-20 35,20 0,40 -35,20 -35,-20" fill="none" stroke="var(--border-medium)" strokeWidth="0.8" />
            {/* Raw quality shape (small area) */}
            <polygon points="0,-15 15,-10 10,5 0,20 -15,5 -10,-10" fill={beforeColor} fillOpacity="0.3" stroke={beforeColor} strokeWidth="1" />
            <text x="-62" y="-12" fill={beforeColor} fontSize="7" fontWeight="bold">Raw: 45</text>
            
            {/* Prepared quality shape (full area) */}
            <polygon points="0,-38 32,-18 32,18 0,38 -32,18 -32,-18" fill="#10b981" fillOpacity="0.4" stroke="#10b981" strokeWidth="2" />
            <text x="36" y="-12" fill="#10b981" fontSize="7" fontWeight="bold">Prep: 100</text>
          </g>
        </svg>
      );

    case 'alerts-dash':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Alerts layout row blocks */}
          <rect x="20" y="15" width="260" height="26" rx="4" fill="#fffbeb" stroke="#fde68a" strokeWidth="1" />
          <text x="32" y="31" fill="#b45309" fontSize="9" fontWeight="bold">🟡 sensor_3 Outliers</text>
          <text x="145" y="31" fill="var(--text-muted)" fontSize="8">142 values clipped (2.1%)</text>
          
          <rect x="20" y="48" width="260" height="26" rx="4" fill="#eff6ff" stroke="#bfdbfe" strokeWidth="1" />
          <text x="32" y="64" fill="#1d4ed8" fontSize="9" fontWeight="bold">🟢 status_code UNK</text>
          <text x="145" y="64" fill="var(--text-muted)" fontSize="8">Rare values encoded to code 3</text>
          
          <rect x="20" y="81" width="260" height="26" rx="4" fill="#eff6ff" stroke="#bfdbfe" strokeWidth="1" />
          <text x="32" y="97" fill="#1d4ed8" fontSize="9" fontWeight="bold">🟢 device_id Ingest</text>
          <text x="145" y="97" fill="var(--text-muted)" fontSize="8">Categorical mapping complete</text>
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

export default function PostPrepare({ onProceed }) {
  // 11 Core Prepare pipeline visualizations
  const visualizations = [
    { 
      id: 'PP1', 
      title: 'Before/After Distribution Overlay', 
      type: 'overlay-hist', 
      check: 'Distribution shift after imputation/scaling', 
      metric: 'KL Divergence >0.1 (Shape change >30%)', 
      decision: 'Detects if imputation or scaling processes are distorting features. Scaled shapes show expected adjustments.' 
    },
    { 
      id: 'PP2', 
      title: 'Missing Values Waterfall Chart', 
      type: 'waterfall-missing', 
      check: 'Null count per column before vs. after', 
      metric: 'Nulls remaining = 0 for all columns', 
      decision: 'Displays missing values counts. Proves that all missing values are fully imputed to 0.' 
    },
    { 
      id: 'PP3', 
      title: 'Outlier Clipping Detection', 
      type: 'clipping-box', 
      check: 'Outlier count and magnitude clipped', 
      metric: 'Clipped outliers ratio >5% of data', 
      decision: 'Checks outlier clipping boundaries. Outliers in sensor_3 were bounded using upper and lower IQR whisker margins.', 
      flagged: true 
    },
    { 
      id: 'PP4', 
      title: 'Scaling Transformation Visualization', 
      type: 'qq-plot', 
      check: 'Quantiles alignment vs. normal standard', 
      metric: 'Points should align diagonally', 
      decision: 'Validates that scaling worked correctly. Linear alignment confirms scaling preserved original shapes.' 
    },
    { 
      id: 'PP5', 
      title: 'Categorical Encoding Mapping', 
      type: 'category-encode', 
      check: 'Category text values to numeric index', 
      metric: 'Category frequency <1% check', 
      decision: 'Explains what numbers represent. Flags warning if UNKNOWN categories represent less than 1% of data.' 
    },
    { 
      id: 'PP6', 
      title: 'Column Type Classification Heatmap', 
      type: 'type-class', 
      check: 'Column classified as numeric vs categorical', 
      metric: 'Any column mismatch count', 
      decision: 'Validates column classification outputs. Automatically scaled 6 numeric columns and encoded 3 text category columns.' 
    },
    { 
      id: 'PP7', 
      title: 'Complete Transformation Timeline', 
      type: 'pipeline-gantt', 
      check: 'Step running time (Load → Classify → Save)', 
      metric: 'Any step duration >30% of total', 
      decision: 'Highlights execution speed per step. Saving raw data frames took 25% of total timing.' 
    },
    { 
      id: 'PP8', 
      title: 'Imputation Strategy Comparison', 
      type: 'impute-compare', 
      check: 'Mean vs Median vs Mode shape shifts', 
      metric: 'Imputation bias metric >5%', 
      decision: 'Compares different imputation values. Median imputation was chosen because it creates the lowest bias shift.' 
    },
    { 
      id: 'PP9', 
      title: 'Scaling Method Comparison', 
      type: 'scale-compare', 
      check: 'Standard vs MinMax vs Robust scaling shape fit', 
      metric: 'Distribution shape consistency', 
      decision: 'Shows how scaling options behave. RobustScaler was selected to optimize outliers handling.' 
    },
    { 
      id: 'PP10', 
      title: 'Data Quality Improvement Scorecard', 
      type: 'quality-radar', 
      check: 'Overall dataset quality improvement', 
      metric: 'Overall quality score <70', 
      decision: 'Validates overall dataset health. Core quality score increased from 45 to 100, meaning data is now ML-ready.' 
    },
    { 
      id: 'PP11', 
      title: 'Problem Detection & Alert Dashboard', 
      type: 'alerts-dash', 
      check: 'Outliers, rare tags, and timing bottlenecks', 
      metric: 'Any critical warnings', 
      decision: 'Alerts you to issues encountered. 1 medium warning is present for sensor_3 outliers (2.1% clipped).', 
      flagged: true 
    }
  ];

  return (
    <div className="page-container">
      {/* Parameters row */}
      <div className="status-action-bar">
        <div className="status-bar-info">
          <div className="status-bar-icon-block" style={{ color: "#10b981", backgroundColor: "rgba(16, 185, 129, 0.1)" }}>
            <Sliders size={20} />
          </div>
          <div className="status-bar-details">
            <div className="status-bar-title-row">
              <span>dataset_preparation</span>
              <span className="status-run-badge">
                <CheckCircle size={12} style={{ color: '#10b981' }} /> Processed
              </span>
            </div>
            
            <div className="status-bar-parameters">
              <div className="param-item">
                <span>🧹 Columns Cleaned: </span>
                <span className="highlight-orange">6 / 6 Columns</span>
              </div>
              <span className="bullet-dot">•</span>
              <div className="param-item">
                <span>⚡ Row count: </span>
                <span className="highlight-green">482,901 rows</span>
              </div>
              <span className="bullet-dot">•</span>
              <div className="param-item">
                <span>⏱️ Execution: </span>
                <span className="highlight-blue">12.4s (Spark Engine)</span>
              </div>
            </div>
          </div>
        </div>
        
        <button className="proceed-cta-btn" onClick={onProceed}>
          Proceed to Feature Engineering <ArrowRight size={16} />
        </button>
      </div>

      {/* Info Callout */}
      <div className="info-callout-banner" style={{ backgroundColor: "#ecfdf5", borderColor: "#a7f3d0", color: "#065f46" }}>
        <Info size={16} className="info-banner-icon" />
        <div className="info-banner-text">
          <strong>Post-Prepare [Prepare] Dataset Explorer:</strong> Tracks columns modifications, imputations, scaling choices, and encoding maps. Inspect checked parameters and decision results below.
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
              <PostPrepareChartRenderer type={card.type} id={card.id} flagged={card.flagged} />
            </div>

            {/* Decision Rule Alert Box */}
            <div className={`viz-card-decision-box ${card.flagged ? 'flagged' : ''}`}>
              <div style={{ fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-muted)', marginBottom: '2px', fontWeight: 'bold' }}>
                {card.flagged ? '⚠️ Warning Action Rule' : '⚙️ Standard Action Rule'}
              </div>
              <div>
                <strong>Metric:</strong> {card.metric}. <br />
                <strong>Logic:</strong> {card.decision}
              </div>
            </div>

          </div>
        ))}
      </div>
    </div>
  );
}
