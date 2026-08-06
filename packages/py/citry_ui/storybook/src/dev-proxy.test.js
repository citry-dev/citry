import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import http from "node:http";
import net from "node:net";
import { fileURLToPath } from "node:url";
import test from "node:test";

const root = fileURLToPath(new URL("..", import.meta.url));

function listen(server, port) {
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(port, "127.0.0.1", resolve);
  });
}

function close(server) {
  return new Promise((resolve, reject) => {
    server.close((error) => (error ? reject(error) : resolve()));
  });
}

function runProxy(adapter) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, ["src/dev-proxy.js", adapter], {
      cwd: root,
      stdio: ["ignore", "pipe", "pipe"],
    });
    let stdout = "";
    let stderr = "";
    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (chunk) => {
      stdout += chunk;
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk;
    });
    child.once("error", reject);
    child.once("close", (code, signal) => resolve({ code, signal, stderr, stdout }));
  });
}

function startProxy(adapter) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, ["src/dev-proxy.js", adapter], {
      cwd: root,
      stdio: ["ignore", "pipe", "pipe"],
    });
    let stderr = "";
    let stdout = "";
    const timeout = setTimeout(() => {
      child.kill("SIGTERM");
      reject(new Error(`Timed out starting the proxy.\n${stdout}\n${stderr}`));
    }, 10_000);
    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (chunk) => {
      stdout += chunk;
      if (stdout.includes("proxy listening on")) {
        clearTimeout(timeout);
        resolve(child);
      }
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk;
    });
    child.once("error", (error) => {
      clearTimeout(timeout);
      reject(error);
    });
    child.once("close", (code, signal) => {
      clearTimeout(timeout);
      reject(
        new Error(
          `Proxy exited before listening (${code ?? signal}).\n${stdout}\n${stderr}`,
        ),
      );
    });
  });
}

function stopProxy(child) {
  if (child.exitCode !== null) {
    return Promise.resolve();
  }
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      child.kill("SIGKILL");
      reject(new Error("Timed out stopping the proxy."));
    }, 10_000);
    child.once("close", () => {
      clearTimeout(timeout);
      resolve();
    });
    child.kill("SIGTERM");
  });
}

function hostileHttpStatus(port) {
  return new Promise((resolve, reject) => {
    const request = http.request(
      {
        headers: { Host: "attacker.example" },
        host: "127.0.0.1",
        path: "/citry/citry.js",
        port,
      },
      (response) => {
        response.resume();
        response.once("end", () => resolve(response.statusCode));
      },
    );
    request.once("error", reject);
    request.end();
  });
}

function hostileUpgradeStatus(port) {
  return new Promise((resolve, reject) => {
    const socket = net.createConnection({ host: "127.0.0.1", port });
    let response = "";
    socket.setEncoding("utf8");
    socket.once("connect", () => {
      socket.write(
        "GET / HTTP/1.1\r\n" +
          "Host: attacker.example\r\n" +
          "Connection: Upgrade\r\n" +
          "Upgrade: websocket\r\n\r\n",
      );
    });
    socket.on("data", (chunk) => {
      response += chunk;
    });
    socket.once("end", () => resolve(response.split("\r\n", 1)[0]));
    socket.once("error", reject);
  });
}

function canConnect(port) {
  return new Promise((resolve) => {
    const socket = net.createConnection({ host: "127.0.0.1", port });
    socket.once("connect", () => {
      socket.destroy();
      resolve(true);
    });
    socket.once("error", () => resolve(false));
  });
}

test("an occupied public port never starts the private Storybook server", async () => {
  const occupied = net.createServer();
  await listen(occupied, 6106);
  try {
    const result = await runProxy("server");
    assert.equal(result.signal, null);
    assert.equal(result.code, 1);
    assert.match(result.stderr, /EADDRINUSE/);
    assert.equal(await canConnect(7106), false);
  } finally {
    await close(occupied);
  }
});

test("the development proxy rejects hostile HTTP and WebSocket authorities", async () => {
  const child = await startProxy("server");
  try {
    assert.equal(await hostileHttpStatus(6106), 403);
    assert.equal(await hostileUpgradeStatus(6106), "HTTP/1.1 403 Forbidden");
  } finally {
    await stopProxy(child);
  }
  assert.equal(await canConnect(7106), false);
});
