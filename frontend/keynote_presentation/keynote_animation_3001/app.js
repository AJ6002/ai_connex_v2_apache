/* ==========================================================================
   TAS AI-ConneX Frontend Extracted UI Component Animation Controller &
   Interactive Jane Chatbot Animation Engine
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  // Engines
  const canvasEngine = new MotionCanvasEngine('stageCanvas');
  if (canvasEngine) canvasEngine.start();
  const audioSynth = new AudioSynthEngine();

  // DOM Elements
  const themeBtn = document.getElementById('themeBtn');
  const soundBtn = document.getElementById('soundBtn');
  const presModeBtn = document.getElementById('presModeBtn');

  const compItems = document.querySelectorAll('.comp-item');
  const showcaseCards = document.querySelectorAll('.showcase-card');
  const catBtns = document.querySelectorAll('.cat-btn');

  const presStepLabel = document.getElementById('presStepLabel');
  const presProgress = document.getElementById('presProgress');
  const presTimerLabel = document.getElementById('presTimerLabel');

  // Presentation State
  let isAutoPres = false;
  let isDarkTheme = true;
  let currentIndex = 0;
  let stepTimer = 0;
  const STEP_DURATION = 5;
  let intervalId = null;

  const COMPONENTS = Array.from(compItems).map(item => {
    return {
      targetId: item.getAttribute('data-target'),
      title: item.querySelector('span')?.textContent || 'Component'
    };
  });

  // Switch Active Component
  function setActiveComponent(index, userTriggered = false) {
    if (index < 0 || index >= COMPONENTS.length) return;
    currentIndex = index;
    const comp = COMPONENTS[index];

    compItems.forEach((item, idx) => {
      item.classList.toggle('active', idx === index);
    });

    showcaseCards.forEach(card => {
      card.classList.toggle('active', card.id === comp.targetId);
    });

    if (presStepLabel) {
      presStepLabel.textContent = `Showing: ${comp.title}`;
    }

    if (userTriggered) {
      audioSynth.playSceneTransition();
      stepTimer = 0;
      if (presProgress) presProgress.style.width = '0%';
    }
  }

  // Auto-Presentation Tick Loop
  function tick() {
    if (!isAutoPres) return;

    stepTimer += 0.1;
    const percent = Math.min((stepTimer / STEP_DURATION) * 100, 100);
    if (presProgress) presProgress.style.width = `${percent}%`;

    if (stepTimer >= STEP_DURATION) {
      stepTimer = 0;
      let nextIdx = (currentIndex + 1) % COMPONENTS.length;
      setActiveComponent(nextIdx);
      audioSynth.playPulse();
    }
  }

  function startPresentationLoop() {
    if (intervalId) clearInterval(intervalId);
    intervalId = setInterval(tick, 100);
  }

  // Event Listeners
  compItems.forEach((item, idx) => {
    item.addEventListener('click', () => {
      setActiveComponent(idx, true);
    });
  });

  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      isDarkTheme = !isDarkTheme;
      document.body.classList.toggle('light-mode', !isDarkTheme);
      audioSynth.playClick();
    });
  }

  if (soundBtn) {
    soundBtn.addEventListener('click', () => {
      audioSynth.toggleMute();
      soundBtn.textContent = audioSynth.isMuted ? '🔇 Muted' : '🔊 Sound FX';
    });
  }

  if (presModeBtn) {
    presModeBtn.classList.remove('active');
    presModeBtn.textContent = '⏸ Presentation Paused';
    presModeBtn.addEventListener('click', () => {
      isAutoPres = !isAutoPres;
      presModeBtn.classList.toggle('active', isAutoPres);
      presModeBtn.textContent = isAutoPres ? '▶ Client Auto-Presentation' : '⏸ Presentation Paused';
      audioSynth.playClick();
    });
  }

  startPresentationLoop();

  // ══════════════════════════════════════════════════════════════
  // JANE CHATBOT INTERACTIVE ANIMATION ENGINE
  // ══════════════════════════════════════════════════════════════
  initJaneChatAnimation(audioSynth);
});

function initJaneChatAnimation(audioSynth) {
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

  // Add User Message to Chat
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

  // Add Jane Response Stream
  async function streamJaneResponse(badgeText, responseText) {
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }).toLowerCase();
    
    // Typing indicator
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

    // Actual Response Bubble
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
    
    // Typewriter streaming effect
    let charIdx = 0;
    const formattedText = responseText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    while (charIdx < responseText.length) {
      charIdx += 3;
      textContentEl.innerHTML = responseText.substring(0, charIdx).replace(/\*\*(.*?)\*\*/g, '<strong style="color:#2B0063;">$1</strong>');
      chatBody.scrollTop = chatBody.scrollHeight;
      if (audioSynth) audioSynth.playPulse();
      await delay(25);
    }
    textContentEl.innerHTML = formattedText.replace(/\*\*(.*?)\*\*/g, '<strong style="color:#2B0063;">$1</strong>');
    chatBody.scrollTop = chatBody.scrollHeight;
  }

  // Simulate Input Typing & Send Interaction
  async function triggerInteraction(promptText, badgeText, responseText) {
    if (isTyping) return;
    isTyping = true;

    if (janeDrawer && janeDrawer.classList.contains('minimized')) {
      janeDrawer.classList.remove('minimized');
    }

    // Type prompt into input field character by character
    inputField.value = '';
    for (let i = 0; i < promptText.length; i++) {
      inputField.value += promptText[i];
      if (audioSynth) audioSynth.playPulse();
      await delay(30);
    }

    await delay(300);

    // Animate Send Button click
    if (sendBtn) {
      sendBtn.style.transform = 'scale(0.85)';
      sendBtn.style.background = '#2B0063';
      setTimeout(() => {
        sendBtn.style.transform = 'scale(1)';
        sendBtn.style.background = '#FF6B35';
      }, 200);
    }
    if (audioSynth) audioSynth.playSceneTransition();

    // Clear input field and add message
    const userQuery = inputField.value;
    inputField.value = '';

    addUserMessage(userQuery);

    // Stream Jane's response
    await streamJaneResponse(badgeText, responseText);
    isTyping = false;
  }

  // Quick Prompt Pill Clicks
  promptPills.forEach((pill, idx) => {
    pill.addEventListener('click', () => {
      const scenario = SCENARIOS[idx % SCENARIOS.length];
      triggerInteraction(scenario.prompt, scenario.badge, scenario.response);
    });
  });

  // Handle Send Button click & Enter Key press
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

  // Automated interaction demo loop every 14 seconds
  setInterval(() => {
    if (!isTyping && janeDrawer && !janeDrawer.classList.contains('minimized')) {
      const scenario = SCENARIOS[autoScenarioIndex % SCENARIOS.length];
      autoScenarioIndex++;
      triggerInteraction(scenario.prompt, scenario.badge, scenario.response);
    }
  }, 14000);
}

function escapeHtml(str) {
  return str.replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[m]));
}

function delay(ms) { return new Promise(r => setTimeout(r, ms)); }
