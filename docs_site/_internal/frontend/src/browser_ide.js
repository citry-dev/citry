import { lintGutter, setDiagnostics } from "@codemirror/lint";
import { syntaxTree } from "@codemirror/language";
import { EditorState } from "@codemirror/state";
import { EditorView, hoverTooltip } from "@codemirror/view";
import { citryAssetAt } from "./citry_regions.js";

const SCHEMA_VERSION = 1;
const REQUEST_TIMEOUT_MS = 15_000;
const MAX_SOURCE_BYTES = 64 * 1024;
const encoder = new TextEncoder();

function exactObject(value, fields) {
  return value !== null
    && typeof value === "object"
    && !Array.isArray(value)
    && Object.keys(value).length === fields.length
    && fields.every((field) => Object.hasOwn(value, field));
}

function validPosition(value) {
  return exactObject(value, ["line", "character"])
    && Number.isSafeInteger(value.line)
    && value.line >= 0
    && Number.isSafeInteger(value.character)
    && value.character >= 0;
}

function validRange(value) {
  return exactObject(value, ["start", "end"])
    && validPosition(value.start)
    && validPosition(value.end);
}

function positionAt(source, offset) {
  const prefix = source.slice(0, offset);
  const line = prefix.split("\n").length - 1;
  const lineStart = prefix.lastIndexOf("\n") + 1;
  return { line, character: source.slice(lineStart, offset).length };
}

function offsetAt(source, position) {
  if (!validPosition(position)) return null;
  const lines = source.split("\n");
  if (position.line >= lines.length) return null;
  const line = lines[position.line].replace(/\r$/, "");
  if (position.character > line.length) return null;
  let offset = position.character;
  for (let index = 0; index < position.line; index += 1) offset += lines[index].length + 1;
  return offset;
}

export function templateRegions(state) {
  const regions = [];
  const read = (from, to) => state.sliceDoc(from, to);
  syntaxTree(state).iterate({
    enter(node) {
      const asset = citryAssetAt(node, read);
      if (asset?.kind !== "template" || !asset.sourceExact) return;
      regions.push({
        id: `${asset.from}:${asset.to}`,
        from: asset.from,
        to: asset.to,
        source: state.sliceDoc(asset.from, asset.to),
      });
    },
  });
  return regions;
}

function regionAt(regions, position) {
  return regions.find((region) => region.from <= position && position <= region.to) || null;
}

function completionInfo(item) {
  const root = document.createElement("div");
  root.className = "cm-citry-ide-completion-info";
  const detail = document.createElement("strong");
  detail.textContent = item.detail;
  const description = document.createElement("p");
  description.textContent = item.documentation;
  const link = document.createElement("a");
  link.href = item.documentationUrl;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.textContent = "Open Citry documentation";
  root.append(detail, description, link);
  return root;
}

function hoverContents(value) {
  const root = document.createElement("div");
  root.className = "cm-citry-ide-hover";
  const signature = document.createElement("code");
  signature.textContent = `<${value.label}>`;
  const detail = document.createElement("strong");
  detail.textContent = value.detail;
  const description = document.createElement("p");
  description.textContent = value.documentation;
  const link = document.createElement("a");
  link.href = value.documentationUrl;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.textContent = "Open Citry documentation";
  root.append(signature, detail, description, link);
  return root;
}

export class BrowserIdeSession {
  constructor({ workerFactory = () => new Worker(new URL("./analysis_worker.js", import.meta.url), { type: "module" }) } = {}) {
    this.worker = workerFactory();
    this.view = null;
    this.version = 0;
    this.source = "";
    this.regions = [];
    this.sequence = 0;
    this.pending = new Map();
    this.failed = false;
    this.worker.onmessage = ({ data }) => this.receive(data);
    this.worker.onerror = (event) => this.disable(String(event.message || "Citry analysis Worker failed."));
    this.completionSource = (context) => this.complete(context);
  }

  extensions() {
    return [
      // Add Citry beside the active nested language's own providers instead
      // of replacing CodeMirror's HTML and Python completion sources.
      EditorState.languageData.of(() => [{ autocomplete: this.completionSource }]),
      lintGutter(),
      hoverTooltip((view, position) => this.hover(view, position), { hideOnChange: true }),
      EditorView.theme({
        ".cm-citry-ide-hover": { display: "grid", gap: "0.4rem", maxWidth: "28rem", padding: "0.25rem" },
        ".cm-citry-ide-hover code": { color: "var(--c-code-name)", fontWeight: "700" },
        ".cm-citry-ide-hover p, .cm-citry-ide-completion-info p": { margin: "0" },
      }),
    ];
  }

  attach(view) {
    this.view = view;
    this.update(view.state);
  }

  update(state) {
    if (this.failed) return;
    this.version += 1;
    this.source = state.doc.toString();
    this.regions = templateRegions(state);
    if (encoder.encode(this.source).byteLength > MAX_SOURCE_BYTES) {
      this.applyDiagnostics([]);
      return;
    }
    this.worker.postMessage({
      schemaVersion: SCHEMA_VERSION,
      type: "document",
      version: this.version,
      regions: this.regions.map(({ id, source }) => ({ id, source })),
    });
  }

  versionForSource(source) {
    return !this.failed && source === this.source ? this.version : null;
  }

  publishCatalog(version, snapshot) {
    if (this.failed || !Number.isSafeInteger(version) || version !== this.version) return false;
    this.worker.postMessage({
      schemaVersion: SCHEMA_VERSION,
      type: "catalog",
      version,
      snapshot,
    });
    return true;
  }

  receive(data) {
    if (data?.schemaVersion !== SCHEMA_VERSION) return;
    if (data.type === "unavailable") {
      if (exactObject(data, ["schemaVersion", "type", "message"]) && typeof data.message === "string") {
        this.disable(data.message);
      }
      return;
    }
    if (data.type === "analysis-error") {
      if (
        exactObject(data, ["schemaVersion", "type", "version", "message"])
        && data.version === this.version
        && typeof data.message === "string"
      ) {
        this.applyDiagnostics([]);
        console.warn(`Citry browser analysis failed: ${data.message}`);
      }
      return;
    }
    if (data.type === "diagnostics") {
      if (
        exactObject(data, ["schemaVersion", "type", "version", "diagnostics"])
        && data.version === this.version
        && Array.isArray(data.diagnostics)
      ) {
        this.applyDiagnostics(data.diagnostics);
      }
      return;
    }
    if (
      data.type === "response"
      && exactObject(data, ["schemaVersion", "type", "kind", "requestId", "version", "value"])
    ) {
      const pending = this.pending.get(data.requestId);
      if (!pending || pending.kind !== data.kind) return;
      clearTimeout(pending.timeout);
      this.pending.delete(data.requestId);
      pending.resolve(data.version === this.version ? data.value : null);
    }
  }

  applyDiagnostics(values) {
    if (this.view === null) return;
    const diagnostics = [];
    for (const value of values) {
      if (
        !exactObject(value, ["regionId", "range", "message", "severity", "code"])
        || !validRange(value.range)
        || typeof value.message !== "string"
        || value.severity !== "error"
        || typeof value.code !== "string"
      ) continue;
      const region = this.regions.find((candidate) => candidate.id === value.regionId);
      if (!region) continue;
      const start = offsetAt(region.source, value.range.start);
      const end = offsetAt(region.source, value.range.end);
      if (start === null || end === null || end < start) continue;
      diagnostics.push({
        from: region.from + start,
        to: region.from + end,
        severity: value.severity,
        source: `citry(${value.code})`,
        message: value.message,
      });
    }
    this.view.dispatch(setDiagnostics(this.view.state, diagnostics));
  }

  request(kind, region, position) {
    if (this.failed) return Promise.resolve(null);
    this.sequence += 1;
    const requestId = `${kind}-${this.sequence}`;
    return new Promise((resolve) => {
      const timeout = setTimeout(() => {
        if (!this.pending.has(requestId)) return;
        this.pending.delete(requestId);
        resolve(null);
      }, REQUEST_TIMEOUT_MS);
      this.pending.set(requestId, { kind, resolve, timeout });
      this.worker.postMessage({
        schemaVersion: SCHEMA_VERSION,
        type: kind,
        requestId,
        version: this.version,
        regionId: region.id,
        position,
      });
    });
  }

  async complete(context) {
    const region = regionAt(this.regions, context.pos);
    if (region === null) return null;
    const node = syntaxTree(context.state).resolveInner(context.pos, -1);
    if (node.name !== "TagName") return null;
    const version = this.version;
    const position = positionAt(region.source, context.pos - region.from);
    const value = await this.request("completion", region, position);
    if (context.aborted || version !== this.version || value === null) return null;
    if (!exactObject(value, ["range", "items"]) || !validRange(value.range) || !Array.isArray(value.items)) return null;
    const from = offsetAt(region.source, value.range.start);
    const to = offsetAt(region.source, value.range.end);
    if (from === null || to === null) return null;
    const options = value.items.flatMap((item) => {
      if (
        !exactObject(item, ["label", "detail", "documentation", "documentationUrl"])
        || [item.label, item.detail, item.documentation, item.documentationUrl].some((part) => typeof part !== "string")
      ) return [];
      return [{
        label: item.label,
        detail: item.detail,
        type: "class",
        info: () => completionInfo(item),
      }];
    });
    return {
      from: region.from + from,
      to: region.from + to,
      options,
      validFor: /^c-[\w-]*$/,
    };
  }

  async hover(view, documentPosition) {
    const region = regionAt(this.regions, documentPosition);
    if (region === null) return null;
    const version = this.version;
    const position = positionAt(region.source, documentPosition - region.from);
    const value = await this.request("hover", region, position);
    if (version !== this.version || value === null) return null;
    if (
      !exactObject(value, ["range", "label", "detail", "documentation", "documentationUrl"])
      || !validRange(value.range)
      || [value.label, value.detail, value.documentation, value.documentationUrl].some((part) => typeof part !== "string")
    ) return null;
    const start = offsetAt(region.source, value.range.start);
    const end = offsetAt(region.source, value.range.end);
    if (start === null || end === null) return null;
    return {
      pos: region.from + start,
      end: region.from + end,
      above: true,
      create: () => ({ dom: hoverContents(value) }),
    };
  }

  disable(message) {
    if (this.failed) return;
    this.failed = true;
    this.applyDiagnostics([]);
    for (const pending of this.pending.values()) {
      clearTimeout(pending.timeout);
      pending.resolve(null);
    }
    this.pending.clear();
    console.warn(`Citry browser IDE unavailable: ${message}`);
  }

  destroy() {
    if (!this.failed) {
      this.failed = true;
      for (const pending of this.pending.values()) {
        clearTimeout(pending.timeout);
        pending.resolve(null);
      }
      this.pending.clear();
    }
    this.worker.terminate();
    this.view = null;
  }
}
