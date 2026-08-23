import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  getJobStatus,
  narrowIntent,
  requestClarification,
  submitParseJob,
} from './api';
import type { IntentDraft, Job } from './types';

/**
 * The ONE place "submit an intent and get a job" lives (guardrail §9.3).
 * Any feature that starts work calls this hook — never a second copy.
 */
export function useSubmitIntent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (draft: IntentDraft): Promise<Job> => {
      const intent = await narrowIntent(draft);
      return submitParseJob(intent);
    },
    onSuccess: (job) => {
      qc.setQueryData(['job', job.jobId], job);
    },
  });
}

const jobIsLive = (job: Job | undefined): boolean =>
  job?.status === 'QUEUED' || job?.status === 'RUNNING';

/** Single job-polling hook — polls while the job is live, stops when terminal. */
export function useJob(jobId: string | undefined) {
  return useQuery({
    queryKey: ['job', jobId],
    queryFn: () => getJobStatus(jobId as string),
    enabled: Boolean(jobId),
    refetchInterval: (query) => (jobIsLive(query.state.data) ? 2000 : false),
  });
}

export function useResolveClarification(jobId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (answer: string) => requestClarification(jobId as string, answer),
    // Write under the same key useJob(jobId) reads from — not job.jobId, which
    // may be a different internal id than the route/cache key.
    onSuccess: (job) => qc.setQueryData(['job', jobId], job),
  });
}
