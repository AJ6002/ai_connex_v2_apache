import React, { useState, useEffect, useRef } from 'react';
import { ViewMode } from '../types';

interface OrbitArcSidebarProps {
  currentView: ViewMode;
  onSelectView: (view: ViewMode) => void;
}

interface NavItem {
  id: ViewMode;
  label: string;
  shortLabel: string;
  icon: string;
  badge?: string;
  cluster: 'ingestion' | 'mlops' | 'system' | 'settings';
}

export const OrbitArcSidebar: React.FC<OrbitArcSidebarProps> = ({ currentView, onSelectView }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [hoveredItemId, setHoveredItemId] = useState<ViewMode | null>(null);
  const [isPinned, setIsPinned] = useState(false);
  const [showPageMenu, setShowPageMenu] = useState(false);

  // Dynamic smooth pointer tracking when unpinned
  const [targetPos, setTargetPos] = useState({ x: window.innerWidth / 2, y: window.innerHeight - 150 });
  const [currentPos, setCurrentPos] = useState({ x: window.innerWidth / 2, y: window.innerHeight - 150 });
  const animFrameRef = useRef<number | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  // Relative mouse tracking for magnetic pull effect
  const [relMouse, setRelMouse] = useState<{ x: number; y: number } | null>(null);

  // Continuously follow mouse pointer with smooth dampening when NOT pinned
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      // Keep semi-arc safely within viewport padding
      const paddingX = 170;
      const paddingY = 120;
      const x = Math.max(paddingX, Math.min(window.innerWidth - paddingX, e.clientX));
      const y = Math.max(paddingY, Math.min(window.innerHeight - paddingY, e.clientY + 20));
      if (!isPinned) {
        setTargetPos({ x, y });
      }

      // Calculate relative mouse position from arc center
      const relX = e.clientX - currentPos.x;
      const relY = e.clientY - currentPos.y;
      if (Math.hypot(relX, relY) < 220) {
        setRelMouse({ x: relX, y: relY });
      } else {
        setRelMouse(null);
      }
    };

    window.addEventListener('mousemove', handleMouseMove);

    // Smooth lerp animation loop
    const updateLoop = () => {
      setCurrentPos((prev) => {
        const dx = targetPos.x - prev.x;
        const dy = targetPos.y - prev.y;
        if (Math.abs(dx) < 0.1 && Math.abs(dy) < 0.1) return prev;
        return {
          x: prev.x + dx * 0.18,
          y: prev.y + dy * 0.18,
        };
      });
      animFrameRef.current = requestAnimationFrame(updateLoop);
    };

    animFrameRef.current = requestAnimationFrame(updateLoop);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [targetPos, currentPos, isPinned]);

  // Close page menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowPageMenu(false);
      }
    };
    if (showPageMenu) {
      window.addEventListener('mousedown', handleClickOutside);
    }
    return () => window.removeEventListener('mousedown', handleClickOutside);
  }, [showPageMenu]);

  const allNavItems: NavItem[] = [
    // Ingestion & ML Core
    { id: 'compiler', label: 'Dataset Compiler', shortLabel: 'Compiler', icon: 'folder_zip', badge: 'Tab 1', cluster: 'ingestion' },
    { id: 'dag_inspector', label: '1,993 Master DAGs', shortLabel: 'DAGs', icon: 'account_tree', badge: 'Tab 2', cluster: 'ingestion' },
    { id: 'workflow', label: '9-Node MLOps Cascade', shortLabel: 'Cascade', icon: 'schema', badge: 'Tab 3', cluster: 'mlops' },
    { id: 'pipeline_studio', label: 'Serving & Drift Monitor', shortLabel: 'Drift', icon: 'query_stats', badge: 'Tab 4', cluster: 'mlops' },

    // System & Ops
    { id: 'administration', label: 'Administration & Envs', shortLabel: 'Admin', icon: 'admin_panel_settings', cluster: 'system' },
    { id: 'quotas', label: 'Quotas & GPU Spend', shortLabel: 'GPU', icon: 'payments', cluster: 'system' },
    { id: 'developer_studio', label: 'Developer Stdout Stream', shortLabel: 'Logs', icon: 'terminal', cluster: 'system' },

    // Settings & Specs
    { id: 'settings', label: 'Platform Settings', shortLabel: 'Settings', icon: 'settings', cluster: 'settings' },
    { id: 'support', label: 'Support & Specs', shortLabel: 'Specs', icon: 'help_outline', cluster: 'settings' },
  ];

  // Dynamic arc bending calculation based on relative mouse position
  const getArcBendingOffset = () => {
    if (!relMouse) return { bendX: 0, bendY: 0 };
    const bendX = Math.max(-28, Math.min(28, relMouse.x * 0.2));
    const bendY = Math.max(-22, Math.min(18, relMouse.y * 0.2));
    return { bendX, bendY };
  };

  const { bendX, bendY } = getArcBendingOffset();

  // Angle math for semi-circle radial distribution (180-degree arch)
  // Arc center: (160, 150), Radius: 108
  const totalItems = allNavItems.length;
  const startAngle = -168; // Degrees
  const endAngle = -12;
  const angleStep = (endAngle - startAngle) / (totalItems - 1);

  // Position calculation for items along the semi-circle arc with magnetic pull & snapping
  const getItemSemiArcStyle = (index: number) => {
    const angle = startAngle + index * angleStep;
    const radius = 108; // Radial distance from center (160, 150)

    const rad = (angle * Math.PI) / 180;
    const baseX = Math.cos(rad) * radius;
    const baseY = Math.sin(rad) * radius;

    let pullX = 0;
    let pullY = 0;
    let scale = 1;

    if (relMouse) {
      const dx = relMouse.x - baseX;
      const dy = relMouse.y - baseY;
      const dist = Math.hypot(dx, dy);

      if (dist < 75) {
        const factor = Math.pow(1 - dist / 75, 1.4);
        pullX = dx * factor * 0.4;
        pullY = dy * factor * 0.4;
        scale = 1 + factor * 0.25;
      }
    }

    const finalX = baseX + pullX;
    const finalY = baseY + pullY;

    return {
      transform: `translate(${finalX}px, ${finalY}px) scale(${scale})`,
      angle,
    };
  };

  // Radial divider lines between sectors
  const dividerLines = Array.from({ length: totalItems - 1 }).map((_, i) => {
    const angle = startAngle + (i + 0.5) * angleStep;
    const rad = (angle * Math.PI) / 180;
    const r1 = 78;
    const r2 = 138;
    const x1 = 160 + Math.cos(rad) * r1;
    const y1 = 150 + Math.sin(rad) * r1;
    const x2 = 160 + Math.cos(rad) * r2;
    const y2 = 150 + Math.sin(rad) * r2;
    return { x1, y1, x2, y2 };
  });

  // Toggle pin on left click
  const togglePin = (e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setIsPinned((prev) => {
      const nextPinned = !prev;
      if (nextPinned) {
        setTargetPos({ ...currentPos });
      }
      return nextPinned;
    });
  };

  // Handle click on arc container
  const handleArcClick = (e: React.MouseEvent) => {
    const targetElement = e.target as HTMLElement;
    if (targetElement.closest('.nav-item-btn') || targetElement.closest('.menu-item-btn')) {
      return;
    }

    if (e.button === 0) {
      togglePin(e);
    }
  };

  // Open Contextual Page Menu on Right Click
  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setShowPageMenu((prev) => !prev);
  };

  return (
    <div
      className="fixed z-50 pointer-events-none select-none transition-transform duration-75 ease-out"
      style={{
        left: `${currentPos.x}px`,
        top: `${currentPos.y}px`,
        transform: 'translate(-50%, -50%)',
      }}
    >
      {/* Collapsed State Orb Button - Red & Blue Theme */}
      {isCollapsed ? (
        <button
          onClick={() => setIsCollapsed(false)}
          className="pointer-events-auto relative flex items-center justify-center w-12 h-12 bg-gradient-to-tr from-[#23388B] via-slate-950 to-[#E30613] text-white rounded-full border-2 border-white/50 shadow-[0_0_20px_rgba(227,6,19,0.5),0_0_20px_rgba(35,56,139,0.5)] backdrop-blur-xl transition-all hover:scale-110 active:scale-95"
          title="Expand Orbit Semi-Arc (Left-click pin, Right-click page menu)"
        >
          <span className="w-2.5 h-2.5 rounded-full bg-tas-red animate-ping absolute -top-0.5 -right-0.5 ring-2 ring-blue-400"></span>
          <span className="material-symbols-outlined text-xl text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.9)]">
            orbit
          </span>
        </button>
      ) : (
        /* Thick 3D Glass Volumetric Semi-Circle Arc */
        <div
          onContextMenu={handleContextMenu}
          onClick={handleArcClick}
          className="relative w-[320px] h-[180px] flex items-center justify-center pointer-events-auto cursor-pointer group"
        >
          {/* SVG Volumetric Glass Arch Band */}
          <svg
            data-arc-bg="true"
            className="absolute inset-0 w-full h-full drop-shadow-[0_20px_40px_rgba(0,0,0,0.65)] pointer-events-none"
            viewBox="0 0 320 180"
          >
            <defs>
              {/* Glass Rim Gradient */}
              <linearGradient id="volumetricGlass" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#2A344A" stopOpacity="0.88" />
                <stop offset="40%" stopColor="#121826" stopOpacity="0.94" />
                <stop offset="70%" stopColor="#0B0F19" stopOpacity="0.96" />
                <stop offset="100%" stopColor="#1E293B" stopOpacity="0.88" />
              </linearGradient>

              {/* Top Specular Bevel Highlights */}
              <linearGradient id="beveledRim" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="rgba(255, 255, 255, 0.65)" />
                <stop offset="50%" stopColor="rgba(255, 255, 255, 0.2)" />
                <stop offset="100%" stopColor="rgba(255, 255, 255, 0.65)" />
              </linearGradient>

              {/* Active Lens Glow */}
              <radialGradient id="activeLensGlow" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="rgba(255, 255, 255, 0.45)" />
                <stop offset="60%" stopColor="rgba(255, 255, 255, 0.15)" />
                <stop offset="100%" stopColor="rgba(255, 255, 255, 0)" />
              </radialGradient>
            </defs>

            {/* Thick Volumetric Base Semi-Arc Path */}
            <path
              d={`M 22 150 Q ${160 + bendX} ${15 + bendY} 298 150`}
              fill="none"
              stroke="url(#volumetricGlass)"
              strokeWidth="60"
              strokeLinecap="round"
              className="backdrop-blur-3xl transition-all duration-75"
            />

            {/* Specular Outer Edge Bevel Highlight */}
            <path
              d={`M 22 150 Q ${160 + bendX} ${15 + bendY} 298 150`}
              fill="none"
              stroke="url(#beveledRim)"
              strokeWidth="60"
              strokeLinecap="round"
              strokeOpacity="0.35"
              className="transition-all duration-75"
            />

            {/* Inner Dark Core Arc Groove Shadow */}
            <path
              d={`M 52 146 Q ${160 + bendX * 0.8} ${42 + bendY * 0.8} 268 146`}
              fill="none"
              stroke="rgba(0, 0, 0, 0.6)"
              strokeWidth="2"
              className="transition-all duration-75"
            />

            {/* Radial Segment Dividers */}
            {dividerLines.map((line, idx) => (
              <line
                key={idx}
                x1={line.x1}
                y1={line.y1}
                x2={line.x2}
                y2={line.y2}
                stroke="rgba(255, 255, 255, 0.15)"
                strokeWidth="1.5"
              />
            ))}
          </svg>

          {/* Radial Navigation Items & Circular Spotlight Lens Highlights */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-auto">
            {allNavItems.map((item, index) => {
              const isActive = currentView === item.id;
              const isHovered = hoveredItemId === item.id;
              const { transform } = getItemSemiArcStyle(index);

              return (
                <button
                  key={item.id}
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelectView(item.id);
                  }}
                  onMouseEnter={() => setHoveredItemId(item.id)}
                  onMouseLeave={() => setHoveredItemId(null)}
                  style={{ transform }}
                  className={`nav-item-btn absolute w-11 h-11 rounded-full flex items-center justify-center transition-all duration-200 ${
                    isActive || isHovered ? 'z-30' : 'z-20'
                  }`}
                >
                  {/* Circular Spotlight Glass Lens Highlight (As seen in reference image) */}
                  {(isHovered || isActive) && (
                    <div className="absolute inset-0 rounded-full bg-white/20 border border-white/50 shadow-[0_0_25px_rgba(255,255,255,0.45)] backdrop-blur-md animate-scaleIn pointer-events-none"></div>
                  )}

                  {/* Icon */}
                  <span
                    className={`material-symbols-outlined transition-all ${
                      isActive
                        ? 'text-white scale-110 font-bold text-xl drop-shadow-[0_2px_8px_rgba(255,255,255,0.8)]'
                        : isHovered
                        ? 'text-white scale-110 text-xl'
                        : 'text-slate-300/80 hover:text-white text-lg'
                    }`}
                  >
                    {item.icon}
                  </span>

                  {/* Item Tooltip on Hover / Active */}
                  {(isHovered || isActive) && (
                    <div className="absolute -top-11 left-1/2 -translate-x-1/2 bg-slate-950/95 backdrop-blur-2xl text-white px-2.5 py-1 rounded-lg text-[10px] font-mono font-bold whitespace-nowrap shadow-2xl border border-white/30 flex items-center gap-1.5 pointer-events-none z-50">
                      <span>{item.label}</span>
                      {item.badge && (
                        <span className="px-1 py-0.2 bg-tas-red text-[8px] rounded font-bold">
                          {item.badge}
                        </span>
                      )}
                    </div>
                  )}
                </button>
              );
            })}
          </div>

          {/* Central Red and Blue Themed Orb Hub */}
          <div className="absolute bottom-2 left-1/2 -translate-x-1/2 z-30 pointer-events-auto">
            <button
              onClick={(e) => togglePin(e)}
              className={`group relative flex items-center justify-center w-14 h-14 bg-gradient-to-tr from-[#23388B] via-slate-950 to-[#E30613] rounded-full border-2 transition-all duration-300 shadow-[0_0_25px_rgba(227,6,19,0.45),0_0_25px_rgba(35,56,139,0.55)] backdrop-blur-3xl hover:scale-110 active:scale-95 ${
                isPinned
                  ? 'border-emerald-400 ring-2 ring-emerald-400/50'
                  : 'border-white/50 hover:border-white ring-1 ring-white/20'
              }`}
              title={isPinned ? "Left-click to Unpin Arc" : "Left-click to Pin Arc in Place"}
            >
              {/* Inner Dual-Tone Ambient Glow Overlay */}
              <div className="absolute inset-0.5 rounded-full bg-gradient-to-br from-[#E30613]/30 via-transparent to-[#23388B]/40 pointer-events-none"></div>

              {/* Central Content */}
              <div className="relative z-10 flex flex-col items-center justify-center text-white">
                <span className="material-symbols-outlined text-xl transition-transform group-hover:scale-110 drop-shadow-[0_2px_8px_rgba(255,255,255,0.9)]">
                  {isPinned ? 'push_pin' : 'play_arrow'}
                </span>
                <span className="text-[8px] font-mono font-bold tracking-widest text-slate-200 -mt-0.5 drop-shadow">
                  {isPinned ? 'PIN' : 'ARC'}
                </span>
              </div>
            </button>
          </div>

          {/* Quick Guidance Hint Badge */}
          <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-950/95 text-slate-300 text-[9px] font-mono px-2.5 py-0.5 rounded-md border border-white/20 whitespace-nowrap pointer-events-none shadow-xl z-40">
            Left-Click: <strong className="text-white">{isPinned ? 'Unpin' : 'Pin'}</strong> | Right-Click: <strong className="text-tas-red">Page Menu</strong>
          </div>

          {/* Contextual Right-Click Page Menu Overlay */}
          {showPageMenu && (
            <div
              ref={menuRef}
              onClick={(e) => e.stopPropagation()}
              className="absolute -top-52 left-1/2 -translate-x-1/2 w-64 bg-slate-950/95 backdrop-blur-2xl rounded-2xl border border-white/20 p-2.5 shadow-2xl z-50 text-white animate-fadeIn"
            >
              <div className="flex items-center justify-between pb-2 mb-2 border-b border-white/10 px-1">
                <span className="text-[10px] font-mono font-bold text-tas-red uppercase tracking-wider flex items-center gap-1">
                  <span className="material-symbols-outlined text-xs">touch_app</span>
                  Select Any Page
                </span>
                <button
                  onClick={() => setShowPageMenu(false)}
                  className="p-0.5 hover:bg-white/10 rounded text-slate-400 hover:text-white"
                >
                  <span className="material-symbols-outlined text-xs">close</span>
                </button>
              </div>

              <div className="space-y-1 max-h-56 overflow-y-auto pr-1">
                {allNavItems.map((navItem) => {
                  const isCurrent = currentView === navItem.id;
                  return (
                    <button
                      key={navItem.id}
                      onClick={() => {
                        onSelectView(navItem.id);
                        setShowPageMenu(false);
                      }}
                      className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-xl text-xs font-mono transition-all text-left ${
                        isCurrent
                          ? 'bg-tas-red text-white font-bold shadow-md'
                          : 'text-slate-300 hover:text-white hover:bg-white/10'
                      }`}
                    >
                      <div className="flex items-center gap-2 truncate">
                        <span className="material-symbols-outlined text-sm text-slate-300">
                          {navItem.icon}
                        </span>
                        <span className="truncate">{navItem.label}</span>
                      </div>
                      {navItem.badge && (
                        <span className="text-[9px] bg-white/20 px-1.5 py-0.2 rounded font-bold">
                          {navItem.badge}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
