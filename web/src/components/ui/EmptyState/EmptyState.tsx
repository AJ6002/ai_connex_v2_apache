import React from 'react';
import './EmptyState.css';

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  className = '',
}) => (
  <div className={`empty-state ${className}`} role="status">
    {icon && <div className="empty-state__icon" aria-hidden="true">{icon}</div>}
    <p className="empty-state__title label-mono">{title}</p>
    {description && <p className="empty-state__desc">{description}</p>}
    {action && <div className="empty-state__action">{action}</div>}
  </div>
);
