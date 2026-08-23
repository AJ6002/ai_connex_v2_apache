/* ==========================================================================
   TAS AIConnex Motion Engine - Strict 3-Color Particle Canvas & Visualizer
   Color Palette: #280B43 Deep Eggplant, #FF6B35 Coral Orange, #FFFFFF White
   ========================================================================== */

class MotionCanvasEngine {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    
    this.particles = [];
    this.numParticles = 60;
    this.connectionDistance = 140;
    this.animFrameId = null;
    
    this.currentMode = 'mesh'; // 'mesh', 'pipeline', 'spectral', 'network', 'roi'
    
    this.resize();
    this.initParticles();
    
    window.addEventListener('resize', () => this.resize());
  }

  resize() {
    const parent = this.canvas.parentElement;
    if (!parent) return;
    this.width = this.canvas.width = parent.clientWidth;
    this.height = this.canvas.height = parent.clientHeight;
  }

  initParticles() {
    this.particles = [];
    for (let i = 0; i < this.numParticles; i++) {
      this.particles.push({
        x: Math.random() * (this.width || 800),
        y: Math.random() * (this.height || 600),
        vx: (Math.random() - 0.5) * 1.2,
        vy: (Math.random() - 0.5) * 1.2,
        radius: Math.random() * 2.5 + 1.5,
        color: Math.random() > 0.4 ? '#FF6B35' : '#FF8F5A',
        pulse: Math.random() * Math.PI * 2
      });
    }
  }

  setMode(mode) {
    this.currentMode = mode;
  }

  start() {
    if (this.animFrameId) cancelAnimationFrame(this.animFrameId);
    const render = () => {
      this.draw();
      this.animFrameId = requestAnimationFrame(render);
    };
    render();
  }

  draw() {
    if (!this.ctx) return;
    this.ctx.clearRect(0, 0, this.width, this.height);
    
    // Update and draw particles
    this.particles.forEach((p, idx) => {
      p.x += p.vx;
      p.y += p.vy;
      p.pulse += 0.03;

      if (p.x < 0 || p.x > this.width) p.vx *= -1;
      if (p.y < 0 || p.y > this.height) p.vy *= -1;

      const alpha = 0.4 + Math.sin(p.pulse) * 0.3;
      
      this.ctx.beginPath();
      this.ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      this.ctx.fillStyle = p.color === '#FF6B35' 
        ? `rgba(255, 107, 53, ${alpha})` 
        : `rgba(255, 143, 90, ${alpha})`;
      this.ctx.fill();

      // Connect near particles
      for (let j = idx + 1; j < this.particles.length; j++) {
        const p2 = this.particles[j];
        const dx = p.x - p2.x;
        const dy = p.y - p2.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < this.connectionDistance) {
          const lineAlpha = (1 - dist / this.connectionDistance) * 0.25;
          this.ctx.beginPath();
          this.ctx.moveTo(p.x, p.y);
          this.ctx.lineTo(p2.x, p2.y);
          this.ctx.strokeStyle = `rgba(255, 107, 53, ${lineAlpha})`;
          this.ctx.lineWidth = 1;
          this.ctx.stroke();
        }
      }
    });

    if (this.currentMode === 'spectral') {
      this.drawWaveform();
    }
  }

  drawWaveform() {
    const time = Date.now() * 0.003;
    this.ctx.beginPath();
    this.ctx.moveTo(0, this.height * 0.7);
    for (let x = 0; x < this.width; x += 10) {
      const y = this.height * 0.7 + Math.sin(x * 0.01 + time) * 20 + Math.cos(x * 0.02 + time * 1.5) * 15;
      this.ctx.lineTo(x, y);
    }
    this.ctx.strokeStyle = 'rgba(255, 107, 53, 0.5)';
    this.ctx.lineWidth = 2;
    this.ctx.stroke();
  }
}

window.MotionCanvasEngine = MotionCanvasEngine;
