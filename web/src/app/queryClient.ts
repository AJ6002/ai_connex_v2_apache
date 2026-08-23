import { QueryClient } from '@tanstack/react-query';

/**
 * Single query client for all server state. This layer — not components —
 * owns fetching, caching, retries, and polling.
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
});
