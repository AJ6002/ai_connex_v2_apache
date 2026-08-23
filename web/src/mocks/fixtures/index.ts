/**
 * Barrel export — mock fixtures split by domain to stay under the guardrail's
 * max-lines limit (plan §9's structural rule applies to mocks too). Import
 * from '@/mocks/fixtures' (this file), never from the per-domain files
 * directly, so handlers.ts and any future consumer has one stable import.
 */
export * from './job';
export * from './dataset';
export * from './profile';
export * from './models';
export * from './deployments';
export * from './agents';
export * from './workspace';
export * from './jane';
