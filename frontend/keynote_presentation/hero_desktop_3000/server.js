const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

const PORT = process.env.PORT || 3000;
const BASE_DIR = __dirname;
const INTENTS_DIR = path.join(BASE_DIR, 'user-intents');

// Ensure user-intents directory exists
if (!fs.existsSync(INTENTS_DIR)) {
    fs.mkdirSync(INTENTS_DIR, { recursive: true });
}

/**
 * Intelligent Intent Classifier & Smart RAG Rule Engine
 */
function classifyIntent(message, context = '') {
    const text = (message || '').toLowerCase().strip ? (message || '').toLowerCase().trim() : (message || '').toLowerCase();
    
    // Explicit Greeting Detection
    if (text === 'hi' || text === 'hello' || text === 'hey' || text.startsWith('hi ') || text.startsWith('hello ') || text.startsWith('hey ') || text.includes('jane')) {
        return {
            intent: 'GREETING',
            confidence: 0.99,
            entities: {},
            response: "Hi there! I'm Jane, Lead Machine Learning Solutions Architect at AIConnex. I'd love to help you build and launch your custom AutoML project! What prediction goal or dataset are you working with today?",
            suggestedActions: ["Predict RUL for Compressor", "Train AutoML Model", "Telemetry Status"],
            navigateTo: null
        };
    }

    if (text.includes('rul') || text.includes('compressor') || text.includes('predict') || text.includes('life') || text.includes('maintenance')) {
        return {
            intent: 'PREDICT_RUL',
            confidence: 0.98,
            entities: { asset: 'compressor', metric: 'Remaining Useful Life (RUL)' },
            response: "Predicting asset failure before it happens is a game changer for maintenance! To point our AntiGravity pipeline in the right direction — are you looking to classify machines into 'Healthy vs. Faulty' states, or predict the exact remaining useful life in hours?",
            suggestedActions: ["Predict RUL", "Train AutoML", "Telemetry Status"],
            navigateTo: null
        };
    }

    if (text.includes('train') || text.includes('automl') || text.includes('model') || text.includes('pipeline')) {
        return {
            intent: 'TRAIN_AUTOML_MODEL',
            confidence: 0.95,
            entities: { action: 'train_model', mode: 'AutoML_4Layer' },
            response: "That makes total sense! Let's get your AutoML pipeline structured. Where is your dataset stored right now (e.g., S3 bucket, local CSV/Parquet file, or PostgreSQL database), and what column holds your target prediction answer?",
            suggestedActions: ["Predict RUL", "Train AutoML", "Telemetry Status"],
            navigateTo: null
        };
    }

    if (text.includes('desktop') || text.includes('home') || text.includes('main page') || text.includes('hero')) {
        return {
            intent: 'NAVIGATE_PAGE',
            confidence: 0.99,
            entities: { destination: 'aiconnex_hero_desktop' },
            response: "Taking you back to the main AIConnex Hero Dashboard now...",
            suggestedActions: ["Go to Main Dashboard"],
            navigateTo: "/aiconnex_hero_desktop/"
        };
    }

    if (text.includes('chat') || text.includes('studio') || text.includes('open assistant')) {
        return {
            intent: 'NAVIGATE_PAGE',
            confidence: 0.99,
            entities: { destination: 'aiconnex_hero_chat_open' },
            response: "Opening the interactive AIConnex Studio workspace for you...",
            suggestedActions: ["Open Studio View"],
            navigateTo: "/aiconnex_hero_chat_open/"
        };
    }

    if (text.includes('doc') || text.includes('help') || text.includes('guide') || text.includes('api') || text.includes('cli')) {
        return {
            intent: 'SEARCH_DOCS',
            confidence: 0.92,
            entities: { topic: 'documentation' },
            response: "I've pulled up the key technical guides for AntiGravity v2.4, including our 4-Layer Feature Synthesis, Telemetry Ingestion (OPC UA/MQTT), and SageMaker/ONNX deployment docs.",
            suggestedActions: ["View CLI Docs", "OPC UA Integration", "ONNX Deployment Guide"],
            navigateTo: null
        };
    }

    if (text.includes('opc') || text.includes('mqtt') || text.includes('sensor') || text.includes('telemetry') || text.includes('modbus')) {
        return {
            intent: 'CHECK_TELEMETRY',
            confidence: 0.94,
            entities: { subsystem: 'telemetry_connectors' },
            response: "Telemetry streams look solid! Our OPC UA, MQTT, and Modbus connectors are running smoothly with 99.9% signal stability.",
            suggestedActions: ["Check Sensor Status", "Add Gateway", "Download Logs"],
            navigateTo: null
        };
    }

    return {
        intent: 'GENERAL_INQUIRY',
        confidence: 0.85,
        entities: {},
        response: "Hey! I'm Jane, Lead ML Solutions Architect at AIConnex. I'm here to help you structure, train, and deploy high-performance ML models on your dataset. Tell me a bit about what problem you're trying to solve — is it predicting equipment failures, forecasting trends, or classifying dataset records?",
        suggestedActions: ["Predict RUL", "Train AutoML", "Telemetry Status"],
        navigateTo: null
    };
}

/**
 * Log intent data to backend user-intent-{userId}.json and user-intent-{userId}.txt
 */
function logUserIntent(userId, userMessage, intentResult, pageContext) {
    const sanitizedUserId = (userId || '1223').toString().replace(/[^a-zA-Z0-9_-]/g, '');
    const jsonFilePath = path.join(INTENTS_DIR, `user-intent-${sanitizedUserId}.json`);
    const txtFilePath = path.join(INTENTS_DIR, `user-intent-${sanitizedUserId}.txt`);
    const timestamp = new Date().toISOString();

    let userLogData = {
        userId: sanitizedUserId,
        createdTime: timestamp,
        lastUpdated: timestamp,
        totalIntentsLogged: 0,
        intents: []
    };

    if (fs.existsSync(jsonFilePath)) {
        try {
            const raw = fs.readFileSync(jsonFilePath, 'utf8');
            userLogData = JSON.parse(raw);
        } catch (e) {
            console.error(`Error reading existing intent file for user ${sanitizedUserId}:`, e);
        }
    }

    const newIntentRecord = {
        intentId: `intent_${Date.now()}_${Math.floor(Math.random() * 1000)}`,
        timestamp: timestamp,
        pageContext: pageContext || 'unknown',
        userMessage: userMessage,
        detectedIntent: intentResult.intent,
        confidence: intentResult.confidence,
        extractedEntities: intentResult.entities,
        agentResponse: intentResult.response,
        navigateTo: intentResult.navigateTo || null
    };

    userLogData.intents.push(newIntentRecord);
    userLogData.totalIntentsLogged = userLogData.intents.length;
    userLogData.lastUpdated = timestamp;

    // Save JSON
    fs.writeFileSync(jsonFilePath, JSON.stringify(userLogData, null, 2), 'utf8');

    // Save formatted TXT log for quick manual inspection
    const txtLine = `[${timestamp}] User: "${userMessage}" | Intent: ${intentResult.intent} (Conf: ${intentResult.confidence}) | Page: ${pageContext}\n`;
    fs.appendFileSync(txtFilePath, txtLine, 'utf8');

    return { jsonFilePath, totalLogged: userLogData.totalIntentsLogged };
}

// Create HTTP Server
const server = http.createServer((req, res) => {
    const parsedUrl = url.parse(req.url, true);
    const pathname = parsedUrl.pathname;
    const method = req.method.toUpperCase();

    // CORS Headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (method === 'OPTIONS') {
        res.writeHead(204);
        res.end();
        return;
    }

    // API Endpoint: Process Chat & Log Intent
    if (pathname === '/api/chat' && method === 'POST') {
        let body = '';
        req.on('data', chunk => { body += chunk.toString(); });
        req.on('end', () => {
            try {
                const payload = JSON.parse(body || '{}');
                const userMessage = payload.message || '';
                const userId = payload.userId || '1223';
                const pageContext = payload.pageContext || 'desktop';

                const intentResult = classifyIntent(userMessage, pageContext);
                const logInfo = logUserIntent(userId, userMessage, intentResult, pageContext);

                const responseData = {
                    success: true,
                    userId: userId,
                    userMessage: userMessage,
                    response: intentResult.response,
                    botResponse: intentResult.response,
                    intent: intentResult.intent,
                    confidence: intentResult.confidence,
                    entities: intentResult.entities,
                    suggestedActions: intentResult.suggestedActions,
                    navigateTo: intentResult.navigateTo,
                    backendIntentFile: `user-intents/user-intent-${userId}.json`,
                    totalLoggedIntents: logInfo.totalLogged
                };

                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify(responseData));
            } catch (err) {
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ success: false, error: 'Invalid JSON payload' }));
            }
        });
        return;
    }

    // API Endpoint: Get user intent logs
    if (pathname.startsWith('/api/intents/') && method === 'GET') {
        const userId = pathname.replace('/api/intents/', '').trim();
        const jsonFilePath = path.join(INTENTS_DIR, `user-intent-${userId}.json`);
        if (fs.existsSync(jsonFilePath)) {
            const fileContent = fs.readFileSync(jsonFilePath, 'utf8');
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(fileContent);
        } else {
            res.writeHead(404, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ success: false, error: `No intent file found for userId: ${userId}` }));
        }
        return;
    }

    // API Endpoint: List all intent files
    if (pathname === '/api/intents' && method === 'GET') {
        const files = fs.readdirSync(INTENTS_DIR).filter(f => f.startsWith('user-intent-'));
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true, files }));
        return;
    }

    // Unified React Application Routing (aiconnex_demo/frontend/dist)
    const distDir = path.join(BASE_DIR, '..', 'aiconnex_demo', 'frontend', 'dist');
    const hasDist = fs.existsSync(distDir);

    let filePath = hasDist 
        ? path.join(distDir, pathname === '/' ? 'index.html' : pathname)
        : path.join(BASE_DIR, pathname === '/' ? 'aiconnex_hero_desktop/code.html' : pathname);

    if (hasDist && !fs.existsSync(filePath)) {
        // SPA fallback to index.html
        filePath = path.join(distDir, 'index.html');
    } else if (!hasDist && fs.existsSync(filePath) && fs.statSync(filePath).isDirectory()) {
        filePath = path.join(filePath, 'code.html');
    }

    const ext = path.extname(filePath).toLowerCase();
    const mimeTypes = {
        '.html': 'text/html',
        '.css': 'text/css',
        '.js': 'text/javascript',
        '.json': 'application/json',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.svg': 'image/svg+xml',
        '.txt': 'text/plain',
        '.woff': 'font/woff',
        '.woff2': 'font/woff2',
        '.ttf': 'font/ttf'
    };

    const contentType = mimeTypes[ext] || 'application/octet-stream';

    fs.readFile(filePath, (err, data) => {
        if (err) {
            // SPA fallback if dist exists
            if (hasDist) {
                fs.readFile(path.join(distDir, 'index.html'), (indexErr, indexData) => {
                    if (indexErr) {
                        res.writeHead(404, { 'Content-Type': 'text/html' });
                        res.end(`<h1>404 Not Found</h1>`);
                    } else {
                        res.writeHead(200, { 'Content-Type': 'text/html' });
                        res.end(indexData);
                    }
                });
            } else {
                res.writeHead(404, { 'Content-Type': 'text/html' });
                res.end(`<h1>404 Not Found</h1><p>The requested URL ${pathname} was not found.</p>`);
            }
        } else {
            res.writeHead(200, { 'Content-Type': contentType });
            res.end(data);
        }
    });
});

let currentPort = PORT;

function startListening(port) {
    server.listen(port, () => {
        console.log(`===================================================`);
        console.log(`🚀 TAS AIConnex Server Running on http://localhost:${port}`);
        console.log(`📄 Desktop View: http://localhost:${port}/aiconnex_hero_desktop/`);
        console.log(`💬 Chat Open View: http://localhost:${port}/aiconnex_hero_chat_open/`);
        console.log(`📁 User Intent Files Saved To: ${INTENTS_DIR}`);
        console.log(`===================================================`);
    });
}

server.on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
        currentPort++;
        console.log(`⚠️ Port ${currentPort - 1} is already in use. Trying fallback port ${currentPort}...`);
        startListening(currentPort);
    } else {
        console.error('Server error:', err);
    }
});

startListening(currentPort);
