/* ============================================================
   PROJECT GENESIS — JavaScript: Full Cinematic Scene Engine
   TAS AIConnex Industrial AI — Jensen Huang Style Keynote
   ============================================================ */

'use strict';

// ── Audio Synthesis Engine ────────────────────────────────────
class GenesisAudio {
  constructor() {
    this.ctx = null;
    this.enabled = false;
    this.masterGain = null;
  }

  init() {
    if (this.ctx) return;
    try {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return;
      this.ctx = new AC();
      this.masterGain = this.ctx.createGain();
      this.masterGain.gain.value = 0.6;
      this.masterGain.connect(this.ctx.destination);
    } catch (e) {}
  }

  toggle() {
    this.enabled = !this.enabled;
    if (this.enabled) this.init();
    return this.enabled;
  }

  _note(freq, type, dur, vol = 0.15, delay = 0) {
    if (!this.enabled || !this.ctx) return;
    try {
      const now = this.ctx.currentTime + delay;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, now);
      gain.gain.setValueAtTime(vol, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + dur);
      osc.connect(gain);
      gain.connect(this.masterGain);
      osc.start(now);
      osc.stop(now + dur);
    } catch (e) {}
  }

  playTransition() {
    // Deep bass drop — orchestral synth
    this._note(60, 'sine', 0.8, 0.25);
    this._note(90, 'triangle', 0.5, 0.12, 0.1);
    this._note(180, 'sine', 0.3, 0.08, 0.3);
    this._note(440, 'sine', 0.2, 0.05, 0.5);
  }

  playDataBlip() {
    this._note(800, 'sine', 0.06, 0.08);
    this._note(1200, 'sine', 0.04, 0.04, 0.05);
  }

  playClick() {
    this._note(600, 'sine', 0.04, 0.1);
  }

  playDeploy() {
    // Triumphant deploy chord
    [220, 277, 330, 440].forEach((f, i) => {
      this._note(f, 'triangle', 1.2, 0.12, i * 0.08);
    });
  }
}

// ── Particle Canvas Engine ────────────────────────────────────
class ParticleField {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.particles = [];
    this.frameId = null;
    this._resize();
    this._seed(50);
    window.addEventListener('resize', () => this._resize());
  }

  _resize() {
    if (!this.canvas) return;
    this.canvas.width  = this.canvas.parentElement.offsetWidth;
    this.canvas.height = this.canvas.parentElement.offsetHeight;
  }

  _seed(n) {
    this.particles = [];
    for (let i = 0; i < n; i++) {
      const isCyan = Math.random() > 0.35;
      this.particles.push({
        x: Math.random() * (this.canvas?.width || 800),
        y: Math.random() * (this.canvas?.height || 600),
        vx: (Math.random() - 0.5) * 0.8,
        vy: (Math.random() - 0.5) * 0.8,
        r: Math.random() * 2 + 1,
        color: isCyan ? [0, 240, 255] : [255, 215, 0],
        phase: Math.random() * Math.PI * 2
      });
    }
  }

  start() {
    if (this.frameId) return;
    const loop = () => {
      this._draw();
      this.frameId = requestAnimationFrame(loop);
    };
    loop();
  }

  stop() {
    if (this.frameId) {
      cancelAnimationFrame(this.frameId);
      this.frameId = null;
    }
  }

  _draw() {
    const { ctx, canvas, particles } = this;
    if (!canvas) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const t = Date.now() * 0.001;

    particles.forEach((p, i) => {
      p.x += p.vx;
      p.y += p.vy;
      p.phase += 0.02;

      if (p.x < 0 || p.x > canvas.width)  p.vx *= -1;
      if (p.y < 0 || p.y > canvas.height) p.vy *= -1;

      const alpha = 0.3 + Math.sin(p.phase) * 0.25;
      const [r, g, b] = p.color;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${r},${g},${b},${alpha})`;
      ctx.fill();

      for (let j = i + 1; j < particles.length; j++) {
        const q = particles[j];
        const dx = p.x - q.x, dy = p.y - q.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          const lineAlpha = (1 - dist / 120) * 0.15;
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(q.x, q.y);
          ctx.strokeStyle = `rgba(0,240,255,${lineAlpha})`;
          ctx.lineWidth = 1;
          ctx.stroke();
        }
      }
    });
  }
}

// ── FFT Live Chart ────────────────────────────────────────────
class FFTChart {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas?.getContext('2d');
    this.t = 0;
    this.frameId = null;
  }

  start() {
    if (!this.canvas || this.frameId) return;
    const loop = () => {
      this._draw();
      this.t += 0.04;
      this.frameId = requestAnimationFrame(loop);
    };
    loop();
  }

  stop() {
    if (this.frameId) { cancelAnimationFrame(this.frameId); this.frameId = null; }
  }

  _draw() {
    const { ctx, canvas, t } = this;
    if (!ctx) return;
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    // Grid lines
    ctx.strokeStyle = 'rgba(255,255,255,0.04)';
    ctx.lineWidth = 1;
    for (let x = 0; x < W; x += 40) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
    }
    for (let y = 0; y < H; y += 20) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
    }

    // Spectrum bars
    const numBars = 48;
    const bw = W / numBars - 1;
    for (let i = 0; i < numBars; i++) {
      const freq = (i / numBars) * 500;
      // Simulate bearing freq spike at ~120 Hz
      let amp = Math.random() * 0.15 + 0.05;
      if (i >= 10 && i <= 14) amp = 0.6 + Math.sin(t * 3) * 0.2; // spike
      if (i >= 20 && i <= 22) amp = 0.25 + Math.sin(t * 2) * 0.1;

      const bh = amp * (H - 10);
      const progress = Math.min(1, t / 3);
      const drawH = bh * progress;

      const isSpiked = (i >= 10 && i <= 14);
      const grad = ctx.createLinearGradient(0, H - drawH, 0, H);
      if (isSpiked) {
        grad.addColorStop(0, 'rgba(239,68,68,0.9)');
        grad.addColorStop(1, 'rgba(239,68,68,0.2)');
      } else {
        grad.addColorStop(0, 'rgba(0,240,255,0.8)');
        grad.addColorStop(1, 'rgba(0,240,255,0.1)');
      }

      ctx.fillStyle = grad;
      ctx.fillRect(i * (bw + 1) + 1, H - drawH, bw, drawH);
    }

    // Spike label
    if (t > 2) {
      ctx.fillStyle = 'rgba(239,68,68,0.9)';
      ctx.font = '9px Inter, monospace';
      ctx.fillText('⚠ 120Hz SPIKE — Bearing Friction', 88, H - 90);
    }
  }
}

// ── Loss Curve Chart ─────────────────────────────────────────
class LossChart {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas?.getContext('2d');
    this.epoch = 0;
    this.maxEpochs = 40;
    this.frameId = null;
  }

  start() {
    if (!this.canvas || this.frameId) return;
    const loop = () => {
      if (this.epoch < this.maxEpochs) this.epoch += 0.5;
      this._draw();
      this.frameId = requestAnimationFrame(loop);
    };
    loop();
  }

  stop() {
    if (this.frameId) { cancelAnimationFrame(this.frameId); this.frameId = null; }
  }

  _draw() {
    const { ctx, canvas, epoch, maxEpochs } = this;
    if (!ctx) return;
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    const curves = [
      { name: 'XGBoost', color: [255,215,0],   noise: 0.03, base: 0.85 },
      { name: 'CNN-LSTM', color: [0,240,255],   noise: 0.05, base: 0.78 },
      { name: 'Transformer', color: [168,85,247], noise: 0.07, base: 0.70 },
    ];

    const pts = Math.floor(epoch);
    curves.forEach(({ color, noise, base }, ci) => {
      ctx.beginPath();
      for (let i = 0; i <= pts; i++) {
        const x = (i / maxEpochs) * W;
        const decay = base * Math.exp(-i / (maxEpochs * 0.35));
        const jitter = (Math.sin(i * 3.7 + ci * 10) * noise);
        const y = H - (decay + 0.05 + jitter) * H * 0.9;
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }
      ctx.strokeStyle = `rgba(${color.join(',')},0.85)`;
      ctx.lineWidth = 2;
      ctx.stroke();
    });
  }
}

// ── Chiller Impeller Animator ─────────────────────────────────
class ChillerAnimator {
  constructor() {
    this.angle = 0;
    this.frameId = null;
    this.anomalyPhase = 0;
  }

  start() {
    if (this.frameId) return;
    const loop = () => {
      this.angle += 0.04;
      this.anomalyPhase += 0.08;
      this._tick();
      this.frameId = requestAnimationFrame(loop);
    };
    loop();
  }

  stop() {
    if (this.frameId) { cancelAnimationFrame(this.frameId); this.frameId = null; }
  }

  _tick() {
    const impA = document.getElementById('impellerA');
    const impB = document.getElementById('impellerB');
    const impC = document.getElementById('impellerC');
    const heat = document.getElementById('heatmapEllipse');

    if (impA) impA.setAttribute('transform', `translate(120,200) rotate(${this.angle * 180 / Math.PI * 2})`);
    if (impC) impC.setAttribute('transform', `translate(400,200) rotate(${this.angle * 180 / Math.PI * 2})`);

    // Impeller B is erratic (bearing friction)
    const jitter = Math.sin(this.anomalyPhase * 3) * 8;
    if (impB) impB.setAttribute('transform',
      `translate(${260 + jitter * 0.3},${200 + jitter * 0.3}) rotate(${this.angle * 180 / Math.PI * 1.3})`);

    // Heat pulse
    if (heat) {
      const rx = 70 + Math.sin(this.anomalyPhase) * 10;
      const ry = 60 + Math.sin(this.anomalyPhase * 1.3) * 8;
      heat.setAttribute('rx', rx);
      heat.setAttribute('ry', ry);
    }
  }
}

// ── Scene 4 Live Readout ──────────────────────────────────────
function startTwinReadouts(audioEngine) {
  let iteration = 0;
  const interval = setInterval(() => {
    iteration++;
    const tempEl = document.getElementById('bearingTemp');
    const vibEl  = document.getElementById('vibRMS');
    const ctrlEl = document.getElementById('aiCtrl');
    const badge  = document.getElementById('twinStatusBadge');
    const mlPill = document.getElementById('mlActionPill');

    if (iteration < 8) {
      // Anomalous state
      if (tempEl) tempEl.textContent = (84 + Math.random() * 3).toFixed(1) + '°C';
      if (vibEl)  vibEl.textContent  = (6 + Math.random() * 0.8).toFixed(1) + ' mm/s';
      audioEngine.playDataBlip();
    } else if (iteration === 8) {
      // ML intervenes
      if (mlPill) mlPill.textContent = 'ML Model: Adjusting flow parameters...';
      audioEngine.playTransition();
    } else {
      // Recovery
      const coolTemp = Math.max(38, 84 - (iteration - 8) * 4.5);
      const coolVib  = Math.max(0.8, 6.4 - (iteration - 8) * 0.55);
      if (tempEl) {
        tempEl.textContent = coolTemp.toFixed(1) + '°C';
        tempEl.className = 'readout-val ' + (coolTemp < 50 ? 'ok' : coolTemp < 70 ? 'warn' : 'danger');
      }
      if (vibEl) {
        vibEl.textContent = coolVib.toFixed(1) + ' mm/s';
        vibEl.className   = 'readout-val ' + (coolVib < 2 ? 'ok' : 'warn');
      }
      if (badge && coolTemp < 50) {
        badge.textContent = 'OPTIMAL ✓';
        badge.className = 'panel-badge';
      }
      if (ctrlEl && coolTemp < 50) ctrlEl.textContent = 'OPTIMAL ✓';
      if (mlPill && coolTemp < 50) mlPill.textContent = 'ML Model: Failure prevented. Zero downtime.';
    }

    if (iteration > 20) clearInterval(interval);
  }, 600);
}

// ── Scene 5 Deploy Sequence ───────────────────────────────────
async function runDeploySequence(audioEngine) {
  const terminal = document.getElementById('deployTerminal');
  const card = document.getElementById('deployStatusCard');
  const badge = document.querySelector('#scene-4 .panel-badge');

  const lines = [
    { txt: '→ Compiling ONNX model (XGBoost Ensemble)...', delay: 600, color: '' },
    { txt: '→ Attaching Predictive Maintenance toolkit...', delay: 1000, color: '' },
    { txt: '→ Attaching Auto Valve Regulation module...', delay: 1400, color: '' },
    { txt: '→ Attaching SCADA Alarm Router...', delay: 1800, color: '' },
    { txt: '→ Wrapping into Industry-Agent-v4 container...', delay: 2400, color: '' },
    { txt: '→ Signing with AIConnex deployment key...', delay: 3000, color: '' },
    { txt: '[SUCCESS] Deploying to Edge Controller — Line 4 Plant...', delay: 3800, color: 'var(--gold)' },
    { txt: 'Status: DEPLOYED | Latency: 4ms | Autonomous Control: ACTIVE ✓', delay: 4600, color: 'var(--ok)' },
  ];

  const moduleIds = ['mod-1', 'mod-2', 'mod-3'];
  const moduleStatuses = ['mod1-status', 'mod2-status', 'mod3-status'];

  for (const [idx, line] of lines.entries()) {
    await delay(line.delay - (lines[idx - 1]?.delay || 0));
    const div = document.createElement('div');
    div.className = 'term-line';
    div.textContent = line.txt;
    if (line.color) div.style.color = line.color;
    terminal.appendChild(div);
    terminal.scrollTop = terminal.scrollHeight;
    audioEngine.playDataBlip();

    // Activate toolkit modules
    if (idx >= 1 && idx <= 3) {
      const modEl = document.getElementById(moduleIds[idx - 1]);
      const statusEl = document.getElementById(moduleStatuses[idx - 1]);
      if (modEl) modEl.classList.add('loaded');
      if (statusEl) statusEl.textContent = 'READY ✓';
    }
  }

  // Show status card
  await delay(600);
  if (card) card.classList.remove('hidden');
  if (badge) {
    badge.textContent = 'DEPLOYED ✓';
    badge.className = 'panel-badge';
  }
  audioEngine.playDeploy();
}

function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

// ── Typewriter ────────────────────────────────────────────────
function typeWriter(el, text, speed = 35) {
  return new Promise(resolve => {
    let i = 0;
    el.textContent = '';
    const t = setInterval(() => {
      el.textContent += text[i++];
      if (i >= text.length) { clearInterval(t); resolve(); }
    }, speed);
  });
}

// ── Scene Director ────────────────────────────────────────────
class GenesisKeynote {
  constructor() {
    this.currentScene = 0;
    this.totalScenes = 5;
    this.isAutoPlaying = false;
    this.autoTimer = null;
    this.sceneTimings = [12000, 10000, 11000, 14000, 16000]; // ms per scene

    this.audio = new GenesisAudio();
    this.particles = [];
    this.activeCharts = { fft: null, loss: null };
    this.chiller = new ChillerAnimator();
    this.sceneStarted = new Array(5).fill(false);

    this._boot();
  }

  _boot() {
    // Initialize all 5 particle fields
    for (let i = 0; i < this.totalScenes; i++) {
      this.particles[i] = new ParticleField(`canvas-${i}`);
    }

    // Nav pills
    document.querySelectorAll('.scene-pill').forEach(btn => {
      btn.addEventListener('click', () => {
        const idx = parseInt(btn.dataset.scene);
        this.goTo(idx, true);
      });
    });

    // Slim Sidebar scene buttons
    document.querySelectorAll('.sidebar-btn[data-scene]').forEach(btn => {
      btn.addEventListener('click', () => {
        const idx = parseInt(btn.dataset.scene);
        this.goTo(idx, true);
      });
    });

    // Next buttons
    document.querySelectorAll('.scene-next-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const next = parseInt(btn.dataset.next);
        this.goTo(next, true);
      });
    });

    // Auto-play
    document.getElementById('autoBtn')?.addEventListener('click', () => {
      this.toggleAutoPlay();
    });

    // Sound
    document.getElementById('soundToggleBtn')?.addEventListener('click', () => {
      const on = this.audio.toggle();
      const btn = document.getElementById('soundToggleBtn');
      if (btn) btn.textContent = on ? '🔊' : '🔇';
      if (on) this.audio.playClick();
    });

    // Restart
    document.getElementById('restartBtn')?.addEventListener('click', () => {
      this.goTo(0, true);
      this.audio.playTransition();
    });

    // Theme Toggle
    document.getElementById('themeBtn')?.addEventListener('click', () => {
      document.body.classList.toggle('light-mode');
      this.audio.playClick();
    });

    // Category nav
    document.querySelectorAll('.cat-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.audio.playClick();
      });
    });

    // Kick off scene 0
    this.particles[0].start();
    this._activateScene(0);

    // Presentation loop stopped by default
    this.isAutoPlaying = false;
    const autoBtn = document.getElementById('autoBtn');
    if (autoBtn) autoBtn.classList.remove('playing');

    // Initialize Jane Chatbot Drawer Animated Interactions
    initJaneChatAnimation(this.audio);
  }

  goTo(idx, userTriggered = false) {
    if (idx < 0 || idx >= this.totalScenes) return;
    if (idx === this.currentScene) return;

    // Hide current
    const current = document.getElementById(`scene-${this.currentScene}`);
    if (current) {
      current.style.opacity = '0';
      current.style.transform = 'translateY(-20px) scale(0.98)';
      setTimeout(() => current.classList.add('hidden-scene'), 400);
    }

    this.particles[this.currentScene]?.stop();

    // Show next
    this.currentScene = idx;
    const next = document.getElementById(`scene-${idx}`);
    if (next) {
      next.classList.remove('hidden-scene');
      next.style.opacity = '0';
      next.style.transform = 'translateY(30px) scale(0.97)';
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          next.style.transition = 'opacity 0.7s cubic-bezier(0.16,1,0.3,1), transform 0.7s cubic-bezier(0.16,1,0.3,1)';
          next.style.opacity = '1';
          next.style.transform = 'translateY(0) scale(1)';
        });
      });
    }

    this.particles[idx]?.start();

    // Update pills
    document.querySelectorAll('.scene-pill').forEach((p, i) => {
      p.classList.toggle('active', i === idx);
    });

    // Update slim sidebar active state (orange = active, matches main app)
    document.querySelectorAll('.sidebar-btn[data-scene]').forEach(btn => {
      btn.classList.toggle('active', parseInt(btn.dataset.scene) === idx);
    });

    // Timeline fill
    const fill = document.getElementById('timelineFill');
    if (fill) fill.style.width = `${((idx + 1) / this.totalScenes) * 100}%`;

    this.audio.playTransition();
    this._activateScene(idx);

    if (userTriggered && this.isAutoPlaying) {
      this._scheduleNextAuto();
    }
  }

  _activateScene(idx) {
    if (this.sceneStarted[idx]) return;
    this.sceneStarted[idx] = true;

    // Synchronize Jane Chatbot Drawer to current keynote scene
    syncJaneChatToScene(idx, this.audio);

    switch (idx) {
      case 0: this._runScene0(); break;
      case 1: this._runScene1(); break;
      case 2: this._runScene2(); break;
      case 3: this._runScene3(); break;
      case 4: this._runScene4(); break;
    }
  }

  async _runScene0() {
    const userMsg = document.getElementById('userMsg');
    const janeReply = document.getElementById('janeReply');

    await delay(800);
    if (userMsg) {
      await typeWriter(userMsg,
        '"We\'re seeing micro-vibrations in our Line 4 chillers. We don\'t know if it\'s bearing friction or thermal load. Fix it."',
        28
      );
    }
    await delay(1200);
    if (janeReply) janeReply.classList.remove('hidden');
    this.audio.playDataBlip();
  }

  _runScene1() {
    // Start FFT chart
    this.activeCharts.fft = new FFTChart('fftCanvas');
    this.activeCharts.fft.start();

    // Animate telemetry stream bars
    const tsBar1 = document.getElementById('tsBar1');
    const tsBar2 = document.getElementById('tsBar2');
    const tsVal1 = document.getElementById('tsVal1');
    const tsVal2 = document.getElementById('tsVal2');
    const intCard = document.getElementById('integrityCard');

    let progress1 = 0, progress2 = 0;
    const barInterval = setInterval(() => {
      progress1 = Math.min(100, progress1 + Math.random() * 4 + 2);
      progress2 = Math.min(100, progress2 + Math.random() * 3 + 1.5);
      if (tsBar1) tsBar1.style.width = progress1 + '%';
      if (tsBar2) tsBar2.style.width = progress2 + '%';
      if (tsVal1) tsVal1.textContent = Math.floor(progress1 * 5.4) + ' Hz';
      if (tsVal2) tsVal2.textContent = Math.floor(progress2 * 4.2) + ' Hz';
      this.audio.playDataBlip();
      if (progress1 >= 100 && progress2 >= 100) {
        clearInterval(barInterval);
        // Show integrity card
        setTimeout(() => {
          if (intCard) {
            intCard.style.opacity = '1';
            this.audio.playTransition();
          }
        }, 800);
      }
    }, 120);
  }

  _runScene2() {
    // Start loss chart
    this.activeCharts.loss = new LossChart('lossCanvas');
    this.activeCharts.loss.start();

    // Animate model rows appearing
    const rows = ['mr-1', 'mr-2', 'mr-3'];
    const fills = [
      { id: 'sf1', val: 96, acc: '96.7%', lat: '2.1ms', mem: '4.2MB' },
      { id: 'sf2', val: 93, acc: '93.4%', lat: '8.7ms', mem: '11.8MB' },
      { id: 'sf3', val: 88, acc: '88.2%', lat: '18ms', mem: '32MB' },
    ];

    rows.forEach((id, i) => {
      setTimeout(() => {
        const row = document.getElementById(id);
        if (row) {
          row.style.opacity = '0';
          row.style.transition = 'opacity 0.6s';
          row.style.opacity = '1';
        }
        const d = fills[i];
        setTimeout(() => {
          const acc = document.getElementById(`acc${i+1}`);
          const lat = document.getElementById(`lat${i+1}`);
          const mem = document.getElementById(`mem${i+1}`);
          const sf  = document.getElementById(d.id);
          if (acc) acc.textContent = d.acc;
          if (lat) lat.textContent = d.lat;
          if (mem) mem.textContent = d.mem;
          if (sf) sf.style.width = d.val + '%';
          this.audio.playDataBlip();
        }, 300);
      }, 600 + i * 900);
    });
  }

  _runScene3() {
    this.chiller.start();
    delay(2000).then(() => startTwinReadouts(this.audio));
  }

  _runScene4() {
    runDeploySequence(this.audio);
  }

  toggleAutoPlay() {
    this.isAutoPlaying = !this.isAutoPlaying;
    const btn = document.getElementById('autoBtn');
    if (btn) btn.classList.toggle('playing', this.isAutoPlaying);
    if (this.isAutoPlaying) {
      this._scheduleNextAuto();
    } else {
      clearTimeout(this.autoTimer);
    }
  }

  _scheduleNextAuto() {
    clearTimeout(this.autoTimer);
    const timing = this.sceneTimings[this.currentScene] || 10000;
    this.autoTimer = setTimeout(() => {
      const next = (this.currentScene + 1) % this.totalScenes;
      this.goTo(next);
      if (this.isAutoPlaying) this._scheduleNextAuto();
    }, timing);
  }
}

// ── Boot ─────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  window._genesis = new GenesisKeynote();
});

// ── JANE CHATBOT INTERACTIVE ANIMATION ENGINE ─────────────────
function initJaneChatAnimation(audioEngine) {
  const janeDrawer = document.getElementById('janeDrawer');
  const chatBody = document.querySelector('.jane-chat-body');
  const inputField = document.querySelector('.jane-input-field');
  const sendBtn = document.querySelector('.jane-send-btn');
  const promptPills = document.querySelectorAll('.prompt-pill');

  if (!chatBody || !inputField) return;

  let isTyping = false;

  const SCENARIOS = [
    {
      prompt: "Predict RUL for Line 4 Chiller Bearing B-02",
      badge: "Intent Identified: Remaining Useful Life Prognostics",
      response: "Analyzed 1,280,000 vibration telemetry data points. Weibull hazard curve fit indicates RUL of **4,120 operating hours** before bearing fatigue limits."
    },
    {
      prompt: "Train AutoML model on salt effluent telemetry",
      badge: "Intent Identified: Bayesian Hyperparameter Optimization",
      response: "Synthesized 14 rolling temporal features across 9 microservices. XGBoost model trial #42 achieved **98.4% precision** with a 4ms ONNX edge latency."
    },
    {
      prompt: "Check 9 Microservices fleet telemetry status",
      badge: "Intent Identified: Infrastructure Audit",
      response: "All 9 Microservices (:8000–:8008) are **100% Operational**. Average fleet latency is 9.4ms. Zero data leakage cryptographic hash verified."
    }
  ];

  let autoScenarioIndex = 0;

  function addUserMessage(text) {
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }).toLowerCase();
    const msgDiv = document.createElement('div');
    msgDiv.style.alignSelf = 'flex-end';
    msgDiv.style.maxWidth = '88%';
    msgDiv.style.margin = '4px 0';
    msgDiv.innerHTML = `
      <div style="background: #FF6B35; color: #FFFFFF; padding: 0.75rem 1rem; border-radius: 16px 16px 2px 16px; font-size: 0.88rem; line-height: 1.5; font-weight: 500; box-shadow: 0 4px 12px rgba(255, 107, 53, 0.3);">
        ${escapeHtml(text)}
        <div style="font-size: 0.65rem; color: rgba(255,255,255,0.8); margin-top: 4px; text-align: right;">${timeStr}</div>
      </div>
    `;
    chatBody.appendChild(msgDiv);
    chatBody.scrollTop = chatBody.scrollHeight;
  }

  async function streamJaneResponse(badgeText, responseText) {
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }).toLowerCase();
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'jane-typing-indicator';
    typingDiv.innerHTML = `
      <div style="font-size: 0.68rem; font-weight: 800; color: #FF6B35; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
        <span style="width: 6px; height: 6px; border-radius: 50%; background: #FF6B35;" class="pulse-dot"></span>
        JANE IS ANALYZING...
      </div>
      <div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 0.75rem 1rem; border-radius: 16px; font-size: 0.85rem; color: #64748B;">
        <span>●</span> <span>●</span> <span>●</span>
      </div>
    `;
    chatBody.appendChild(typingDiv);
    chatBody.scrollTop = chatBody.scrollHeight;

    await delay(1200);
    typingDiv.remove();

    const msgDiv = document.createElement('div');
    msgDiv.innerHTML = `
      <div class="msg-author-tag" style="margin-top: 8px;">
        <span class="msg-author-dot"></span>
        JANE — LEAD ML ARCHITECT
      </div>
      <div class="msg-bubble-jane">
        <div style="font-size: 0.68rem; font-weight: 700; background: rgba(255,107,53,0.12); color: #FF6B35; border: 1px solid rgba(255,107,53,0.3); border-radius: 99px; padding: 2px 8px; margin-bottom: 6px; display: inline-block;">
          ${escapeHtml(badgeText)}
        </div>
        <div class="jane-text-content"></div>
        <div class="msg-timestamp">${timeStr}</div>
      </div>
    `;
    chatBody.appendChild(msgDiv);

    const textContentEl = msgDiv.querySelector('.jane-text-content');
    let charIdx = 0;
    const formattedText = responseText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    while (charIdx < responseText.length) {
      charIdx += 3;
      textContentEl.innerHTML = responseText.substring(0, charIdx).replace(/\*\*(.*?)\*\*/g, '<strong style="color:#2B0063;">$1</strong>');
      chatBody.scrollTop = chatBody.scrollHeight;
      if (audioEngine) audioEngine.playDataBlip();
      await delay(25);
    }
    textContentEl.innerHTML = formattedText.replace(/\*\*(.*?)\*\*/g, '<strong style="color:#2B0063;">$1</strong>');
    chatBody.scrollTop = chatBody.scrollHeight;
  }

  async function triggerInteraction(promptText, badgeText, responseText) {
    if (isTyping) return;
    isTyping = true;

    if (janeDrawer && janeDrawer.classList.contains('minimized')) {
      janeDrawer.classList.remove('minimized');
    }

    inputField.value = '';
    for (let i = 0; i < promptText.length; i++) {
      inputField.value += promptText[i];
      if (audioEngine) audioEngine.playDataBlip();
      await delay(30);
    }

    await delay(300);

    if (sendBtn) {
      sendBtn.style.transform = 'scale(0.85)';
      sendBtn.style.background = '#2B0063';
      setTimeout(() => {
        sendBtn.style.transform = 'scale(1)';
        sendBtn.style.background = '#FF6B35';
      }, 200);
    }
    if (audioEngine) audioEngine.playTransition();

    const userQuery = inputField.value;
    inputField.value = '';

    addUserMessage(userQuery);

    await streamJaneResponse(badgeText, responseText);
    isTyping = false;
  }

  promptPills.forEach((pill, idx) => {
    pill.addEventListener('click', () => {
      const scenario = SCENARIOS[idx % SCENARIOS.length];
      triggerInteraction(scenario.prompt, scenario.badge, scenario.response);
    });
  });

  if (sendBtn) {
    sendBtn.addEventListener('click', () => {
      const val = inputField.value.trim();
      if (!val || isTyping) return;
      const scenario = SCENARIOS[Math.floor(Math.random() * SCENARIOS.length)];
      triggerInteraction(val, "Intent Identified: Custom Operator Intent", scenario.response);
    });
  }

  inputField.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const val = inputField.value.trim();
      if (!val || isTyping) return;
      const scenario = SCENARIOS[Math.floor(Math.random() * SCENARIOS.length)];
      triggerInteraction(val, "Intent Identified: Custom Operator Intent", scenario.response);
    }
  });

  setInterval(() => {
    if (!isTyping && janeDrawer && !janeDrawer.classList.contains('minimized')) {
      const scenario = SCENARIOS[autoScenarioIndex % SCENARIOS.length];
      autoScenarioIndex++;
      triggerInteraction(scenario.prompt, scenario.badge, scenario.response);
    }
  }, 14000);
}

// ── SCENE SYNCHRONIZED JANE CHATBOT ENGINE ─────────────────────
const JANE_SCENE_SCRIPTS = [
  {
    prompt: "We're seeing micro-vibrations in Line 4 chillers. Fix it.",
    badge: "Intent Identified: Anomaly Diagnosis & Fourier Spectral Analysis",
    response: "Parsing unstructured intent... **Line 4 CRAH Chiller B-02** tagged. Triggering FFT Data Studio pipeline and engaging Data Agents now."
  },
  {
    prompt: "Prepare data & generate live visualization cards",
    badge: "Data Studio: 22 Agent Visual Cards Generated",
    response: "Data Agents initialized! Synthesized **22 Live Data Visual Cards**: FFT Spectrum, Feature Drift Distribution, Correlation Matrix (r=0.94), Outlier Severity Boxplot, Memory Treemap, and SHA-256 Sealed Cryptographic Audit Report."
  },
  {
    prompt: "Train & benchmark AutoML models",
    badge: "ML Studio: Hyperparameter Optimization Complete",
    response: "Bayesian HPO sweep finished across 3 model families. Benchmark Winner: **XGBoost Ensemble** achieving **98.4% precision** with a 4ms ONNX edge latency."
  },
  {
    prompt: "Instantiate 3D Digital Twin of CRAH Chiller B-02",
    badge: "Digital Twin: Auto Coolant Regulation Active",
    response: "Instantiated 3D Digital Twin. Detected **84.2°C bearing friction anomaly** on Unit B. Live AI model executing automated coolant valve regulation to normalize thermal load."
  },
  {
    prompt: "Package & deploy Agentic Toolkit to Edge Controller",
    badge: "Edge Deploy: Industry-Agent-v4 Operational",
    response: "Wrapped model in **Industry-Agent-v4** toolkit (Predictive Maintenance, Auto Valve Regulation, SCADA Alarm Routing). Deployed to Edge Controller at 4ms latency — **$4.2M Annual Savings & 88% Downtime Reduction**."
  }
];

function syncJaneChatToScene(sceneIdx, audioEngine) {
  const janeDrawer = document.getElementById('janeDrawer');
  const chatBody = document.querySelector('.jane-chat-body');
  const inputField = document.querySelector('.jane-input-field');

  if (!chatBody || !inputField) return;
  const script = JANE_SCENE_SCRIPTS[sceneIdx % JANE_SCENE_SCRIPTS.length];
  if (!script) return;

  if (janeDrawer && janeDrawer.classList.contains('minimized')) {
    janeDrawer.classList.remove('minimized');
  }

  // Type in input field
  inputField.value = script.prompt;
  
  // Add User Message
  const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }).toLowerCase();
  const userMsgDiv = document.createElement('div');
  userMsgDiv.style.alignSelf = 'flex-end';
  userMsgDiv.style.maxWidth = '88%';
  userMsgDiv.style.margin = '4px 0';
  userMsgDiv.innerHTML = `
    <div style="background: #FF6B35; color: #FFFFFF; padding: 0.75rem 1rem; border-radius: 16px 16px 2px 16px; font-size: 0.88rem; line-height: 1.5; font-weight: 500; box-shadow: 0 4px 12px rgba(255, 107, 53, 0.3);">
      ${escapeHtml(script.prompt)}
      <div style="font-size: 0.65rem; color: rgba(255,255,255,0.8); margin-top: 4px; text-align: right;">${timeStr}</div>
    </div>
  `;
  chatBody.appendChild(userMsgDiv);
  chatBody.scrollTop = chatBody.scrollHeight;
  inputField.value = '';

  // Stream Jane Response
  setTimeout(() => {
    const janeMsgDiv = document.createElement('div');
    janeMsgDiv.innerHTML = `
      <div class="msg-author-tag" style="margin-top: 8px;">
        <span class="msg-author-dot"></span>
        JANE — LEAD ML ARCHITECT
      </div>
      <div class="msg-bubble-jane">
        <div style="font-size: 0.68rem; font-weight: 700; background: rgba(255,107,53,0.12); color: #FF6B35; border: 1px solid rgba(255,107,53,0.3); border-radius: 99px; padding: 2px 8px; margin-bottom: 6px; display: inline-block;">
          ${escapeHtml(script.badge)}
        </div>
        <div class="jane-text-content"></div>
        <div class="msg-timestamp">${timeStr}</div>
      </div>
    `;
    chatBody.appendChild(janeMsgDiv);
    const textEl = janeMsgDiv.querySelector('.jane-text-content');
    
    let cIdx = 0;
    const interval = setInterval(() => {
      cIdx += 3;
      textEl.innerHTML = script.response.substring(0, cIdx).replace(/\*\*(.*?)\*\*/g, '<strong style="color:#2B0063;">$1</strong>');
      chatBody.scrollTop = chatBody.scrollHeight;
      if (audioEngine) audioEngine.playDataBlip();
      if (cIdx >= script.response.length) {
        clearInterval(interval);
        textEl.innerHTML = script.response.replace(/\*\*(.*?)\*\*/g, '<strong style="color:#2B0063;">$1</strong>');
      }
    }, 20);
  }, 600);
}


