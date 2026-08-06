import http from "node:http";
import { spawn } from "node:child_process";

import { createProxyServer } from "httpxy";

const adapters = {
  html: {
    config: ".storybook-html",
    internalPort: 7107,
    port: 6107,
  },
  server: {
    config: ".storybook-server",
    internalPort: 7106,
    port: 6106,
  },
};

const adapterName = process.argv[2];
const adapter = adapters[adapterName];
if (!adapter) {
  throw new Error("Expected a Storybook adapter name: 'server' or 'html'.");
}

const storybook = createProxyServer({
  target: `http://127.0.0.1:${adapter.internalPort}`,
  ws: true,
});
const citry = createProxyServer({
  changeOrigin: true,
  target: "http://127.0.0.1:8123",
  ws: true,
});
const allowedAuthorities = new Set([
  `127.0.0.1:${adapter.port}`,
  `localhost:${adapter.port}`,
]);

function reportProxyError(error, request, response) {
  if (response.writeHead && !response.headersSent) {
    response.writeHead(502, { "content-type": "text/plain; charset=utf-8" });
  }
  if (response.end) {
    response.end(`Storybook proxy failed for ${request.url}: ${error.message}`);
  }
}

storybook.on("error", reportProxyError);
citry.on("error", reportProxyError);

function proxyFor(request) {
  return request.url === "/citry" || request.url.startsWith("/citry/")
    ? citry
    : storybook;
}

function hasTrustedAuthority(request) {
  return allowedAuthorities.has(request.headers.host);
}

const server = http.createServer((request, response) => {
  if (!hasTrustedAuthority(request)) {
    response.writeHead(403, { "content-type": "text/plain; charset=utf-8" });
    response.end("Untrusted Citry Storybook Host.");
    return;
  }
  proxyFor(request).web(request, response);
});
server.on("upgrade", (request, socket, head) => {
  if (!hasTrustedAuthority(request)) {
    socket.end("HTTP/1.1 403 Forbidden\r\nConnection: close\r\n\r\n");
    return;
  }
  proxyFor(request).ws(request, socket, head);
});

let child = null;
let stopping = false;
function stop(signal) {
  if (stopping) {
    return;
  }
  stopping = true;
  server.close();
  if (child?.exitCode === null) {
    child.kill(signal);
  }
}

process.on("SIGINT", () => stop("SIGINT"));
process.on("SIGTERM", () => stop("SIGTERM"));
server.on("error", (error) => {
  process.stderr.write(`Citry Storybook proxy failed to listen: ${error.message}\n`);
  process.exitCode = 1;
});

server.listen(adapter.port, "127.0.0.1", () => {
  process.stdout.write(
    `Citry Storybook ${adapterName} proxy listening on http://127.0.0.1:${adapter.port}\n`,
  );
  child = spawn(
    "pnpm",
    [
      "exec",
      "storybook",
      "dev",
      "--config-dir",
      adapter.config,
      "--port",
      String(adapter.internalPort),
      "--no-open",
    ],
    { stdio: "inherit" },
  );
  child.on("error", (error) => {
    process.stderr.write(`Citry Storybook failed to start: ${error.message}\n`);
    server.close();
    process.exitCode = 1;
  });
  child.on("exit", (code, signal) => {
    server.close();
    if (!stopping && code !== 0) {
      process.exitCode = code ?? (signal ? 1 : 0);
    }
  });
});
