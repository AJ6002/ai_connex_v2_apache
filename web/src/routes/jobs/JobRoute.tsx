import { useParams } from 'react-router-dom';
import { JobView } from '@/features/jobs/components/JobView';

export function JobRoute() {
  const { jobId } = useParams();
  return <JobView jobId={jobId ?? ''} />;
}
