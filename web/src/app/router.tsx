import { type ReactNode } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AdminLayout } from '@/features/admin/components/AdminLayout';
import { AuditLogsRoute } from '@/routes/admin/AuditLogsRoute';
import { UsageQuotasRoute } from '@/routes/admin/UsageQuotasRoute';
import { WorkspaceConfigRoute } from '@/routes/admin/WorkspaceConfigRoute';
import { SystemStatesRoute } from '@/routes/admin/SystemStatesRoute';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { RootLayout } from '@/routes/RootLayout';
import { LandingPage } from '@/features/landing/components/LandingPage';
import { IntakeRoute } from '@/routes/intake/IntakeRoute';
import { JobRoute } from '@/routes/jobs/JobRoute';
import { DataStudioRoute } from '@/routes/data-studio/DataStudioRoute';
import { DiscoverySegmentationRoute } from '@/routes/data-studio/DiscoverySegmentationRoute';
import { ModelsRoute } from '@/routes/models/ModelsRoute';
import { ModelDetailRoute } from '@/routes/models/ModelDetailRoute';
import { DeploymentsRoute } from '@/routes/deployments/DeploymentsRoute';
import { DeploymentDetailRoute } from '@/routes/deployments/DeploymentDetailRoute';
import { DeploymentConfigRoute } from '@/routes/deployments/DeploymentConfigRoute';
import { AdminRoute } from '@/routes/admin/AdminRoute';
import { AgentsRoute } from '@/routes/agents/AgentsRoute';
import { ComponentCatalog } from '@/routes/catalog/ComponentCatalog';
import { WorkspaceOverviewRoute } from '@/routes/workspace/WorkspaceOverviewRoute';
import { NewWorkspaceRoute } from '@/routes/workspace/NewWorkspaceRoute';

/** Every route element is wrapped so a crash is contained to that route. */
const guard = (node: ReactNode): ReactNode => <ErrorBoundary>{node}</ErrorBoundary>;

export const router = createBrowserRouter([
  // Public marketing landing — standalone, no app shell.
  { path: '/', element: guard(<LandingPage />) },

  // Product app — wrapped in the dark AppShell (rail + top bar + Jane dock).
  {
    element: <RootLayout />,
    children: [
      { path: 'workspace', element: guard(<WorkspaceOverviewRoute />) },
      { path: 'workspace/new', element: guard(<NewWorkspaceRoute />) },
      { path: 'intake', element: guard(<IntakeRoute />) },
      { path: 'jobs/:jobId', element: guard(<JobRoute />) },
      { path: 'data-studio', element: guard(<DataStudioRoute />) },
      { path: 'data-studio/discovery/:assetId', element: guard(<DiscoverySegmentationRoute />) },
      { path: 'models', element: guard(<ModelsRoute />) },
      { path: 'models/:modelId', element: guard(<ModelDetailRoute />) },
      { path: 'deployments', element: guard(<DeploymentsRoute />) },
      { path: 'deployments/new', element: guard(<DeploymentConfigRoute />) },
      { path: 'deployments/:deploymentId', element: guard(<DeploymentDetailRoute />) },
      { path: 'agents', element: guard(<AgentsRoute />) },
      {
        path: 'admin',
        element: <AdminLayout />,
        children: [
          { index: true, element: <Navigate to="/admin/access-control" replace /> },
          { path: 'access-control', element: guard(<AdminRoute />) },
          { path: 'audit-logs', element: guard(<AuditLogsRoute />) },
          { path: 'usage-quotas', element: guard(<UsageQuotasRoute />) },
          { path: 'workspace', element: guard(<WorkspaceConfigRoute />) },
          { path: 'system-states', element: guard(<SystemStatesRoute />) },
        ],
      },
      { path: 'catalog', element: guard(<ComponentCatalog />) },
    ],
  },
]);
