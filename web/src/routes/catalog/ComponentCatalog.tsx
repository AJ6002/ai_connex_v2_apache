import React, { useState } from 'react';
import {
  Button,
  Card, CardHeader, CardBody,
  Input,
  StatusBadge,
  Progress,
  Skeleton, SkeletonText,
  EmptyState,
  ErrorState,
  Tabs, TabList, TabTrigger, TabPanel,
  DataTable,
  Dialog,
} from '@/components/ui';
import type { DataTableColumn } from '@/components/ui';
import './ComponentCatalog.css';

// ─── Sample Data ──────────────────────────────────────────────────────────────
interface SampleRow { id: string; name: string; role: string; status: string; }
const SAMPLE_ROWS: SampleRow[] = [
  { id: 'USR-001', name: 'Dr. Aris Vance', role: 'ADMIN', status: 'Active' },
  { id: 'USR-002', name: 'Elena Rostova', role: 'ENGINEER', status: 'Active' },
  { id: 'USR-003', name: 'Kai Nakamura', role: 'ANALYST', status: 'Inactive' },
];
const SAMPLE_COLS: DataTableColumn<SampleRow>[] = [
  { key: 'name', header: 'Name / ID', cell: (r) => <><div style={{ color: 'var(--fg)' }}>{r.name}</div><div style={{ fontSize: 11, color: 'var(--fg-muted)' }}>{r.id}</div></> },
  { key: 'role', header: 'Role', cell: (r) => <span className="label-mono" style={{ fontSize: 10 }}>{r.role}</span> },
  { key: 'status', header: 'Status', cell: (r) => <StatusBadge status={r.status === 'Active' ? 'RUNNING' : 'CANCELLED'} dot={r.status === 'Active'} size="sm" /> },
];

export const ComponentCatalog: React.FC = () => {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [inputVal, setInputVal] = useState('');

  return (
    <div className="catalog">
      <header className="catalog__header">
        <h1 className="catalog__title">AI-ConneX UI Primitives</h1>
        <p className="catalog__subtitle label-mono">Sprint 2 — Design System Catalog — All values from tokens.css</p>
      </header>

      {/* ── Color Tokens ─────────────────────────────────────────────────── */}
      <section className="catalog__section">
        <h2 className="catalog__section-title label-mono">Color Tokens</h2>
        <div className="catalog__swatches">
          {[
            ['--color-assistant-identity', 'Lime (Primary CTA)'],
            ['--color-action-proposed',    'Cyan (AI Action)'],
            ['--color-intent-clarification','Amber (Clarification)'],
            ['--color-error',              'Error'],
            ['--color-status-running',     'Running'],
            ['--color-surface-container',  'Surface Container'],
            ['--color-surface-container-high', 'Surface High'],
            ['--color-outline',            'Outline'],
            ['--color-grid-line',          'Grid Line'],
          ].map(([token, label]) => (
            <div key={token} className="catalog__swatch">
              <div className="catalog__swatch-color" style={{ background: `var(${token})` }} />
              <code className="catalog__swatch-token">{token}</code>
              <span className="catalog__swatch-label">{label}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ── Buttons ──────────────────────────────────────────────────────── */}
      <section className="catalog__section">
        <h2 className="catalog__section-title label-mono">Button</h2>
        <div className="catalog__row">
          <Button variant="primary" size="sm">Primary SM</Button>
          <Button variant="primary" size="md">Primary MD</Button>
          <Button variant="primary" size="lg">Primary LG</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="danger">Danger</Button>
          <Button variant="cyan">Cyan</Button>
          <Button variant="primary" loading>Loading</Button>
          <Button variant="primary" disabled>Disabled</Button>
        </div>
      </section>

      {/* ── Status Badges ─────────────────────────────────────────────────── */}
      <section className="catalog__section">
        <h2 className="catalog__section-title label-mono">StatusBadge</h2>
        <div className="catalog__row">
          {(['RUNNING','COMPLETED','FAILED','PENDING','NEEDS_CLARIFICATION','QUARANTINED','MACHINE_READY','MACHINE_READY_WITH_WARNINGS'] as const).map(s => (
            <StatusBadge key={s} status={s} dot={s === 'RUNNING'} />
          ))}
        </div>
      </section>

      {/* ── Progress ─────────────────────────────────────────────────────── */}
      <section className="catalog__section">
        <h2 className="catalog__section-title label-mono">Progress</h2>
        <div className="catalog__stack">
          <Progress value={64} label="MODEL_TRAINING" showValue variant="lime" size="md" />
          <Progress value={35} label="PROFILING" showValue variant="blue" size="md" />
          <Progress value={82} label="SLA_COMPLIANCE" showValue variant="amber" size="sm" />
          <Progress value={12} label="FAILED_RATIO" showValue variant="red" size="sm" />
        </div>
      </section>

      {/* ── Input ────────────────────────────────────────────────────────── */}
      <section className="catalog__section">
        <h2 className="catalog__section-title label-mono">Input</h2>
        <div className="catalog__stack" style={{ maxWidth: 400 }}>
          <Input label="DATA_OWNER_ID" placeholder="USR-9942-A" value={inputVal} onChange={e => setInputVal(e.target.value)} />
          <Input label="SOURCE_ORIGIN" placeholder="Internal Telemetry" hint="Select the data source type" />
          <Input label="ERROR_STATE" placeholder="Invalid" error="FIELD_REQUIRED — value cannot be empty" />
        </div>
      </section>

      {/* ── Cards ────────────────────────────────────────────────────────── */}
      <section className="catalog__section">
        <h2 className="catalog__section-title label-mono">Card</h2>
        <div className="catalog__row catalog__row--wrap">
          {(['low','default','high','highest'] as const).map(el => (
            <Card key={el} elevation={el} style={{ minWidth: 160 }}>
              <CardHeader title={`ELEVATION_${el.toUpperCase()}`} />
              <CardBody><p style={{ color: 'var(--fg-muted)', fontSize: 13 }}>Surface: {el}</p></CardBody>
            </Card>
          ))}
          {(['lime','cyan','amber','red','blue'] as const).map(a => (
            <Card key={a} accent={a} style={{ minWidth: 160 }}>
              <CardBody><span className="label-mono" style={{ fontSize: 10 }}>ACCENT_{a.toUpperCase()}</span></CardBody>
            </Card>
          ))}
        </div>
      </section>

      {/* ── Tabs ─────────────────────────────────────────────────────────── */}
      <section className="catalog__section">
        <h2 className="catalog__section-title label-mono">Tabs (Horizontal)</h2>
        <Card>
          <Tabs defaultTab="intake">
            <TabList>
              <TabTrigger id="intake">Intake</TabTrigger>
              <TabTrigger id="jobs">Jobs</TabTrigger>
              <TabTrigger id="data-studio">Data Studio</TabTrigger>
              <TabTrigger id="models">Models</TabTrigger>
            </TabList>
            <TabPanel id="intake"><div style={{ padding: 16 }}><p>Asset registration & intake screen content.</p></div></TabPanel>
            <TabPanel id="jobs"><div style={{ padding: 16 }}><p>Job tracking & execution pipeline content.</p></div></TabPanel>
            <TabPanel id="data-studio"><div style={{ padding: 16 }}><p>Data Studio Brain — Profiler / DAG / Prepare-Math.</p></div></TabPanel>
            <TabPanel id="models"><div style={{ padding: 16 }}><p>Model registry and evaluation content.</p></div></TabPanel>
          </Tabs>
        </Card>

        <h2 className="catalog__section-title label-mono" style={{ marginTop: 24 }}>Tabs (Vertical — STITCH side-rail pattern)</h2>
        <Card>
          <Tabs defaultTab="data-platform" orientation="vertical" style={{ minHeight: 240 }}>
            <TabList>
              <TabTrigger id="data-platform">Data Platform</TabTrigger>
              <TabTrigger id="process-builder">Process Builder</TabTrigger>
              <TabTrigger id="expert-network">Expert Network</TabTrigger>
              <TabTrigger id="evaluations">Evaluations</TabTrigger>
              <TabTrigger id="agents">Agents</TabTrigger>
            </TabList>
            <TabPanel id="data-platform"><div style={{ padding: 16 }}><p>Data Platform view.</p></div></TabPanel>
            <TabPanel id="process-builder"><div style={{ padding: 16 }}><p>Process Builder — Atomic workflow documentation.</p></div></TabPanel>
            <TabPanel id="expert-network"><div style={{ padding: 16 }}><p>Expert Network connection view.</p></div></TabPanel>
            <TabPanel id="evaluations"><div style={{ padding: 16 }}><p>Evaluations dashboard.</p></div></TabPanel>
            <TabPanel id="agents"><div style={{ padding: 16 }}><p>Agent orchestration view.</p></div></TabPanel>
          </Tabs>
        </Card>
      </section>

      {/* ── DataTable ────────────────────────────────────────────────────── */}
      <section className="catalog__section">
        <h2 className="catalog__section-title label-mono">DataTable</h2>
        <DataTable columns={SAMPLE_COLS} data={SAMPLE_ROWS} rowKey={r => r.id} />
        <DataTable columns={SAMPLE_COLS} data={[]} rowKey={r => r.id} emptyMessage="NO_PERSONNEL_FOUND" />
      </section>

      {/* ── Skeleton ─────────────────────────────────────────────────────── */}
      <section className="catalog__section">
        <h2 className="catalog__section-title label-mono">Skeleton</h2>
        <div className="catalog__stack" style={{ maxWidth: 400 }}>
          <Skeleton height="40px" />
          <Skeleton height="20px" width="60%" />
          <SkeletonText lines={4} />
        </div>
      </section>

      {/* ── EmptyState & ErrorState ───────────────────────────────────────── */}
      <section className="catalog__section">
        <h2 className="catalog__section-title label-mono">EmptyState / ErrorState</h2>
        <div className="catalog__row">
          <Card style={{ flex: 1 }}>
            <EmptyState icon="▣" title="NO_ARTIFACTS_PRODUCED_YET" description="Model binaries and evaluation reports will appear here upon completion." />
          </Card>
          <Card style={{ flex: 1 }}>
            <ErrorState title="SYSTEM_ERROR" message="The operation failed. A network error occurred during artifact retrieval." retry={() => alert('retry')} />
          </Card>
        </div>
      </section>

      {/* ── Dialog ───────────────────────────────────────────────────────── */}
      <section className="catalog__section">
        <h2 className="catalog__section-title label-mono">Dialog</h2>
        <Button variant="secondary" onClick={() => setDialogOpen(true)}>Open Dialog</Button>
        <Dialog
          open={dialogOpen}
          onClose={() => setDialogOpen(false)}
          title="CONFIRM_ACTION"
          description="This operation cannot be undone. Proceed with caution."
          footer={
            <>
              <Button variant="ghost" onClick={() => setDialogOpen(false)}>Cancel</Button>
              <Button variant="danger" onClick={() => setDialogOpen(false)}>Confirm Delete</Button>
            </>
          }
        >
          <p style={{ fontSize: 14, color: 'var(--fg-muted)' }}>The selected artifact package will be removed from the registry and all downstream jobs referencing it will be invalidated.</p>
        </Dialog>
      </section>
    </div>
  );
};
