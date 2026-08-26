import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import lottie, { AnimationItem } from 'lottie-web';
import './LandingPage.css';

interface LottiePlayerProps {
  animationPath: string;
  className?: string;
  loop?: boolean;
  autoplay?: boolean;
}

function LottiePlayer({ animationPath, className, loop = true, autoplay = true }: LottiePlayerProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const anim: AnimationItem = lottie.loadAnimation({
      container: containerRef.current,
      renderer: 'svg',
      loop,
      autoplay,
      path: animationPath,
    });

    return () => {
      anim.destroy();
    };
  }, [animationPath, loop, autoplay]);

  return <div ref={containerRef} className={className} />;
}

import { LandingNavbar } from './LandingNavbar';
import { PlatformShowcase } from './PlatformShowcase';
import { WorkflowArchitecture } from './WorkflowArchitecture';
import { CorePillars } from './CorePillars';
import { DowntimeSimulator } from './DowntimeSimulator';
import { KnowledgeSearchSection } from './KnowledgeSearchSection';

const REEL_WORDS = [
  'intelligent decisions.',
  'predictive maintenance.',
  'anomaly detection.',
  'quality intelligence.',
  'automated ML workflows.',
] as const;

const MARQUEE_ITEMS = [
  'Trained >80% of World’s Leading AI Models',
  '44,000+ Decision Makers',
  'SOC 2 Type II Certified',
  'Zero-Copy Apache DataFusion Processing',
  'ISO 27001 & HIPAA Compliant',
];

/**
 * Public marketing landing page — faithful to STITCH-Design/landing.
 * Light "Schematic Minimalist" theme; standalone (NOT inside the dark AppShell).
 * Scoped light tokens live in LandingPage.css under `.lp`.
 */
export function LandingPage() {
  const [reelIndex, setReelIndex] = useState<number>(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setReelIndex((prev) => (prev + 1) % REEL_WORDS.length);
    }, 2800);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('lp__reveal--visible');
          }
        });
      },
      { threshold: 0.15 }
    );

    const elements = document.querySelectorAll('.lp__reveal');
    elements.forEach((el) => observer.observe(el));

    return () => observer.disconnect();
  }, []);

  return (
    <div className="lp">
      {/* ── Announcement banner ────────────────────────────────────────── */}
      <div className="lp__banner">
        <span>AIConneX 2.0 Released: Autonomous Agent Orchestration at Scale</span>
        <a className="lp__banner-pill" href="#release">
          <span className="material-symbols-outlined">north_east</span> READ RELEASE
        </a>
      </div>

      {/* ── Fixed Floating Navigation ──────────────────────────────────── */}
      <LandingNavbar />

      {/* ── Hero ───────────────────────────────────────────────────────── */}
      <section className="lp__hero lp__grid-bg" id="top">
        <div className="lp__hero-inner lp__reveal">
          {/* Animated Industrial Compressor GIF centered above headline */}
          <div className="lp__hero-gif-container">
            <img
              src="/compresser.gif"
              alt="AIConneX Industrial Compressor Analytics"
              className="lp__hero-gif"
            />
          </div>

          <h1 className="lp__hero-title">
            Turn <span className="lp__hero-title-muted">industrial data</span> into<br />
            <span className="lp__reel-viewport">
              <span
                className="lp__reel-track"
                style={{ transform: `translateY(-${reelIndex * 1.15}em)` }}
              >
                {REEL_WORDS.map((word) => (
                  <span key={word} className="lp__reel-item">
                    {word}
                  </span>
                ))}
              </span>
            </span>
          </h1>

          <p className="lp__hero-sub">
            Talk to Jane to explore your data, understand what is happening, build ML workflows, and move results toward deployment.
          </p>

          <div className="lp__hero-ctas">
            <Link to="/intake" className="lp__cta-black">
              <span className="material-symbols-outlined">north_east</span> GET STARTED
            </Link>
            <a href="#demo" className="lp__cta-outline">
              WATCH DEMO
            </a>
          </div>
        </div>

        {/* ── Invisible-Tech style: full-bleed lottie layer, no card container ── */}
        <div className="lp__hero-lottie-wrapper" aria-hidden="true">
          {/* Slot _2 — right flank (Automation Workflow) */}
          <div className="lp__lottie-slot lp__lottie-slot--2">
            <LottiePlayer
              animationPath="/animations/automation.json"
              className="lp__lottie hp__lottie--automation"
            />
          </div>
        </div>
      </section>

      {/* ── Marquee Ticker ──────────────────────────────────────────────── */}
      <div className="lp__marquee">
        <div className="lp__marquee-track">
          {[...MARQUEE_ITEMS, ...MARQUEE_ITEMS].map((item, idx) => (
            <div key={`${item}-${idx}`} className="lp__marquee-item">
              <span className="lp__marquee-dot" />
              <span>{item}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Platform showcase ──────────────────────────────────────────── */}
      <PlatformShowcase />

      {/* ── Dovetail-Inspired 4-Step Workflow Architecture ─────────────── */}
      <WorkflowArchitecture />

      {/* ── 4 Core Solution & Data Architecture Pillars ────────────────── */}
      <CorePillars />

      {/* ── Interactive Financial & Downtime Simulator ──────────────────── */}
      <DowntimeSimulator />

      {/* ── Knowledge Intelligence Engine / Search Section ─────────────── */}
      <KnowledgeSearchSection />

      {/* ── Dark transition ────────────────────────────────────────────── */}
      <section className="lp__dark">
        <div className="lp__dark-glow" aria-hidden="true" />
        <div className="lp__dark-inner lp__reveal">
          <div className="lp__dark-icon">
            <div className="lp__dark-icon-sq" />
          </div>
          <h2 className="lp__dark-title">
            From people to process to platform, we solve the thing behind the thing.
          </h2>
          <p className="lp__dark-sub">Call it services-to-software. Or just call it done.</p>
        </div>
      </section>

      {/* ── Footer ─────────────────────────────────────────────────────── */}
      <footer className="lp__footer">
        <div className="lp__footer-brand">
          <span className="lp__footer-name">AI Connex</span>
          <p className="lp__footer-copy">© 2024 AI Connex. All rights reserved.</p>
        </div>
        <div className="lp__footer-col">
          <a href="#solutions">SOLUTIONS</a>
          <a href="#platform">PLATFORM</a>
          <a href="#datalab">DATA LAB</a>
        </div>
        <div className="lp__footer-col">
          <a href="#resources">RESOURCES</a>
          <a href="#company">COMPANY</a>
        </div>
        <div className="lp__footer-col">
          <a href="#soc2">SOC 2</a>
          <a href="#iso">ISO 27001</a>
          <a href="#hipaa">HIPAA</a>
        </div>
      </footer>
    </div>
  );
}
