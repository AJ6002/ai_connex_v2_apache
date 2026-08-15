/**
 * TAS AIConnex — Project Genesis Keynote Server
 * Port 3001  (Main app stays on 3000, untouched)
 */
const http = require('http');
const fs   = require('fs');
const path = require('path');

const PORT = process.env.GENESIS_PORT || 3001;

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

const server = http.createServer((req, res) => {
  let urlPath = req.url.split('?')[0];

  // Route root → genesis.html
  if (urlPath === '/' || urlPath === '/genesis') {
    urlPath = '/genesis.html';
  }

  const filePath = path.join(__dirname, urlPath);
  const ext = path.extname(filePath).toLowerCase();

  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(err.code === 'ENOENT' ? 404 : 500, { 'Content-Type': 'text/plain' });
      res.end(err.code === 'ENOENT' ? '404 Not Found' : `500 Server Error: ${err.message}`);
      return;
    }
    res.writeHead(200, {
      'Content-Type': MIME[ext] || 'application/octet-stream',
      'Cache-Control': 'no-cache',
      'Access-Control-Allow-Origin': '*',
    });
    res.end(data);
  });
});

server.listen(PORT, () => {
  console.log('');
  console.log('╔══════════════════════════════════════════════════════════╗');
  console.log('║  PROJECT GENESIS — Cinematic Keynote Showcase Server     ║');
  console.log(`║  http://localhost:${PORT}/genesis.html                   ║`);
  console.log('╠══════════════════════════════════════════════════════════╣');
  console.log('║  Main Application  →  http://localhost:3000/             ║');
  console.log('║  Genesis Keynote   →  http://localhost:3001/             ║');
  console.log('╚══════════════════════════════════════════════════════════╝');
  console.log('');
});
