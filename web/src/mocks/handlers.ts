import { http, HttpResponse } from 'msw';
import { config } from '@/config/env';
import {
  agentsFixture,
  archiveInspectionFixture,
  auditLogsFixture,
  credentialsFixture,
  datasetFixture,
  deploymentsFixture,
  discoveryArtifactFixture,
  executeJaneActionState,
  getDiscoveryArtifactState,
  getJaneSessionState,
  reviewDiscoverySegmentState,
  intentFixture,
  jobFixture,
  jobForId,
  resolveJaneClarificationState,
  resolveJobClarification,
  modelsFixture,
  parsePlanFixture,
  personnelFixture,
  planValidationFixture,
  profileSummaryFixture,
  recentDatasetsFixture,
  recentJobsFixture,
  workspaceFixture,
} from './fixtures';

/** Absolute URL for a capability endpoint, resolved from the single API base. */
const cap = (name: string): string => `${config.apiBase}/api/v1/capabilities/${name}`;

/**
 * One handler per Capability Registry function (new-arch §13).
 * This is the mock "backend" the app develops against, independent of readiness.
 */
export const handlers = [
  // dataset-scoped
  http.post(cap('inspect_archive'), () => HttpResponse.json(archiveInspectionFixture)),
  http.post(cap('create_discovery_artifact'), () => HttpResponse.json(discoveryArtifactFixture)),
  http.get(cap('get_discovery_artifact'), () => HttpResponse.json(getDiscoveryArtifactState())),
  http.post(cap('review_discovery_segment'), async ({ request }) => {
    const { segmentId, decision } = (await request.json()) as {
      segmentId: string;
      decision: 'APPROVED' | 'REJECTED';
    };
    return HttpResponse.json(reviewDiscoverySegmentState(segmentId, decision));
  }),
  http.post(cap('promote_dataset'), () => HttpResponse.json(datasetFixture)),

  // intent / job / plan
  http.post(cap('narrow_intent'), () => HttpResponse.json(intentFixture)),
  http.post(cap('request_clarification'), async ({ request }) => {
    const { jobId } = (await request.json()) as { jobId: string };
    return HttpResponse.json(resolveJobClarification(jobId));
  }),
  http.post(cap('create_parse_plan'), () => HttpResponse.json(parsePlanFixture)),
  http.post(cap('validate_parse_plan'), () => HttpResponse.json(planValidationFixture)),
  http.post(cap('submit_parse_job'), () =>
    HttpResponse.json({ ...jobFixture, status: 'RUNNING' }),
  ),
  http.get(`${cap('get_job_status')}/:jobId`, ({ params }) => {
    const id = String(params.jobId);
    // Preserve the completed-with-artifact contract used by the unit test.
    if (id === 'job_demo_0001') return HttpResponse.json(jobFixture);
    return HttpResponse.json(jobForId(id));
  }),
  http.post(cap('request_compilation'), () => HttpResponse.json(jobFixture)),
  http.post(cap('request_math_analysis'), () => HttpResponse.json(jobFixture)),

  // profile
  http.get(cap('read_profile_summary'), () => HttpResponse.json(profileSummaryFixture)),

  // models / deployments / agents / workspace
  http.get(cap('list_models'), () => HttpResponse.json(modelsFixture)),
  http.get(`${cap('get_model')}/:id`, () => HttpResponse.json(modelsFixture[0])),
  http.get(cap('list_deployments'), () => HttpResponse.json(deploymentsFixture)),
  http.get(`${cap('get_deployment')}/:id`, () => HttpResponse.json(deploymentsFixture[0])),
  http.get(cap('list_agents'), () => HttpResponse.json(agentsFixture)),
  http.get(cap('get_workspace'), () => HttpResponse.json(workspaceFixture)),
  http.get(cap('list_personnel'), () => HttpResponse.json(personnelFixture)),
  http.get(cap('list_credentials'), () => HttpResponse.json(credentialsFixture)),
  http.get(cap('list_audit_logs'), () => HttpResponse.json(auditLogsFixture)),
  http.get(cap('list_recent_jobs'), () => HttpResponse.json(recentJobsFixture)),
  http.get(cap('list_recent_datasets'), () => HttpResponse.json(recentDatasetsFixture)),
  http.post(cap('create_workspace'), () => HttpResponse.json(workspaceFixture)),

  // Jane conversational session
  http.get(cap('get_jane_session'), () => HttpResponse.json(getJaneSessionState())),
  http.post(cap('resolve_jane_clarification'), async ({ request }) => {
    const { option } = (await request.json()) as { option: string };
    return HttpResponse.json(resolveJaneClarificationState(option));
  }),
  http.post(cap('execute_jane_action'), () => HttpResponse.json(executeJaneActionState())),
];
