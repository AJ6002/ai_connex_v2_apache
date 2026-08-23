import type { ReactNode } from 'react';

interface AsyncStateProps {
  isLoading: boolean;
  isError: boolean;
  isEmpty?: boolean;
  error?: unknown;
  loading?: ReactNode;
  empty?: ReactNode;
  children: ReactNode;
}

/**
 * The single, shared loading / error / empty wrapper every feature uses.
 * Replaces the old app's ad-hoc conditionals and silent `catch {}`.
 * Intentionally unstyled in Sprint 1 — visual treatment arrives in Sprint 2/4.
 */
export function AsyncState({
  isLoading,
  isError,
  isEmpty = false,
  error,
  loading,
  empty,
  children,
}: AsyncStateProps): ReactNode {
  if (isLoading) return <>{loading ?? <div data-testid="async-loading">Loading…</div>}</>;
  if (isError) {
    const message = error instanceof Error ? error.message : 'Request failed';
    return (
      <div role="alert" data-testid="async-error">
        {message}
      </div>
    );
  }
  if (isEmpty) return <>{empty ?? <div data-testid="async-empty">Nothing here yet.</div>}</>;
  return <>{children}</>;
}
