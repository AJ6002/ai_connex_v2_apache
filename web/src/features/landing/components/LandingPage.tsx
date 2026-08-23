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

const NAV_LINKS = ['Platform', 'Solutions', 'Agent Engine', 'Data Lab', 'Resources', 'Company'];

const SHOWCASE_TABS = [
  'Agent Workflows',
  'Data Engine',
  'Expert Network',
  'Evals',
  'RL Labs',
] as const;

const REEL_WORDS = [
  'enterprise scale',
  'insurance',
  'life sciences',
  'frontline enterprise',
  'financial services',
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
  const [activeTab, setActiveTab] = useState<(typeof SHOWCASE_TABS)[number]>('Agent Workflows');
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
        <span>AI Connex 2.0 Released: Autonomous Agent Orchestration at Scale</span>
        <a className="lp__banner-pill" href="#release">
          <span className="material-symbols-outlined">north_east</span> READ RELEASE
        </a>
      </div>

      {/* ── Top nav (Sticky Glassmorphism) ──────────────────────────────── */}
      <header className="lp__nav-sticky">
        <nav className="lp__nav">
          <div className="lp__nav-left">
            <Link to="/" className="lp__logo">
              <img src="/tas-logo.png" alt="TAS Logo" className="lp__logo-img" />
              <span className="lp__logo-text">AI Connex</span>
            </Link>
            <div className="lp__nav-links">
              {NAV_LINKS.map((label, i) => (
                <a
                  key={label}
                  href="#platform"
                  className={`lp__nav-link${i === 0 ? ' lp__nav-link--active' : ''}`}
                >
                  {label}
                  {(label === 'Solutions' || label === 'Data Lab' || label === 'Resources' || label === 'Company') && (
                    <span className="material-symbols-outlined lp__caret">expand_more</span>
                  )}
                </a>
              ))}
            </div>
          </div>
          <div className="lp__nav-right">
            <span className="lp__expert">Expert Network</span>
            <Link to="/intake" className="lp__cta-lime">
              <span className="material-symbols-outlined">north_east</span> BOOK A DEMO
            </Link>
          </div>
        </nav>
      </header>

      {/* ── Hero ───────────────────────────────────────────────────────── */}
      <section className="lp__hero lp__grid-bg">
        <div className="lp__hero-inner lp__reveal">
          <h1 className="lp__hero-title">
            Orchestrating Autonomous AI Workflows<br />
            from <span className="lp__hero-title-muted">frontier intelligence</span> to<br />
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
            AI Connex trains, deploys, and manages multi-agent systems and real-time data pipelines
            with enterprise governance.
          </p>
          <div className="lp__hero-ctas">
            <Link to="/intake" className="lp__cta-black">
              <span className="material-symbols-outlined">north_east</span> GET STARTED
            </Link>
            <a href="#demo" className="lp__cta-outline">
              Watch Demo
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
      <section className="lp__showcase" id="platform">
        <div className="lp__showcase-head lp__reveal">
          <span className="lp__eyebrow">
            <span className="lp__eyebrow-dot" /> CORE INFRASTRUCTURE
          </span>
          <h2 className="lp__h2">Building blocks, not black boxes</h2>
        </div>

        <div className="lp__showcase-grid lp__reveal">
          <div className="lp__tabs">
            {SHOWCASE_TABS.map((tab) => (
              <button
                key={tab}
                type="button"
                className={`lp__tab${activeTab === tab ? ' lp__tab--active' : ''}`}
                onClick={() => setActiveTab(tab)}
              >
                {tab}
                {activeTab === tab && <span className="material-symbols-outlined">arrow_forward</span>}
              </button>
            ))}
          </div>

          <div className="lp__canvas">
            <div className="lp__canvas-dots">
              <span /> <span /> <span />
            </div>
            <h3 className="lp__canvas-title">Axon Agent Pipeline</h3>
            <p className="lp__canvas-sub">Build governed agents that mirror your workflows.</p>
            <div className="lp__diagram">
              <div className="lp__node">
                <span className="lp__node-label">DATA INGEST</span>
                <span className="lp__node-name">Raw Inputs</span>
              </div>
              <div className="lp__connector" />
              <div className="lp__node lp__node--active">
                <span className="lp__node-badge">
                  <span className="lp__node-badge-dot" /> ACTIVE
                </span>
                <span className="lp__node-label">PROCESSING</span>
                <span className="lp__node-name">{activeTab}</span>
              </div>
              <div className="lp__connector" />
              <div className="lp__node">
                <span className="lp__node-label">OUTPUT</span>
                <span className="lp__node-name">Structured Data</span>
              </div>
            </div>
          </div>
        </div>
      </section>

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
