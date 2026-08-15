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
  const [isCollapsed, setIsCollapsed] = useState(true);
  const [hoveredItemId, setHoveredItemId] = useState<ViewMode | null>(null);
  const [isPinned, setIsPinned] = useState(false);
  const [showPageMenu, setShowPageMenu] = useState(false);

  // Dynamic smooth pointer tracking when unpinned
  const [targetPos, setTargetPos] = useState({ x: window.innerWidth - 110, y: window.innerHeight - 130 });
  const [currentPos, setCurrentPos] = useState({ x: window.innerWidth - 110, y: window.innerHeight - 130 });
  const animFrameRef = useRef<number | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  // Relative mouse tracking for magnetic pull effect
  const [relMouse, setRelMouse] = useState<{ x: number; y: number } | null>(null);

  // Continuously follow mouse pointer with smooth dampening when UNPINNED
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isPinned) return;

      if (isCollapsed) {
        // Floating Assistive Touch button follows mouse cursor with smooth offset
        const paddingX = 40;
        const paddingY = 40;
        const x = Math.max(paddingX, Math.min(window.innerWidth - paddingX, e.clientX + 28));
        const y = Math.max(paddingY, Math.min(window.innerHeight - paddingY, e.clientY + 28));
        setTargetPos({ x, y });
        return;
      }

      // Keep semi-arc safely within viewport padding when open & unpinned
      const paddingX = 180;
      const paddingY = 150;
      const x = Math.max(paddingX, Math.min(window.innerWidth - paddingX, e.clientX));
      const y = Math.max(paddingY, Math.min(window.innerHeight - paddingY, e.clientY + 20));
      setTargetPos({ x, y });

      // Calculate relative mouse position from arc center
      const relX = e.clientX - currentPos.x;
      const relY = e.clientY - currentPos.y;
      if (Math.hypot(relX, relY) < 250) {
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
  }, [targetPos, currentPos, isPinned, isCollapsed]);

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

  // Outer Arc Items (Ordered Pipeline Pages 1 through 8 + Admin)
  const outerNavItems: NavItem[] = [
    { id: 'compiler', label: 'Page 1: Upload Page', shortLabel: 'Upload', icon: 'upload_file', badge: 'Page 1', cluster: 'ingestion' },
    { id: 'data_explorer', label: 'Page 2: Data Explorer', shortLabel: 'Explore', icon: 'bar_chart', badge: 'Page 2', cluster: 'ingestion' },
    { id: 'node4', label: 'Page 3: Prepare Node', shortLabel: 'Prepare', icon: 'cleaning_services', badge: 'Page 3', cluster: 'ingestion' },
    { id: 'vg1', label: 'Page 4: Validation Gate 1', shortLabel: 'VG 1', icon: 'verified', badge: 'Page 4', cluster: 'ingestion' },
    { id: 'node5', label: 'Page 5: Feature Engineer Node', shortLabel: 'Features', icon: 'science', badge: 'Page 5', cluster: 'mlops' },
    { id: 'node7', label: 'Page 6: Train Node', shortLabel: 'Train', icon: 'model_training', badge: 'Page 6', cluster: 'mlops' },
    { id: 'vg2', label: 'Page 7: Validation Gate 2', shortLabel: 'VG 2', icon: 'fact_check', badge: 'Page 7', cluster: 'mlops' },
    { id: 'node9', label: 'Page 8: Deploy Node', shortLabel: 'Deploy', icon: 'rocket_launch', badge: 'Page 8', cluster: 'mlops' },
    { id: 'pipeline_studio', label: 'Page 9: Monitor Node', shortLabel: 'Monitor', icon: 'monitoring', badge: 'Page 9', cluster: 'mlops' },
    { id: 'master_data', label: 'Master Data & Recipes', shortLabel: 'Master', icon: 'database', badge: 'Recipes', cluster: 'system' },
    { id: 'administration', label: 'Administration & Envs', shortLabel: 'Admin', icon: 'admin_panel_settings', cluster: 'system' },
    { id: 'agent_manager', label: 'Agent Manager & Fleet Control', shortLabel: 'Agents', icon: 'smart_toy', badge: 'Admin', cluster: 'system' },
    { id: 'templates', label: 'Templates Library', shortLabel: 'Templates', icon: 'description', cluster: 'system' },
    { id: 'settings', label: 'Platform Settings', shortLabel: 'Settings', icon: 'settings', cluster: 'settings' },
  ];

  // Inner Arc Items (The 9 microservice nodes)
  const innerNavItems: NavItem[] = [
    { id: 'node1', label: 'Node 1: Dataset Profiler', shortLabel: 'Profiler', icon: 'analytics', cluster: 'mlops' },
    { id: 'node2', label: 'Node 2: DAG Matcher', shortLabel: 'DAG Matcher', icon: 'route', cluster: 'mlops' },
    { id: 'node3', label: 'Node 3: Recipe Orchestrator', shortLabel: 'Recipe', icon: 'hub', cluster: 'mlops' },
    { id: 'node4', label: 'Node 4: Data Prepare', shortLabel: 'Prepare', icon: 'cleaning_services', cluster: 'mlops' },
    { id: 'node5', label: 'Node 5: Feature Engineering', shortLabel: 'Feature Eng', icon: 'science', cluster: 'mlops' },
    { id: 'node6', label: 'Node 6: Validation Gate 1', shortLabel: 'VG 1', icon: 'verified', cluster: 'mlops' },
    { id: 'node7', label: 'Node 7: Train API', shortLabel: 'Train', icon: 'model_training', cluster: 'mlops' },
    { id: 'node8', label: 'Node 8: Validation Gate 2', shortLabel: 'VG 2', icon: 'fact_check', cluster: 'mlops' },
    { id: 'node9', label: 'Node 9: Deploy API', shortLabel: 'Deploy', icon: 'rocket_launch', cluster: 'mlops' },
  ];

  const allNavItems = [...outerNavItems, ...innerNavItems];

  // Dynamic arc bending calculation based on relative mouse position
  const getArcBendingOffset = () => {
    if (!relMouse) return { bendX: 0, bendY: 0 };
    const bendX = Math.max(-28, Math.min(28, relMouse.x * 0.2));
    const bendY = Math.max(-22, Math.min(18, relMouse.y * 0.2));
    return { bendX, bendY };
  };

  const { bendX, bendY } = getArcBendingOffset();

  // Angle math for semi-circle radial distribution (180-degree arch)
  const totalItems = 9; // Inner/divider count
  const startAngle = -168; // Degrees
  const endAngle = -12;
  const angleStep = (endAngle - startAngle) / (totalItems - 1);
  const outerAngleStep = (endAngle - startAngle) / (outerNavItems.length - 1);

  // Position calculation for items along the outer semi-circle arc
  const getOuterItemSemiArcStyle = (index: number, itemId: ViewMode) => {
    const angle = startAngle + index * outerAngleStep;
    const radius = 132; // Outer radius

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

      if (dist < 60) {
        const factor = Math.pow(1 - dist / 60, 1.4);
        pullX = dx * factor * 0.35;
        pullY = dy * factor * 0.35;
        scale = 1 + factor * 0.22;
      }
    }

    const finalX = baseX + pullX;
    const finalY = baseY + pullY;

    return {
      transform: `translate(${finalX}px, ${finalY}px) scale(${scale})`,
    };
  };

  // Position calculation for items along the inner semi-circle arc
  const getInnerItemSemiArcStyle = (index: number, itemId: ViewMode) => {
    const angle = startAngle + index * angleStep;
    const radius = 72; // Inner radius

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

      if (dist < 50) {
        const factor = Math.pow(1 - dist / 50, 1.4);
        pullX = dx * factor * 0.35;
        pullY = dy * factor * 0.35;
        scale = 1 + factor * 0.22;
      }
    }

    const finalX = baseX + pullX;
    const finalY = baseY + pullY;

    return {
      transform: `translate(${finalX}px, ${finalY}px) scale(${scale})`,
    };
  };

  // Radial divider lines between sectors spanning both arcs
  const dividerLines = Array.from({ length: totalItems - 1 }).map((_, i) => {
    const angle = startAngle + (i + 0.5) * angleStep;
    const rad = (angle * Math.PI) / 180;
    const r1 = 52;
    const r2 = 150;
    const x1 = 160 + Math.cos(rad) * r1;
    const y1 = 150 + Math.sin(rad) * r1;
    const x2 = 160 + Math.cos(rad) * r2;
    const y2 = 150 + Math.sin(rad) * r2;
    return { x1, y1, x2, y2 };
  });

  // Open Arc & Pin in place
  const handleOpenArc = (e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setIsCollapsed(false);
    setIsPinned(true);
  };

  // Close Arc & Unpin back to cursor-following Assistive Touch
  const handleCloseArc = (e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setIsPinned(false);
    setIsCollapsed(true);
  };

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

  // Handle click on arc container: left click unpins & switches back to Assistive Touch
  const handleArcClick = (e: React.MouseEvent) => {
    const targetElement = e.target as HTMLElement;
    if (targetElement.closest('.nav-item-btn') || targetElement.closest('.menu-item-btn')) {
      return;
    }

    if (e.button === 0) {
      handleCloseArc(e);
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
      {/* Collapsed State Assistive Touch Button with Orbiting Satellite Dots */}
      {isCollapsed ? (
        <div className="pointer-events-auto relative group flex items-center justify-center cursor-pointer">
          {/* Orbiting Satellite Dots in an Arc */}
          {[-150, -115, -90, -65, -30].map((angle, idx) => {
            const rad = (angle * Math.PI) / 180;
            const dist = 46;
            const x = Math.cos(rad) * dist;
            const y = Math.sin(rad) * dist;
            return (
              <div
                key={idx}
                style={{
                  transform: `translate(${x}px, ${y}px)`,
                }}
                className="absolute w-3.5 h-3.5 rounded-full bg-slate-300/85 shadow-[0_2px_8px_rgba(0,0,0,0.5),0_0_8px_rgba(255,255,255,0.6)] backdrop-blur-md transition-all duration-300 group-hover:scale-125 group-hover:bg-white"
              />
            );
          })}

          {/* Central Concentric Ring Assistive Touch Button */}
          <button
            onClick={handleOpenArc}
            className="relative w-14 h-14 rounded-full bg-[#182232] border-[5px] border-[#223046] shadow-[0_12px_36px_rgba(0,0,0,0.75),0_0_20px_rgba(255,255,255,0.2)] flex items-center justify-center transition-all duration-300 hover:scale-110 active:scale-95 group-hover:border-slate-400 group-hover:shadow-[0_12px_40px_rgba(227,6,19,0.4)]"
            title="Click Assistive Touch to Open OrbitalARC"
          >
            {/* Inner Ring Layer 2 */}
            <div className="w-10 h-10 rounded-full bg-[#334155] border-4 border-[#475569] flex items-center justify-center shadow-inner">
              {/* Inner Core Layer 3 - White Glow Disk */}
              <div className="w-5 h-5 rounded-full bg-white shadow-[0_0_12px_rgba(255,255,255,0.95)] animate-pulse flex items-center justify-center" />
            </div>
          </button>

          {/* Quick Tooltip Hint */}
          <div className="absolute -top-10 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-950/95 text-white text-[10px] font-mono px-3 py-1 rounded-xl border border-white/20 whitespace-nowrap shadow-2xl pointer-events-none z-50 flex items-center gap-1.5">
            <span className="material-symbols-outlined text-xs text-tas-red">touch_app</span>
            <span>Click Assistive Touch to Open OrbitalARC</span>
          </div>
        </div>
      ) : (
        /* Thick 3D Glass Volumetric Concentric Semi-Circle Arc */
        <div
          onClick={handleArcClick}
          className="relative w-[340px] h-[190px] flex items-center justify-center pointer-events-auto cursor-pointer group"
        >
          {/* SVG Volumetric Glass Arch Band */}
          <svg
            data-arc-bg="true"
            className="absolute inset-0 w-full h-full drop-shadow-[0_20px_40px_rgba(0,0,0,0.65)] pointer-events-none"
            viewBox="0 0 340 190"
          >
            <defs>
              {/* Glass Rim Gradient - Core Operations (Outer) */}
              <linearGradient id="volumetricGlassOuter" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#23388B" stopOpacity="0.75" />
                <stop offset="40%" stopColor="#121826" stopOpacity="0.94" />
                <stop offset="70%" stopColor="#0B0F19" stopOpacity="0.96" />
                <stop offset="100%" stopColor="#1E293B" stopOpacity="0.85" />
              </linearGradient>

              {/* Glass Rim Gradient - MLOps Nodes (Inner) */}
              <linearGradient id="volumetricGlassInner" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#E30613" stopOpacity="0.75" />
                <stop offset="40%" stopColor="#121826" stopOpacity="0.94" />
                <stop offset="70%" stopColor="#0B0F19" stopOpacity="0.96" />
                <stop offset="100%" stopColor="#23388B" stopOpacity="0.85" />
              </linearGradient>

              {/* Top Specular Bevel Highlights */}
              <linearGradient id="beveledRim" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="rgba(255, 255, 255, 0.65)" />
                <stop offset="50%" stopColor="rgba(255, 255, 255, 0.2)" />
                <stop offset="100%" stopColor="rgba(255, 255, 255, 0.65)" />
              </linearGradient>
            </defs>

            {/* Thick Volumetric Outer Semi-Arc Path */}
            <path
              d={`M 28 150 Q ${170 + bendX} ${18 + bendY} 312 150`}
              fill="none"
              stroke="url(#volumetricGlassOuter)"
              strokeWidth="42"
              strokeLinecap="round"
              className="backdrop-blur-3xl transition-all duration-75"
            />

            {/* Thick Volumetric Inner Semi-Arc Path */}
            <path
              d={`M 88 150 Q ${170 + bendX * 0.6} ${78 + bendY * 0.6} 252 150`}
              fill="none"
              stroke="url(#volumetricGlassInner)"
              strokeWidth="34"
              strokeLinecap="round"
              className="backdrop-blur-3xl transition-all duration-75"
            />

            {/* Specular Outer Edge Bevel Highlight */}
            <path
              d={`M 28 150 Q ${170 + bendX} ${18 + bendY} 312 150`}
              fill="none"
              stroke="url(#beveledRim)"
              strokeWidth="42"
              strokeLinecap="round"
              strokeOpacity="0.25"
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
                stroke="rgba(255, 255, 255, 0.12)"
                strokeWidth="1.2"
              />
            ))}
          </svg>

          {/* Concentric Navigation Items Container */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-auto">
            
            {/* 1. OUTER ARC ITEMS */}
            {outerNavItems.map((item, index) => {
              const isActive = currentView === item.id;
              const isHovered = hoveredItemId === item.id;
              const { transform } = getOuterItemSemiArcStyle(index, item.id);

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
                  className={`nav-item-btn absolute w-9 h-9 rounded-full flex items-center justify-center transition-all duration-200 ${
                    isActive || isHovered ? 'z-30' : 'z-20'
                  }`}
                >
                  {/* Spotlight Glow (Solar Orange for core operations) */}
                  {(isHovered || isActive) && (
                    <div className="absolute inset-0 rounded-full bg-[#E86326] border border-[#2B0063] shadow-[0_0_16px_rgba(232,99,38,0.6)] backdrop-blur-md animate-scaleIn pointer-events-none"></div>
                  )}

                  {/* Icon */}
                  <span
                    className={`material-symbols-outlined transition-all ${
                      isActive
                        ? 'text-[#0D1533] scale-110 font-bold text-lg'
                        : isHovered
                        ? 'text-[#0D1533] scale-110 text-lg'
                        : 'text-slate-300/80 hover:text-white text-base'
                    }`}
                  >
                    {item.icon}
                  </span>

                  {/* Tooltip */}
                  {(isHovered || isActive) && (
                    <div className="absolute -top-11 left-1/2 -translate-x-1/2 bg-[#2B0063] text-white px-3 py-1.5 rounded-xl text-xs font-mono font-bold whitespace-nowrap shadow-2xl border-2 border-[#FF6B35] flex items-center gap-1.5 pointer-events-none z-50 animate-fadeIn">
                      <span>{item.label}</span>
                      {item.badge && (
                        <span className="px-1.5 py-0.5 bg-[#FF6B35] text-white text-[10px] rounded-md font-bold">
                          {item.badge}
                        </span>
                      )}
                    </div>
                  )}
                </button>
              );
            })}

            {/* 2. INNER ARC ITEMS (9 NODES) */}
            {innerNavItems.map((item, index) => {
              const isActive = currentView === item.id;
              const isHovered = hoveredItemId === item.id;
              const { transform } = getInnerItemSemiArcStyle(index, item.id);

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
                  className={`nav-item-btn absolute w-8 h-8 rounded-full flex items-center justify-center transition-all duration-200 ${
                    isActive || isHovered ? 'z-30' : 'z-20'
                  }`}
                >
                  {/* Spotlight Glow (Solar Orange for microservice nodes) */}
                  {(isHovered || isActive) && (
                    <div className="absolute inset-0 rounded-full bg-[#E86326] border border-[#2B0063] shadow-[0_0_16px_rgba(232,99,38,0.6)] backdrop-blur-md animate-scaleIn pointer-events-none"></div>
                  )}

                  {/* Icon */}
                  <span
                    className={`material-symbols-outlined transition-all ${
                      isActive
                        ? 'text-[#0D1533] scale-110 font-bold text-base'
                        : isHovered
                        ? 'text-[#0D1533] scale-110 text-base'
                        : 'text-slate-400/80 hover:text-white text-[15px]'
                    }`}
                  >
                    {item.icon}
                  </span>

                  {/* Tooltip */}
                  {(isHovered || isActive) && (
                    <div className="absolute -top-11 left-1/2 -translate-x-1/2 bg-[#2B0063] text-white px-3 py-1.5 rounded-xl text-xs font-mono font-bold whitespace-nowrap shadow-2xl border-2 border-[#FF6B35] flex items-center gap-1.5 pointer-events-none z-50 animate-fadeIn">
                      <span className="text-[#FF6B35] font-bold">Node {index + 1}:</span>
                      <span>{item.shortLabel}</span>
                    </div>
                  )}
                </button>
              );
            })}
          </div>

          {/* Central Orb Hub: PIN & HIDE */}
          <div className="absolute bottom-2 left-1/2 -translate-x-1/2 z-30 pointer-events-auto flex items-center gap-2">
            {/* Pin / Free Toggle */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsPinned(!isPinned);
              }}
              className={`group relative flex items-center justify-center w-12 h-12 rounded-full border-2 transition-all duration-300 shadow-xl backdrop-blur-3xl hover:scale-110 active:scale-95 ${
                isPinned
                  ? 'bg-[#FF6B35]/20 border-[#FF6B35] text-[#FF6B35] ring-2 ring-[#FF6B35]/40'
                  : 'bg-[#280B43]/90 border-white/50 text-white hover:border-white'
              }`}
              title={isPinned ? "Currently Pinned in Place. Click to Free" : "Currently Free. Click to Pin in Place"}
            >
              <div className="relative z-10 flex flex-col items-center justify-center">
                <span className="material-symbols-outlined text-lg">
                  {isPinned ? 'push_pin' : 'pin_drop'}
                </span>
                <span className="text-[7px] font-mono font-bold tracking-widest -mt-0.5">
                  {isPinned ? 'PINNED' : 'FREE'}
                </span>
              </div>
            </button>

            {/* Minimize / Unpin back to Assistive Touch */}
            <button
              onClick={handleCloseArc}
              className="group relative flex items-center justify-center w-12 h-12 bg-slate-900/90 rounded-full border-2 border-white/40 hover:border-tas-red text-white shadow-xl backdrop-blur-3xl hover:scale-110 active:scale-95 transition-all"
              title="Minimize back to Floating Assistive Touch"
            >
              <div className="relative z-10 flex flex-col items-center justify-center text-white">
                <span className="material-symbols-outlined text-lg text-slate-200 group-hover:text-tas-red">
                  close
                </span>
                <span className="text-[7px] font-mono font-bold tracking-widest text-slate-400 group-hover:text-white -mt-0.5">
                  HIDE
                </span>
              </div>
            </button>
          </div>

          {/* Quick Guidance Hint Badge */}
          <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-950/95 text-slate-300 text-[9px] font-mono px-2.5 py-0.5 rounded-md border border-white/20 whitespace-nowrap pointer-events-none shadow-xl z-40">
            Outer Arc: <strong className="text-blue-400">Core</strong> | Inner Arc: <strong className="text-rose-400">9 Nodes</strong> | Right-Click: <strong className="text-tas-red">List</strong>
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
