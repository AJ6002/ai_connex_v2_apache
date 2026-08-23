import React from 'react';
import './Button.css';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'cyan';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  iconOnly?: boolean;
  /** Renders as an anchor when provided */
  href?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  loading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      iconOnly = false,
      href,
      leftIcon,
      rightIcon,
      loading = false,
      disabled,
      className = '',
      children,
      ...rest
    },
    ref,
  ) => {
    const cls = [
      'btn',
      `btn-${variant}`,
      iconOnly ? 'btn-icon' : `btn-${size}`,
      className,
    ]
      .filter(Boolean)
      .join(' ');

    const content = (
      <>
        {loading ? (
          <span aria-hidden="true" style={{ display: 'inline-block', width: 12, height: 12, border: '2px solid currentColor', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} />
        ) : leftIcon ? (
          <span aria-hidden="true">{leftIcon}</span>
        ) : null}
        {children}
        {rightIcon && !loading && <span aria-hidden="true">{rightIcon}</span>}
      </>
    );

    if (href) {
      return (
        <a href={href} className={cls}>
          {content}
        </a>
      );
    }

    return (
      <button ref={ref} className={cls} disabled={disabled || loading} {...rest}>
        {content}
      </button>
    );
  },
);

Button.displayName = 'Button';
