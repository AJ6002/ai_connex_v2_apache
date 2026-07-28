import React from 'react';

export const SupportView: React.FC = () => {
  return (
    <div className="space-y-6 pb-12 animate-fadeIn max-w-4xl">
      <div className="border-b border-slate-200 pb-4">
        <h1 className="font-headline text-3xl font-bold text-slate-900 tracking-tight">Documentation &amp; Support</h1>
        <p className="text-slate-500 text-xs mt-1">
          AI-Connexx Total Automation Solutions architectural documentation &amp; support channels.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white border border-slate-200 p-6 rounded-xl shadow-sm space-y-3">
          <span className="material-symbols-outlined text-tas-blue text-3xl">menu_book</span>
          <h3 className="font-headline text-base font-bold text-slate-900">Architecture Specifications</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Detailed breakdown of DAG Family classifications, Recipe Orchestrator steps, Validation Gateways VG_1 and VG_2, and distributed GPU cluster limits.
          </p>
          <a
            href="#docs"
            onClick={(e) => e.preventDefault()}
            className="inline-block text-xs font-mono font-bold text-tas-blue hover:text-tas-blue-hover hover:underline"
          >
            Read Technical Docs &rarr;
          </a>
        </div>

        <div className="bg-white border border-slate-200 p-6 rounded-xl shadow-sm space-y-3">
          <span className="material-symbols-outlined text-tas-blue text-3xl">support_agent</span>
          <h3 className="font-headline text-base font-bold text-slate-900">Priority Engineering Support</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Need custom pipeline recipes or cluster quota adjustments? Contact the Total Automation Solutions (TAS) engineering team directly.
          </p>
          <a
            href="#support"
            onClick={(e) => e.preventDefault()}
            className="inline-block text-xs font-mono font-bold text-tas-blue hover:text-tas-blue-hover hover:underline"
          >
            Open Support Ticket &rarr;
          </a>
        </div>
      </div>
    </div>
  );
};
