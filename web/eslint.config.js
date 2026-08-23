import globals from 'globals';
import tseslint from 'typescript-eslint';

/**
 * Guardrails from the migration plan, enforced by lint:
 *  - §9.2 no hardcoded hosts/IPs outside config/  (no-restricted-syntax)
 *  - §P2  no giant files                          (max-lines)
 */
export default tseslint.config(
  { ignores: ['dist', 'node_modules', 'coverage', 'playwright-report', 'test-results', 'public'] },
  ...tseslint.configs.recommended,
  {
    files: ['src/**/*.{ts,tsx}'],
    languageOptions: {
      globals: { ...globals.browser, ...globals.node },
    },
    rules: {
      'max-lines': ['error', { max: 400, skipBlankLines: true, skipComments: true }],
      'no-restricted-syntax': [
        'error',
        {
          selector: 'Literal[value=/^https?:\\/\\//]',
          message:
            'No hardcoded URLs. Resolve the host from src/config/env.ts instead.',
        },
        {
          selector: 'Literal[value=/^\\d{1,3}(\\.\\d{1,3}){3}/]',
          message: 'No hardcoded IP addresses. Use src/config/env.ts.',
        },
        {
          selector: 'Literal[value=/^#(?:[0-9a-fA-F]{3,4}){1,2}$/]',
          message: 'Raw hex colors are banned in component JS/TS. Use CSS variable tokens from tokens.css instead.',
        },
      ],
    },
  },
  {
    // Sanctioned URL literals: env config, and mock fixtures (which carry
    // backend-provided values like serving endpoint URLs as data, not hosts
    // the app calls). App code still may never hardcode a host.
    files: ['src/config/**', 'src/mocks/**'],
    rules: { 'no-restricted-syntax': 'off' },
  },
);
