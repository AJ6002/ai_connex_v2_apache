import React, { useState } from 'react';
import { 
  CheckCircle, 
  Workflow, 
  ArrowRight, 
  Info, 
  AlertTriangle,
  Cpu
} from 'lucide-react';

interface PostTrainProps {
  compiledCsvPath?: string;
  runId?: string;
  dagId?: string;
}

// Reusable SVG Chart Renderer for Post-Train / Split / Evaluate visualizations (140px uniform height)
function PostTrainChartRenderer({ type, id, flagged }: { type: string; id: string | number; flagged?: boolean }) {
  const primaryColor = '#ec4899'; // Pink for Train accent
  const beforeColor = '#94a3b8'; // Grey
  const blueColor = '#1e47c8'; // Blue
  const greenColor = '#10b981'; // Green
  const purpleColor = '#8b5cf6'; // Purple
  
  switch (type) {
    case 'split-strategy':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Split donut */}
          <circle cx="150" cy="60" r="32" fill="none" stroke="#eff6ff" strokeWidth="8" />
          {/* Train (70%) */}
          <circle 
            cx="150" 
            cy="60" 
            r="32" 
            fill="none" 
            stroke={blueColor} 
            strokeWidth="8" 
            strokeDasharray={`${2 * Math.PI * 32}`}
            strokeDashoffset={`${(1 - 0.70) * (2 * Math.PI * 32)}`}
            transform="rotate(-90 150 60)"
          />
          {/* Val (15%) */}
          <circle 
            cx="150" 
            cy="60" 
            r="32" 
            fill="none" 
            stroke={purpleColor} 
            strokeWidth="8" 
            strokeDasharray={`${2 * Math.PI * 32}`}
            strokeDashoffset={`${(1 - 0.15) * (2 * Math.PI * 32)}`}
            transform="rotate(162 150 60)"
          />
          {/* Test (15%) */}
          <circle 
            cx="150" 
            cy="60" 
            r="32" 
            fill="none" 
            stroke={greenColor} 
            strokeWidth="8" 
            strokeDasharray={`${2 * Math.PI * 32}`}
            strokeDashoffset={`${(1 - 0.15) * (2 * Math.PI * 32)}`}
            transform="rotate(216 150 60)"
          />
          <text x="150" y="64" textAnchor="middle" fill="var(--text-main)" fontSize="8" fontWeight="bold">
            Train: 70%
          </text>
        </svg>
      );

    case 'entity-split':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Partition timeline bars */}
          <text x="20" y="32" fill="var(--text-muted)" fontSize="8" fontWeight="bold" fontFamily="var(--font-mono)">Train (Eng 1-70)</text>
          <rect x="120" y="24" width="130" height="10" rx="2" fill={blueColor} />
          
          <text x="20" y="62" fill="var(--text-muted)" fontSize="8" fontWeight="bold" fontFamily="var(--font-mono)">Val (Eng 71-85)</text>
          <rect x="120" y="54" width="60" height="10" rx="2" fill={purpleColor} />
          
          <text x="20" y="92" fill="var(--text-muted)" fontSize="8" fontWeight="bold" fontFamily="var(--font-mono)">Test (Eng 86-100)</text>
          <rect x="120" y="84" width="60" height="10" rx="2" fill={greenColor} />
        </svg>
      );

    case 'feature-consistency':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Aligned KDE curves */}
          <path d="M 20 100 Q 80 100 120 30 T 220 100 L 280 100" fill="none" stroke={blueColor} strokeWidth="2.5" />
          <path d="M 20 100 Q 82 100 122 32 T 222 100 L 280 100" fill="none" stroke={purpleColor} strokeWidth="1.5" strokeDasharray="3" />
          <path d="M 20 100 Q 78 100 118 28 T 218 100 L 280 100" fill="none" stroke={greenColor} strokeWidth="1" strokeDasharray="1.5" />
          
          <text x="170" y="40" fill={blueColor} fontSize="8" fontWeight="bold">Train/Val/Test Alignment</text>
        </svg>
      );

    case 'split-summary':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Partition summaries */}
          <g transform="translate(15, 25)">
            <rect x="0" y="0" width="80" height="70" rx="4" fill="#eff6ff" stroke="#3b82f6" strokeWidth="1" />
            <text x="40" y="24" textAnchor="middle" fill="#1d4ed8" fontSize="10" fontWeight="bold">TRAIN</text>
            <text x="40" y="45" textAnchor="middle" fill="var(--text-main)" fontSize="11" fontWeight="bold">14,421 rows</text>
            <text x="40" y="60" textAnchor="middle" fill="var(--text-muted)" fontSize="8">Devices 1-70</text>
          </g>
          <g transform="translate(110, 25)">
            <rect x="0" y="0" width="80" height="70" rx="4" fill="#f5f3ff" stroke="#8b5cf6" strokeWidth="1" />
            <text x="40" y="24" textAnchor="middle" fill="#5b21b6" fontSize="10" fontWeight="bold">VAL</text>
            <text x="40" y="45" textAnchor="middle" fill="var(--text-main)" fontSize="11" fontWeight="bold">3,210 rows</text>
            <text x="40" y="60" textAnchor="middle" fill="var(--text-muted)" fontSize="8">Devices 71-85</text>
          </g>
          <g transform="translate(205, 25)">
            <rect x="0" y="0" width="80" height="70" rx="4" fill="#ecfdf5" stroke="#10b981" strokeWidth="1" />
            <text x="40" y="24" textAnchor="middle" fill="#047857" fontSize="10" fontWeight="bold">TEST</text>
            <text x="40" y="45" textAnchor="middle" fill="var(--text-main)" fontSize="11" fontWeight="bold">3,000 rows</text>
            <text x="40" y="60" textAnchor="middle" fill="var(--text-muted)" fontSize="8">Devices 86-100</text>
          </g>
        </svg>
      );

    case 'hpo-progress':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Hyperparameter trial scores line */}
          <line x1="30" y1="90" x2="270" y2="90" stroke="var(--border-medium)" strokeWidth="1" />
          
          <path d="M 30 25 Q 70 85 110 50 T 190 35 T 270 20" fill="none" stroke={primaryColor} strokeWidth="1.5" strokeDasharray="2" />
          
          {/* Best parameters path */}
          <circle cx="30" cy="25" r="3" fill="#94a3b8" />
          <circle cx="70" cy="70" r="3" fill="#94a3b8" />
          <circle cx="110" cy="50" r="3" fill="#94a3b8" />
          <circle cx="150" cy="42" r="3" fill="#94a3b8" />
          <circle cx="190" cy="35" r="3" fill="#94a3b8" />
          <circle cx="230" cy="24" r="3" fill="#94a3b8" />
          <circle cx="270" cy="20" r="4.5" fill="#10b981" />
          <text x="270" y="12" fill="#10b981" fontSize="7" fontWeight="bold" textAnchor="middle">Best #120</text>
        </svg>
      );

    case 'hpo-parallel':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Parallel coordinate parameters axis lines */}
          <line x1="50" y1="20" x2="50" y2="100" stroke="var(--border-medium)" strokeWidth="1.5" />
          <text x="50" y="112" fill="var(--text-muted)" fontSize="8" textAnchor="middle">n_estim</text>
          
          <line x1="110" y1="20" x2="110" y2="100" stroke="var(--border-medium)" strokeWidth="1.5" />
          <text x="110" y="112" fill="var(--text-muted)" fontSize="8" textAnchor="middle">lr</text>
          
          <line x1="170" y1="20" x2="170" y2="100" stroke="var(--border-medium)" strokeWidth="1.5" />
          <text x="170" y="112" fill="var(--text-muted)" fontSize="8" textAnchor="middle">depth</text>
          
          <line x1="230" y1="20" x2="230" y2="100" stroke="var(--border-medium)" strokeWidth="1.5" />
          <text x="230" y="112" fill="var(--text-muted)" fontSize="8" textAnchor="middle">RMSE</text>
          
          {/* Best parameter route (green) */}
          <path d="M 50 30 L 110 80 L 170 30 L 230 30" fill="none" stroke="#10b981" strokeWidth="2.5" />
          
          {/* Alternative routes (purple/grey) */}
          <path d="M 50 50 L 110 50 L 170 60 L 230 65" fill="none" stroke="#8b5cf6" strokeWidth="1" opacity="0.6" />
          <path d="M 50 90 L 110 20 L 170 90 L 230 85" fill="none" stroke="#94a3b8" strokeWidth="1" opacity="0.4" />
        </svg>
      );

    case 'learning-curves':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Train vs Val loss curves */}
          <path d="M 30 20 Q 80 80 150 40 T 270 20" fill="none" stroke="#3b82f6" strokeWidth="2.5" />
          <text x="60" y="40" fill="#3b82f6" fontSize="8" fontWeight="bold">Train Loss</text>
          
          <path d="M 30 35 Q 85 95 155 52 T 270 30" fill="none" stroke="#ec4899" strokeWidth="1.5" strokeDasharray="3" />
          <text x="150" y="72" fill="#ec4899" fontSize="8" fontWeight="bold">Val Loss</text>
          
          {/* Best epoch check */}
          <circle cx="210" cy="33" r="4.5" fill="#10b981" />
          <text x="210" y="24" fill="#10b981" fontSize="8" fontWeight="bold" textAnchor="middle">Best Epoch 32</text>
        </svg>
      );

    case 'model-importance':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Model feature importances (Gain values) */}
          <text x="20" y="30" fill="var(--text-muted)" fontSize="8" fontWeight="bold" fontFamily="var(--font-mono)">voltage_lag_1</text>
          <rect x="110" y="22" width="130" height="10" rx="2" fill="#8b5cf6" />
          
          <text x="20" y="55" fill="var(--text-muted)" fontSize="8" fontWeight="bold" fontFamily="var(--font-mono)">temp_mean_5</text>
          <rect x="110" y="47" width="105" height="10" rx="2" fill="#8b5cf6" />
          
          <text x="20" y="80" fill="var(--text-muted)" fontSize="8" fontWeight="bold" fontFamily="var(--font-mono)">voltage_diff_1</text>
          <rect x="110" y="72" width="85" height="10" rx="2" fill="#8b5cf6" />
          
          <text x="20" y="105" fill="var(--text-muted)" fontSize="8" fontWeight="bold" fontFamily="var(--font-mono)">voltage_raw</text>
          <rect x="110" y="97" width="35" height="10" rx="2" fill="#3b82f6" />
        </svg>
      );

    case 'job-status':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Speeds resource gauges */}
          <g transform="translate(75, 60)">
            <circle cx="0" cy="0" r="30" fill="none" stroke="var(--border-medium)" strokeWidth="6" />
            <path d="M -21 21 A 30 30 0 1 1 21 21" fill="none" stroke="#3b82f6" strokeWidth="6" strokeDasharray="140" strokeDashoffset="25" />
            <text x="0" y="4" textAnchor="middle" fill="#3b82f6" fontSize="10" fontWeight="bold">85%</text>
            <text x="0" y="42" textAnchor="middle" fill="var(--text-muted)" fontSize="8" fontWeight="bold">CPU</text>
          </g>
          <g transform="translate(225, 60)">
            <circle cx="0" cy="0" r="30" fill="none" stroke="var(--border-medium)" strokeWidth="6" />
            <path d="M -21 21 A 30 30 0 1 1 21 21" fill="none" stroke="#ec4899" strokeWidth="6" strokeDasharray="140" strokeDashoffset="45" />
            <text x="0" y="4" textAnchor="middle" fill="#ec4899" fontSize="10" fontWeight="bold">70%</text>
            <text x="0" y="42" textAnchor="middle" fill="var(--text-muted)" fontSize="8" fontWeight="bold">Memory</text>
          </g>
        </svg>
      );

    case 'performance-kpi':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* KPI box metrics */}
          <g transform="translate(15, 25)">
            <rect x="0" y="0" width="80" height="70" rx="4" fill="#eff6ff" stroke="#3b82f6" strokeWidth="1" />
            <text x="40" y="24" textAnchor="middle" fill="#1d4ed8" fontSize="10" fontWeight="bold">R² SCORE</text>
            <text x="40" y="45" textAnchor="middle" fill="var(--text-main)" fontSize="13" fontWeight="bold">0.884</text>
            <text x="40" y="60" textAnchor="middle" fill="#10b981" fontSize="8" fontWeight="bold">✓ PASS (gate &gt; 0.7)</text>
          </g>
          <g transform="translate(110, 25)">
            <rect x="0" y="0" width="80" height="70" rx="4" fill="#fdf2f8" stroke="#f472b6" strokeWidth="1" />
            <text x="40" y="24" textAnchor="middle" fill="#be185d" fontSize="10" fontWeight="bold">MAE</text>
            <text x="40" y="45" textAnchor="middle" fill="var(--text-main)" fontSize="13" fontWeight="bold">12.14</text>
            <text x="40" y="60" textAnchor="middle" fill="#10b981" fontSize="8" fontWeight="bold">✓ PASS (gate &lt; 20)</text>
          </g>
          <g transform="translate(205, 25)">
            <rect x="0" y="0" width="80" height="70" rx="4" fill="#ecfdf5" stroke="#10b981" strokeWidth="1" />
            <text x="40" y="24" textAnchor="middle" fill="#047857" fontSize="10" fontWeight="bold">RMSE</text>
            <text x="40" y="45" textAnchor="middle" fill="var(--text-main)" fontSize="13" fontWeight="bold">15.39</text>
            <text x="40" y="60" textAnchor="middle" fill="#10b981" fontSize="8" fontWeight="bold">✓ PASS (gate &lt; 25)</text>
          </g>
        </svg>
      );

    case 'actual-predicted':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Diagonal target line */}
          <line x1="60" y1="100" x2="240" y2="20" stroke="var(--border-medium)" strokeWidth="1.5" strokeDasharray="3" />
          
          {/* Actual vs predicted scatter points */}
          <circle cx="80" cy="85" r="3" fill="#3b82f6" />
          <circle cx="110" cy="74" r="3.5" fill="#3b82f6" />
          <circle cx="130" cy="68" r="3" fill="#3b82f6" />
          <circle cx="150" cy="55" r="4.5" fill="#3b82f6" />
          <circle cx="170" cy="48" r="3" fill="#3b82f6" />
          <circle cx="200" cy="34" r="3" fill="#3b82f6" />
          <circle cx="220" cy="26" r="3.5" fill="#3b82f6" />
          
          <text x="150" y="112" fill="var(--text-muted)" fontSize="8" textAnchor="middle">Actual Values</text>
          <text x="15" y="60" fill="var(--text-muted)" fontSize="8" transform="rotate(-90 15 60)" textAnchor="middle">Predicted</text>
        </svg>
      );

    case 'residual-analysis':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Zero baseline axis line */}
          <line x1="30" y1="60" x2="270" y2="60" stroke="var(--border-medium)" strokeWidth="1.5" />
          
          {/* Evenly scattered error points */}
          <circle cx="50" cy="42" r="3" fill="#ec4899" />
          <circle cx="80" cy="78" r="3" fill="#ec4899" />
          <circle cx="110" cy="50" r="3" fill="#ec4899" />
          <circle cx="140" cy="65" r="3" fill="#ec4899" />
          <circle cx="170" cy="38" r="3.5" fill="#ec4899" />
          <circle cx="200" cy="82" r="3" fill="#ec4899" />
          <circle cx="230" cy="58" r="3" fill="#ec4899" />
          <circle cx="260" cy="62" r="3" fill="#ec4899" />
          <text x="150" y="112" fill="var(--text-muted)" fontSize="8" textAnchor="middle">Fitted Values (No Homoscedastic Pattern)</text>
        </svg>
      );

    case 'performance-entity':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Vertical RMSE bars per device */}
          <rect x="30" y="45" width="18" height="65" fill="#3b82f6" rx="2" />
          <text x="39" y="118" fill="var(--text-muted)" fontSize="7" textAnchor="middle">DEV_86</text>
          
          <rect x="65" y="55" width="18" height="55" fill="#3b82f6" rx="2" />
          <text x="74" y="118" fill="var(--text-muted)" fontSize="7" textAnchor="middle">DEV_87</text>
          
          <rect x="100" y="35" width="18" height="75" fill="#3b82f6" rx="2" />
          <text x="109" y="118" fill="var(--text-muted)" fontSize="7" textAnchor="middle">DEV_88</text>
          
          <rect x="135" y="65" width="18" height="45" fill="#10b981" rx="2" />
          <text x="144" y="118" fill="#10b981" fontSize="7" fontWeight="bold" textAnchor="middle">DEV_89</text>
          
          <rect x="170" y="50" width="18" height="60" fill="#3b82f6" rx="2" />
          <text x="179" y="118" fill="var(--text-muted)" fontSize="7" textAnchor="middle">DEV_90</text>
          
          <rect x="205" y="20" width="18" height="90" fill="#ef4444" rx="2" />
          <text x="214" y="118" fill="#ef4444" fontSize="7" fontWeight="bold" textAnchor="middle">DEV_91 ⚠️</text>
        </svg>
      );

    case 'confusion-matrix':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Confusion matrix grid */}
          <g transform="translate(70, 20)">
            {/* Box 1 (OK -> OK) */}
            <rect x="0" y="0" width="45" height="35" fill="#dcfce7" stroke="#86efac" />
            <text x="22" y="22" fill="#166534" fontSize="9" fontWeight="bold" textAnchor="middle">1,200</text>
            
            {/* Box 2 (OK -> WARN) */}
            <rect x="45" y="0" width="45" height="35" fill="#fffbeb" stroke="#fde68a" />
            <text x="67" y="22" fill="#b45309" fontSize="9" textAnchor="middle">80</text>
            
            {/* Box 3 (OK -> ERR) */}
            <rect x="90" y="0" width="45" height="35" fill="#eff6ff" stroke="#bfdbfe" />
            <text x="112" y="22" fill="#1d4ed8" fontSize="9" textAnchor="middle">20</text>
            
            {/* Row 2 */}
            <rect x="0" y="35" width="45" height="35" fill="#eff6ff" stroke="#bfdbfe" />
            <text x="22" y="57" fill="#1d4ed8" fontSize="9" textAnchor="middle">150</text>
            
            <rect x="45" y="35" width="45" height="35" fill="#dcfce7" stroke="#86efac" />
            <text x="67" y="57" fill="#166534" fontSize="9" fontWeight="bold" textAnchor="middle">600</text>
            
            <rect x="90" y="35" width="45" height="35" fill="#fffbeb" stroke="#fde68a" />
            <text x="112" y="57" fill="#b45309" fontSize="9" textAnchor="middle">50</text>
            
            {/* Row 3 */}
            <rect x="0" y="70" width="45" height="35" fill="#eff6ff" stroke="#bfdbfe" />
            <text x="22" y="92" fill="#1d4ed8" fontSize="9" textAnchor="middle">20</text>
            
            <rect x="45" y="70" width="45" height="35" fill="#eff6ff" stroke="#bfdbfe" />
            <text x="67" y="92" fill="#1d4ed8" fontSize="9" textAnchor="middle">30</text>
            
            <rect x="90" y="70" width="45" height="35" fill="#dcfce7" stroke="#86efac" />
            <text x="112" y="92" fill="#166534" fontSize="9" fontWeight="bold" textAnchor="middle">150</text>
            
            {/* Axes Labels */}
            <text x="-12" y="20" fill="var(--text-muted)" fontSize="8" textAnchor="middle" transform="rotate(-90 -12 20)">OK</text>
            <text x="-12" y="55" fill="var(--text-muted)" fontSize="8" textAnchor="middle" transform="rotate(-90 -12 55)">WARN</text>
            <text x="-12" y="90" fill="var(--text-muted)" fontSize="8" textAnchor="middle" transform="rotate(-90 -12 90)">ERR</text>
            
            <text x="22" y="-6" fill="var(--text-muted)" fontSize="8" textAnchor="middle">OK</text>
            <text x="67" y="-6" fill="var(--text-muted)" fontSize="8" textAnchor="middle">WARN</text>
            <text x="112" y="-6" fill="var(--text-muted)" fontSize="8" textAnchor="middle">ERR</text>
          </g>
        </svg>
      );

    case 'validation-gate':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* Gate validations flow */}
          <rect x="20" y="20" width="260" height="25" rx="3" fill="#dcfce7" stroke="#22c55e" strokeWidth="1" />
          <text x="32" y="36" fill="#166534" fontSize="9" fontWeight="bold">✓ R²: 0.884</text>
          <text x="120" y="35" fill="var(--text-muted)" fontSize="8">Threshold ≥ 0.70 (Exceeded)</text>
          
          <rect x="20" y="50" width="260" height="25" rx="3" fill="#dcfce7" stroke="#22c55e" strokeWidth="1" />
          <text x="32" y="66" fill="#166534" fontSize="9" fontWeight="bold">✓ MAE: 12.14</text>
          <text x="120" y="65" fill="var(--text-muted)" fontSize="8">Threshold ≤ 20.0 (Within limit)</text>
          
          <rect x="20" y="80" width="260" height="25" rx="3" fill="#dcfce7" stroke="#22c55e" strokeWidth="1" />
          <text x="32" y="96" fill="#166534" fontSize="9" fontWeight="bold">✓ RMSE: 15.39</text>
          <text x="120" y="95" fill="var(--text-muted)" fontSize="8">Threshold ≤ 25.0 (Within limit)</text>
        </svg>
      );

    case 'e2e-summary':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          {/* End to end summary timeline flowchart */}
          <rect x="20" y="45" width="60" height="30" rx="4" fill="#dbeafe" stroke="#3b82f6" strokeWidth="1.5" />
          <text x="50" y="64" fill="#1e40af" fontSize="8" fontWeight="bold" textAnchor="middle">1. SPLIT</text>
          
          <line x1="80" y1="60" x2="115" y2="60" stroke="var(--border-medium)" strokeWidth="1.5" />
          <polygon points="115,57 121,60 115,63" fill="var(--text-muted)" />
          
          <rect x="121" y="45" width="60" height="30" rx="4" fill="#fce7f3" stroke="#ec4899" strokeWidth="1.5" />
          <text x="151" y="64" fill="#9d174d" fontSize="8" fontWeight="bold" textAnchor="middle">2. TRAIN</text>
          
          <line x1="181" y1="60" x2="216" y2="60" stroke="var(--border-medium)" strokeWidth="1.5" />
          <polygon points="216,57 222,60 216,63" fill="var(--text-muted)" />
          
          <rect x="222" y="45" width="60" height="30" rx="4" fill="#dcfce7" stroke="#10b981" strokeWidth="1.5" />
          <text x="252" y="64" fill="#166534" fontSize="8" fontWeight="bold" textAnchor="middle">3. EVAL</text>
        </svg>
      );

    default:
      return (
        <div className="w-full h-full flex items-center justify-center text-xs text-slate-400 font-mono">
          Post-Train Plot ({type})
        </div>
      );
  }
}

export const PostTrain: React.FC<PostTrainProps> = ({
  compiledCsvPath,
  runId = 'run_20250115_143022',
  dagId = 'DAG_201'
}) => {
  const [activeCategory, setActiveCategory] = useState<'split' | 'train' | 'eval'>('train');
  const [nodesOnline, setNodesOnline] = useState({ train: false, eval: false });

  React.useEffect(() => {
    Promise.all([
      fetch('http://localhost:8006/api/v1/health').then(r => r.ok).catch(() => false),
      fetch('http://localhost:8007/api/v1/health').then(r => r.ok).catch(() => false)
    ]).then(([train, evalOk]) => {
      setNodesOnline({ train, eval: evalOk });
    });
  }, []);

  // Three sub-sections categories for split, train and evaluate
  const categories = [
    { id: 'split', label: 'Node 6: Split', count: 4 },
    { id: 'train', label: 'Node 7: Train', count: 5 },
    { id: 'evaluate', label: 'Node 8: Evaluate', count: 7 }
  ];

  // 16 visualizations split by category
  const visualizations = {
    split: [
      {
        id: 'PP_SPLIT1',
        title: 'Split Strategy & Partition Visualization',
        type: 'split-strategy',
        check: 'Train/Val/Test split percentages',
        metric: 'Train: 70%, Val: 15%, Test: 15%',
        decision: 'Shows data allocation ratio. Split 14,421 rows for training, 3,210 for validation, and 3,000 for testing.'
      },
      {
        id: 'PP_SPLIT2',
        title: 'Entity/Time Distribution Across Splits',
        type: 'entity-split',
        check: 'Entity device timeline partitioning',
        metric: 'No overlapping devices between splits',
        decision: 'Validates partition separation. Confirms devices are kept group-intact chronologically without overlap.'
      },
      {
        id: 'PP_SPLIT3',
        title: 'Feature Distribution Consistency Check',
        type: 'feature-consistency',
        check: 'Feature distribution similarities per split',
        metric: 'KS test statistic p-value >0.05',
        decision: 'Compares value spreads. Statistical consistency (p-value > 0.05) proves the partitions represent similar patterns.'
      },
      {
        id: 'PP_SPLIT4',
        title: 'Split Metrics Summary Card',
        type: 'split-summary',
        check: 'Overall partition stats and targets',
        metric: 'Data partitions saved successfully',
        decision: 'Summary card confirming split complete with zero temporal leakage.'
      }
    ],
    train: [
      {
        id: 'PP_TRAIN5',
        title: 'HPO Training Progress Dashboard',
        type: 'hpo-progress',
        check: 'Trial optimization target performance score',
        metric: 'Hyperparameter trials score improvements',
        decision: 'Tracks optimization performance. Checked 150 search trials; score stabilized to best RMSE 11.5 at trial 120.'
      },
      {
        id: 'PP_TRAIN6',
        title: 'Hyperparameter Importance & Sensitivity',
        type: 'hpo-parallel',
        check: 'Parameter combinations vs target performance',
        metric: 'Best parameter combinations regions',
        decision: 'Identifies tuning impacts. Shows n_estimators (>100) and learning_rate (<0.06) generate best accuracy scores.'
      },
      {
        id: 'PP_TRAIN7',
        title: 'Learning Curves (Training vs. Validation)',
        type: 'learning-curves',
        check: 'Loss score progress over epoch iterations',
        metric: 'Train/Val generalization gap threshold',
        decision: 'Checks for overfitting. Lowest loss reached at Epoch 32 with a healthy generalization gap of 3.3.'
      },
      {
        id: 'PP_TRAIN8',
        title: 'Feature Importance From Model',
        type: 'model-importance',
        check: 'Features weight values computed by model',
        metric: 'Top 10 features importance ranking',
        decision: 'Tracks model feature dependencies. Engineered variables (lags and roll aggregations) dominate 78% of model importance.'
      },
      {
        id: 'PP_TRAIN9',
        title: 'Training Job Status & Resources',
        type: 'job-status',
        check: 'CPU and memory usage thresholds during run',
        metric: 'Resource saturation levels <80%',
        decision: 'Monitors job run limits. Training completed in 4.23s, hitting CPU peak at 85% and RAM at 70%.'
      }
    ],
    evaluate: [
      {
        id: 'PP_EVAL10',
        title: 'Model Performance Metrics Dashboard',
        type: 'performance-kpi',
        check: 'Standard metrics compared to limits',
        metric: 'R² score >0.70, MAE <20.0, RMSE <25.0',
        decision: 'Evaluates validation outputs. All metric criteria passed quality gates.'
      },
      {
        id: 'PP_EVAL11',
        title: 'Actual vs. Predicted Scatter Plot',
        type: 'actual-predicted',
        check: 'Prediction error spreads vs target diagonal',
        metric: 'Point spreads around ideal y=x line',
        decision: 'Measures model variance. Linear shape confirms the model remains unbiased with error distribution centered around zero.'
      },
      {
        id: 'PP_EVAL12',
        title: 'Residual Analysis Plots',
        type: 'residual-analysis',
        check: 'Errors patterns across predicted fitted values',
        metric: 'Homoscedastic variance spread',
        decision: 'Validates prediction error uniformity. Normal spread verifies that the model assumptions hold.'
      },
      {
        id: 'PP_EVAL13',
        title: 'Performance by Entity/Group',
        type: 'performance-entity',
        check: 'Prediction errors split by device IDs',
        metric: 'Consistency across test groups',
        decision: 'Finds performance outliers. DEV_91 showed the highest error rate (RMSE: 16.8) and needs validation.',
        flagged: true
      },
      {
        id: 'PP_EVAL14',
        title: 'Confusion Matrix (For Classification)',
        type: 'confusion-matrix',
        check: 'Anomaly prediction checks per category',
        metric: 'Precision, Recall, and F1 per class',
        decision: 'Details classification accuracy. Average precision is 87.5% with very few false warnings.'
      },
      {
        id: 'PP_EVAL15',
        title: 'VG_2 Validation Gate Report',
        type: 'validation-gate',
        check: 'Validation gates status criteria',
        metric: 'All verification gates = PASSED',
        decision: 'Determines deployment approval. Model exceeded all criteria; deployment approved (deploy_approved = True).'
      },
      {
        id: 'PP_EVAL16',
        title: 'End-to-End Pipeline Summary',
        type: 'e2e-summary',
        check: 'Pipeline steps sequence outputs',
        metric: 'Chronological progression confirmation',
        decision: 'Traces complete model journey from ingestion up to model packaging.',
        flagged: true
      }
    ]
  };

  const getActiveCards = () => {
    return visualizations[activeCategory] || [];
  };

  return (
    <div className="page-container font-sans text-xs">
      
      {/* Parameters Row */}
      <section className="status-action-bar">
        <div className="status-bar-info">
          <div className="status-bar-icon-block bg-pink-50 text-pink-600">
            <Cpu size={20} />
          </div>
          <div className="status-bar-details">
            <div className="status-bar-title-row">
              <span>Pipeline Stage 4 Transit: Post-Train [Training &amp; Evaluation]</span>
              <span className={`status-run-badge ${nodesOnline.train ? 'bg-pink-100 text-pink-800 font-bold' : ''}`}>
                {nodesOnline.train ? '● Nodes 7 & 8: Train & Evaluate APIs (Ports 8006/8007) Online' : 'Model Compiled'}
              </span>
            </div>
            
            <div className="status-bar-parameters">
              <div className="param-item">
                <span>🤖 Architecture: </span>
                <span className="highlight-orange font-bold">One-class SVM (RBF Kernel)</span>
              </div>
              <span>•</span>
              <div className="param-item">
                <span>🎯 Validation F1: </span>
                <span className="highlight-green font-bold">0.941</span>
              </div>
              <span>•</span>
              <div className="param-item">
                <span>⏱️ Training time: </span>
                <span className="highlight-blue font-bold">4.8s (120 Epochs)</span>
              </div>
            </div>
          </div>
        </div>
        
        <button className="proceed-cta-btn bg-pink-600 hover:bg-pink-700" onClick={() => alert('Model published to Registry!')}>
          Publish to Registry <ArrowRight size={16} />
        </button>
      </section>

      {/* Info Callout */}
      <div className="info-callout-banner bg-pink-50 border-pink-200 text-pink-900">
        <Info size={16} className="info-banner-icon text-pink-600" />
        <div className="info-banner-text">
          <strong>Post-Train [Training] Stage Completed:</strong> Tracks chronological data splits, hyperparameter optimizations, learning curve training iterations, and final deployment gate checks.
        </div>
      </div>

      {/* Categories Nested Tabs Sub-navigation */}
      <div className="preprepare-subtabs">
        {categories.map((cat) => (
          <button
            key={cat.id}
            className={`preprepare-subtab-btn ${activeCategory === cat.id ? 'active' : ''}`}
            onClick={() => setActiveCategory(cat.id as any)}
            style={{ 
              borderBottomColor: activeCategory === cat.id ? '#ec4899' : 'transparent',
              color: activeCategory === cat.id ? '#ec4899' : 'var(--text-muted)'
            }}
          >
            <span>{cat.label}</span>
            <span className="stage-tab-number">{cat.count}</span>
          </button>
        ))}
      </div>

      {/* Visualizations Uniform Cards Grid */}
      <div className="viz-grid">
        {getActiveCards().map((card) => (
          <div 
            key={card.id} 
            className="viz-card" 
            style={{ borderTop: card.flagged ? '3px solid #C8102E' : '1px solid var(--border-light)' }}
          >
            {/* Header */}
            <div className="viz-card-header">
              <div className="viz-card-title-group">
                <div className="viz-card-title-row">
                  {card.flagged ? (
                    <AlertTriangle size={15} className="text-red-600 animate-bounce" />
                  ) : (
                    <CheckCircle size={15} className="text-emerald-500" />
                  )}
                  <span className="font-bold text-slate-800">{card.title}</span>
                </div>
                <div className="viz-card-checked">
                  <strong>Checks:</strong> {card.check}
                </div>
              </div>
              <span className="viz-card-id font-mono text-[9px]">{card.id}</span>
            </div>

            {/* Visual Canvas (Uniform 140px size) */}
            <div className="viz-chart-box">
              <PostTrainChartRenderer type={card.type} id={card.id} flagged={card.flagged} />
            </div>

            {/* Decision Rule Box */}
            <div className={`viz-card-decision-box ${card.flagged ? 'flagged' : ''}`}>
              <div style={{ fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-muted)', marginBottom: '2px', fontWeight: 'bold' }}>
                {card.flagged ? '⚠️ Warning Action Rule' : '⚙️ Standard Action Rule'}
              </div>
              <div className="text-[11px] leading-relaxed">
                <strong>Metric Goal:</strong> {card.metric}. <br />
                <strong>Decision Logic:</strong> {card.decision}
              </div>
            </div>

          </div>
        ))}
      </div>

    </div>
  );
};

export default PostTrain;
