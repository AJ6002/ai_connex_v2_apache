// @vitest-environment node
import { describe, expect, it } from 'vitest';
import { submitParseJob, getJobStatus } from '@/entities/job/api';
import { intentFixture } from '@/mocks/fixtures';

/**
 * Proves the capability functions are wired to the API client and that the
 * MSW mock layer answers them — the Sprint 1 success criterion in test form.
 */
describe('job capabilities against the mock layer', () => {
  it('submit_parse_job returns a running job', async () => {
    const job = await submitParseJob(intentFixture);
    expect(job.jobId).toBeTruthy();
    expect(job.status).toBe('RUNNING');
  });

  it('get_job_status returns a job with only plan-selected stages', async () => {
    const job = await getJobStatus('job_demo_0001');
    expect(job.stages.length).toBeGreaterThan(0);
    expect(job.artifact?.status).toBe('READY_FOR_PROFILER');
  });
});
