import React from 'react';
import './Card.css';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  elevation?: 'low' | 'default' | 'high' | 'highest';
  /** Adds a coloured left-border accent (STITCH status-line pattern) */
  accent?: 'lime' | 'cyan' | 'amber' | 'red' | 'blue' | 'gray';
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export const Card: React.FC<CardProps> = ({
  elevation = 'default',
  accent,
  padding = 'md',
  className = '',
  children,
  ...rest
}) => {
  const cls = [
    'card',
    `card--${elevation}`,
    `card--pad-${padding}`,
    accent ? `card--accent-${accent}` : '',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={cls} {...rest}>
      {children}
    </div>
  );
};

export interface CardHeaderProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'title'> {
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  actions?: React.ReactNode;
}

export const CardHeader: React.FC<CardHeaderProps> = ({
  title,
  subtitle,
  actions,
  className = '',
  children,
  ...rest
}) => (
  <div className={`card-header ${className}`} {...rest}>
    {title && (
      <div className="card-header__text">
        <span className="card-header__title label-mono">{title}</span>
        {subtitle && <span className="card-header__subtitle">{subtitle}</span>}
      </div>
    )}
    {actions && <div className="card-header__actions">{actions}</div>}
    {children}
  </div>
);

export const CardBody: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className = '',
  children,
  ...rest
}) => (
  <div className={`card-body ${className}`} {...rest}>
    {children}
  </div>
);
