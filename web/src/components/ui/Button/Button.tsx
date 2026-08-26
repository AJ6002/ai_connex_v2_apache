import React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';
import './Button.css';

export const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        primary: "btn-primary",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        danger: "btn-danger",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary: "btn-secondary",
        ghost: "btn-ghost",
        link: "text-primary underline-offset-4 hover:underline",
        cyan: "btn-cyan",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "btn-sm",
        md: "btn-md",
        lg: "btn-lg",
        icon: "btn-icon",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  },
);

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'cyan' | 'default' | 'destructive' | 'outline' | 'link';
export type ButtonSize = 'sm' | 'md' | 'lg' | 'default' | 'icon';

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  iconOnly?: boolean;
  /** Renders as an anchor when provided */
  href?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  loading?: boolean;
  asChild?: boolean;
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
      asChild = false,
      ...rest
    },
    ref,
  ) => {
    const cls = [
      'btn',
      `btn-${variant}`,
      iconOnly ? 'btn-icon' : `btn-${size}`,
      cn(buttonVariants({ variant, size, className })),
    ]
      .filter(Boolean)
      .join(' ');

    const content = (
      <>
        {loading ? (
          <span aria-hidden="true" style={{ display: 'inline-block', width: 12, height: 12, border: '2px solid currentColor', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} />
        ) : leftIcon ? (
          <span aria-hidden="true" className="mr-2 inline-flex items-center">{leftIcon}</span>
        ) : null}
        {children}
        {rightIcon && !loading && <span aria-hidden="true" className="ml-2 inline-flex items-center">{rightIcon}</span>}
      </>
    );

    if (href) {
      return (
        <a href={href} className={cls}>
          {content}
        </a>
      );
    }

    const Comp = asChild ? Slot : "button";

    return (
      <Comp ref={ref} className={cls} disabled={disabled || loading} {...rest}>
        {content}
      </Comp>
    );
  },
);

Button.displayName = 'Button';
