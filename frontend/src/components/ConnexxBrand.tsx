import React from 'react';

/**
 * Inline Connexx wordmark image — replaces text occurrences of "Connexx" / "AI-Connexx"
 * with the actual brand logo image (no background).
 *
 * Props:
 *  - variant: 'dark' for light backgrounds, 'white' for dark backgrounds
 *  - height: CSS class for height (default "h-5")
 *  - prefix: Optional prefix text (e.g. "AI-") rendered before the logo
 */
interface ConnexxBrandProps {
  variant?: 'dark' | 'white';
  height?: string;
  prefix?: string;
  className?: string;
}

export const ConnexxBrand: React.FC<ConnexxBrandProps> = ({
  variant = 'dark',
  height = 'h-5',
  prefix,
  className = ''
}) => {
  const src = variant === 'white' ? '/connexx-white.png' : '/connexx-dark.png';
  return (
    <span className={`inline-flex items-center gap-0.5 ${className}`}>
      {prefix && <span>{prefix}</span>}
      <img
        src={src}
        alt="Connexx"
        className={`${height} w-auto object-contain inline-block align-middle`}
        loading="eager"
      />
    </span>
  );
};
