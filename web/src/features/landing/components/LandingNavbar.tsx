import { useRef, useState } from 'react';
import { Link } from 'react-router-dom';

export interface NavDropdownItem {
  title: string;
  description: string;
  icon: string;
  href: string;
}

export interface NavCategory {
  key: string;
  label: string;
  items: NavDropdownItem[];
}

export const NAV_MENU_CATEGORIES: NavCategory[] = [
  {
    key: 'platform',
    label: 'Platform',
    items: [
      {
        title: 'Platform Overview',
        description: 'Comprehensive MLOps & AutoML infrastructure overview',
        icon: 'dashboard',
        href: '#platform',
      },
      {
        title: 'Data Studio',
        description: 'Dataset profiling, quality checks & data discovery',
        icon: 'analytics',
        href: '/data-studio',
      },
      {
        title: 'ML Studio',
        description: 'Automated model training, HPO & architecture search',
        icon: 'model_training',
        href: '/models',
      },
      {
        title: 'Agentic AI',
        description: 'Autonomous agent orchestration with governance',
        icon: 'smart_toy',
        href: '/agents',
      },
      {
        title: 'Deployment & Monitoring',
        description: 'Real-time inference, health telemetry & rollbacks',
        icon: 'rocket_launch',
        href: '/deployments',
      },
    ],
  },
  {
    key: 'solutions',
    label: 'Solutions',
    items: [
      {
        title: 'Predictive Maintenance',
        description: 'Equipment health telemetry & failure forecasting',
        icon: 'build_circle',
        href: '#solutions',
      },
      {
        title: 'Industrial Analytics',
        description: 'Root-cause insights & sensor stream processing',
        icon: 'precision_manufacturing',
        href: '#solutions',
      },
      {
        title: 'Anomaly Detection',
        description: 'Outlier identification in streaming industrial data',
        icon: 'warning',
        href: '#solutions',
      },
      {
        title: 'Quality Intelligence',
        description: 'Defect detection & manufacturing quality control',
        icon: 'verified',
        href: '#solutions',
      },
      {
        title: 'Custom Industrial AI',
        description: 'Tailored enterprise AI pipeline development',
        icon: 'memory',
        href: '#solutions',
      },
    ],
  },
  {
    key: 'resources',
    label: 'Resources',
    items: [
      {
        title: 'Documentation',
        description: 'API contracts, architecture guides & SDK references',
        icon: 'description',
        href: '#resources',
      },
      {
        title: 'Case Studies',
        description: 'Real-world industrial enterprise deployment outcomes',
        icon: 'article',
        href: '#resources',
      },
      {
        title: 'Blogs',
        description: 'Engineering insights on MLOps & agentic automation',
        icon: 'rss_feed',
        href: '#resources',
      },
      {
        title: 'Technical Insights',
        description: 'In-depth architecture teardowns & whitepapers',
        icon: 'menu_book',
        href: '#resources',
      },
      {
        title: 'FAQs',
        description: 'Frequently asked questions & platform capabilities',
        icon: 'help',
        href: '#resources',
      },
    ],
  },
  {
    key: 'company',
    label: 'Company',
    items: [
      {
        title: 'About AIConnex',
        description: 'Our mission, enterprise vision & engineering team',
        icon: 'corporate_fare',
        href: '#company',
      },
      {
        title: 'Our Technology',
        description: 'Apache DataFusion, Arrow & LangGraph foundation',
        icon: 'terminal',
        href: '#company',
      },
      {
        title: 'Partners',
        description: 'Ecosystem integrations & cloud infrastructure partners',
        icon: 'handshake',
        href: '#company',
      },
      {
        title: 'Careers',
        description: 'Join our mission to transform industrial AI',
        icon: 'work',
        href: '#company',
      },
      {
        title: 'Contact',
        description: 'Get in touch with our solutions engineering team',
        icon: 'mail',
        href: '#company',
      },
    ],
  },
];

export function LandingNavbar() {
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState<boolean>(false);
  const leaveTimerRef = useRef<NodeJS.Timeout | null>(null);

  const handleMouseEnterCategory = (key: string) => {
    if (leaveTimerRef.current) {
      clearTimeout(leaveTimerRef.current);
      leaveTimerRef.current = null;
    }
    setActiveDropdown(key);
  };

  const handleMouseLeaveNav = () => {
    leaveTimerRef.current = setTimeout(() => {
      setActiveDropdown(null);
    }, 150);
  };

  const handleDropdownMouseEnter = () => {
    if (leaveTimerRef.current) {
      clearTimeout(leaveTimerRef.current);
      leaveTimerRef.current = null;
    }
  };

  return (
    <header className="lp__nav-sticky" onMouseLeave={handleMouseLeaveNav}>
      <nav className="lp__nav">
        <div className="lp__nav-left">
          <Link to="/" className="lp__logo">
            <span className="lp__logo-text">AIConneX</span>
          </Link>
          <div className="lp__nav-links">
            {NAV_MENU_CATEGORIES.map((cat) => {
              const isActive = activeDropdown === cat.key;
              return (
                <div
                  key={cat.key}
                  className="lp__nav-item-wrapper"
                  onMouseEnter={() => handleMouseEnterCategory(cat.key)}
                  onMouseLeave={handleMouseLeaveNav}
                >
                  <button
                    type="button"
                    className={`lp__nav-link${isActive ? ' lp__nav-link--active' : ''}`}
                    onClick={() =>
                      setActiveDropdown((prev) => (prev === cat.key ? null : cat.key))
                    }
                  >
                    {cat.label}
                    <span className={`material-symbols-outlined lp__caret${isActive ? ' lp__caret--open' : ''}`}>
                      south_east
                    </span>
                  </button>

                  {/* ── Dropdown Popover aligned under its parent category button ── */}
                  {isActive && (
                    <div
                      className="lp__dropdown-popover lp__dropdown-popover--visible"
                      onMouseEnter={handleDropdownMouseEnter}
                      onMouseLeave={handleMouseLeaveNav}
                    >
                      <div className="lp__dropdown-container">
                        <div className="lp__dropdown-header">
                          <span className="lp__dropdown-badge">{cat.label}</span>
                          <span className="lp__dropdown-subtext">
                            Explore {cat.label.toLowerCase()} capabilities & workflows
                          </span>
                        </div>
                        <div className="lp__dropdown-grid">
                          {cat.items.map((item) => (
                            <Link
                              key={item.title}
                              to={item.href.startsWith('/') ? item.href : '/intake'}
                              className="lp__dropdown-item"
                              onClick={() => setActiveDropdown(null)}
                            >
                              <div className="lp__dropdown-icon-box">
                                <span className="material-symbols-outlined">{item.icon}</span>
                              </div>
                              <div className="lp__dropdown-content">
                                <div className="lp__dropdown-title">
                                  {item.title}
                                  <span className="material-symbols-outlined lp__dropdown-arrow">
                                    arrow_forward
                                  </span>
                                </div>
                                <p className="lp__dropdown-desc">{item.description}</p>
                              </div>
                            </Link>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
        <div className="lp__nav-right">
          <Link to="/intake" className="lp__cta-lime">
            <span className="material-symbols-outlined">north_east</span> START WITH JANE
          </Link>
          <button
            type="button"
            className="lp__mobile-toggle"
            aria-label="Toggle mobile menu"
            onClick={() => setIsMobileMenuOpen((prev) => !prev)}
          >
            <span className="material-symbols-outlined">
              {isMobileMenuOpen ? 'close' : 'menu'}
            </span>
          </button>
        </div>
      </nav>
      {isMobileMenuOpen && (
        <div className="lp__mobile-drawer">
          {NAV_MENU_CATEGORIES.map((cat) => (
            <div key={cat.key} className="lp__mobile-cat">
              <div className="lp__mobile-cat-title">{cat.label}</div>
              <div className="lp__mobile-cat-items">
                {cat.items.map((item) => (
                  <Link
                    key={item.title}
                    to={item.href.startsWith('/') ? item.href : '/intake'}
                    className="lp__mobile-item"
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    <span className="material-symbols-outlined">{item.icon}</span>
                    <span>{item.title}</span>
                  </Link>
                ))}
              </div>
            </div>
          ))}
          <div className="lp__mobile-footer">
            <Link
              to="/intake"
              className="lp__cta-lime lp__cta-lime--full"
              onClick={() => setIsMobileMenuOpen(false)}
            >
              <span className="material-symbols-outlined">north_east</span> START WITH JANE
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
