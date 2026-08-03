import React from 'react';
import { 
  Workflow, 
  ArrowRight, 
  Info, 
  AlertCircle,
  FileText,
  Sliders,
  Cpu,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';

interface PostPrepareProps {
  onProceed?: () => void;
  compiledCsvPath?: string;
  runId?: string;
  dagId?: string;
}

// Reusable SVG Chart Renderer for Post-Prepare visualizations (140px uniform height)
function PostPrepareChartRenderer({ type, id, flagged }: { type: string; id: string | number; flagged?: boolean }) {
  const primaryColor = flagged ? '#C8102E' : '#10b981';
  const beforeColor = '#94a3b8';
  const blueColor = '#1E47C8';
  
  switch (type) {
    case 'overlay-hist':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          <path d="M 20 100 Q 80 100 120 40 T 220 100 L 280 100" fill="none" stroke={beforeColor} strokeWidth="1.5" strokeDasharray="3" />
          <text x="50" y="55" fill={beforeColor} fontSize="8" fontWeight="bold">Raw (Before)</text>
          <path d="M 20 100 Q 110 100 150 20 T 260 100" fill="none" stroke="#10b981" strokeWidth="2.5" />
          <text x="180" y="35" fill="#10b981" fontSize="8" fontWeight="bold">Prepared (After)</text>
          <circle cx="150" cy="20" r="4.5" fill="#10b981" />
        </svg>
      );

    case 'waterfall-missing':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
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
          <text x="20" y="28" fill={beforeColor} fontSize="8" fontWeight="bold">Before (Raw):</text>
          <line x1="120" y1="24" x2="220" y2="24" stroke={beforeColor} strokeWidth="1" />
          <rect x="140" y="14" width="50" height="20" rx="2" fill="none" stroke={beforeColor} strokeWidth="1" />
          <line x1="165" y1="14" x2="165" y2="34" stroke={beforeColor} strokeWidth="1.5" />
          <circle cx="250" cy="24" r="3" fill="#C8102E" />
          <circle cx="270" cy="24" r="3" fill="#C8102E" />
          <text x="250" y="14" fill="#C8102E" fontSize="7">Outliers (24k)</text>
          
          <text x="20" y="78" fill="#10b981" fontSize="8" fontWeight="bold">After (Clipped):</text>
          <line x1="120" y1="74" x2="220" y2="74" stroke="#10b981" strokeWidth="1" />
          <rect x="140" y="64" width="50" height="20" rx="2" fill="none" stroke="#10b981" strokeWidth="1.5" />
          <line x1="165" y1="64" x2="165" y2="84" stroke="#10b981" strokeWidth="2.5" />
          <line x1="220" y1="64" x2="220" y2="84" stroke="#C8102E" strokeWidth="2" />
          <text x="225" y="60" fill="#C8102E" fontSize="7">Clipped (1,450 max)</text>
        </svg>
      );

    case 'qq-plot':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          <line x1="40" y1="100" x2="260" y2="20" stroke="var(--border-medium)" strokeWidth="1.5" strokeDasharray="3" />
          <circle cx="60" cy="92" r="3" fill={blueColor} />
          <circle cx="100" cy="78" r="3" fill={blueColor} />
          <circle cx="150" cy="58" r="3" fill={blueColor} />
          <circle cx="200" cy="40" r="3" fill={blueColor} />
          <circle cx="240" cy="26" r="3" fill={blueColor} />
          <text x="140" y="112" fill="var(--text-muted)" fontSize="8" textAnchor="middle">Theoretical Quantiles</text>
        </svg>
      );

    case 'scorecard':
      return (
        <svg viewBox="0 0 300 120" className="w-full h-full">
          <circle cx="150" cy="55" r="38" fill="none" stroke="var(--border-medium)" strokeWidth="8" />
          <circle 
            cx="150" 
            cy="55" 
            r="38" 
            fill="none" 
            stroke="#10b981" 
            strokeWidth="8" 
            strokeDasharray={`${2 * Math.PI * 38}`}
            strokeDashoffset={`${(1 - 0.98) * (2 * Math.PI * 38)}`}
            strokeLinecap="round"
            transform="rotate(-90 150 55)"
          />
          <text x="150" y="61" textAnchor="middle" fill="#10b981" fontSize="18" fontWeight="bold" fontFamily="var(--font-heading)">
            98%
          </text>
          <text x="150" y="110" textAnchor="middle" fill="var(--text-muted)" fontSize="9" fontWeight="bold">
            Data Cleanliness Score
          </text>
        </svg>
      );

    default:
      return (
        <div className="w-full h-full flex items-center justify-center text-xs text-slate-400 font-mono">
          Post-Prepare Plot ({type})
        </div>
      );
  }
}

export const PostPrepare: React.FC<PostPrepareProps> = ({
  onProceed,
  runId = 'run_20250115_143022',
  dagId = 'DAG_201'
}) => {
  const postPreparePlots = [
    {
      id: 'pp-1',
      title: 'Imputation Recovery Waterfall',
      type: 'waterfall-missing',
      check: '100% missing values successfully imputed',
      threshold: '0 remaining NaNs',
      flagged: false,
      exp: 'Shows how missing NaNs in sensor_1, sensor_2, and sensor_3 were 100% recovered using median imputation.'
    },
    {
      id: 'pp-2',
      title: 'Before vs After Distribution Overlay',
      type: 'overlay-hist',
      check: 'Distribution shape preservation post-scaling',
      threshold: 'KS p-value > 0.05',
      flagged: false,
      exp: 'Compares raw unscaled data against prepared data, confirming smooth distribution scaling without distortion.'
    },
    {
      id: 'pp-3',
      title: 'Outlier Capping & Trimming Box Plot',
      type: 'clipping-box',
      check: 'Extreme values bounded to 1.5x IQR upper whisker',
      threshold: '24k outliers clipped',
      flagged: true,
      exp: 'Pinpoints extreme outlier readings capped at maximum threshold limit to prevent model skew.'
    },
    {
      id: 'pp-4',
      title: 'StandardScaler Q-Q Quantile Plot',
      type: 'qq-plot',
      check: 'Feature alignment to standard normal distribution N(0,1)',
      threshold: 'Linear R² > 0.95',
      flagged: false,
      exp: 'Quantile-quantile plot confirming normalized features align closely to Gaussian zero-mean unit-variance distribution.'
    },
    {
      id: 'pp-5',
      title: 'Data Cleanliness Scorecard',
      type: 'scorecard',
      check: 'Overall dataset cleanliness and deduplication health',
      threshold: 'Target Score > 95%',
      flagged: false,
      exp: 'Overall health gauge scoring cleaned data at 98%, ready for Stage 3 Feature Engineering.'
    }
  ];

  return (
    <div className="page-container font-sans text-xs">
      
      {/* Action Bar */}
      <section className="status-action-bar">
        <div className="status-bar-info">
          <div className="status-bar-icon-block bg-teal-50 text-teal-600">
            <Workflow size={20} />
          </div>
          <div className="status-bar-details">
            <div className="status-bar-title-row">
              <span>Pipeline Stage 2 Transit: Post-Prepare [Prepare]</span>
              <span className="status-run-badge">
                Node 4: Data Cleaning &amp; Imputation Complete
              </span>
            </div>
            <div className="status-bar-parameters">
              <div className="param-item">
                <span>Imputation Strategy:</span>
                <span className="highlight-green font-bold font-mono">Median (Auto ✓)</span>
              </div>
              <span>•</span>
              <div className="param-item">
                <span>Outlier Bounding:</span>
                <span className="highlight-blue font-bold">1.5x IQR Capping</span>
              </div>
              <span>•</span>
              <div className="param-item">
                <span>Scaling:</span>
                <span className="highlight-orange font-bold font-mono">StandardScaler</span>
              </div>
            </div>
          </div>
        </div>

        {onProceed && (
          <button className="proceed-cta-btn bg-teal-600 hover:bg-teal-700" onClick={onProceed}>
            Proceed to Feature Engineering
            <ArrowRight size={16} />
          </button>
        )}
      </section>

      {/* Info Callout */}
      <section className="info-callout-banner bg-teal-50 border-teal-200 text-teal-900">
        <Info size={18} className="info-banner-icon text-teal-600" />
        <div className="info-banner-text">
          <strong>Post-Prepare Analytics:</strong> Review the cleaning and transformation diagnostics below. Missing values have been imputed, extreme outliers capped, and numerical features scaled.
        </div>
      </section>

      {/* Post-Prepare Analytics Grid */}
      <section className="dashboard-card">
        <div className="card-header-row">
          <div className="card-title-group">
            <CheckCircle className="card-title-icon-wrapper text-teal-600" size={18} />
            <h2 className="card-title">Stage 2: Post-Prepare Cleaning &amp; Scaling Analytics</h2>
          </div>
          <span className="card-header-badge-blue bg-teal-600">Prepare Stage Complete</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {postPreparePlots.map((plot) => (
            <div 
              key={plot.id}
              className={`p-4 bg-white rounded-xl border transition-all flex flex-col justify-between gap-3 shadow-sm ${
                plot.flagged ? 'border-amber-300 bg-amber-50/20' : 'border-slate-200 hover:border-teal-300'
              }`}
            >
              <div className="flex justify-between items-start gap-2 border-b border-slate-100 pb-2">
                <div className="font-bold text-slate-800 text-[12px]">{plot.title}</div>
                {plot.flagged && (
                  <span className="bg-amber-100 text-amber-800 text-[9px] font-bold px-2 py-0.5 rounded border border-amber-200">
                    Clipped
                  </span>
                )}
              </div>

              <div className="w-full h-[130px] bg-slate-50 rounded-lg p-1 overflow-hidden border border-slate-100">
                <PostPrepareChartRenderer type={plot.type} id={plot.id} flagged={plot.flagged} />
              </div>

              <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-100 text-[10.5px] text-slate-600 leading-snug flex items-start gap-1.5">
                <Info size={12} className="text-teal-600 flex-shrink-0 mt-0.5" />
                <span>{plot.exp}</span>
              </div>

              <div className="text-[9.5px] font-mono text-slate-400 border-t border-slate-100 pt-1.5 flex justify-between items-center">
                <span>Check: {plot.check}</span>
                <span className="text-slate-500 font-bold">#{plot.id}</span>
              </div>
            </div>
          ))}
        </div>
      </section>

    </div>
  );
};

export default PostPrepare;
