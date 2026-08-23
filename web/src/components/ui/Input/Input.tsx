import React from 'react';
import './Input.css';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  leftAddon?: React.ReactNode;
  rightAddon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, leftAddon, rightAddon, id, className = '', ...rest }, ref) => {
    const inputId = id ?? `input-${Math.random().toString(36).slice(2, 8)}`;
    return (
      <div className="input-root">
        {label && (
          <label className="input-label label-mono" htmlFor={inputId}>
            {label}
          </label>
        )}
        <div className={`input-wrapper ${error ? 'input-wrapper--error' : ''}`}>
          {leftAddon && <span className="input-addon input-addon--left">{leftAddon}</span>}
          <input
            ref={ref}
            id={inputId}
            className={`input-field ${leftAddon ? 'input-field--pl' : ''} ${rightAddon ? 'input-field--pr' : ''} ${className}`}
            aria-invalid={!!error}
            aria-describedby={error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined}
            {...rest}
          />
          {rightAddon && <span className="input-addon input-addon--right">{rightAddon}</span>}
        </div>
        {error && <span id={`${inputId}-error`} className="input-error">{error}</span>}
        {hint && !error && <span id={`${inputId}-hint`} className="input-hint">{hint}</span>}
      </div>
    );
  },
);

Input.displayName = 'Input';
