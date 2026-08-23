/**
 * The ONLY place in the app allowed to read environment configuration or
 * declare a backend host. Nothing else references a URL, port, or IP directly.
 * (Enforced by the no-hardcoded-URL ESLint rule — see eslint.config.js.)
 */

interface AppConfig {
  /** Base URL of the AI-ConneX FastAPI application layer. */
  apiBase: string;
  /** Whether the MSW mock layer should intercept all capability calls. */
  useMocks: boolean;
}

function readConfig(): AppConfig {
  const apiBase = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';
  const useMocks = import.meta.env.VITE_USE_MOCKS === 'true';
  return { apiBase, useMocks };
}

export const config: AppConfig = readConfig();
