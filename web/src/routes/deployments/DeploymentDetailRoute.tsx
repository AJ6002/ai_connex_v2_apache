import { useParams } from 'react-router-dom';
import { DeploymentDetailView } from '@/features/deployments/components/DeploymentDetailView';

export function DeploymentDetailRoute() {
  const { deploymentId } = useParams();
  return <DeploymentDetailView deploymentId={deploymentId ?? ''} />;
}
