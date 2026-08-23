import React, { useState, useRef, useEffect } from 'react';
import { ViewMode } from '../types';

interface BoardNode {
  id: string;
  name: string;
  viewId: ViewMode;
  category: 'Ingestion' | 'Orchestration' | 'Engineering' | 'Execution' | 'Deployment';
  x: number;
  y: number;
  icon: string;
  port: string;
  status: 'Online' | 'Offline';
}

interface Connection {
  id: string;
  fromId: string;
  toId: string;
}

interface OrchestratorBoardViewProps {
  onSelectNode: (nodeId: ViewMode) => void;
}

const CATEGORY_COLORS = {
  Ingestion:     { bg: 'rgba(255,107,53,0.10)', border: 'rgba(255,107,53,0.40)', text: '#FF6B35' },
  Orchestration: { bg: 'rgba(255,255,255,0.06)', border: 'rgba(255,255,255,0.30)', text: '#FFFFFF' },
  Engineering:   { bg: 'rgba(255,255,255,0.06)', border: 'rgba(255,255,255,0.20)', text: 'rgba(255,255,255,0.80)' },
  Execution:     { bg: 'rgba(255,107,53,0.08)', border: 'rgba(255,107,53,0.25)', text: '#FF8F5A' },
  Deployment:    { bg: 'rgba(255,107,53,0.12)', border: 'rgba(255,107,53,0.45)', text: '#FF6B35' }
};

const PALETTE_COMPONENTS: Omit<BoardNode, 'x' | 'y'>[] = [
  { id: 'prof', name: 'Dataset Upload Controller', viewId: 'compiler', category: 'Ingestion', icon: 'cloud_upload', port: ':8000', status: 'Online' },
  { id: 'prepare', name: 'Data Explorer & Telemetry', viewId: 'data_explorer', category: 'Ingestion', icon: 'analytics', port: ':8003', status: 'Online' },
  { id: 'matcher', name: 'Agent Fleet Orchestrator', viewId: 'agent_manager', category: 'Orchestration', icon: 'smart_toy', port: ':8001', status: 'Online' },
  { id: 'recipe', name: 'Master Data & Recipes', viewId: 'master_data', category: 'Orchestration', icon: 'database', port: ':8002', status: 'Online' },
  { id: 'feature', name: 'ML Pipeline Studio', viewId: 'pipeline_studio', category: 'Engineering', icon: 'monitoring', port: ':8004', status: 'Online' },
  { id: 'split', name: 'Validation Gate 1', viewId: 'vg1', category: 'Engineering', icon: 'verified', port: 'GATE', status: 'Online' },
  { id: 'vg1', name: 'Validation Gate 1', viewId: 'vg1', category: 'Engineering', icon: 'verified', port: 'GATE', status: 'Online' },
  { id: 'train', name: 'ML Pipeline Studio', viewId: 'pipeline_studio', category: 'Execution', icon: 'model_training', port: ':8006', status: 'Online' },
  { id: 'vg2', name: 'Validation Gate 2', viewId: 'vg2', category: 'Execution', icon: 'fact_check', port: 'GATE', status: 'Online' },
  { id: 'deploy', name: 'Pipeline Monitor', viewId: 'pipeline_studio', category: 'Deployment', icon: 'rocket_launch', port: ':8008', status: 'Online' },
  { id: 'monitor', name: 'Pipeline Monitor', viewId: 'pipeline_studio', category: 'Deployment', icon: 'monitoring', port: ':8001', status: 'Online' }
];

export const OrchestratorBoardView: React.FC<OrchestratorBoardViewProps> = ({ onSelectNode }) => {
  const [nodes, setNodes] = useState<BoardNode[]>([
    { id: 'prof', name: 'Dataset Upload Controller', viewId: 'compiler', category: 'Ingestion', icon: 'cloud_upload', port: ':8000', status: 'Online', x: 50, y: 150 },
    { id: 'matcher', name: 'Data Explorer & Telemetry', viewId: 'data_explorer', category: 'Ingestion', icon: 'analytics', port: ':8001', status: 'Online', x: 280, y: 150 }
  ]);
  const [connections, setConnections] = useState<Connection[]>([
    { id: 'conn-1', fromId: 'prof', toId: 'matcher' }
  ]);

  const [activePort, setActivePort] = useState<{ nodeId: string; type: 'in' | 'out' } | null>(null);
  const [draggedNodeId, setDraggedNodeId] = useState<string | null>(null);
  const dragStartOffset = useRef({ x: 0, y: 0 });
  const canvasRef = useRef<HTMLDivElement>(null);
  
  const [validationReport, setValidationReport] = useState<{ passed: boolean; message: string; details: string[] }>({
    passed: false,
    message: 'Pipeline Incomplete',
    details: ['Data Ingestion and Training API are not fully wired together.']
  });

  const runValidation = () => {
    const details: string[] = [];
    const hasIngestion = nodes.some(n => n.category === 'Ingestion');
    const hasExecution = nodes.some(n => n.id === 'train');
    const hasDeployment = nodes.some(n => n.id === 'deploy');

    // Simple path checking
    const adjacency = new Map<string, string[]>();
    connections.forEach(c => {
      const list = adjacency.get(c.fromId) || [];
      list.push(c.toId);
      adjacency.set(c.fromId, list);
    });

    // Check if there is a path from any Ingestion node to Train node, and from Train to Deploy
    let pathIngestionToTrain = false;
    let pathTrainToDeploy = false;

    const findPath = (start: string, end: string, visited = new Set<string>()): boolean => {
      if (start === end) return true;
      visited.add(start);
      const neighbors = adjacency.get(start) || [];
      for (const n of neighbors) {
        if (!visited.has(n)) {
          if (findPath(n, end, visited)) return true;
        }
      }
      return false;
    };

    const ingestionNodes = nodes.filter(n => n.category === 'Ingestion').map(n => n.id);
    ingestionNodes.forEach(iNode => {
      if (findPath(iNode, 'train')) pathIngestionToTrain = true;
    });

    if (findPath('train', 'deploy')) pathTrainToDeploy = true;

    if (!hasIngestion) details.push('Add at least one Data Ingestion component (Profiler or Prepare).');
    if (!hasExecution) details.push('Add the Train API component to run model HPO.');
    if (!hasDeployment) details.push('Add the Deploy API component to expose predictions.');
    
    if (hasIngestion && hasExecution && !pathIngestionToTrain) {
      details.push('Wire your Ingestion/Prepare nodes to the Model Training API.');
    }
    if (hasExecution && hasDeployment && !pathTrainToDeploy) {
      details.push('Wire the Train API to the Deploy API output.');
    }

    const passed = details.length === 0;
    setValidationReport({
      passed,
      message: passed ? 'Pipeline Fully Validated & Healthy!' : 'Pipeline Wiring Incomplete',
      details: passed ? ['All essential connections are established and active. Ready for deployment.'] : details
    });
  };

  useEffect(() => {
    runValidation();
  }, [nodes, connections]);

  const handleCanvasDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleCanvasDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const dataStr = e.dataTransfer.getData('text/plain');
    if (!dataStr) return;

    try {
      const template = JSON.parse(dataStr) as Omit<BoardNode, 'x' | 'y'>;
      
      // Ensure no duplicates on canvas for simplicity
      if (nodes.some(n => n.id === template.id)) {
        return;
      }

      const rect = canvasRef.current?.getBoundingClientRect();
      const x = rect ? e.clientX - rect.left - 100 : 100;
      const y = rect ? e.clientY - rect.top - 30 : 100;

      const newNode: BoardNode = {
        ...template,
        x: Math.max(10, Math.min(x, 1100)),
        y: Math.max(10, Math.min(y, 450))
      };

      setNodes(prev => [...prev, newNode]);
    } catch (err) {
      console.error(err);
    }
  };

  // Drag node on canvas
  const handlePointerDown = (e: React.PointerEvent, nodeId: string) => {
    if ((e.target as HTMLElement).closest('.port-circle')) return;
    e.preventDefault();
    setDraggedNodeId(nodeId);
    
    const node = nodes.find(n => n.id === nodeId);
    if (node) {
      dragStartOffset.current = {
        x: e.clientX - node.x,
        y: e.clientY - node.y
      };
    }
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!draggedNodeId) return;
    e.preventDefault();
    
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;

    const x = e.clientX - dragStartOffset.current.x;
    const y = e.clientY - dragStartOffset.current.y;

    setNodes(prev => prev.map(n => n.id === draggedNodeId ? {
      ...n,
      x: Math.max(10, Math.min(x, 1000)),
      y: Math.max(10, Math.min(y, 480))
    } : n));
  };

  const handlePointerUp = (e: React.PointerEvent) => {
    if (draggedNodeId) {
      e.preventDefault();
      (e.target as HTMLElement).releasePointerCapture(e.pointerId);
      setDraggedNodeId(null);
    }
  };

  // Handle port click to connect
  const handlePortClick = (nodeId: string, type: 'in' | 'out') => {
    if (!activePort) {
      setActivePort({ nodeId, type });
      return;
    }

    if (activePort.nodeId === nodeId) {
      setActivePort(null);
      return;
    }

    // Connect Out port to In port
    if (activePort.type === 'out' && type === 'in') {
      const connId = `conn-${activePort.nodeId}-${nodeId}`;
      if (!connections.some(c => c.fromId === activePort.nodeId && c.toId === nodeId)) {
        setConnections(prev => [...prev, { id: connId, fromId: activePort.nodeId, toId: nodeId }]);
      }
    } else if (activePort.type === 'in' && type === 'out') {
      const connId = `conn-${nodeId}-${activePort.nodeId}`;
      if (!connections.some(c => c.fromId === nodeId && c.toId === activePort.nodeId)) {
        setConnections(prev => [...prev, { id: connId, fromId: nodeId, toId: activePort.nodeId }]);
      }
    }

    setActivePort(null);
  };

  // Auto-wire pipeline en-to-end
  const handleAutoWire = () => {
    const layout = [
      { id: 'prof', viewId: 'node1' as ViewMode, x: 50, y: 150 },
      { id: 'matcher', viewId: 'node2' as ViewMode, x: 240, y: 150 },
      { id: 'recipe', viewId: 'node3' as ViewMode, x: 430, y: 150 },
      { id: 'prepare', viewId: 'node4' as ViewMode, x: 620, y: 150 },
      { id: 'feature', viewId: 'node5' as ViewMode, x: 810, y: 150 },
      { id: 'split', viewId: 'node6' as ViewMode, x: 50, y: 320 },
      { id: 'train', viewId: 'node7' as ViewMode, x: 240, y: 320 },
      { id: 'vg1', viewId: 'vg1' as ViewMode, x: 430, y: 320 },
      { id: 'vg2', viewId: 'vg2' as ViewMode, x: 620, y: 320 },
      { id: 'deploy', viewId: 'node9' as ViewMode, x: 810, y: 320 }
    ];

    const newNodes = layout.map(l => {
      const template = PALETTE_COMPONENTS.find(p => p.id === l.id)!;
      return {
        ...template,
        x: l.x,
        y: l.y
      };
    });

    const newConnections: Connection[] = [];
    for (let i = 0; i < layout.length - 1; i++) {
      newConnections.push({
        id: `conn-${layout[i].id}-${layout[i + 1].id}`,
        fromId: layout[i].id,
        toId: layout[i + 1].id
      });
    }

    setNodes(newNodes);
    setConnections(newConnections);
    setActivePort(null);
  };

  // Clear Board
  const handleClearBoard = () => {
    setNodes([]);
    setConnections([]);
    setActivePort(null);
  };

  return (
    <div className="flex flex-col gap-6 animate-fadeIn">
      {/* Board Header */}
      <div className="flex justify-between items-center glass-panel p-5 rounded-2xl shadow-xl"
        style={{background:'rgba(255,255,255,0.92)', border:'1.5px solid rgba(30,71,200,0.15)'}}>
        <div>
          <h1 className="text-xl font-bold flex items-center gap-2" style={{color:'#0D1533'}}>
            <span className="material-symbols-outlined text-[#1E47C8] text-2xl">hub</span>
            <span>MLOps Microservice Pipeline Orchestrator Board</span>
          </h1>
          <p className="text-xs text-slate-500 font-mono mt-1">
            Drag and connect compute blocks to customize data streaming and automated model routing.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleAutoWire}
            className="px-4 py-2 bg-[#1E47C8] hover:bg-[#1533A0] text-white text-xs font-mono font-bold rounded-xl flex items-center gap-1.5 shadow-lg shadow-blue-500/25 transition-all"
          >
            <span className="material-symbols-outlined text-sm">auto_mode</span>
            <span>Auto-Wire Sequence</span>
          </button>
          <button
            onClick={handleClearBoard}
            className="px-4 py-2 border border-slate-200 hover:bg-slate-50 text-slate-600 text-xs font-mono font-bold rounded-xl flex items-center gap-1.5 transition-all"
          >
            <span className="material-symbols-outlined text-sm">clear_all</span>
            <span>Clear Board</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-6 items-start">
        {/* Component Palette (Left Panel) */}
        <div className="col-span-1 glass-panel p-4 rounded-2xl flex flex-col gap-4 shadow-xl max-h-[600px] overflow-y-auto"
          style={{background:'rgba(255,255,255,0.92)', border:'1.5px solid rgba(13,21,51,0.08)'}}>
          <h2 className="text-xs font-mono font-bold uppercase pb-2 border-b text-slate-600">
            Categorized Palette
          </h2>
          
          {(['Ingestion', 'Orchestration', 'Engineering', 'Execution', 'Deployment'] as const).map(cat => {
            const catComp = PALETTE_COMPONENTS.filter(p => p.category === cat);
            return (
              <div key={cat} className="space-y-2">
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider block" style={{ color: CATEGORY_COLORS[cat].text }}>
                  {cat}
                </span>
                <div className="flex flex-col gap-1.5">
                  {catComp.map(comp => (
                    <div
                      key={comp.id}
                      draggable
                      onDragStart={(e) => {
                        e.dataTransfer.setData('text/plain', JSON.stringify(comp));
                        e.dataTransfer.effectAllowed = 'copy';
                      }}
                      className="flex items-center gap-2.5 p-2 bg-slate-50 border border-slate-100 hover:border-slate-300 rounded-xl cursor-grab transition-all text-xs font-mono"
                    >
                      <span className="material-symbols-outlined text-sm text-slate-500">{comp.icon}</span>
                      <span className="flex-1 truncate">{comp.name}</span>
                      <span className="text-[9px] px-1 bg-slate-200/50 rounded font-mono text-slate-500">{comp.port}</span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        {/* Drag-and-Drop Canvas Panel */}
        <div className="col-span-3 flex flex-col gap-6">
          <div
            ref={canvasRef}
            onDragOver={handleCanvasDragOver}
            onDrop={handleCanvasDrop}
            className="w-full h-[500px] rounded-2xl shadow-inner relative overflow-hidden glass-panel"
            style={{
              background: '#060914',
              backgroundImage: 'radial-gradient(rgba(200, 16, 46, 0.12) 1px, transparent 1px)',
              backgroundSize: '24px 24px',
              border: '1.5px solid rgba(255,255,255,0.06)'
            }}
          >
            {/* SVG Overlay for Connections */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none z-0">
              <defs>
                <marker
                  id="arrow"
                  viewBox="0 0 10 10"
                  refX="6"
                  refY="5"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 2 L 8 5 L 0 8 z" fill="rgba(255,255,255,0.4)" />
                </marker>
              </defs>
              
              {connections.map(conn => {
                const fromNode = nodes.find(n => n.id === conn.fromId);
                const toNode = nodes.find(n => n.id === conn.toId);
                if (!fromNode || !toNode) return null;

                // Derive ports position relative to node coordinate
                const x1 = fromNode.x + 200; // Out port is on right edge
                const y1 = fromNode.y + 35;  // Middle of height
                const x2 = toNode.x;         // In port is on left edge
                const y2 = toNode.y + 35;    // Middle of height

                // Draw curve path
                const dx = Math.abs(x2 - x1) * 0.4;
                const pathStr = `M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`;

                return (
                  <path
                    key={conn.id}
                    d={pathStr}
                    fill="none"
                    stroke="rgba(30, 71, 200, 0.65)"
                    strokeWidth="2.5"
                    markerEnd="url(#arrow)"
                    className="animate-pulse"
                    style={{ filter: 'drop-shadow(0 0 4px rgba(30, 71, 200, 0.4))' }}
                  />
                );
              })}
            </svg>

            {/* Canvas Nodes */}
            {nodes.map(node => {
              const colors = CATEGORY_COLORS[node.category];
              const isSelectedSource = activePort?.nodeId === node.id;
              
              return (
                <div
                  key={node.id}
                  onPointerDown={(e) => handlePointerDown(e, node.id)}
                  onPointerMove={handlePointerMove}
                  onPointerUp={handlePointerUp}
                  onDoubleClick={() => onSelectNode(node.viewId)}
                  className="absolute w-[200px] h-[70px] rounded-xl flex items-center justify-between px-3 cursor-move select-none z-10 transition-shadow duration-200 hover:shadow-2xl"
                  style={{
                    left: `${node.x}px`,
                    top: `${node.y}px`,
                    background: '#0d1533',
                    border: isSelectedSource ? '2px solid #5B8EF0' : `1.5px solid ${colors.border}`,
                    boxShadow: isSelectedSource ? '0 0 16px rgba(91,142,240,0.50)' : 'none'
                  }}
                >
                  {/* Left INPUT Port */}
                  <button
                    onClick={() => handlePortClick(node.id, 'in')}
                    className="port-circle absolute -left-2 top-1/2 -translate-y-1/2 w-4 h-4 rounded-full flex items-center justify-center bg-[#060914] border-2 transition-all hover:scale-125"
                    style={{ borderColor: colors.border }}
                    title="Input Port"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-[#7EB0FF]" />
                  </button>

                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-lg" style={{ color: colors.text }}>
                      {node.icon}
                    </span>
                    <div className="flex flex-col">
                      <span className="text-[10px] font-mono font-bold text-white truncate max-w-[120px]">
                        {node.name.split(':')[0]}
                      </span>
                      <span className="text-[9px] text-white/50 font-mono truncate max-w-[125px]">
                        {node.name.split(':').slice(1).join(':') || node.category}
                      </span>
                    </div>
                  </div>

                  <span className="text-[8px] font-mono px-1.5 py-0.5 rounded bg-white/5 text-white/40">
                    {node.port}
                  </span>

                  {/* Right OUTPUT Port */}
                  <button
                    onClick={() => handlePortClick(node.id, 'out')}
                    className="port-circle absolute -right-2 top-1/2 -translate-y-1/2 w-4 h-4 rounded-full flex items-center justify-center bg-[#060914] border-2 transition-all hover:scale-125"
                    style={{ borderColor: colors.border }}
                    title="Output Port"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-[#E8405A]" />
                  </button>
                </div>
              );
            })}
          </div>

          {/* Connection Validation Panel */}
          <div className="glass-panel p-5 rounded-2xl shadow-xl flex items-start gap-4"
            style={{
              background: 'rgba(58,18,89,0.95)',
              border: validationReport.passed ? '1.5px solid rgba(255,107,53,0.50)' : '1.5px solid rgba(255,255,255,0.20)'
            }}
          >
            <span className="material-symbols-outlined text-2xl mt-0.5"
              style={{ color: validationReport.passed ? '#FF6B35' : 'rgba(255,255,255,0.55)' }}
            >
              {validationReport.passed ? 'check_circle' : 'warning'}
            </span>
            <div className="flex-1 space-y-1">
              <span className="text-sm font-mono font-bold" style={{ color: '#FFFFFF' }}>
                {validationReport.message}
              </span>
              <ul className="text-xs font-mono text-white/50 list-disc list-inside space-y-1 pl-1">
                {validationReport.details.map((detail, idx) => (
                  <li key={idx}>{detail}</li>
                ))}
              </ul>
            </div>
            {validationReport.passed && (
              <button className="px-4 py-2 bg-[#FF6B35] hover:bg-[#E85520] text-white text-xs font-mono font-bold rounded-xl transition-all shadow-lg shadow-[#FF6B35]/25">
                Deploy Flow
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
