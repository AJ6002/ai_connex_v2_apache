import { defineConfig } from '@playwright/test';

/**
 * E2E tooling is reserved in Sprint 1; the first real spec
 * (intake → job → data-studio) is written in Sprint 4.
 */
export default defineConfig({
  testDir: './e2e',
  use: {
    baseURL: 'http://localhost:3100',
  },
});
