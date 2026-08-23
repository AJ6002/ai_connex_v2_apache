import React, { useState } from 'react';
import { BillableRun } from '../types';

interface QuotasViewProps {
  billableRuns: BillableRun[];
  onExportReport: () => void;
  onAdjustQuotas: () => void;
}

export const QuotasView: React.FC<QuotasViewProps> = ({
  billableRuns,
  onExportReport,
  onAdjustQuotas,
}) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [filterTier, setFilterTier] = useState<string>('ALL');

  const filteredRuns = filterTier === 'ALL'
    ? billableRuns
    : billableRuns.filter(r => r.resourceTier.includes(filterTier));

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* Header & Main Actions */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="font-headline text-3xl font-bold text-slate-900 tracking-tight">
            Quotas &amp; Resource Usage
          </h1>
          <p className="text-slate-500 text-xs mt-1">
            Administrative overview of fleet compute expenditure and allocation across US-EAST-1 clusters.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onExportReport}
            className="px-4 py-2 border border-slate-300 text-slate-700 hover:bg-slate-50 font-bold text-xs rounded-lg transition-all shadow-xs"
          >
            EXPORT REPORT
          </button>
          <button
            onClick={onAdjustQuotas}
            className="px-4 py-2 bg-tas-blue hover:bg-tas-blue-hover text-white font-bold text-xs rounded-lg transition-all shadow-xs active:scale-95"
          >
            ADJUST QUOTAS
          </button>
        </div>
      </div>

      {/* KPI Stats Bento Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1 */}
        <div className="bg-white border border-slate-200 p-5 rounded-xl shadow-sm">
          <div className="flex justify-between items-start mb-3">
            <span className="text-[11px] font-mono font-bold text-slate-400 uppercase tracking-wider">
              CURRENT MONTHLY SPEND
            </span>
            <span className="material-symbols-outlined text-tas-blue">payments</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-mono text-3xl font-bold text-slate-900">$14,204</span>
            <span className="text-xs font-mono font-bold text-tas-red flex items-center">
              <span className="material-symbols-outlined text-xs">trending_up</span> 8.4%
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">Vs. last month ($13,103)</p>
        </div>

        {/* KPI 2 */}
        <div className="bg-white border border-slate-200 p-5 rounded-xl shadow-sm">
          <div className="flex justify-between items-start mb-3">
            <span className="text-[11px] font-mono font-bold text-slate-400 uppercase tracking-wider">
              ACTIVE COMPUTE RUNS
            </span>
            <span className="material-symbols-outlined text-tas-blue">memory</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-mono text-3xl font-bold text-slate-900">42</span>
            <span className="text-xs font-mono font-bold text-tas-blue">STABLE</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">12 high-priority GPU jobs</p>
        </div>

        {/* KPI 3 */}
        <div className="bg-white border border-slate-200 p-5 rounded-xl shadow-sm">
          <div className="flex justify-between items-start mb-3">
            <span className="text-[11px] font-mono font-bold text-slate-400 uppercase tracking-wider">
              ALLOCATION EFFICIENCY
            </span>
            <span className="material-symbols-outlined text-tas-blue">speed</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-mono text-3xl font-bold text-slate-900">92%</span>
            <span className="text-xs font-mono font-bold text-[#FF6B35] flex items-center">
              <span className="material-symbols-outlined text-xs">trending_flat</span> +0.2%
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">Resource waste minimized</p>
        </div>

        {/* KPI 4 */}
        <div className="bg-white border border-slate-200 p-5 rounded-xl shadow-sm">
          <div className="flex justify-between items-start mb-3">
            <span className="text-[11px] font-mono font-bold text-slate-400 uppercase tracking-wider">
              BUDGET REMAINING
            </span>
            <span className="material-symbols-outlined text-tas-blue">account_balance_wallet</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-mono text-3xl font-bold text-slate-900">$5,796</span>
            <span className="text-xs font-mono font-bold text-tas-red flex items-center">
              <span className="material-symbols-outlined text-xs">warning</span> 21%
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">Refills on 1st of month</p>
        </div>
      </div>

      {/* Cluster Usage Visualizations (Donut Charts) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* GPU Cluster Usage */}
        <div className="bg-white border border-slate-200 p-6 rounded-xl shadow-sm flex flex-col md:flex-row items-center gap-8">
          <div className="relative w-44 h-44 flex-shrink-0">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
              <path
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="#e2e8f0"
                strokeWidth="3.5"
              />
              <path
                className="donut-ring"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="#23388B"
                strokeDasharray="78, 100"
                strokeWidth="3.5"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="font-mono text-3xl font-bold text-slate-900">78%</span>
              <span className="text-[9px] font-mono font-bold text-slate-400 uppercase tracking-widest">
                GPU LOAD
              </span>
            </div>
          </div>

          <div className="flex-1 space-y-3 w-full">
            <h3 className="font-headline text-lg font-bold text-slate-900 tracking-tight">GPU Cluster Usage</h3>
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between items-center border-b border-slate-100 pb-1.5">
                <span className="text-slate-500">Allocated Hours Used</span>
                <span className="font-bold text-slate-900">1,560 / 2,000 hrs</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500">Remaining Quota</span>
                <span className="font-bold text-slate-900">440 hrs</span>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-200 flex items-start gap-2 text-[11px] text-slate-600">
              <span className="material-symbols-outlined text-tas-red text-sm mt-0.5">info</span>
              <p className="leading-relaxed">
                Cluster utilization peaked during "Alpha-Model-Training" between 02:00 and 04:00 UTC today. Projection suggests quota exhaustion in 6 days.
              </p>
            </div>
          </div>
        </div>

        {/* CPU Core Hours */}
        <div className="bg-white border border-slate-200 p-6 rounded-xl shadow-sm flex flex-col md:flex-row items-center gap-8">
          <div className="relative w-44 h-44 flex-shrink-0">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
              <path
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="#e2e8f0"
                strokeWidth="3.5"
              />
              <path
                className="donut-ring"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="#23388B"
                strokeDasharray="42, 100"
                strokeWidth="3.5"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="font-mono text-3xl font-bold text-slate-900">42%</span>
              <span className="text-[9px] font-mono font-bold text-slate-400 uppercase tracking-widest">
                CPU LOAD
              </span>
            </div>
          </div>

          <div className="flex-1 space-y-3 w-full">
            <h3 className="font-headline text-lg font-bold text-slate-900 tracking-tight">CPU Core Hours</h3>
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between items-center border-b border-slate-100 pb-1.5">
                <span className="text-slate-500">Allocated Hours Used</span>
                <span className="font-bold text-slate-900">4,200 / 10,000 hrs</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500">Remaining Quota</span>
                <span className="font-bold text-slate-900">5,800 hrs</span>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-200 flex items-start gap-2 text-[11px] text-slate-600">
              <span className="material-symbols-outlined text-[#FF6B35] text-sm mt-0.5">check_circle</span>
              <p className="leading-relaxed">
                CPU resources are currently underutilized. Consider scheduling maintenance or asynchronous batch processing tasks to maximize fleet value.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Billable Runs Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-200 flex justify-between items-center bg-slate-50/50">
          <h3 className="font-headline text-lg font-bold text-slate-900 tracking-tight">Recent Billable Runs</h3>

          <div className="flex items-center gap-4 text-xs font-mono font-bold text-slate-500">
            <div className="flex items-center gap-1.5">
              <span>FILTER TIER:</span>
              <select
                value={filterTier}
                onChange={(e) => setFilterTier(e.target.value)}
                className="bg-white border border-slate-200 px-2.5 py-1 rounded-md text-xs text-slate-900 outline-none focus:ring-2 focus:ring-tas-blue"
              >
                <option value="ALL">ALL TIERS</option>
                <option value="A100">A100-80GB</option>
                <option value="V100">V100-32GB</option>
                <option value="CPU">STANDARD-CPU</option>
              </select>
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-100 text-slate-500 font-mono text-[11px] uppercase tracking-wider border-b border-slate-200">
                <th className="px-6 py-3.5 font-semibold">Timestamp</th>
                <th className="px-6 py-3.5 font-semibold">User</th>
                <th className="px-6 py-3.5 font-semibold">Operation</th>
                <th className="px-6 py-3.5 font-semibold">Resource Tier</th>
                <th className="px-6 py-3.5 font-semibold">Duration</th>
                <th className="px-6 py-3.5 font-semibold text-right">Cost</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs">
              {filteredRuns.map((run) => (
                <tr key={run.id} className="hover:bg-slate-50 transition-colors cursor-pointer">
                  <td className="px-6 py-4 font-mono text-slate-900">{run.timestamp}</td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div
                        className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold font-mono ${run.userColor}`}
                      >
                        {run.userInitials}
                      </div>
                      <span className="font-medium text-slate-900">{run.userName}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-slate-600">{run.operation}</td>
                  <td className="px-6 py-4">
                    <span
                      className={`px-2 py-0.5 text-[10px] font-mono font-bold uppercase rounded ${run.tierBadgeColor}`}
                    >
                      {run.resourceTier}
                    </span>
                  </td>
                  <td className="px-6 py-4 font-mono text-slate-900">{run.duration}</td>
                  <td className="px-6 py-4 font-mono text-right text-tas-blue font-bold">
                    ${run.cost.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Table Footer Pagination */}
        <div className="p-4 bg-slate-50/50 border-t border-slate-200 flex justify-between items-center text-xs font-mono font-bold text-slate-500 uppercase">
          <span>Showing {filteredRuns.length} of 248 entries</span>
          <div className="flex items-center gap-2">
            <button
              disabled={currentPage === 1}
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              className="px-3 py-1 border border-slate-200 rounded-md hover:bg-white transition-all disabled:opacity-40"
            >
              PREV
            </button>
            <button className="px-3 py-1 bg-tas-blue text-white rounded-md">1</button>
            <button className="px-3 py-1 border border-slate-200 rounded-md hover:bg-white transition-all">2</button>
            <button className="px-3 py-1 border border-slate-200 rounded-md hover:bg-white transition-all">3</button>
            <button
              onClick={() => setCurrentPage((p) => p + 1)}
              className="px-3 py-1 border border-slate-200 rounded-md hover:bg-white transition-all"
            >
              NEXT
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
