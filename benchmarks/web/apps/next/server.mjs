import http from "node:http";
import next from "next";

const port = Number(process.argv[2]);
if (!Number.isInteger(port) || port < 1024) throw new Error("A benchmark port is required");

const app = next({dev: false, hostname: "127.0.0.1", port});
await app.prepare();
const handle = app.getRequestHandler();

function ackHeaders(response, headers = null) {
  const values =
    headers?.["set-cookie"] ??
    headers?.["Set-Cookie"] ??
    response.getHeader("set-cookie") ??
    response.getHeader("Set-Cookie");
  const cookies = Array.isArray(values) ? values : values ? [String(values)] : [];
  const cookie = cookies.find(value => value.startsWith("citry-bench-ack="));
  if (!cookie) return null;
  const encoded = cookie.slice("citry-bench-ack=".length).split(";", 1)[0];
  let candidate = encoded;
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      return JSON.parse(candidate);
    } catch {
      try {
        const decoded = decodeURIComponent(candidate);
        if (decoded === candidate) return null;
        candidate = decoded;
      } catch {
        return null;
      }
    }
  }
  return null;
}

const server = http.createServer(async (request, response) => {
  const started = performance.now();
  const pathname = new URL(request.url || "/", "http://127.0.0.1").pathname;
  const initialDocument = request.method === "GET" && pathname === "/";
  const measuredDocument = pathname === "/";
  let injected = false;
  const originalSetHeader = response.setHeader.bind(response);
  const setAckHeaders = ack => {
    if (!ack || response.headersSent) return;
    if (Number.isInteger(ack.revision) && typeof ack.operation === "string") {
      originalSetHeader("x-bench-operation", ack.operation);
      originalSetHeader("x-bench-revision", String(ack.revision));
    }
  };
  response.setHeader = (name, value) => {
    const result = originalSetHeader(name, value);
    if (String(name).toLowerCase() === "set-cookie") setAckHeaders(ackHeaders(response));
    return result;
  };
  const inject = headers => {
    if (injected || response.headersSent) return;
    injected = true;
    const duration = (performance.now() - started).toFixed(3);
    // Initial App Router HTML is the server-rendered phase. Server Actions
    // return an RSC/delta payload, so their preparation is classified
    // separately by the hybrid adapter contract.
    if (measuredDocument) {
      const metric = initialDocument ? "render" : "prepare";
      const timing = `application;dur=${duration}, ${metric};dur=${duration}`;
      // The benchmark owns this header: retaining an internal Next metric could
      // create duplicate `render` entries and make the phase ambiguous.
      originalSetHeader("server-timing", timing);
    }
    response.setHeader("cache-control", "no-store");
    setAckHeaders(ackHeaders(response, headers));
  };
  const writeHead = response.writeHead.bind(response);
  const write = response.write.bind(response);
  const end = response.end.bind(response);
  const flushHeaders = response.flushHeaders.bind(response);
  response.writeHead = (...args) => {
    const headers = typeof args.at(-1) === "object" && args.at(-1) !== null ? args.at(-1) : null;
    inject(headers);
    return writeHead(...args);
  };
  response.write = (...args) => { inject(); return write(...args); };
  response.end = (...args) => { inject(); return end(...args); };
  response.flushHeaders = (...args) => { inject(); return flushHeaders(...args); };
  try {
    await handle(request, response);
  } catch (error) {
    response.statusCode = 500;
    response.end(String(error));
  }
});

server.listen(port, "127.0.0.1");
