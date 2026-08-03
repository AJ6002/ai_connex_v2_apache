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
  Search,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';

// Reusable custom SVG Chart Renderer to guarantee uniform sizes (140px height) and distinct visualizations
function ChartRenderer({ type, id, flagged }) {
  const primaryColor = flagged ? '#ef4444' : '#1d4ed8';
  const secondaryColor = flagged ? '#fca5a5' : '#93c5fd';
  const accentColor = '#8b5cf6';
  
  switch (type) {
    case 'line':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          <defs>
            <linearGradient id={`grad-line-${id}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={primaryColor} stopOpacity="0.2"/>
              <stop offset="100%" stopColor={primaryColor} stopOpacity="0.0"/>
            </linearGradient>
          </defs>
          {/* Grid lines */}
          <line x1="20" y1="20" x2="280" y2="20" stroke="var(--border-light)" strokeWidth="0.5" strokeDasharray="3" />
          <line x1="20" y1="60" x2="280" y2="60" stroke="var(--border-light)" strokeWidth="0.5" strokeDasharray="3" />
          <line x1="20" y1="100" x2="280" y2="100" stroke="var(--border-light)" strokeWidth="0.5" strokeDasharray="3" />
          {/* Fill */}
          <path d={`M 20 100 Q 80 ${flagged ? 10 : 40} 140 ${flagged ? 90 : 70} T 280 ${flagged ? 10 : 50} L 280 100 L 20 100 Z`} fill={`url(#grad-line-${id})`} />
          {/* Stroke */}
          <path d={`M 20 100 Q 80 ${flagged ? 10 : 40} 140 ${flagged ? 90 : 70} T 280 ${flagged ? 10 : 50}`} fill="none" stroke={primaryColor} strokeWidth="2.5" />
          {/* Highlight Points */}
          <circle cx="140" cy={flagged ? 90 : 70} r="4" fill={primaryColor} />
          {flagged && <circle cx="280" cy="10" r="5" fill="#ef4444" className="animate-pulse" />}
        </svg>
      );

    case 'heatmap':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {Array.from({ length: 4 }).map((_, r) => 
            Array.from({ length: 8 }).map((_, c) => {
              const val = Math.sin(r * c + 1) * 0.5 + 0.5;
              const isCellFlagged = flagged && r === 2 && c === 4;
              return (
                <rect 
                  key={`${r}-${c}`}
                  x={20 + c * 32}
                  y={12 + r * 24}
                  width="28"
                  height="20"
                  rx="3"
                  fill={isCellFlagged ? '#ef4444' : primaryColor}
                  opacity={isCellFlagged ? 0.95 : Math.max(0.1, val)}
                  stroke={isCellFlagged ? '#fee2e2' : 'none'}
                  strokeWidth="1.5"
                />
              );
            })
          )}
        </svg>
      );

    case 'donut':
      const percentage = flagged ? 18 : 84;
      const radius = 35;
      const circumference = 2 * Math.PI * radius;
      const strokeDashoffset = circumference - (percentage / 100) * circumference;
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          <circle cx="150" cy="60" r={radius} fill="none" stroke="var(--border-medium)" strokeWidth="8" />
          <circle 
            cx="150" 
            cy="60" 
            r={radius} 
            fill="none" 
            stroke={primaryColor} 
            strokeWidth="8" 
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            transform="rotate(-90 150 60)"
          />
          <text x="150" y="66" textAnchor="middle" fill="var(--text-main)" fontSize="16" fontWeight="bold" fontFamily="var(--font-heading)">
            {percentage}%
          </text>
        </svg>
      );

    case 'bar':
      const bars = flagged ? [85, 92, 12, 74, 98, 110] : [70, 75, 82, 79, 88, 85];
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Threshold marker */}
          <line x1="20" y1="40" x2="280" y2="40" stroke="#f59e0b" strokeWidth="1" strokeDasharray="4" />
          {bars.map((h, i) => {
            const isBarFlagged = flagged && i === 2;
            return (
              <rect 
                key={i}
                x={25 + i * 42}
                y={110 - (h * 0.8)}
                width="24"
                height={h * 0.8}
                rx="3"
                fill={isBarFlagged ? '#ef4444' : primaryColor}
              />
            );
          })}
        </svg>
      );

    case 'scatter':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Grid background */}
          <line x1="20" y1="100" x2="280" y2="100" stroke="var(--border-light)" strokeWidth="0.5" />
          <line x1="20" y1="20" x2="20" y2="100" stroke="var(--border-light)" strokeWidth="0.5" />
          {/* Main cluster */}
          {Array.from({ length: 20 }).map((_, i) => {
            const x = 50 + (Math.cos(i) * 30) + (i * 8);
            const y = 60 + (Math.sin(i * 1.5) * 20);
            return <circle key={i} cx={x} cy={y} r="3.5" fill={primaryColor} opacity="0.6" />;
          })}
          {/* Flagged outlier dots */}
          {flagged && (
            <>
              <circle cx="260" cy="25" r="5" fill="#ef4444" />
              <line x1="260" y1="25" x2="210" y2="55" stroke="#ef4444" strokeWidth="1" strokeDasharray="2" />
              <text x="250" y="16" fill="#ef4444" fontSize="8" fontWeight="bold">Outlier</text>
            </>
          )}
        </svg>
      );

    case 'barcode':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {Array.from({ length: 48 }).map((_, i) => {
            const isMissing = flagged && (i > 18 && i < 24);
            return (
              <line 
                key={i}
                x1={20 + i * 5.5}
                y1="25"
                x2={20 + i * 5.5}
                y2="95"
                stroke={isMissing ? 'var(--border-light)' : primaryColor}
                strokeWidth={isMissing ? 0.5 : 2}
                opacity={isMissing ? 0.2 : 0.85}
              />
            );
          })}
          {flagged && (
            <rect x="120" y="20" width="36" height="80" fill="none" stroke="#ef4444" strokeWidth="1.5" strokeDasharray="3" rx="4" />
          )}
        </svg>
      );

    case 'gauge':
      const angle = flagged ? 140 : 45; // degree angle
      const rad = (angle - 180) * Math.PI / 180;
      const pointerX = 150 + 45 * Math.cos(rad);
      const pointerY = 90 + 45 * Math.sin(rad);
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Arc */}
          <path d="M 90 90 A 60 60 0 0 1 210 90" fill="none" stroke="var(--border-medium)" strokeWidth="12" strokeLinecap="round" />
          <path d={`M 90 90 A 60 60 0 0 1 ${150 + 60 * Math.cos(rad)} ${90 + 60 * Math.sin(rad)}`} fill="none" stroke={primaryColor} strokeWidth="12" strokeLinecap="round" />
          {/* Pointer */}
          <line x1="150" y1="90" x2={pointerX} y2={pointerY} stroke="var(--text-main)" strokeWidth="3" strokeLinecap="round" />
          <circle cx="150" cy="90" r="6" fill="var(--text-main)" />
        </svg>
      );

    case 'matrix':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {Array.from({ length: 3 }).map((_, r) => 
            Array.from({ length: 6 }).map((_, c) => {
              const isConflict = flagged && r === 1 && c === 3;
              return (
                <g key={`${r}-${c}`} transform={`translate(${30 + c * 40}, ${20 + r * 30})`}>
                  <rect width="32" height="22" rx="4" fill="var(--bg-card)" stroke="var(--border-medium)" strokeWidth="1" />
                  {isConflict ? (
                    <text x="16" y="16" textAnchor="middle" fill="#ef4444" fontSize="12" fontWeight="bold">⚠️</text>
                  ) : (
                    <circle cx="16" cy="11" r="3.5" fill="#10b981" />
                  )}
                </g>
              );
            })
          )}
        </svg>
      );

    case 'treemap':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Main big box */}
          <rect x="20" y="15" width="160" height="90" rx="4" fill={primaryColor} opacity="0.85" stroke="var(--bg-card)" strokeWidth="1.5" />
          <text x="30" y="35" fill="white" fontSize="11" fontWeight="bold">Feature_Set_A</text>
          <text x="30" y="55" fill="white" fontSize="10" opacity="0.8">{flagged ? '58% MB' : '65% MB'}</text>
          
          {/* Small boxes */}
          <rect x="185" y="15" width="95" height="42" rx="4" fill={secondaryColor} stroke="var(--bg-card)" strokeWidth="1.5" />
          <text x="192" y="32" fill="var(--text-main)" fontSize="9" fontWeight="bold">Feature_B</text>
          
          <rect x="185" y="60" width="50" height="45" rx="4" fill={accentColor} opacity="0.6" stroke="var(--bg-card)" strokeWidth="1.5" />
          <rect x="238" y="60" width="42" height="45" rx="4" fill={flagged ? '#f87171' : secondaryColor} opacity="0.8" stroke="var(--bg-card)" strokeWidth="1.5" />
        </svg>
      );

    case 'waterfall':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Increments and decrements cascading */}
          <rect x="20" y="20" width="30" height="80" fill="#1d4ed8" rx="2" />
          <rect x="60" y="20" width="30" height="20" fill="#10b981" rx="2" />
          <line x1="50" y1="20" x2="60" y2="20" stroke="var(--text-muted)" strokeWidth="1" strokeDasharray="2" />
          
          <rect x="100" y="40" width="30" height="30" fill="#10b981" rx="2" />
          <line x1="90" y1="40" x2="100" y2="40" stroke="var(--text-muted)" strokeWidth="1" strokeDasharray="2" />
          
          <rect x="140" y="70" width="30" height="25" fill="#ef4444" rx="2" />
          <line x1="130" y1="70" x2="140" y2="70" stroke="var(--text-muted)" strokeWidth="1" strokeDasharray="2" />
          
          <rect x="180" y="95" width="30" height="15" fill={flagged ? '#ef4444' : '#1d4ed8'} rx="2" />
          <line x1="170" y1="95" x2="180" y2="95" stroke="var(--text-muted)" strokeWidth="1" strokeDasharray="2" />
        </svg>
      );

    case 'kde':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Curve 1: Baseline */}
          <path d="M 20 100 C 60 100, 100 15, 140 15 C 180 15, 220 100, 280 100" fill="none" stroke="var(--border-medium)" strokeWidth="2" />
          {/* Curve 2: Shifted */}
          <path 
            d={`M 20 100 C 70 100, 120 ${flagged ? 45 : 20}, 160 ${flagged ? 45 : 20} C 200 ${flagged ? 45 : 20}, 240 100, 280 100`} 
            fill="none" 
            stroke={primaryColor} 
            strokeWidth="2.5" 
          />
          {flagged && (
            <path d="M 140 15 L 160 45" stroke="#ef4444" strokeWidth="1.5" strokeDasharray="3" markerEnd="url(#arrow)" />
          )}
        </svg>
      );

    case 'box':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Whisker line */}
          <line x1="40" y1="60" x2="250" y2="60" stroke="var(--text-main)" strokeWidth="1.5" />
          <line x1="40" y1="45" x2="40" y2="75" stroke="var(--text-main)" strokeWidth="1.5" />
          <line x1="250" y1="45" x2="250" y2="75" stroke="var(--text-main)" strokeWidth="1.5" />
          
          {/* Box */}
          <rect x="90" y="35" width="100" height="50" fill={secondaryColor} stroke="var(--text-main)" strokeWidth="1.5" rx="3" />
          <line x1="140" y1="35" x2="140" y2="85" stroke={primaryColor} strokeWidth="3" />
          
          {/* Outliers */}
          <circle cx="20" cy="60" r="3" fill="#ef4444" />
          <circle cx="270" cy="60" r="3" fill="#ef4444" />
          {flagged && (
            <>
              <circle cx="285" cy="60" r="3" fill="#ef4444" />
              <circle cx="292" cy="60" r="3.5" fill="#ef4444" />
            </>
          )}
        </svg>
      );

    case 'radar':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          <g transform="translate(150, 60)">
            {/* Hexagon lines */}
            <polygon points="0,-45 39,-22.5 39,22.5 0,45 -39,22.5 -39,-22.5" fill="none" stroke="var(--border-medium)" strokeWidth="1" />
            <polygon points="0,-25 21,-12.5 21,12.5 0,25 -21,12.5 -21,-12.5" fill="none" stroke="var(--border-light)" strokeWidth="0.5" />
            {/* Radar shape */}
            <polygon 
              points={flagged 
                ? "0,-42 35,-15 15,10 0,40 -35,5 -10,-20"
                : "0,-30 30,-18 25,18 0,32 -25,18 -20,-18"
              } 
              fill={primaryColor} 
              fillOpacity="0.4" 
              stroke={primaryColor} 
              strokeWidth="2" 
            />
          </g>
        </svg>
      );

    case 'sankey':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Left blocks */}
          <rect x="20" y="20" width="15" height="30" fill={primaryColor} rx="2" />
          <rect x="20" y="65" width="15" height="35" fill={accentColor} rx="2" />
          
          {/* Paths */}
          <path d={`M 35 35 C 100 35, 120 ${flagged ? 85 : 55}, 180 ${flagged ? 85 : 55}`} fill="none" stroke={primaryColor} strokeWidth="8" opacity="0.35" />
          <path d="M 35 80 C 100 80, 120 45, 180 45" fill="none" stroke={accentColor} strokeWidth="12" opacity="0.35" />
          
          {/* Right blocks */}
          <rect x="180" y="30" width="15" height="25" fill={accentColor} rx="2" />
          <rect x="180" y="65" width="15" height="30" fill={primaryColor} rx="2" />
        </svg>
      );

    case 'tree':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Root node */}
          <rect x="135" y="15" width="30" height="15" rx="3" fill="var(--text-main)" />
          {/* Branches */}
          <line x1="150" y1="30" x2="90" y2="55" stroke="var(--border-medium)" strokeWidth="1.5" />
          <line x1="150" y1="30" x2="210" y2="55" stroke="var(--border-medium)" strokeWidth="1.5" />
          
          {/* Level 1 nodes */}
          <rect x="75" y="55" width="30" height="15" rx="3" fill={primaryColor} />
          <rect x="195" y="55" width="30" height="15" rx="3" fill={secondaryColor} />
          
          <line x1="90" y1="70" x2="60" y2="95" stroke="var(--border-medium)" strokeWidth="1" />
          <line x1="90" y1="70" x2="120" y2="95" stroke="var(--border-medium)" strokeWidth="1" />
          
          {/* Level 2 nodes */}
          <rect x="45" y="95" width="30" height="15" rx="3" fill={flagged ? '#ef4444' : secondaryColor} />
          <rect x="105" y="95" width="30" height="15" rx="3" fill="#10b981" />
        </svg>
      );

    case 'gantt':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Grid lines */}
          <line x1="60" y1="20" x2="60" y2="100" stroke="var(--border-light)" strokeWidth="0.5" />
          <line x1="130" y1="20" x2="130" y2="100" stroke="var(--border-light)" strokeWidth="0.5" />
          <line x1="200" y1="20" x2="200" y2="100" stroke="var(--border-light)" strokeWidth="0.5" />
          
          {/* Gantt Tasks */}
          <rect x="30" y="25" width="70" height="14" rx="4" fill={primaryColor} />
          <rect x="90" y="50" width={flagged ? 130 : 80} height="14" rx="4" fill={flagged ? '#ef4444' : accentColor} />
          <rect x="160" y="75" width="90" height="14" rx="4" fill="#10b981" />
        </svg>
      );

    case 'calendar':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Small 3x10 grid matrix representing calendar days */}
          {Array.from({ length: 3 }).map((_, r) => 
            Array.from({ length: 12 }).map((_, c) => {
              const isDark = (r + c) % 3 === 0;
              const isHighlight = flagged && r === 1 && c === 8;
              return (
                <rect 
                  key={`${r}-${c}`}
                  x={24 + c * 21}
                  y={25 + r * 22}
                  width="16"
                  height="16"
                  rx="3"
                  fill={isHighlight ? '#ef4444' : (isDark ? primaryColor : 'var(--border-medium)')}
                  opacity={isHighlight ? 1.0 : (isDark ? 0.75 : 0.3)}
                />
              );
            })
          )}
        </svg>
      );

    case 'parallel':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Vertical axes */}
          <line x1="50" y1="20" x2="50" y2="100" stroke="var(--text-muted)" strokeWidth="1.5" />
          <line x1="150" y1="20" x2="150" y2="100" stroke="var(--text-muted)" strokeWidth="1.5" />
          <line x1="250" y1="20" x2="250" y2="100" stroke="var(--text-muted)" strokeWidth="1.5" />
          
          {/* Data Lines */}
          <path d={`M 50 40 L 150 ${flagged ? 90 : 50} L 250 30`} fill="none" stroke={primaryColor} strokeWidth="2.5" opacity="0.9" />
          <path d="M 50 80 L 150 30 L 250 80" fill="none" stroke={accentColor} strokeWidth="1.5" opacity="0.6" />
          <path d="M 50 60 L 150 70 L 250 50" fill="none" stroke="#10b981" strokeWidth="1.5" opacity="0.6" />
        </svg>
      );

    case 'graph':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Connection edges */}
          <line x1="60" y1="60" x2="130" y2="30" stroke="var(--text-muted)" strokeWidth="1.5" />
          <line x1="60" y1="60" x2="130" y2="90" stroke="var(--text-muted)" strokeWidth="1.5" />
          <line x1="130" y1="30" x2="220" y2="60" stroke={primaryColor} strokeWidth="2.5" />
          <line x1="130" y1="90" x2="220" y2="60" stroke="var(--text-muted)" strokeWidth="1.5" />
          
          {/* Node circles */}
          <circle cx="60" cy="60" r="10" fill="var(--text-main)" />
          <circle cx="130" cy="30" r="10" fill={accentColor} />
          <circle cx="130" cy="90" r="10" fill={primaryColor} />
          <circle cx="220" cy="60" r={flagged ? 12 : 10} fill={flagged ? '#ef4444' : '#10b981'} />
        </svg>
      );

    case 'diff':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Rect representing text editor container */}
          <rect x="15" y="10" width="270" height="100" fill="var(--bg-card)" stroke="var(--border-medium)" strokeWidth="1" rx="4" />
          {/* Highlight deletions/additions */}
          <rect x="20" y="25" width="260" height="18" fill="#fee2e2" opacity="0.9" />
          <rect x="20" y="47" width="260" height="18" fill="#dcfce7" opacity="0.9" />
          {/* Code text lines */}
          <text x="30" y="37" fill="#b91c1c" fontSize="9" fontFamily="var(--font-mono)">- "impute_strategy": "mean"</text>
          <text x="30" y="60" fill="#15803d" fontSize="9" fontFamily="var(--font-mono)">+ "impute_strategy": "median"</text>
          <text x="30" y="82" fill="var(--text-muted)" fontSize="9" fontFamily="var(--font-mono)">  "oversample": "SMOTE"</text>
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

export default function PrePrepare({ onProceed }) {
  const [activeCategory, setActiveCategory] = useState('compiler');

  // Categories definitions
  const categories = [
    { id: 'compiler', label: '⚙️ Compiler', count: 10 },
    { id: 'profiler', label: '📊 Data Profiler', count: 15 },
    { id: 'orchestrator', label: '🕸️ Orchestrator', count: 15 },
    { id: 'recipe', label: '🧪 Recipe', count: 15 },
    { id: 'cross-component', label: '🔍 Cross-Component', count: 15 }
  ];

  // Visualizations Dictionary covering all 65 cards
  const visualizations = {
    compiler: [
      { id: 'C1', title: 'File Merge Trace', type: 'line', check: 'Row count per merged file', metric: 'Individual file row count vs. expected range', decision: 'Verify row boundaries per file stream. Flags files that are smaller than 100 rows or exceed 3x normal average.', techDecision: 'Check shape boundary offsets on pd.concat. Outlier trigger threshold: count < 100 || count > 3 * mean_count.' },
      { id: 'C2', title: 'Schema Consistency Heatmap', type: 'heatmap', check: 'Column presence across all files', metric: 'Column coverage % per file', decision: 'Highlights missing table columns. Warns if more than 2 critical inputs are missing.', techDecision: 'Check null column schema indexes. Flag schema drift if missing columns threshold > 2 count.' },
      { id: 'C3', title: 'Data Type Distribution Donut', type: 'donut', check: '% of int, float, string, date, bool', metric: 'Type ratio change >15% from typical', decision: 'Checks data parsing consistency. Flags warnings if text/string types increase by more than 20%.', techDecision: 'Check parser dtype allocations. Alert if string type percentage delta > 20% compared to metadata baseline.' },
      { id: 'C4', title: 'Row Count Timeline', type: 'bar', check: 'Row count stability across files', metric: 'Coefficient of Variation (CV) of row counts', decision: 'Monitors file size stability. Triggers warning if volume variability coefficient is high (CV > 0.5).', techDecision: 'Validate row count variations. Trigger warning if standard deviation / mean (CV) > 0.5 bounds.', flagged: true },
      { id: 'C5', title: 'File Size vs. Row Count Scatter', type: 'scatter', check: 'Data density (MB per row)', metric: 'Density outliers >2 standard deviations', decision: 'Checks data density. Highlights entries exceeding 2 standard deviations indicating potential corrupted binary streams.', techDecision: 'Evaluate MB/row density. Flags outlier observations falling outside 2 sigma boundaries (density > 2σ).' },
      { id: 'C6', title: 'Column Co-occurrence Barcode', type: 'barcode', check: 'Which columns appear in which files', metric: 'Column presence pattern matrix', decision: 'Highlights files missing specific columns entirely. A gap in the stripe indicates structure mismatches.', techDecision: 'Check structural barcodes. Flag empty vertical slice denoting column indices omitted from compiler buffer.' },
      { id: 'C7', title: 'Duplicate Row Count', type: 'donut', check: '% of duplicate rows', metric: 'Duplicate percentage >5%', decision: 'Flags when identical rows are compiled. Over 5% duplicates triggers deduplication scripts.', techDecision: 'Check row hashing caches. Triggers warning if duplicate ratio is greater than 0.05 index.', flagged: true },
      { id: 'C8', title: 'Compilation Duration Gauge', type: 'gauge', check: 'Time taken to compile (seconds)', metric: 'Duration > historical avg + 2x std dev', decision: 'Monitors processing speed. Slow compilation triggers storage pipeline disk performance alerts.', techDecision: 'Duration validation. Trigger slow disk alerts if ingestion compile speed > historical_mean + 2 * std_dev.' },
      { id: 'C9', title: 'Column Type Conflict Detector', type: 'matrix', check: 'Same column, different data types across files', metric: 'Number of type conflicts per column', decision: 'Identifies columns parsed with different types across files. Automatically coercing is recommended.', techDecision: 'Detect mismatched parser schemas. Type casting conflict detected if columns match with distinct dtype keys.' },
      { id: 'C10', title: 'Memory Footprint Treemap', type: 'treemap', check: 'Memory usage per data type/column', metric: 'Object/Datetime columns memory %', decision: 'Identifies memory heavy columns. Highlights text columns exceeding 30% of total memory to recommend schema casting.', techDecision: 'Trace memory usage. Trigger memory alerts if string/object columns consume > 30% of memory footprint.' }
    ],
    profiler: [
      { id: 'P1', title: 'Feature Distribution Overlay', type: 'kde', check: 'Distribution shift per feature', metric: 'Kolmogorov-Smirnov (KS) statistic', decision: 'Traces changes in data behavior. Significant shifts flag potential training data drift.', techDecision: 'Calculate KS distribution shift. Trigger model warning if KS p-value < 0.05 index bounds.' },
      { id: 'P2', title: 'Null Value Waterfall', type: 'waterfall', check: 'Missing value % change per column', metric: 'Missing % change >10% from baseline', decision: 'Tracks missing values count. Flags issues if null percentage rises above 10%.', techDecision: 'Check missing values trend. Trigger quality gate warnings if null increase delta > 10%.' },
      { id: 'P3', title: 'Feature Correlation Shift', type: 'heatmap', check: 'Correlation change between features', metric: 'Correlation delta >0.3', decision: 'Monitors relationships between columns. Flags warnings if correlation shifts by more than 0.3.', techDecision: 'Check correlation matrix shifts. Warning triggered if Pearson coefficient delta exceeds 0.3.' },
      { id: 'P4', title: 'Target Distribution KDE', type: 'kde', check: 'Target variable distribution shift', metric: 'Overlap coefficient <0.7', decision: 'Traces concept drift. Warns if overlap of target class distribution drops below 70%.', techDecision: 'Target variable shift assessment. Trigger alert if overlap coefficient is less than 0.7.' },
      { id: 'P5', title: 'Outlier Density Timeline', type: 'box', check: 'Outlier % per batch', metric: 'Outlier % >1% of dataset', decision: 'Identifies anomaly density. High outlier density (>1%) shifts recommendation to robust models.', techDecision: 'Verify dataset outlier density. Flag robust algorithm variant if outlier observations > 1.0%.', flagged: true },
      { id: 'P6', title: 'Categorical Frequency Change', type: 'bar', check: 'Category distribution shift', metric: 'Chi-square test p-value <0.05', decision: 'Identifies category distribution changes. Shift flags population drift.', techDecision: 'Check categorical frequency. Flag drift warning if Chi-square test p-value is less than 0.05.' },
      { id: 'P7', title: 'Feature Importance Radar', type: 'radar', check: 'Top 10 features SHAP importance', metric: 'Importance change >0.05', decision: 'Checks features contribution value. Retraining needed if primary feature values drop > 5%.', techDecision: 'Monitor SHAP values. Retrain warning is triggered if SHAP feature delta > 0.05 index.' },
      { id: 'P8', title: 'Sparsity Detection Matrix', type: 'heatmap', check: '% of zero values per feature', metric: 'Sparsity ratio >60%', decision: 'Flags columns with sparse/zero values. Over 60% zeros routes flow to Sparse models.', techDecision: 'Check sparsity metrics. Zero-count threshold check triggers Sparse pathing if zeros ratio > 60%.' },
      { id: 'P9', title: 'Skewness Diagnostic', type: 'bar', check: 'Skewness value per numeric feature', metric: 'Skewness >|1.5|', decision: 'Identifies skewed columns. Highly skewed values (>1.5) trigger log transformations recommendations.', techDecision: 'Calculate distribution skewness. Recommend log/sqrt scaling if skewness coefficient > |1.5|.' },
      { id: 'P10', title: 'Memory Footprint Treemap', type: 'treemap', check: 'Memory usage per column/feature', metric: 'Object column memory >40% total', decision: 'Monitors memory efficiency. Advises downcasting numeric formats if text columns exceed 40% memory.', techDecision: 'Check schema optimization bounds. Downcast features if object category footprint > 40%.' },
      { id: 'P11', title: 'IQR Outlier Detector', type: 'box', check: 'IQR range and whisker outliers', metric: 'Outliers >1.5x IQR', decision: 'Checks interquartile ranges. Outliers > 1% trigger RobustScaler scaling recommendation.', techDecision: 'IQR boundary analysis. Recommend RobustScaler optimization if outlier ratio is greater than 1%.' },
      { id: 'P12', title: 'VIF Collinearity Heatmap', type: 'heatmap', check: 'Variance Inflation Factor per feature', metric: 'VIF >10', checkText: 'Multi-collinearity checks', decision: 'Checks for overlapping features. Highly collinear variables (VIF > 10) trigger reduction or PCA paths.', techDecision: 'Evaluate VIF coefficients. High collinearity alert triggered if VIF metric exceeds 10.', flagged: true },
      { id: 'P13', title: 'Target Class Imbalance', type: 'donut', check: 'Minority class percentage', metric: 'Minority class <20%', decision: 'Identifies class imbalances. Target class below 20% triggers SMOTE balancing algorithms.', techDecision: 'Check classification splits. Trigger class balance pipelines if minority class count < 20%.' },
      { id: 'P14', title: 'Data Type Conversion Tracker', type: 'sankey', check: 'Original → New data type mapping', metric: 'Conversion success rate <95%', decision: 'Tracks data coercion issues. Conversions below 95% highlight potential cleaning bugs.', techDecision: 'Type validation checks. Warning flags if successful type conversion rate < 95%.' },
      { id: 'P15', title: 'DAG Recommendation Tree', type: 'tree', check: 'Decision path to recommended DAG', metric: 'All previous conditions combined', decision: 'Traces recommendations criteria. Shows why a specific DAG flow was chosen.', techDecision: 'Tree traversal verification. Renders decision tree paths leading to recommendation configurations.' }
    ],
    orchestrator: [
      { id: 'O1', title: 'Pipeline Status Gantt', type: 'gantt', check: 'Step completion times (Compile → Train)', metric: 'Any step duration >3x average', decision: 'Traces time bottlenecks. Flag warnings if any steps take over 3x historical averages.', techDecision: 'Gantt execution duration tracker. Alert if component duration > 3 * mean_duration.' },
      { id: 'O2', title: 'Hyperparameter Change Radar', type: 'radar', check: 'Hyperparameter values (old vs. current)', metric: 'Value change >20%', decision: 'Tracks parameter modification history. Investigates why hyperparameters drifted by >20%.', techDecision: 'Hyperparameter tuning delta checks. Alert if parameter values shift by > 20%.' },
      { id: 'O3', title: 'Recipe Override Heatmap', type: 'heatmap', check: 'Default vs. Override per recipe setting', metric: 'Override count >3 per recipe', decision: 'Flags manual recipe deviations. Overrides exceeding 3 risk template reproducibility.', techDecision: 'Check customization overrides. Warnings triggered if count > 3 overrides.' },
      { id: 'O4', title: 'Quality Gate Boundary Scatter', type: 'scatter', check: 'Metric vs. Gate limits (RMSE, R², MAE)', metric: 'Metric within [min, max] limits', decision: 'Verifies performance thresholds. Values falling outside gates fail the pipeline validation.', techDecision: 'Validate quality gates. Pipeline status sets to FAILED if performance metrics breach threshold bounds.' },
      { id: 'O5', title: 'DAG Selection Evolution', type: 'sankey', check: 'DAG ID transitions across runs', metric: 'DAG change frequency >30% of runs', decision: 'Tracks stability of selected models. Frequent model swaps point to potential data volatility.', techDecision: 'Monitor selection transitions. Flag unstable model pathing if change frequency > 30%.' },
      { id: 'O6', title: 'Schema Validation Matrix', type: 'matrix', check: 'Required columns presence', metric: 'All required columns present', decision: 'Checks schema requirements. Missing columns break contract interfaces immediately.', techDecision: 'DataFrame schema contract validation. Flag errors if any required columns are omitted.' },
      { id: 'O7', title: 'Feature Engineering Impact', type: 'parallel', check: 'Raw features → Engineered features', metric: 'Transformation type distribution', decision: 'Tracks raw-to-engineered flow. Visualizes feature additions and their scaling impacts.', techDecision: 'Coordinate map of feature scaling. Displays transformation pipeline stages and output distributions.' },
      { id: 'O8', title: 'Run Comparison Dashboard', type: 'radar', check: 'Performance metrics across runs', metric: 'Metric variance >15%', decision: 'Compares current run to history. High variance (>15%) flags warnings for model instability.', techDecision: 'Perform statistical comparisons across runs. Alert if performance variance > 15%.', flagged: true },
      { id: 'O9', title: 'File Dependency Graph', type: 'graph', check: 'File → Recipe → Output dependencies', metric: 'Missing file count >0', decision: 'Traces file pipeline dependency flows. Missing inputs break task execution paths.', techDecision: 'Check task dependency paths. Omit nodes if source files count < 1.' },
      { id: 'O10', title: 'Split Ratio Diagram', type: 'donut', check: 'Train/Val/Test split percentages', metric: 'Train size >90% or <60%', decision: 'Validates validation ratios. Train ratios exceeding 90% or under 60% risk overfitting.', techDecision: 'Check split partitions. Warn on skewness if train split falls outside [60%, 90%] limits.' },
      { id: 'O11', title: 'Execution Timeline', type: 'bar', check: 'Time spent per pipeline step', metric: 'Step time vs. SLA threshold', decision: 'Monitors timeline performance. Steps exceeding SLA limits require optimization.', techDecision: 'Evaluate SLA timing benchmarks. Warnings flagged if step execution time > SLA_limit.' },
      { id: 'O12', title: 'Data Topology Validator', type: 'matrix', check: 'Tabular, Sequence, Image, Text', metric: 'Topology mismatch', decision: 'Validates dataset structure matching algorithms. Mismatches abort pipeline runs.', techDecision: 'Verify structure matching. Abort run if data topology is incompatible with model requirements.' },
      { id: 'O13', title: 'Entity/Timestamp Coverage', type: 'calendar', check: 'Date range and entity coverage', metric: 'Missing dates >5%', decision: 'Tracks temporal gaps in source data. Over 5% missing dates can cause training errors.', techDecision: 'Check datetime indexes. Alert if missing date index ratios exceed 5%.' },
      { id: 'O14', title: 'Resource Utilization', type: 'line', check: 'CPU/Memory over time', metric: 'Resource usage >80% for extended period', decision: 'Monitors host compute capacity. Prolonged utilization (>80%) flags server load warnings.', techDecision: 'Track system metrics. Alert if compute resources exceed 80% capacity constraints.' },
      { id: 'O15', title: 'Run-to-Run Delta', type: 'diff', check: 'What changed from previous run', metric: 'Any schema, hyperparameter, recipe change', decision: 'Shows modifications at a glance. Easily review what changed from the previous pipeline run.', techDecision: 'Execute JSON diff parser on configs. Display additions, deletions, and updates.' }
    ],
    recipe: [
      { id: 'R1', title: 'Parameter Delta Matrix', type: 'heatmap', check: 'Old → New parameter values', metric: 'Parameter change >20%', decision: 'Monitors custom parameter variations. Shifts exceeding 20% warrant manual review.', techDecision: 'Check parameter changes. Alert if parameter values shift by > 20%.' },
      { id: 'R2', title: 'Preprocessing Flowchart', type: 'sankey', check: 'Raw → Impute → Scale → Encode → Output', metric: 'Step sequence and order', decision: 'Traces steps sequence logic. Skipping scaling or encoding stages flags validation errors.', techDecision: 'Preprocessing graph validation. Warning flags if core transformation sequences are bypassed.' },
      { id: 'R3', title: 'Algorithm Performance Scatter', type: 'scatter', check: 'Accuracy vs. Speed per algorithm variant', metric: 'Pareto frontier selection', decision: 'Balances accuracy vs speed. Visualizes chosen models on the pareto frontier.', techDecision: 'Pareto efficiency calculation. Model selected based on the accuracy vs speed tradeoff.' },
      { id: 'R4', title: 'Hyperparameter Tuning Trace', type: 'line', check: 'Metric improvement over tuning iterations', metric: 'Flat line for >20 iterations', decision: 'Monitors model optimization curves. Flat performance over 20 iterations triggers early stopping.', techDecision: 'Tuning curve optimization. Trigger early stopping if validation metric variance < threshold.' },
      { id: 'R5', title: 'Recipe Source Treemap', type: 'treemap', check: '% from Default, User, Auto, System', metric: 'User override >40%', decision: 'Checks custom overrides ratios. High customizations (>40%) may impact maintenance.', techDecision: 'Check overrides statistics. Alert if manual configs exceed 40% of standard blueprints.' },
      { id: 'R6', title: 'Imputation Impact Violin', type: 'box', check: 'Distribution before/after imputation', metric: 'Shape change >30%', decision: 'Assesses imputation skew risks. Drastic shape changes (>30%) indicate bias risks.', techDecision: 'Imputation distribution check. Warning triggers if shape skewness shift > 30%.' },
      { id: 'R7', title: 'Scaling Q-Q Plot', type: 'scatter', check: 'Original vs. Scaled distribution', metric: 'Points off diagonal', decision: 'Checks data scaling linearity. Deviation from diagonal indicates scaling errors.', techDecision: 'Normal Q-Q scaling check. Alert flags if residuals drift from normal diagonal lines.' },
      { id: 'R8', title: 'Feature Selection Stability', type: 'line', check: 'Feature coefficients across runs', metric: 'Coefficient variance >0.5', decision: 'Tracks feature coefficient shifts. High variance indicates model parameter instability.', techDecision: 'Evaluate feature stability index. Alert if coefficient variance exceeds 0.5.' },
      { id: 'R9', title: 'Early Stopping Learning Curve', type: 'line', check: 'Train/Val loss with stopping point', metric: 'Gap between train/val >15%', decision: 'Tracks train vs validation curves. Large separation gaps (>15%) flag overfitting warnings.', techDecision: 'Learning curve convergence validation. Trigger overfitting alert if validation gap > 15%.', flagged: true },
      { id: 'R10', title: 'Recipe Diff Viewer', type: 'diff', check: 'Added, Removed, Modified keys', metric: 'Any key modified', decision: 'Shows modifications at a glance. Pinpoint exact key value updates.', techDecision: 'Evaluate blueprint diff trees. Identifies parameter changes in active models.' },
      { id: 'R11', title: 'Cross-Validation Fold Performance', type: 'box', check: 'CV scores per fold', metric: 'CV variance >10%', decision: 'Validates fold consistency. High score variance (>10%) signals model instability.', techDecision: 'Check validation fold variances. Alert if cross-validation scores variance > 10%.' },
      { id: 'R12', title: 'Feature Importance Bar', type: 'bar', check: 'Top 20 feature importances', metric: 'Cumulative importance of top 5 >80%', decision: 'Identifies feature dominance. Top 5 features holding >80% weight suggest simplifying feature counts.', techDecision: 'SHAP value aggregation. Flags feature reductions if top 5 hold > 80% total weight.' },
      { id: 'R13', title: 'Confusion Matrix Heatmap', type: 'heatmap', check: 'Actual vs. Predicted classes', metric: 'Any off-diagonal >20%', decision: 'Identifies misclassification patterns. Over 20% off-diagonal flags class-weight needs.', techDecision: 'Analyze classification grids. Trigger warning if error rates exceed 20%.' },
      { id: 'R14', title: 'Residuals vs. Fitted', type: 'scatter', check: 'Residual distribution vs. Predicted', metric: 'Residual pattern (funnel shape)', decision: 'Checks for error biases. Funnel distributions highlight model variance errors.', techDecision: 'Check heteroscedasticity metrics. Alert if residuals distribution displays funnel patterns.' },
      { id: 'R15', title: 'Recipe Version Timeline', type: 'line', check: 'Recipe changes over version history', metric: 'Number of changes per version', decision: 'Traces configuration modifications timeline. Frequent modifications flag volatile requirements.', techDecision: 'Track blueprint modifications history. Alert if changes frequency > threshold.' }
    ],
    'cross-component': [
      { id: 'CC1', title: 'Change Impact Sankey', type: 'sankey', check: 'Data Change → Profile → Orchestrator → Recipe', metric: 'Cascading change count', decision: 'Traces cascading shifts across all four pipeline steps. Connects data edits to model results.', techDecision: 'Trace pipeline propagation pathways. Logs cascading component revisions.' },
      { id: 'CC2', title: 'Data Quality Scorecard', type: 'gauge', check: 'Overall data quality (0-100)', metric: 'Score <70 → Red', decision: 'Evaluates global dataset health. Combined metrics dropping under 70 triggers compilation audits.', techDecision: 'Consolidate pipeline quality stats. Flag warning status if combined score < 70.' },
      { id: 'CC3', title: 'DAG Selection Drift Timeline', type: 'gantt', check: 'DAG changes over time', metric: 'DAG changes >1/3 runs', decision: 'Tracks the stability of recommended model pipelines. Swapping recommended models more than 33% indicates volatility.', techDecision: 'Calculate run-to-run recommendation swaps. Warning triggered if variance exceeds 0.33.', flagged: true },
      { id: 'CC4', title: 'Compiler-Profiler Consistency', type: 'bar', check: 'Compiled data vs Profiler data integrity', metric: 'Δ >5%', decision: 'Validates that compiled records align with profiling shapes. Discrepancies >5% report corruption.', techDecision: 'DataFrame rows consistency validation. Trigger critical audit alert if delta > 0.05.' },
      { id: 'CC5', title: 'DAG Recommendation Confidence', type: 'donut', check: 'Selected DAG probability score', metric: 'Confidence <70%', decision: 'Tracks how confident the system is in its DAG decision. Low confidence (<70%) requires manual approval.', techDecision: 'Classifier softmax class probability score. Warn if confidence < 0.70 bounds.' },
      { id: 'CC6', title: 'Model Decay Curve', type: 'line', check: 'Model performance over time', metric: 'Performance drop >10%', decision: 'Monitors accuracy levels over long-term operations. Drops >10% flag immediate retrain gates.', techDecision: 'Model evaluation degradation metrics. Retrain warning is triggered if metric decay > 10%.' },
      { id: 'CC7', title: 'Drift Dashboard', type: 'gauge', check: 'All drift metrics (KS, PSI, Overlap)', metric: 'PSI >0.2 (Population Stability Index)', decision: 'Traces feature statistical shifts over operational periods. PSI >0.2 alerts that models require updates.', techDecision: 'Drift index validation. Retraining alert triggered if PSI value exceeds 0.2.', flagged: true },
      { id: 'CC8', title: 'Quality Gate Violation History', type: 'calendar', check: 'Rule gate checks across runs', metric: 'Any violation', decision: 'Logs historic validation pass results. Any rule violations break quality pipeline release gates.', techDecision: 'Trace historical quality violations logs. Trigger fails on breach counts > 0.' },
      { id: 'CC9', title: 'Pipeline Execution Time Trend', type: 'bar', check: 'Total duration shifts', metric: '>30% increase', decision: 'Monitors overall run durations. Time increases >30% flag disk/CPU optimization bottlenecks.', techDecision: 'Timing drift validation metrics. Warn if total duration > 1.3 * historical_mean.' },
      { id: 'CC10', title: 'Feature Evolution Tracker', type: 'parallel', check: 'SHAP rank fluctuations', metric: 'Any new/removed feature', decision: 'Tracks important features dropping from model matrices. Identifies structural variable drifts.', techDecision: 'Evaluate active columns delta. Trigger retraining checks if feature set updates.' },
      { id: 'CC11', title: 'Recipe Override Impact Analysis', type: 'scatter', check: 'Accuracy delta from user overrides', metric: 'Δ >5%', decision: 'Compares customized models against template baselines. Overrides should improve validation scores by >5%.', techDecision: 'Compute performance improvement offset. Highlight redundant config if custom delta < 0.05.' },
      { id: 'CC12', title: 'Recipe Stability Index', type: 'line', check: '% default settings over runs', metric: 'Default % <60%', decision: 'Monitors customization ratios. Custom configurations exceeding 40% risk template reproducibility.', techDecision: 'Trace configuration variance factors. Alert if default configuration ratios < 60%.' },
      { id: 'CC13', title: 'Schema Change Impact Assessment', type: 'diff', check: 'Columns insertions/removals', metric: 'Breaking changes', decision: 'Audits structural database schema revisions. Red alerts identify modifications that disrupt recipes.', techDecision: 'Check structural columns contract validations. Alert on breaking changes.' },
      { id: 'CC14', title: 'Failure Pattern Analysis', type: 'matrix', check: 'Failure correlation coefficients', metric: '>2 failures/component', decision: 'Identifies fragile modules. Components failing >2 times suggest local code integration defects.', techDecision: 'Track component exception records. Trigger alert if failure counts > 2.', flagged: true },
      { id: 'CC15', title: 'Data Volume vs. Complexity', type: 'scatter', check: 'Dataset size vs DAG depth', metric: 'Correlation >0.7', decision: 'Checks pipeline scaling. Correlations >0.7 indicate models are growing too complex relative to data sizes.', techDecision: 'Compute Pearson correlation coefficients (Volume vs DAG). Warn if correlation > 0.70.' }
    ]
  };

  const getActiveCards = () => {
    return visualizations[activeCategory] || [];
  };

  return (
    <div className="page-container">
      {/* Sensor Readings Alert Bar */}
      <div className="status-action-bar">
        <div className="status-bar-info">
          <div className="status-bar-icon-block">
            <Workflow size={20} />
          </div>
          <div className="status-bar-details">
            <div className="status-bar-title-row">
              <span>sensor_readings</span>
              <span className="status-run-badge">
                <GitCommit size={12} /> Run: active
              </span>
            </div>
            
            <div className="status-bar-parameters">
              <div className="param-item">
                <span>🪄 Decisive Parameter: </span>
                <span className="highlight-orange">DAG_201 (One-class SVM | Standard)</span>
              </div>
              <span className="bullet-dot">•</span>
              <div className="param-item">
                <span>📈 Loss: </span>
                <span className="highlight-green">0.42</span>
              </div>
              <span className="bullet-dot">•</span>
              <div className="param-item">
                <span>⚙️ Trigger: </span>
                <span className="highlight-blue">Outlier Density &gt; 1.5%</span>
              </div>
            </div>
          </div>
        </div>
        
        <button className="proceed-cta-btn" onClick={onProceed}>
          Proceed to Preparation <ArrowRight size={16} />
        </button>
      </div>

      {/* Info Callout Banner */}
      <div className="info-callout-banner">
        <Info size={16} className="info-banner-icon" />
        <div className="info-banner-text">
          <strong>Pre-Prepare [Brain] Dataset Explorer:</strong> Traces data pipeline diagnostics across 5 segments. Switch category sub-tabs below to inspect checked parameters, visualizations, and custom decision rules.
        </div>
      </div>

      {/* Categories Nested Tabs Sub-navigation */}
      <div className="preprepare-subtabs">
        {categories.map((cat) => (
          <button
            key={cat.id}
            className={`preprepare-subtab-btn ${activeCategory === cat.id ? 'active' : ''}`}
            onClick={() => setActiveCategory(cat.id)}
          >
            <span>{cat.label}</span>
            <span className="stage-tab-number">{cat.count}</span>
          </button>
        ))}
      </div>

      {/* Visualizations Uniform Cards Grid */}
      <div className="viz-grid">
        {getActiveCards().map((card) => (
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
              <ChartRenderer type={card.type} id={card.id} flagged={card.flagged} />
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
