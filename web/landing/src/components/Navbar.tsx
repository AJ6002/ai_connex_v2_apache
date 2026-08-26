import React, { useState } from 'react';
import { ArrowUpRight, ArrowDownRight, ChevronDown, Database, Cpu, Users, Bot, Sparkles, Shield, Wrench, BarChart3, LineChart, FileText } from 'lucide-react';

interface NavbarProps {
  onStartWithJane: () => void;
  onOpenDemo: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onStartWithJane, onOpenDemo }) => {
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-[#E2E4E6] transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
        {/* Brand Logo */}
        <div className="flex items-center gap-10">
          <a href="#" className="flex items-center gap-2 group">
            <span className="text-2xl sm:text-[26px] font-bold tracking-tight text-[#191c1d] font-sans">
              AIConneX
            </span>
          </a>

          {/* Desktop Navigation Links */}
          <nav className="hidden lg:flex items-center gap-8 text-[15px] font-medium text-[#191c1d]">
            {/* Platform Dropdown */}
            <div 
              className="relative"
              onMouseEnter={() => setActiveDropdown('platform')}
              onMouseLeave={() => setActiveDropdown(null)}
            >
              <button 
                id="nav-platform-btn"
                className="flex items-center gap-1 hover:text-[#536600] transition-colors py-2 cursor-pointer"
              >
                <span>Platform</span>
                <ArrowDownRight className="w-3.5 h-3.5 text-[#757964] stroke-[2]" />
              </button>

              {activeDropdown === 'platform' && (
                <div className="absolute top-full left-0 w-80 bg-white border border-[#E2E4E6] rounded-2xl shadow-xl p-3 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                  <div className="text-[11px] font-bold uppercase tracking-widest text-[#757964] font-mono px-3 py-1.5">
                    Core Capabilities
                  </div>
                  <a href="#platform-section" className="flex items-start gap-3 p-2.5 rounded-xl hover:bg-[#f3f4f5] transition-colors">
                    <div className="p-2 bg-[#d4f658] text-[#000000] rounded-lg shrink-0 mt-0.5">
                      <Database className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-[#191c1d]">Neuron Data Platform</div>
                      <div className="text-xs text-[#666666]">Zero-copy multi-source industrial ETL & telemetry.</div>
                    </div>
                  </a>
                  <a href="#platform-section" className="flex items-start gap-3 p-2.5 rounded-xl hover:bg-[#f3f4f5] transition-colors">
                    <div className="p-2 bg-[#d4f658] text-[#000000] rounded-lg shrink-0 mt-0.5">
                      <Cpu className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-[#191c1d]">Process Builder</div>
                      <div className="text-xs text-[#666666]">Visual DAG workflow and agent pipelines.</div>
                    </div>
                  </a>
                  <a href="#platform-section" className="flex items-start gap-3 p-2.5 rounded-xl hover:bg-[#f3f4f5] transition-colors">
                    <div className="p-2 bg-[#d4f658] text-[#000000] rounded-lg shrink-0 mt-0.5">
                      <Users className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-[#191c1d]">Expert Network</div>
                      <div className="text-xs text-[#666666]">Human-in-the-loop mechanical verification.</div>
                    </div>
                  </a>
                  <a href="#platform-section" className="flex items-start gap-3 p-2.5 rounded-xl hover:bg-[#f3f4f5] transition-colors">
                    <div className="p-2 bg-[#006df8] text-white rounded-lg shrink-0 mt-0.5">
                      <Bot className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-[#191c1d]">Jane AI Agent</div>
                      <div className="text-xs text-[#666666]">Autonomous copilot for anomaly diagnosis.</div>
                    </div>
                  </a>
                </div>
              )}
            </div>

            {/* Solutions Dropdown */}
            <div 
              className="relative"
              onMouseEnter={() => setActiveDropdown('solutions')}
              onMouseLeave={() => setActiveDropdown(null)}
            >
              <button 
                id="nav-solutions-btn"
                className="flex items-center gap-1 hover:text-[#536600] transition-colors py-2 cursor-pointer"
              >
                <span>Solutions</span>
                <ArrowDownRight className="w-3.5 h-3.5 text-[#757964] stroke-[2]" />
              </button>

              {activeDropdown === 'solutions' && (
                <div className="absolute top-full left-0 w-80 bg-white border border-[#E2E4E6] rounded-2xl shadow-xl p-3 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                  <div className="text-[11px] font-bold uppercase tracking-widest text-[#757964] font-mono px-3 py-1.5">
                    Industrial Solutions
                  </div>
                  <button onClick={() => { setActiveDropdown(null); onOpenDemo(); }} className="w-full text-left flex items-start gap-3 p-2.5 rounded-xl hover:bg-[#f3f4f5] transition-colors cursor-pointer">
                    <div className="p-2 bg-[#f3f4f5] text-[#191c1d] rounded-lg shrink-0 mt-0.5">
                      <Wrench className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-[#191c1d]">Predictive Maintenance</div>
                      <div className="text-xs text-[#666666]">Forecast bearing and turbine failure 72h ahead.</div>
                    </div>
                  </button>
                  <button onClick={() => { setActiveDropdown(null); onOpenDemo(); }} className="w-full text-left flex items-start gap-3 p-2.5 rounded-xl hover:bg-[#f3f4f5] transition-colors cursor-pointer">
                    <div className="p-2 bg-[#f3f4f5] text-[#191c1d] rounded-lg shrink-0 mt-0.5">
                      <BarChart3 className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-[#191c1d]">Telemetry Ingestion</div>
                      <div className="text-xs text-[#666666]">High-throughput SCADA & OPC-UA streams.</div>
                    </div>
                  </button>
                  <button onClick={() => { setActiveDropdown(null); onOpenDemo(); }} className="w-full text-left flex items-start gap-3 p-2.5 rounded-xl hover:bg-[#f3f4f5] transition-colors cursor-pointer">
                    <div className="p-2 bg-[#f3f4f5] text-[#191c1d] rounded-lg shrink-0 mt-0.5">
                      <LineChart className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-[#191c1d]">Root Cause Analytics</div>
                      <div className="text-xs text-[#666666]">Instant multi-sensor correlation and logs.</div>
                    </div>
                  </button>
                </div>
              )}
            </div>

            {/* Resources Dropdown */}
            <div 
              className="relative"
              onMouseEnter={() => setActiveDropdown('resources')}
              onMouseLeave={() => setActiveDropdown(null)}
            >
              <button 
                id="nav-resources-btn"
                className="flex items-center gap-1 hover:text-[#536600] transition-colors py-2 cursor-pointer"
              >
                <span>Resources</span>
                <ArrowDownRight className="w-3.5 h-3.5 text-[#757964] stroke-[2]" />
              </button>

              {activeDropdown === 'resources' && (
                <div className="absolute top-full left-0 w-72 bg-white border border-[#E2E4E6] rounded-2xl shadow-xl p-3 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                  <button onClick={() => { setActiveDropdown(null); onOpenDemo(); }} className="w-full text-left flex items-center gap-3 p-2.5 rounded-xl hover:bg-[#f3f4f5] transition-colors cursor-pointer">
                    <FileText className="w-4 h-4 text-[#666666]" />
                    <span className="text-sm font-medium text-[#191c1d]">Product Walkthrough</span>
                  </button>
                  <button onClick={() => { setActiveDropdown(null); onOpenDemo(); }} className="w-full text-left flex items-center gap-3 p-2.5 rounded-xl hover:bg-[#f3f4f5] transition-colors cursor-pointer">
                    <Sparkles className="w-4 h-4 text-[#666666]" />
                    <span className="text-sm font-medium text-[#191c1d]">Architecture Review</span>
                  </button>
                  <button onClick={() => { setActiveDropdown(null); onOpenDemo(); }} className="w-full text-left flex items-center gap-3 p-2.5 rounded-xl hover:bg-[#f3f4f5] transition-colors cursor-pointer">
                    <Shield className="w-4 h-4 text-[#666666]" />
                    <span className="text-sm font-medium text-[#191c1d]">Security Whitepaper</span>
                  </button>
                </div>
              )}
            </div>

            {/* Company Dropdown */}
            <div 
              className="relative"
              onMouseEnter={() => setActiveDropdown('company')}
              onMouseLeave={() => setActiveDropdown(null)}
            >
              <button 
                id="nav-company-btn"
                className="flex items-center gap-1 hover:text-[#536600] transition-colors py-2 cursor-pointer"
              >
                <span>Company</span>
                <ArrowDownRight className="w-3.5 h-3.5 text-[#757964] stroke-[2]" />
              </button>

              {activeDropdown === 'company' && (
                <div className="absolute top-full left-0 w-64 bg-white border border-[#E2E4E6] rounded-2xl shadow-xl p-3 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                  <button onClick={() => { setActiveDropdown(null); onOpenDemo(); }} className="w-full text-left block p-2 rounded-lg hover:bg-[#f3f4f5] text-sm font-medium text-[#191c1d] cursor-pointer">About AIConneX</button>
                  <button onClick={() => { setActiveDropdown(null); onOpenDemo(); }} className="w-full text-left block p-2 rounded-lg hover:bg-[#f3f4f5] text-sm font-medium text-[#191c1d] cursor-pointer">Careers <span className="text-[10px] bg-[#d4f658] text-[#000000] px-1.5 py-0.5 rounded font-mono ml-1 font-bold">WE'RE HIRING</span></button>
                  <button onClick={() => { setActiveDropdown(null); onOpenDemo(); }} className="w-full text-left block p-2 rounded-lg hover:bg-[#f3f4f5] text-sm font-medium text-[#191c1d] cursor-pointer">Contact Sales</button>
                </div>
              )}
            </div>
          </nav>
        </div>

        {/* Right CTA Button */}
        <div className="hidden sm:flex items-center gap-3">
          <button
            id="nav-start-jane-btn"
            onClick={onStartWithJane}
            className="flex items-center gap-2 bg-[#d4f658] hover:bg-[#c4ea42] text-[#000000] font-mono font-bold px-6 py-2.5 rounded-full text-xs uppercase tracking-wider transition-all duration-150 cursor-pointer shadow-xs hover:scale-[1.02]"
          >
            <ArrowUpRight className="w-3.5 h-3.5 stroke-[2.5]" />
            <span>START WITH JANE</span>
          </button>
        </div>

        {/* Mobile Menu Button */}
        <div className="flex lg:hidden items-center gap-2">
          <button
            id="mobile-start-jane-btn"
            onClick={onStartWithJane}
            className="flex items-center gap-1 bg-[#d4f658] text-[#000000] font-mono font-bold px-3.5 py-1.5 rounded-full text-[11px] uppercase tracking-wider"
          >
            <ArrowUpRight className="w-3.5 h-3.5 stroke-[2.5]" />
            <span>Jane</span>
          </button>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 text-[#191c1d] hover:text-[#666666]"
            aria-label="Toggle menu"
          >
            <ChevronDown className={`w-5 h-5 transition-transform ${mobileMenuOpen ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-[#E2E4E6] bg-[#f8f9fa] px-4 pt-3 pb-6 space-y-3">
          <a href="#platform-section" onClick={() => setMobileMenuOpen(false)} className="block py-2 text-[#191c1d] font-medium">Platform Overview</a>
          <button onClick={() => { setMobileMenuOpen(false); onOpenDemo(); }} className="block w-full text-left py-2 text-[#191c1d] font-medium cursor-pointer">Solutions & Workflows</button>
          <button onClick={() => { setMobileMenuOpen(false); onOpenDemo(); }} className="block w-full text-left py-2 text-[#191c1d] font-medium cursor-pointer">Security & Architecture</button>
          <div className="pt-2 flex flex-col gap-2">
            <button
              onClick={() => { setMobileMenuOpen(false); onOpenDemo(); }}
              className="w-full text-center py-2.5 rounded-full border border-[#000000] bg-white text-[#000000] text-xs font-mono font-bold uppercase tracking-wider cursor-pointer"
            >
              Watch Demo
            </button>
            <button
              onClick={() => { setMobileMenuOpen(false); onStartWithJane(); }}
              className="w-full text-center py-2.5 rounded-full bg-[#d4f658] text-[#000000] text-xs font-mono font-bold uppercase tracking-wider cursor-pointer shadow-xs"
            >
              Start with Jane
            </button>
          </div>
        </div>
      )}
    </header>
  );
};

