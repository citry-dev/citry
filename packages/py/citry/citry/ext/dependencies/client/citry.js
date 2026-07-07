/**
 * Citry's client-side dependency manager.
 *
 * The server inlines this script into pages rendered with the "document"
 * strategy (or, once a web integration is mounted, serves it at a URL). It
 * has three jobs:
 *
 * 1. Run components' per-instance JS. A component's JS registers a callback
 *    with `$onComponent(...)` (expanded server-side to
 *    `Citry.manager.registerComponent("<classId>", ...)`); the page carries
 *    a JSON manifest naming which instances to call with which data; the
 *    manager matches the two and calls the callback with the instance's
 *    elements (the ones carrying its `data-cid-<id>` marker) and its
 *    `js_data()` result.
 *
 * 2. Track which scripts/stylesheets are already on the page (by URL), so
 *    an HTML fragment inserted later does not fetch them again.
 *
 * 3. Load the scripts/stylesheets a fragment needs (`loadJs`/`loadCss` from
 *    JSON tag descriptors).
 *
 * Manifests are JSON script tags carrying the `data-citry` attribute. JSON
 * is inert no matter how the HTML lands in the page (innerHTML included), so
 * a MutationObserver watches for inserted manifest tags and processes them;
 * manifests already in the document are processed at startup. String fields
 * inside a manifest ride as base64, so content can never break out of the
 * script tag.
 *
 * Design: docs/design/dependencies.md section 8.
 */
(function () {
  "use strict";

  if (globalThis.Citry && globalThis.Citry.manager) {
    return; // already loaded (e.g. both a document page and a fragment included it)
  }

  // ----- state -----

  // URLs already on the page, per type ("js" / "css").
  var loaded = { js: new Set(), css: new Set() };
  // classId -> array of $onComponent callbacks.
  var callbacks = new Map();
  // "classId:varsHash" -> the registered js_data() payload.
  var componentData = new Map();
  // Calls whose callback or data has not arrived yet.
  var pendingCalls = [];

  var fromBase64 = function (value) {
    return decodeURIComponent(
      Array.prototype.map
        .call(atob(value), function (ch) {
          return "%" + ("00" + ch.charCodeAt(0).toString(16)).slice(-2);
        })
        .join("")
    ); // atob alone mangles non-ASCII; this decodes the bytes as UTF-8
  };

  // ----- loaded-URL bookkeeping -----

  var markScriptLoaded = function (type, url) {
    loaded[type].add(url);
  };

  var isScriptLoaded = function (type, url) {
    return loaded[type].has(url);
  };

  // ----- element creation from {tag, attrs, content} descriptors -----

  var createElement = function (descriptor) {
    var el = document.createElement(descriptor.tag);
    Object.keys(descriptor.attrs || {}).forEach(function (name) {
      var value = descriptor.attrs[name];
      if (value === true) el.setAttribute(name, "");
      else if (value !== false && value != null) el.setAttribute(name, String(value));
    });
    if (descriptor.content) el.textContent = descriptor.content;
    return el;
  };

  // Append a <script> descriptor to <body>; resolves once it has loaded.
  var loadJs = function (descriptor) {
    var url = descriptor.attrs && descriptor.attrs.src;
    if (url && isScriptLoaded("js", url)) return Promise.resolve();
    var el = createElement(descriptor);
    if (url) markScriptLoaded("js", url);
    return new Promise(function (resolve, reject) {
      if (url) {
        el.onload = resolve;
        el.onerror = reject;
        document.body.appendChild(el);
      } else {
        document.body.appendChild(el); // inline scripts run synchronously
        resolve();
      }
    });
  };

  // Append a <link rel="stylesheet"> (or inline <style>) descriptor to <head>.
  var loadCss = function (descriptor) {
    var url = descriptor.attrs && descriptor.attrs.href;
    if (url && isScriptLoaded("css", url)) return Promise.resolve();
    var el = createElement(descriptor);
    if (url) markScriptLoaded("css", url);
    document.head.appendChild(el);
    return Promise.resolve();
  };

  // ----- component callbacks and data -----

  var registerComponent = function (classId, fn) {
    var fns = callbacks.get(classId);
    if (!fns) callbacks.set(classId, (fns = []));
    fns.push(fn);
    flushCalls();
  };

  var registerComponentData = function (classId, varsHash, data) {
    componentData.set(classId + ":" + varsHash, data);
    flushCalls();
  };

  var callComponent = function (classId, componentId, varsHash) {
    pendingCalls.push({ classId: classId, componentId: componentId, varsHash: varsHash });
    flushCalls();
  };

  var isCallReady = function (call) {
    if (!callbacks.has(call.classId)) return false;
    return call.varsHash == null || componentData.has(call.classId + ":" + call.varsHash);
  };

  // Run every pending call whose callback and data have both arrived. Calls
  // stay queued (in order) until they are ready, so the manifest, the
  // component's JS, and the data script may arrive in any order.
  var flushCalls = function () {
    var stillPending = [];
    pendingCalls.forEach(function (call) {
      if (!isCallReady(call)) {
        stillPending.push(call);
        return;
      }
      var data = call.varsHash == null ? null : componentData.get(call.classId + ":" + call.varsHash);
      var els = Array.prototype.slice.call(
        document.querySelectorAll("[data-cid-" + call.componentId + "]")
      );
      callbacks.get(call.classId).forEach(function (fn) {
        try {
          fn({ id: call.componentId, els: els, data: data });
        } catch (err) {
          console.error("[Citry] component callback for '" + call.classId + "' failed:", err);
        }
      });
    });
    pendingCalls = stillPending;
  };

  // ----- manifests -----

  // Process one manifest object (already JSON-parsed; string fields base64):
  //   markLoaded: {js: [url...], css: [url...]}   already on the page
  //   fetch:      {js: [tag descriptor JSON...], css: [...]}   load now
  //   calls:      [[classId, componentId, varsHash | null], ...]
  var loadComponentScripts = function (manifest) {
    var markLoaded = manifest.markLoaded || {};
    (markLoaded.js || []).forEach(function (url) {
      markScriptLoaded("js", fromBase64(url));
    });
    (markLoaded.css || []).forEach(function (url) {
      markScriptLoaded("css", fromBase64(url));
    });

    var fetch = manifest.fetch || {};
    (fetch.css || []).forEach(function (encoded) {
      loadCss(JSON.parse(fromBase64(encoded)));
    });
    (fetch.js || []).forEach(function (encoded) {
      loadJs(JSON.parse(fromBase64(encoded)));
    });

    (manifest.calls || []).forEach(function (call) {
      callComponent(
        fromBase64(call[0]),
        fromBase64(call[1]),
        call[2] == null ? null : fromBase64(call[2])
      );
    });
  };

  var processManifestTag = function (el) {
    if (el.dataset.citryProcessed != null) return;
    el.dataset.citryProcessed = "";
    try {
      loadComponentScripts(JSON.parse(el.textContent));
    } catch (err) {
      console.error("[Citry] failed to process dependency manifest:", err);
    }
  };

  var manifestSelector = 'script[type="application/json"][data-citry]';

  new MutationObserver(function (mutations) {
    mutations.forEach(function (mutation) {
      mutation.addedNodes.forEach(function (node) {
        if (node.nodeType !== 1) return;
        if (node.matches && node.matches(manifestSelector)) processManifestTag(node);
        else if (node.querySelectorAll) {
          node.querySelectorAll(manifestSelector).forEach(processManifestTag);
        }
      });
    });
  }).observe(document.documentElement, { childList: true, subtree: true });

  // ----- public surface -----

  globalThis.Citry = globalThis.Citry || {};
  globalThis.Citry.manager = {
    registerComponent: registerComponent,
    registerComponentData: registerComponentData,
    callComponent: callComponent,
    loadJs: loadJs,
    loadCss: loadCss,
    markScriptLoaded: markScriptLoaded,
    isScriptLoaded: isScriptLoaded,
    _loadComponentScripts: loadComponentScripts,
  };

  // Manifests that were already in the document before this script ran.
  var processExisting = function () {
    document.querySelectorAll(manifestSelector).forEach(processManifestTag);
  };
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", processExisting);
  } else {
    processExisting();
  }
})();
