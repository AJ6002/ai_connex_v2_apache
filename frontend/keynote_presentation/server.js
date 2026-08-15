/**
 * TAS AIConnex — Unified Enterprise Hero & Cinematic Keynote Server Suite
 * 
 * Port 3000: Main Enterprise Hero Desktop & Jane Chatbot RAG Engine
 * Port 3001: Project Genesis Cinematic Motion Animation & Keynote
 */

const http = require('http');
const fs   = require('fs');
const path = require('path');

const PORT_HERO = process.env.PORT || 3000;
const PORT_GENESIS = process.env.GENESIS_PORT || 3001;

const HERO_DIR = path.join(__dirname, 'hero_desktop_3000');
const KEYNOTE_DIR = path.join(__dirname, 'keynote_animation_3001');

const MIME = {
  '.html':  'text/html; charset=utf-8',
  '.css':   'text/css; charset=utf-8',
  '.js':    'application/javascript; charset=utf-8',
  '.json':  'application/json; charset=utf-8',
  '.png':   'image/png',
  '.jpg':   'image/jpeg',
  '.svg':   'image/svg+xml',
  '.ico':   'image/x-icon',
  '.woff2': 'font/woff2',
};

// ── PORT 3000 SERVER (Hero Desktop & Intent Classifier) ──────
const heroServer = http.createServer((req, res) => {
  let urlPath = req.url.split('?')[0];

  if (req.method === 'POST' && urlPath === '/api/chat') {
    let body = '';
    req.on('data', chunk => body += chunk.toString());
    req.on('end', () => {
      try {
        const payload = JSON.parse(body || '{}');
        const userMsg = (payload.message || '').toLowerCase();
        
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          status: 'success',
          reply: `Jane AI: Processing query "${payload.message}". Recommended action: Initiate predictive analytics pipeline on Line 4 chillers.`,
          timestamp: new Date().toISOString()
        }));
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Invalid JSON payload' }));
      }
    });
    return;
  }

  if (urlPath === '/' || urlPath === '/hero') {
    urlPath = '/aiconnex_hero_desktop/code.html';
  } else if (urlPath === '/chat') {
    urlPath = '/aiconnex_hero_chat_open/code.html';
  }

  const filePath = path.join(HERO_DIR, urlPath);
  const ext = path.extname(filePath).toLowerCase();

  fs.readFile(filePath, (err, data) => {
    if (err) {
      // Fallback check in keynote dir if missing
      const altPath = path.join(KEYNOTE_DIR, urlPath);
      fs.readFile(altPath, (err2, data2) => {
        if (err2) {
          res.writeHead(404, { 'Content-Type': 'text/plain' });
          res.end('404 Page Not Found');
          return;
        }
        res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
        res.end(data2);
      });
      return;
    }
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
    res.end(data);
  });
});

heroServer.listen(PORT_HERO, () => {
  console.log(`[Hero Server] Running at http://localhost:${PORT_HERO}/`);
});

// ── PORT 3001 SERVER (Cinematic Keynote & Animation) ─────────
const genesisServer = http.createServer((req, res) => {
  let urlPath = req.url.split('?')[0];

  if (urlPath === '/' || urlPath === '/genesis') {
    urlPath = '/genesis.html';
  } else if (urlPath === '/motion') {
    urlPath = '/index.html';
  }

  const filePath = path.join(KEYNOTE_DIR, urlPath);
  const ext = path.extname(filePath).toLowerCase();

  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('404 Keynote Page Not Found');
      return;
    }
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
    res.end(data);
  });
});

genesisServer.listen(PORT_GENESIS, () => {
  console.log(`[Keynote Server] Running at http://localhost:${PORT_GENESIS}/genesis.html`);
});

console.log('');
console.log('╔════════════════════════════════════════════════════════════════╗');
console.log('║  TAS AIConnex — Enterprise Hero & Keynote Animation Suite      ║');
console.log('╠════════════════════════════════════════════════════════════════╣');
console.log(`║  1. Main Hero UI       →  http://localhost:${PORT_HERO}/                 ║`);
console.log(`║  2. Genesis Keynote    →  http://localhost:${PORT_GENESIS}/genesis.html    ║`);
console.log('╚════════════════════════════════════════════════════════════════╝');
console.log('');
