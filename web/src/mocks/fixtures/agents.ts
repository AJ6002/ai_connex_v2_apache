export const agentsFixture = [
  {
    agentId: 'AGT-001',
    tenantUid: 'tenant_demo_0001',
    schemaVersion: '1.0.0',
    name: 'Jane Agent',
    role: 'Autonomous Industrial Assistant',
    status: 'SYSTEM_READY' as const,
    capabilities: [{ name: 'Intake Inspection', description: 'Inspects raw files', version: '1.0' }],
    lastActive: new Date().toISOString(),
  },
];
