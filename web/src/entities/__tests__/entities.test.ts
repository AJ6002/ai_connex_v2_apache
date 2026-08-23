import { describe, it, expect } from 'vitest';
import { modelApi } from '../model/api';
import { deploymentApi } from '../deployment/api';
import { agentApi } from '../agent/api';
import { workspaceApi } from '../workspace/api';

describe('Entity API Layer — Product Structure', () => {
  it('modelApi fetches models list', async () => {
    const models = await modelApi.listModels();
    expect(Array.isArray(models)).toBe(true);
  });

  it('deploymentApi fetches deployments list', async () => {
    const deployments = await deploymentApi.listDeployments();
    expect(Array.isArray(deployments)).toBe(true);
  });

  it('agentApi fetches agents list', async () => {
    const agents = await agentApi.listAgents();
    expect(Array.isArray(agents)).toBe(true);
  });

  it('workspaceApi fetches workspace info and personnel', async () => {
    const workspace = await workspaceApi.getWorkspaceInfo();
    expect(workspace).toHaveProperty('workspaceId');
    const personnel = await workspaceApi.listPersonnel();
    expect(Array.isArray(personnel)).toBe(true);
  });
});
