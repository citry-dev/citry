// src/clientLifecycle.ts
var RestartCoordinator = class {
  constructor(restart) {
    this.restart = restart;
  }
  restart;
  requested = false;
  running;
  request() {
    this.requested = true;
    if (this.running === void 0) {
      this.running = this.run();
    }
    return this.running;
  }
  settled() {
    return this.running ?? Promise.resolve();
  }
  async run() {
    try {
      while (this.requested) {
        this.requested = false;
        await this.restart();
      }
    } finally {
      this.running = void 0;
    }
  }
};
var WatchedFileChangeBatcher = class {
  constructor(send, delayMs = 100) {
    this.send = send;
    this.delayMs = delayMs;
  }
  send;
  delayMs;
  pending = /* @__PURE__ */ new Map();
  timer;
  push(uri, type) {
    this.pending.set(uri, type);
    if (this.timer === void 0) {
      this.timer = setTimeout(() => this.flush(), this.delayMs);
    }
  }
  flush() {
    if (this.timer !== void 0) {
      clearTimeout(this.timer);
      this.timer = void 0;
    }
    if (this.pending.size === 0) {
      return;
    }
    const changes = [...this.pending].map(([uri, type]) => ({ uri, type }));
    this.pending.clear();
    this.send(changes);
  }
  dispose() {
    if (this.timer !== void 0) {
      clearTimeout(this.timer);
      this.timer = void 0;
    }
    this.pending.clear();
  }
};
async function stopLanguageClient(client, timeoutMs = 2e3) {
  if (!client.needsStop()) {
    return;
  }
  const process = client.serverProcess;
  try {
    await client.stop(timeoutMs);
  } catch {
    if (process === void 0 || process.exitCode !== null || process.signalCode !== null) {
      return;
    }
    process.kill("SIGTERM");
    const escalation = setTimeout(() => {
      if (process.exitCode === null && process.signalCode === null) {
        process.kill("SIGKILL");
      }
    }, 250);
    escalation.unref();
  }
}
export {
  RestartCoordinator,
  WatchedFileChangeBatcher,
  stopLanguageClient
};
