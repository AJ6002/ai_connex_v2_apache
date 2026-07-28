import React, { useEffect, useRef } from 'react';

export const InteractiveDotGrid: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const mouse = {
      x: width / 2,
      y: height / 2,
      targetX: width / 2,
      targetY: height / 2,
      active: false,
    };

    const handleResize = () => {
      if (!canvas) return;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.scale(dpr, dpr);
      initGrid();
    };

    const handleMouseMove = (e: MouseEvent) => {
      mouse.targetX = e.clientX;
      mouse.targetY = e.clientY;
      mouse.active = true;
    };

    const handleMouseLeave = () => {
      mouse.active = false;
    };

    window.addEventListener('resize', handleResize);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseleave', handleMouseLeave);

    interface Dot {
      x: number;
      y: number;
      baseX: number;
      baseY: number;
      color: 'red' | 'blue';
      baseRadius: number;
      currentRadius: number;
      targetRadius: number;
      alpha: number;
      targetAlpha: number;
      phase: number;
    }

    let dots: Dot[] = [];
    const spacing = 30; // Distance between grid dots

    const initGrid = () => {
      dots = [];
      const cols = Math.ceil(width / spacing) + 2;
      const rows = Math.ceil(height / spacing) + 2;

      for (let i = 0; i < cols; i++) {
        for (let j = 0; j < rows; j++) {
          const x = i * spacing;
          const y = j * spacing;
          // Alternate red and blue dots
          const isRed = (i + j) % 2 === 0;
          dots.push({
            x,
            y,
            baseX: x,
            baseY: y,
            color: isRed ? 'red' : 'blue',
            baseRadius: isRed ? 2.0 : 2.0,
            currentRadius: isRed ? 2.0 : 2.0,
            targetRadius: isRed ? 2.0 : 2.0,
            alpha: isRed ? 0.45 : 0.4,
            targetAlpha: isRed ? 0.45 : 0.4,
            phase: Math.random() * Math.PI * 2,
          });
        }
      }
    };

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    ctx.scale(dpr, dpr);
    initGrid();

    let time = 0;
    const maxInfluenceRadius = 220; // Radius where dots react to mouse

    const render = () => {
      time += 0.02;

      // Smooth mouse interpolation for liquid trailing physics
      mouse.x += (mouse.targetX - mouse.x) * 0.15;
      mouse.y += (mouse.targetY - mouse.y) * 0.15;

      ctx.clearRect(0, 0, width, height);

      // Clean white background with subtle ambient radial backlight
      ctx.fillStyle = '#FFFFFF';
      ctx.fillRect(0, 0, width, height);

      const bgGradient = ctx.createRadialGradient(
        mouse.x,
        mouse.y,
        0,
        mouse.x,
        mouse.y,
        550
      );
      bgGradient.addColorStop(0, 'rgba(227, 6, 19, 0.06)'); // Soft red liquid glow center
      bgGradient.addColorStop(0.5, 'rgba(35, 56, 139, 0.05)'); // Soft TAS blue halo
      bgGradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
      ctx.fillStyle = bgGradient;
      ctx.fillRect(0, 0, width, height);

      // Render dots
      for (let i = 0; i < dots.length; i++) {
        const dot = dots[i];

        // Subtle idle ambient floating wave
        const idleWave = Math.sin(time + dot.phase) * 0.3;

        // Calculate distance to mouse cursor
        const dx = mouse.x - dot.baseX;
        const dy = mouse.y - dot.baseY;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < maxInfluenceRadius) {
          // Proximity ratio (1 at cursor, 0 at boundary)
          const factor = Math.pow(1 - dist / maxInfluenceRadius, 2);

          // Dot expansion on hover - GROW WHEREVER MOUSE MOVES (Halved expansion size)
          const maxGrow = dot.color === 'red' ? 5.5 : 4.75;
          dot.targetRadius = dot.baseRadius + factor * maxGrow;
          dot.targetAlpha = Math.min(0.95, dot.color === 'red' ? 0.5 + factor * 0.45 : 0.45 + factor * 0.5);

          // Slight displacement away or towards cursor for liquid surface effect
          const pushForce = factor * 7;
          const angle = Math.atan2(dy, dx);
          dot.x = dot.baseX - Math.cos(angle) * pushForce;
          dot.y = dot.baseY - Math.sin(angle) * pushForce;
        } else {
          dot.targetRadius = dot.baseRadius + idleWave * 0.3;
          dot.targetAlpha = dot.color === 'red' ? 0.4 : 0.35;
          dot.x += (dot.baseX - dot.x) * 0.1;
          dot.y += (dot.baseY - dot.y) * 0.1;
        }

        // Smooth transition to target states
        dot.currentRadius += (dot.targetRadius - dot.currentRadius) * 0.18;
        dot.alpha += (dot.targetAlpha - dot.alpha) * 0.18;

        // Draw Dot with radial glass glow
        ctx.beginPath();
        ctx.arc(dot.x, dot.y, Math.max(0.1, dot.currentRadius), 0, Math.PI * 2);

        if (dot.color === 'red') {
          ctx.fillStyle = `rgba(227, 6, 19, ${dot.alpha})`;
          // Glowing aura for large hovered red dots
          if (dot.currentRadius > 4) {
            ctx.shadowColor = 'rgba(227, 6, 19, 0.7)';
            ctx.shadowBlur = dot.currentRadius * 2.2;
          } else {
            ctx.shadowBlur = 0;
          }
        } else {
          ctx.fillStyle = `rgba(35, 56, 139, ${dot.alpha})`;
          if (dot.currentRadius > 4) {
            ctx.shadowColor = 'rgba(35, 56, 139, 0.7)';
            ctx.shadowBlur = dot.currentRadius * 2.2;
          } else {
            ctx.shadowBlur = 0;
          }
        }

        ctx.fill();
        ctx.shadowBlur = 0; // Reset shadow for next iteration
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseleave', handleMouseLeave);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-0 transition-opacity duration-500"
      style={{ background: 'linear-gradient(135deg, #090D18 0%, #0F172A 50%, #111827 100%)' }}
    />
  );
};
