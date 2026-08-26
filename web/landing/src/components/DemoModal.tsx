import React, { useState } from 'react';
import { X, CheckCircle2, ArrowUpRight, Bot, Play } from 'lucide-react';

interface DemoModalProps {
  isOpen: boolean;
  type: 'start-jane' | 'book-demo' | 'watch-demo' | 'release' | null;
  onClose: () => void;
}

export const DemoModal: React.FC<DemoModalProps> = ({ isOpen, type, onClose }) => {
  if (!isOpen || !type) return null;

  const [submitted, setSubmitted] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    company: '',
    fleetSize: '10-50 assets',
    notes: ''
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="bg-white rounded-3xl max-w-lg w-full p-6 sm:p-8 shadow-2xl border border-[#E5E5E1] relative max-h-[90vh] overflow-y-auto">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 w-8 h-8 rounded-full bg-[#f3f4f5] hover:bg-[#e2e4e6] text-[#191c1d] flex items-center justify-center transition cursor-pointer"
          aria-label="Close modal"
        >
          <X className="w-4 h-4" />
        </button>

        {type === 'watch-demo' ? (
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-xs font-mono font-bold text-[#757964] uppercase tracking-widest">
              <Play className="w-4 h-4 text-[#006df8] fill-current" />
              <span>AIConneX 2.0 Product Tour</span>
            </div>
            <h3 className="text-2xl font-bold text-[#191c1d] tracking-tight font-sans">
              Watch Jane in Action
            </h3>
            <div className="bg-[#0e1824] rounded-2xl aspect-video relative flex items-center justify-center overflow-hidden border border-[#1f2d3d]">
              <div className="text-center p-6 space-y-3">
                <div className="w-12 h-12 rounded-full bg-[#d4f658] text-[#000000] flex items-center justify-center mx-auto shadow-lg">
                  <Play className="w-5 h-5 fill-current ml-0.5" />
                </div>
                <div className="text-sm font-mono text-white font-bold">Interactive Telemetry Walkthrough (3:14)</div>
                <p className="text-xs text-[#a4a9ad] font-sans max-w-xs">
                  See how Jane detects turbine bearing spallation 72 hours before vibration alarm trip.
                </p>
              </div>
            </div>
            <div className="pt-2 flex justify-end">
              <button
                onClick={onClose}
                className="bg-[#d4f658] hover:bg-[#c4ea42] text-[#000000] font-mono font-bold px-6 py-2.5 rounded-full text-xs uppercase tracking-wider transition cursor-pointer"
              >
                Close Preview
              </button>
            </div>
          </div>
        ) : type === 'release' ? (
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-[#d4f658] text-[#000000] text-xs font-mono font-bold">
              <span>RELEASE 2.0.4 // CHANGELOG</span>
            </div>
            <h3 className="text-2xl font-bold text-[#191c1d] tracking-tight font-sans">
              AIConneX 2.0 Released
            </h3>
            <div className="space-y-3 text-sm text-[#666666]">
              <div className="p-3 bg-[#f8f9fa] rounded-xl border border-[#E2E4E6]">
                <div className="font-bold text-[#191c1d]">Zero-Copy Apache DataFusion Ingest</div>
                <div className="text-xs text-[#666666] mt-1">4x reduction in CPU memory overhead on high-frequency vibration streams.</div>
              </div>
              <div className="p-3 bg-[#f8f9fa] rounded-xl border border-[#E2E4E6]">
                <div className="font-bold text-[#191c1d]">Jane Multi-Modal Reasoner</div>
                <div className="text-xs text-[#666666] mt-1">Cross-correlates SCADA telemetry with OEM PDF manuals and CAD schematics.</div>
              </div>
              <div className="p-3 bg-[#f8f9fa] rounded-xl border border-[#E2E4E6]">
                <div className="font-bold text-[#191c1d]">Direct SAP PM Two-Way Sync</div>
                <div className="text-xs text-[#666666] mt-1">Autonomous work order dispatch with closed-loop telemetry confirmation.</div>
              </div>
            </div>
            <div className="pt-2 flex justify-end">
              <button
                onClick={onClose}
                className="bg-[#d4f658] hover:bg-[#c4ea42] text-[#000000] font-mono font-bold px-6 py-2.5 rounded-full text-xs uppercase tracking-wider transition cursor-pointer"
              >
                Got It
              </button>
            </div>
          </div>
        ) : submitted ? (
          <div className="py-8 text-center space-y-4">
            <div className="w-14 h-14 rounded-full bg-[#d4f658] text-[#000000] flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-8 h-8" />
            </div>
            <h3 className="text-2xl font-bold text-[#191c1d]">
              Demo Access Initiated
            </h3>
            <p className="text-sm text-[#666666] max-w-sm mx-auto">
              Thanks {formData.name || 'there'}! A reliability solutions engineer and Jane sandbox invite will be dispatched to <strong className="text-[#191c1d]">{formData.email || 'your email'}</strong> within 15 minutes.
            </p>
            <button
              onClick={() => { setSubmitted(false); onClose(); }}
              className="mt-4 bg-[#000000] hover:bg-[#1f2328] text-white font-mono font-bold px-6 py-2.5 rounded-full text-xs uppercase tracking-wider cursor-pointer"
            >
              Done
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="inline-flex items-center gap-2 text-xs font-mono font-bold text-[#757964] uppercase tracking-widest">
              <Bot className="w-4 h-4 text-[#006df8]" />
              <span>{type === 'start-jane' ? 'Instant Sandbox Access' : 'Architecture Consultation'}</span>
            </div>

            <h3 className="text-2xl font-bold text-[#191c1d] tracking-tight font-sans">
              {type === 'start-jane' ? 'Start with Jane AI Platform' : 'Schedule a Custom Architecture Walkthrough'}
            </h3>

            <p className="text-xs text-[#666666]">
              Connect your telemetry, run zero-copy anomaly detection, and test predictive workflows on your plant assets.
            </p>

            <div className="space-y-3 pt-2">
              <div>
                <label className="block text-xs font-bold text-[#191c1d] uppercase font-mono mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. Alex Henderson"
                  className="w-full bg-[#f8f9fa] border border-[#E2E4E6] rounded-xl px-3.5 py-2 text-sm text-[#191c1d] focus:outline-hidden focus:ring-2 focus:ring-[#006df8]/20 focus:border-[#006df8]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-[#191c1d] uppercase font-mono mb-1">Work Email</label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="alex@enterprise-energy.com"
                  className="w-full bg-[#f8f9fa] border border-[#E2E4E6] rounded-xl px-3.5 py-2 text-sm text-[#191c1d] focus:outline-hidden focus:ring-2 focus:ring-[#006df8]/20 focus:border-[#006df8]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-[#191c1d] uppercase font-mono mb-1">Company / Plant</label>
                  <input
                    type="text"
                    required
                    value={formData.company}
                    onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                    placeholder="Siemens, ABB, etc."
                    className="w-full bg-[#f8f9fa] border border-[#E2E4E6] rounded-xl px-3.5 py-2 text-sm text-[#191c1d] focus:outline-hidden focus:ring-2 focus:ring-[#006df8]/20 focus:border-[#006df8]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-[#191c1d] uppercase font-mono mb-1">Fleet Assets</label>
                  <select
                    value={formData.fleetSize}
                    onChange={(e) => setFormData({ ...formData, fleetSize: e.target.value })}
                    className="w-full bg-[#f8f9fa] border border-[#E2E4E6] rounded-xl px-3 py-2 text-sm text-[#191c1d] focus:outline-hidden focus:ring-2 focus:ring-[#006df8]/20 focus:border-[#006df8]"
                  >
                    <option>1 - 10 assets</option>
                    <option>10 - 50 assets</option>
                    <option>50 - 200 assets</option>
                    <option>200+ global fleet</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="pt-4">
              <button
                type="submit"
                className="w-full flex items-center justify-center gap-2 bg-[#d4f658] hover:bg-[#c4ea42] text-[#000000] font-mono font-bold py-3 rounded-full text-xs uppercase tracking-wider transition cursor-pointer shadow-xs"
              >
                <span>Initiate Access</span>
                <ArrowUpRight className="w-4 h-4 stroke-[2.5]" />
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
