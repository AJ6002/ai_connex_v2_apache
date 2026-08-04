import express from "express";
import path from "path";
import { createServer as createViteServer } from "vite";
import http from "http";

async function startServer() {
  const app = express();
  const PORT = 3000;

  // Proxy all /api requests to the Flask backend
  app.use("/api", (req, res) => {
    const options = {
      hostname: "localhost",
      port: 5000,
      path: req.originalUrl,
      method: req.method,
      headers: req.headers,
    };
    const proxyReq = http.request(options, (proxyRes) => {
      res.writeHead(proxyRes.statusCode!, proxyRes.headers);
      proxyRes.pipe(res);
    });
    proxyReq.on("error", (err) => {
      console.error("Proxy error:", err);
      res.status(502).json({ reply: "Backend server is not running." });
    });
    req.pipe(proxyReq);
  });

  // Vite middleware for development
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`AI Connexx Suite server running on http://0.0.0.0:${PORT}`);
  });
}

startServer().catch((err) => {
  console.error("Fatal error starting AI Connexx Suite server:", err);
  process.exit(1);
});
