import React from 'react';
import './Skeleton.css';

export interface SkeletonProps {
  width?: string;
  height?: string;
  rounded?: boolean;
  className?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  width = '100%',
  height = '16px',
  rounded = false,
  className = '',
}) => (
  <span
    className={`skeleton ${rounded ? 'skeleton--rounded' : ''} ${className}`}
    style={{ width, height }}
    aria-hidden="true"
  />
);

/** Preset for a full text paragraph */
export const SkeletonText: React.FC<{ lines?: number }> = ({ lines = 3 }) => (
  <div className="skeleton-text">
    {Array.from({ length: lines }).map((_, i) => (
      <Skeleton
        key={i}
        height="14px"
        width={i === lines - 1 ? '60%' : '100%'}
      />
    ))}
  </div>
);
