import React, { useState, useEffect } from 'react';

export const DeveloperStudioView: React.FC = () => {
  const [logs, setLogs] = useState<Array<{ timestamp: string; level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG'; message: string }>>([
    { timestamp: '14:22:01.042', level: 'INFO', message: 'Initialized Cluster US-EAST-1 Node #42 with GPU A100-80GB' },
    { timestamp: '14:22:05.189', level: 'INFO', message: 'Recipe Orchestrator DAG #8042 loaded 2,400,000 profiling rows' },
    { timestamp: '14:22:12.630', level: 'WARN', message: 'Data Drift detected in Feature [vibration_index]: +2.4% shift' },
    { timestamp: '14:22:20.911', level: 'INFO', message: 'Validation Gateway VG_1 passed: Accuracy score 94.2% >= 90.0%' },
    { timestamp: '14:22:28.402', level: 'INFO', message: 'Validation Gateway VG_2 passed: Latency 28ms <= 50ms' },
    { timestamp: '14:22:35.001', level: 'DEBUG', message: 'Checkpoint saved to s3://ai-connexx-artifacts/models/v2.4.1/model.pt' }
  ]);

  const [isStreaming, setIsStreaming] = useState(true);
  const [logFilter, setLogFilter] = useState<'ALL' | 'INFO' | 'WARN' | 'ERROR'>('ALL');
  const [searchTerm, setSearchTerm] = useState('');

  // Simulate periodic log streaming
  useEffect(() => {
    if (!isStreaming) return;
    const interval = setInterval(() => {
      const now = new Date();
      const timeStr = now.toTimeString().split(' ')[0] + '.' + String(now.getMilliseconds()).padStart(3, '0');
      const sampleLogs: Array<{ level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG'; message: string }> = [
        { level: 'INFO', message: 'Telemetry ping received from Edge Engine #104 [Latency: 24ms]' },
        { level: 'INFO', message: 'Inference request served for model Alpha_Predict_V4 [200 OK]' },
        { level: 'DEBUG', message: 'Prometheus metrics scraped: memory_usage_bytes=142049102' },
        { level: 'WARN', message: 'GPU temperature warm: 72C on Node-04 (Safe threshold 85C)' },
      ];
      const randomLog = sampleLogs[Math.floor(Math.random() * sampleLogs.length)];
      setLogs((prev) => [...prev.slice(-100), { timestamp: timeStr, ...randomLog }]);
    }, 3000);

    return () => clearInterval(interval);
  }, [isStreaming]);

  const filteredLogs = logs.filter((l) => {
    if (logFilter !== 'ALL' && l.level !== logFilter) return false;
    if (searchTerm && !l.message.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="font-headline text-3xl font-bold text-slate-900 tracking-tight">Developer Studio</h1>
          <p className="text-slate-500 text-xs mt-1">
            Real-time telemetry stream, cluster stdout/stderr log inspector, and live worker threads.
          </p>
        </div>

        <div className="flex items-center gap-3 font-mono text-xs">
          <button
            onClick={() => setIsStreaming(!isStreaming)}
            className={`px-4 py-2 rounded-lg font-bold flex items-center gap-2 transition-all shadow-xs ${
              isStreaming ? 'bg-tas-red hover:bg-tas-red-hover text-white' : 'bg-tas-blue hover:bg-tas-blue-hover text-white'
            }`}
          >
            <span className="material-symbols-outlined text-sm">
              {isStreaming ? 'pause' : 'play_arrow'}
            </span>
            <span>{isStreaming ? 'Pause Stream' : 'Resume Stream'}</span>
          </button>

          <button
            onClick={() => setLogs([])}
            className="px-3 py-2 border border-slate-200 text-slate-600 hover:bg-slate-50 rounded-lg font-semibold transition-colors"
          >
            Clear Console
          </button>
        </div>
      </div>

      {/* Console Controls & Search */}
      <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-sm flex flex-wrap justify-between items-center gap-4">
        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="text-slate-400 font-bold">LEVEL:</span>
          {(['ALL', 'INFO', 'WARN', 'ERROR'] as const).map((lvl) => (
            <button
              key={lvl}
              onClick={() => setLogFilter(lvl)}
              className={`px-3 py-1 rounded-md text-xs font-bold transition-colors ${
                logFilter === lvl
                  ? 'bg-tas-blue text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {lvl}
            </button>
          ))}
        </div>

        <div className="relative w-64">
          <span className="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400 text-sm">
            search
          </span>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Filter logs by keyword..."
            className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-8 pr-3 py-1.5 text-xs font-mono outline-none focus:ring-2 focus:ring-tas-blue"
          />
        </div>
      </div>

      {/* Terminal Display */}
      <div className="bg-[#1A0530] text-[#FF6B35] font-mono text-xs rounded-xl border border-white/10 shadow-xl p-5 h-96 overflow-y-auto space-y-1.5 leading-relaxed">
        {filteredLogs.length === 0 ? (
          <div className="text-white/35 italic">No logs match the selected filter.</div>
        ) : (
          filteredLogs.map((log, idx) => (
            <div key={idx} className="flex items-start gap-3">
              <span className="text-white/35 flex-shrink-0">[{log.timestamp}]</span>
              <span
                className={`font-bold px-1.5 py-0.2 rounded text-[10px] uppercase flex-shrink-0 ${
                  log.level === 'INFO'
                    ? 'bg-[#FF6B35]/20 text-[#FF6B35]'
                    : log.level === 'WARN'
                    ? 'bg-white/10 text-white/70'
                    : log.level === 'ERROR'
                    ? 'bg-white/8 text-white/50'
                    : 'bg-white/5 text-white/40'
                }`}
              >
                {log.level}
              </span>
              <span className="text-white/85 break-all">{log.message}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
