// Render recorded Citry pages with Vue's own server renderer.
//
// Input (argv[2]): a JSON array of pages, each {digest, manifest, tags,
// definitions}, as `check.py` passes them. Output (argv[3]): a JSON object
// mapping each digest to {html} or {error}.
//
// Every definition runs its real browser JavaScript, the bundle the server
// sends. The small runtime below stands in for the parts of Citry's client
// (`citry/_vue/client.js`) that decide what a render creates: the compiler
// helpers (`compilerRuntime`), the component options that expose
// `$citryPrepared` and each `js_data` key on the instance, and the
// `citry-opaque-html` component. Pieces copied from client.js say so.
import { createRequire } from "node:module";
import { readFileSync, writeFileSync } from "node:fs";

// Vue resolves from the client package, which pins the version the browser
// runtime is built with.
const root = new URL("../../", import.meta.url);
const require = createRequire(new URL("packages/js/citry-client/package.json", root));
const V = require("vue");
const { renderToString } = require("vue/server-renderer");

const [pagesPath, resultsPath] = process.argv.slice(2);
const pages = JSON.parse(readFileSync(pagesPath, "utf8"));

// Names this check adds to element props so the comparison can tell which
// attributes Vue itself sets while hydrating. `check.py` strips them.
const PATCHED_MARKER = "data-citry-parity-patched";
const SHOW_MARKER = "data-citry-parity-show";
// Marks an element whose only content is a dynamic `textContent` (`v-text`
// with no children of its own), which the Rust side may leave empty.
const TEXT_MARKER = "data-citry-parity-text";

// A value only the browser knows: a key read from the instance that neither
// `$citryPrepared`, `js_data` nor Vue provides here (component `data()`,
// `setup()`, methods, injections, browser plugins). It is callable and
// readable at any depth, so a render that uses such a value still finishes;
// the Rust side declines these values, so they should only reach shells.
const BROWSER_TEXT = "‹browser-only›";
const BROWSER = new Proxy(function browserOnly() {}, {
  get(_target, key) {
    if (key === Symbol.toPrimitive) return () => BROWSER_TEXT;
    if (typeof key === "symbol") return undefined;
    // Vue probes these flags on values it receives; answering "no" keeps
    // the value an ordinary one.
    if (key.startsWith("__v_") || key === "then") return undefined;
    return BROWSER;
  },
  apply: () => BROWSER,
});
// Counts the browser-only values each page's render read, so the check can
// flag a page where Vue read one but the Rust side declined nothing.
let browserReads = 0;
const browserAware = (ctx) =>
  new Proxy(ctx, {
    get(target, key, receiver) {
      if (typeof key === "symbol" || key in target) return Reflect.get(target, key, receiver);
      browserReads += 1;
      return BROWSER;
    },
  });

// Adapted from client.js: `vnodeProps` strips the input model site and derives the
// vnode key from it. The key never reaches the HTML, so a fixed stand-in is
// enough here.
const INPUT_MODEL_SITE = "__citryInputModelSite";
const vnodeProps = (props) => {
  if (props === null || props === undefined || !Object.hasOwn(props, INPUT_MODEL_SITE)) return props;
  const prepared = { ...props };
  delete prepared[INPUT_MODEL_SITE];
  prepared.key = JSON.stringify(["citry-input-model", props[INPUT_MODEL_SITE], prepared.key]);
  return prepared;
};

// The keys `hydrateElement` in runtime-core 3.5.42 patches on an element
// instead of trusting the server's attributes: listeners (never written by
// the server renderer), `value`-like keys on input and option, `.prop`
// keys, every key of a custom element, and the keys listed as dynamic.
function patchedKeys(type, props, dynamicProps) {
  const keys = new Set(dynamicProps || []);
  for (const key of Object.keys(props || {})) {
    if ((type === "input" || type === "option") && (key.endsWith("value") || key === "indeterminate")) keys.add(key);
    if (key.startsWith(".") || type.includes("-")) keys.add(key);
  }
  return [...keys];
}

function compilerCreateVNode(type, props, children, dynamicProps) {
  let prepared = vnodeProps(props);
  if (typeof type === "string") {
    const keys = patchedKeys(type, prepared, dynamicProps);
    if (keys.length) prepared = { ...(prepared || {}), [PATCHED_MARKER]: JSON.stringify(keys) };
    // Vue's server renderer writes a `textContent` or `innerHTML` prop as
    // the element's contents. For a key listed as dynamic, hydration sets
    // the key itself and replaces whatever the server wrote, so the server
    // may write the vnode's own children there; render those instead.
    // The exception is `textContent` on an element with no children: the
    // Rust side writes that text when it knows the value, so the stand-in
    // keeps the key and Vue's server renderer writes the text to compare
    // against; the marker lets the comparison accept an element the Rust
    // side left empty for hydration to fill.
    for (const key of ["textContent", "innerHTML"]) {
      if (keys.includes(key) && Object.hasOwn(prepared, key)) {
        prepared = { ...prepared };
        if (key === "textContent" && children == null) {
          prepared[TEXT_MARKER] = "";
        } else {
          delete prepared[key];
        }
      }
    }
  }
  // client.js creates every vnode with patch flag 0. It also passes a constant
  // or server-sent `value` on text inputs, select and textarea as `.value`; both spellings
  // write the same property and attribute on the first render, so `value`
  // stays here. Hydration also writes `.value` on select and textarea, which
  // `patchedKeys` does not list, so this comparison stays the stricter one.
  return V.createVNode(type, prepared, children, 0, dynamicProps);
}

const compilerRuntime = Object.create(V);
Object.defineProperty(compilerRuntime, "openBlock", { value: () => null, enumerable: true });
for (const name of ["createVNode", "createElementVNode", "createBlock", "createElementBlock"]) {
  Object.defineProperty(compilerRuntime, name, {
    value: (type, props, children, _patchFlag, dynamicProps) => compilerCreateVNode(type, props, children, dynamicProps),
    enumerable: true,
  });
}
Object.defineProperty(compilerRuntime, "createTextVNode", { value: (text) => V.createTextVNode(text), enumerable: true });
// `v-show` sets `display` while hydrating (its `beforeMount` hook), so the
// comparison lets the server leave out `display` when the value is
// browser-only.
Object.defineProperty(compilerRuntime, "withDirectives", {
  enumerable: true,
  value(vnode, directives) {
    if (directives.some(([directive]) => directive === V.vShow)) {
      vnode.props = { ...(vnode.props || {}), [SHOW_MARKER]: "" };
    }
    return V.withDirectives(vnode, directives);
  },
});

// Adapted from client.js: `runtimeForDynamicElements` maps `<component :is>` tag
// aliases back to the real tag.
function runtimeForDynamicElements(entries) {
  if (entries.length === 0) return compilerRuntime;
  const aliases = new Map(entries.map((entry) => [entry.alias, entry.tag]));
  const runtime = Object.create(compilerRuntime);
  for (const name of ["createVNode", "createElementVNode", "createBlock", "createElementBlock"]) {
    Object.defineProperty(runtime, name, {
      enumerable: true,
      value(type, props, children, _patchFlag, dynamicProps) {
        if (typeof type === "string" && type.startsWith("citry-dynamic-")) {
          if (!aliases.has(type)) throw new Error("unknown prepared dynamic element alias: " + type);
          type = aliases.get(type);
        }
        return compilerCreateVNode(type, props, children, dynamicProps);
      },
    });
  }
  return Object.freeze(runtime);
}

// Adapted from client.js: the `citry-opaque-html` component. Each record
// is a Fragment holding one static vnode with the record's HTML (or no
// children when the HTML parses into no nodes).
const opaqueHtmlComponent = {
  name: "CitryOpaqueHtml",
  props: { record: { type: Object, required: true } },
  setup(props) {
    return () => {
      const record = props.record;
      if (
        Object.keys(record).sort().join(",") !== "html,nodeCount" ||
        typeof record.html !== "string" ||
        !Number.isSafeInteger(record.nodeCount) ||
        record.nodeCount < 0
      ) {
        throw new TypeError("invalid opaque HTML record");
      }
      const children = record.nodeCount === 0 ? [] : [V.createStaticVNode(record.html, record.nodeCount)];
      return V.h(V.Fragment, { key: record.html }, children);
    };
  },
};

// Each definition's bundle registers its render function on
// `window.__citryRuntimeDefinitions`, reading helpers through
// `__citryRuntime.compilerRuntime`, as it does in the browser.
globalThis.window = globalThis;
globalThis.__citryRuntime = { compilerRuntime: { runtimeForDynamicElements } };
function loadDefinition(id, javascript) {
  if (!globalThis.__citryRuntimeDefinitions?.[id]) new Function(javascript)();
  const definition = globalThis.__citryRuntimeDefinitions[id];
  if (!definition) throw new Error("definition did not register: " + id);
  return definition;
}

// The component options client.js builds for one type (`typeOptions`),
// reduced to what a first render reads: the `citryId` prop, the
// occurrence's `preparedData` as `$citryPrepared`, each `js_data` key as an
// instance property, and the definition's render function called with the
// component instance.
function typeOptions(typeKey, occurrences, definitions) {
  return {
    name: "CitryComponent_" + typeKey,
    props: { citryId: { type: String, required: true } },
    beforeCreate() {
      const occurrence = occurrences.get(this.citryId);
      if (!occurrence || occurrence.typeKey !== typeKey) throw new Error("unknown or wrong-type occurrence");
      for (const key of Object.keys(occurrence.serverData || {})) {
        Object.defineProperty(this, key, { enumerable: true, configurable: true, get: () => occurrence.serverData[key] });
      }
      Object.defineProperty(this, "$citryPrepared", {
        enumerable: false,
        configurable: true,
        get: () => occurrence.preparedData || {},
      });
    },
    render(ctx, _cache, ...rest) {
      const occurrence = occurrences.get(this.citryId);
      const definition = definitions.get(occurrence.definitionId);
      if (!definition) throw new Error("missing definition " + occurrence.definitionId);
      // A fresh handler cache per render, as client.js keeps one per mount.
      return definition.render.call(this, browserAware(ctx), [], ...rest);
    },
  };
}

async function renderPage(page) {
  const manifest = JSON.parse(page.manifest);
  const occurrences = new Map(manifest.occurrences.map((item) => [item.id, item]));
  const definitions = new Map();
  for (const [id, definition] of Object.entries(page.definitions)) {
    definitions.set(id, loadDefinition(id, definition.javascript));
  }
  const types = new Map();
  for (const [typeKey, tag] of Object.entries(page.tags)) types.set(tag, typeOptions(typeKey, occurrences, definitions));
  const rootOccurrence = occurrences.get(manifest.rootId);
  const rootType = types.get(page.tags[rootOccurrence.typeKey]);
  const app = V.createSSRApp({ render: () => V.h(rootType, { citryId: manifest.rootId }) });
  for (const [tag, options] of types) app.component(tag, options);
  app.component("citry-opaque-html", opaqueHtmlComponent);
  // Vue's warnings for browser-only values would flood the output.
  app.config.warnHandler = () => {};
  let failure;
  app.config.errorHandler = (error) => {
    failure ??= error;
  };
  const html = await renderToString(app);
  if (failure) throw failure;
  return html;
}

const results = {};
for (const page of pages) {
  try {
    browserReads = 0;
    const html = await renderPage(page);
    results[page.digest] = { html, browserReads };
  } catch (error) {
    results[page.digest] = { error: String(error?.stack || error).split("\n").slice(0, 3).join(" | ") };
  }
}
writeFileSync(resultsPath, JSON.stringify({ vue: V.version, results }));
