import React from 'react';
import { ShieldCheck, Lock, Server } from 'lucide-react';

export const EnterpriseTrustBento: React.FC = () => {
  return (
    <section id="security" className="py-16 sm:py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-[#E5E5E1]">
      <div className="text-center max-w-3xl mx-auto mb-14">
        <div className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-[#6B6B6B] font-mono mb-3">
          <span className="w-2 h-2 rounded-full bg-[#1A1A1A]" />
          <span>SECURITY & COMPLIANCE INFRASTRUCTURE</span>
        </div>
        <h2 className="text-3xl sm:text-5xl font-bold text-[#1A1A1A] tracking-tight leading-tight">
          Air-gapped security for mission-critical infrastructure.
        </h2>
        <p className="mt-4 text-[#6B6B6B] text-base sm:text-lg">
          Zero data retention for LLM training. Full customer data residency and hardware-enforced encryption.
        </p>
      </div>

      {/* Bento Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Card 1 */}
        <div className="bg-white border border-[#E5E5E1] rounded-3xl p-7 flex flex-col justify-between hover:border-[#1A1A1A] transition shadow-2xs">
          <div className="space-y-4">
            <div className="w-10 h-10 rounded-2xl bg-[#EEEBE5] text-[#1A1A1A] flex items-center justify-center">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="text-xl font-bold text-[#1A1A1A]">SOC 2 Type II & ISO 27001</h3>
            <p className="text-sm text-[#6B6B6B] leading-relaxed">
              Independently audited by top-tier assurance firms. Continuous automated compliance monitoring with HIPAA and GDPR ready controls.
            </p>
          </div>
          <div className="pt-6 font-mono text-[11px] font-bold text-[#A1A19A]">
            AUDIT REPORT AVAILABLE ON REQUEST
          </div>
        </div>

        {/* Card 2 */}
        <div className="bg-white border border-[#E5E5E1] rounded-3xl p-7 flex flex-col justify-between hover:border-[#1A1A1A] transition shadow-2xs">
          <div className="space-y-4">
            <div className="w-10 h-10 rounded-2xl bg-[#EEEBE5] text-[#1A1A1A] flex items-center justify-center">
              <Server className="w-5 h-5" />
            </div>
            <h3 className="text-xl font-bold text-[#1A1A1A]">Air-Gapped & On-Premise</h3>
            <p className="text-sm text-[#6B6B6B] leading-relaxed">
              Deploy AIConneX directly inside your plant firewall or Kubernetes edge clusters without outbound internet connectivity requirements.
            </p>
          </div>
          <div className="pt-6 font-mono text-[11px] font-bold text-[#A1A19A]">
            K8S / OPENVINO / TENSORRT COMPATIBLE
          </div>
        </div>

        {/* Card 3 */}
        <div className="bg-white border border-[#E5E5E1] rounded-3xl p-7 flex flex-col justify-between hover:border-[#1A1A1A] transition shadow-2xs">
          <div className="space-y-4">
            <div className="w-10 h-10 rounded-2xl bg-[#EEEBE5] text-[#1A1A1A] flex items-center justify-center">
              <Lock className="w-5 h-5" />
            </div>
            <h3 className="text-xl font-bold text-[#1A1A1A]">Zero LLM Data Retention</h3>
            <p className="text-sm text-[#6B6B6B] leading-relaxed">
              Your proprietary sensor telemetry, P&IDs, and mechanical logs are never used to train public foundational models. Complete tenant isolation.
            </p>
          </div>
          <div className="pt-6 font-mono text-[11px] font-bold text-[#A1A19A]">
            HARDWARE-ENFORCED ENCRYPTION AT REST
          </div>
        </div>
      </div>
    </section>
  );
};

