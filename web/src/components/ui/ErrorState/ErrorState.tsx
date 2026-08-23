import React from 'react';
import './ErrorState.css';

export interface ErrorStateProps {
  title?: string;
  message?: string;
  retry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'SYSTEM_ERROR',
  message = 'An unexpected error occurred. The operation could not be completed.',
  retry,
  className = '',
}) => (
  <div className={`error-state ${className}`} role="alert">
    <div className="error-state__icon" aria-hidden="true">⚠</div>
    <p className="error-state__title label-mono">{title}</p>
    <p className="error-state__msg">{message}</p>
    {retry && (
      <button className="btn btn-secondary btn-sm error-state__retry" onClick={retry}>
        Retry
      </button>
    )}
  </div>
);
