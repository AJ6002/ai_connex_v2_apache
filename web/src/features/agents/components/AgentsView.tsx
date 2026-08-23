import React from 'react';
import { Card, CardHeader, CardBody, StatusBadge } from '@/components/ui';
import { useAgents } from '@/entities/agent/hooks';

export const AgentsView: React.FC = () => {
  const { data: agents = [], isLoading } = useAgents();

  return (
    <div className="feature-view agents-view" style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 24 }}>
      <header>
        <h1 style={{ fontSize: 32, marginBottom: 8 }}>Agents & Orchestration</h1>
        <p className="label-mono">Autonomous Agents, Jane Assistant, and Task Execution</p>
      </header>

      <Card elevation="default">
        <CardHeader title="ACTIVE_AGENTS" />
        <CardBody>
          {isLoading ? (
            <p className="label-mono">Connecting Agent Network...</p>
          ) : agents.length === 0 ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <div style={{ fontWeight: 600 }}>Jane Agent</div>
                <div className="label-mono" style={{ fontSize: 11 }}>Autonomous Industrial Assistant</div>
              </div>
              <StatusBadge status="LIVE" dot size="sm" />
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {agents.map((agent) => (
                <div key={agent.agentId} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ fontWeight: 600 }}>{agent.name}</div>
                    <div className="label-mono" style={{ fontSize: 11 }}>{agent.role}</div>
                  </div>
                  <StatusBadge status={agent.status === 'SYSTEM_READY' ? 'LIVE' : 'PENDING'} dot size="sm" />
                </div>
              ))}
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
};
