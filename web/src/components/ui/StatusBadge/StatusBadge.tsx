import React from 'react';
import type { ArtifactStatus } from '@/entities/artifact/types';
import type { JobStatus } from '@/entities/job/types';
import type { ModelStatus } from '@/entities/model/types';
import type { DeploymentStatus } from '@/entities/deployment/types';
import './StatusBadge.css';

export type BadgeStatus =
  | ArtifactStatus
  | JobStatus
  | ModelStatus
  | DeploymentStatus
  | 'PENDING'
  | 'CANCELLED'
  | 'LIVE'
  | 'OPERATIONAL'
  | 'DEGRADED';

const STATUS_MAP: Record<
  string,
  { label: string; variant: string }
> = {
  /* Job & Deployment statuses */
  PENDING:                      { label: 'Pending',      variant: 'queued' },
  RUNNING:                      { label: 'Running',      variant: 'running' },
  ACTIVE:                       { label: 'Active',       variant: 'running' },
  COMPLETED:                    { label: 'Completed',    variant: 'completed' },
  READY:                        { label: 'Ready',        variant: 'ready' },
  TRAINING:                     { label: 'Training',     variant: 'running' },
  EVALUATING:                   { label: 'Evaluating',   variant: 'running' },
  DEPRECATED:                   { label: 'Deprecated',   variant: 'queued' },
  STOPPED:                      { label: 'Stopped',      variant: 'queued' },
  FAILED:                       { label: 'Failed',       variant: 'failed' },
  CANCELLED:                    { label: 'Cancelled',    variant: 'queued' },
  /* Artifact Package statuses */
  MACHINE_READY:                { label: 'Machine Ready',    variant: 'ready' },
  MACHINE_READY_WITH_WARNINGS:  { label: 'Ready w/ Warnings',variant: 'warnings' },
  READY_FOR_PROFILER:           { label: 'Ready for Profiler',variant: 'running' },
  NEEDS_CLARIFICATION:          { label: 'Clarification',    variant: 'clarification' },
  NEEDS_USER_CORRECTION:        { label: 'Correction Needed',variant: 'clarification' },
  QUARANTINED:                  { label: 'Quarantined',      variant: 'quarantined' },
  /* Generic */
  LIVE:                         { label: 'Live',          variant: 'running' },
  OPERATIONAL:                  { label: 'Operational',   variant: 'completed' },
  DEGRADED:                     { label: 'Degraded',      variant: 'clarification' },
};

export interface StatusBadgeProps {
  status: BadgeStatus;
  /** Show a blinking dot indicator */
  dot?: boolean;
  size?: 'sm' | 'md';
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  dot = false,
  size = 'md',
  className = '',
}) => {
  const mapped = STATUS_MAP[status] ?? { label: status, variant: 'queued' };
  const cls = [
    'status-badge',
    `status-badge--${mapped.variant}`,
    `status-badge--${size}`,
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <span className={cls} role="status" aria-label={mapped.label}>
      {dot && <span className="status-badge__dot" aria-hidden="true" />}
      {mapped.label}
    </span>
  );
};
