import { setupWorker } from 'msw/browser';
import { handlers } from './handlers';

/** Browser-side mock worker, started from main.tsx when VITE_USE_MOCKS=true. */
export const worker = setupWorker(...handlers);
