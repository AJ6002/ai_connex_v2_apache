import { useParams } from 'react-router-dom';
import { ModelDetailView } from '@/features/models/components/ModelDetailView';

export function ModelDetailRoute() {
  const { modelId } = useParams();
  return <ModelDetailView modelId={modelId ?? ''} />;
}
