import React from 'react';
import './Progress.css';

export interface ProgressProps {
  value: number;        // 0–100
  max?: number;
  label?: string;
  showValue?: boolean;
  variant?: 'lime' | 'blue' | 'amber' | 'red';
  size?: 'sm' | 'md';
  className?: string;
}

export const Progress: React.FC<ProgressProps> = ({
  value,
  max = 100,
  label,
  showValue = false,
  variant = 'lime',
  size = 'md',
  className = '',
}) => {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));

  return (
    <div className={`progress-root ${className}`}>
      {(label || showValue) && (
        <div className="progress-header">
          {label && <span className="progress-label label-mono">{label}</span>}
          {showValue && (
            <span className="progress-value label-mono">{Math.round(pct)}%</span>
          )}
        </div>
      )}
      <div
        className={`progress-track progress-track--${size}`}
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
        aria-label={label}
      >
        <div
          className={`progress-fill progress-fill--${variant}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
};
