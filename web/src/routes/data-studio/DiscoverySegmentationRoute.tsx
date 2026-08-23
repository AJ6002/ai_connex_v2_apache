import { useParams } from 'react-router-dom';
import { DiscoverySegmentationView } from '@/features/data-studio/components/DiscoverySegmentationView';

export function DiscoverySegmentationRoute() {
  const { assetId } = useParams();
  return <DiscoverySegmentationView assetId={assetId ?? 'asset_demo_0001'} />;
}
