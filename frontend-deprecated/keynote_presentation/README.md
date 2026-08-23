# TAS AIConnex — Enterprise Hero & Keynote Animation Suite

This folder consolidates all code files for the **TAS AIConnex Enterprise Hero Application** (`localhost:3000`) and the **Project Genesis Cinematic Keynote & Animation Engine** (`localhost:3001`).

## 📁 Directory Overview

- **`hero_desktop_3000/`**:
  - `aiconnex_hero_desktop/`: Main Enterprise Hero UI layout & canvas
  - `aiconnex_hero_chat_open/`: Interactive Jane AI Chatbot Drawer UI
  - `user-intents/`: Intent logs & telemetry state persistence
  - `server.js`: HTTP server for port 3000

- **`keynote_animation_3001/`**:
  - `genesis.html`: Keynote presentation slide deck
  - `genesis.js`: Scene engine & audio synthesizer
  - `genesis.css`: Keynote visual styles
  - `index.html` & `app.js`: Motion canvas particle background
  - `server-genesis.js`: Keynote server for port 3001

- **`server.js` (Root)**:
  - Unified server script that launches **both** Port 3000 and Port 3001 simultaneously.

---

## 🚀 Quick Start

Run the following command in terminal:

```bash
npm start
# OR
node server.js
```

### Access Ports:
- 🖥️ **Main Enterprise Hero UI**: [http://localhost:3000](http://localhost:3000)
- 🎬 **Project Genesis Keynote & Animation**: [http://localhost:3001/genesis.html](http://localhost:3001/genesis.html)
