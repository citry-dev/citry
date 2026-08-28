import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

export const ALPINE_VERSION = "3.16.2";
export const GENERATED_BANNER =
  "/* Citry events client runtime. GENERATED FILE, do not edit: built from packages/js/citry-client/src/citry-events.ts (pnpm run build there). Bundles AlpineJS 3.16.2 + @alpinejs/morph 3.16.2 (MIT). */";
export const CSP_GENERATED_BANNER =
  "/* Citry events CSP client runtime. GENERATED FILE, do not edit: built from packages/js/citry-client/src/citry-events.ts (pnpm run build there). Bundles @alpinejs/csp 3.16.2 + @alpinejs/morph 3.16.2 (MIT). */";
export const I18N_GENERATED_BANNER =
  "/* Citry i18n client runtime. GENERATED FILE, do not edit: built from packages/js/citry-client/src/citry-i18n.ts (pnpm run build there). Bundles @fluent/bundle 0.19.1 (Apache-2.0). */";

const DIRECTIVES_IMPORTS = `import { onAttributeRemoved, onElRemoved } from './mutation'
import { evaluate, evaluateLater } from './evaluator'
import { elementBoundEffect } from './reactivity'
import Alpine from './alpine'
`;

const INSTRUMENTED_DIRECTIVES_IMPORTS = `${DIRECTIVES_IMPORTS}
function runCitryAmbientDirective(el, attributeName, registerCleanup, callback) {
    let run = globalThis.Citry && globalThis.Citry.alpine && globalThis.Citry.alpine._runDirective

    return typeof run === 'function' ? run(el, attributeName, registerCleanup, callback) : callback()
}
`;

const DIRECTIVE_HANDLER = `        handler.inline && handler.inline(el, directive, utilities)

        handler = handler.bind(handler, el, directive, utilities)

        isDeferringHandlers ? directiveHandlerStacks.get(currentHandlerStackKey).push(handler) : handler()`;

const INSTRUMENTED_DIRECTIVE_HANDLER = `        handler.inline && runCitryAmbientDirective(
            el,
            directive.original,
            utilities.cleanup,
            () => handler.inline(el, directive, utilities),
        )

        handler = handler.bind(handler, el, directive, utilities)

        let runHandler = () => runCitryAmbientDirective(el, directive.original, utilities.cleanup, handler)

        isDeferringHandlers ? directiveHandlerStacks.get(currentHandlerStackKey).push(runHandler) : runHandler()`;

const MORPH_CONTEXT_ENTRY = `function createMorphContext(options = {}) {`;

const PLANNING_ENTRY = `function cloneCitryPlanningTree(source, sources) {
  let clone = source.cloneNode(false);
  sources.set(clone, source);
  if (source._x_bindings) clone._x_bindings = source._x_bindings;
  Array.from(source.childNodes).forEach((child) => clone.appendChild(cloneCitryPlanningTree(child, sources)));
  return clone;
}
function planBetween(from, to, options = {}) {
  let fromSources = new WeakMap();
  let toSources = new WeakMap();
  let fromClone = cloneCitryPlanningTree(from, fromSources);
  let toClone = cloneCitryPlanningTree(to, toSources);
  let updating = options.updating || (() => {
  });
  let adding = options.adding || (() => {
  });
  let removing = options.removing || (() => {
  });
  let context = createMorphContext({
    ...options,
    planning: true,
    adding(node, skip) {
      let source = toSources.get(node);
      if (source) return adding(source, skip);
    },
    added: () => {
    },
    removing(node, skip) {
      let source = fromSources.get(node);
      if (source) return removing(source, skip);
    },
    removed: () => {
    },
    updated: () => {
    },
    updating(fromNode, toNode, childrenOnly, skip, skipChildren, skipUntil) {
      let sourceFrom = fromSources.get(fromNode);
      let sourceTo = toSources.get(toNode);
      if (!sourceFrom || !sourceTo) return;
      return updating(sourceFrom, sourceTo, childrenOnly, skip, skipChildren, skipUntil);
    }
  });
  context.patchChildren(fromClone, toClone);
}`;

const MORPH_CONTEXT_OPTIONS = `  let context = {
    key: options.key || defaultGetKey,`;

const PLANNING_CONTEXT_OPTIONS = `  let context = {
    planning: options.planning || false,
    key: options.key || defaultGetKey,
    keyMapFilter: options.keyMapFilter || (() => true),`;

const MORPH_KEY_MAP_LOOP = `    for (let el of els) {
      let theKey = context.getKey(el);`;

const FILTERED_KEY_MAP_LOOP = `    for (let el of els) {
      if (!context.keyMapFilter(el)) continue;
      let theKey = context.getKey(el);`;

const MORPH_PATCH_BODY = `    if (from.nodeType === 1 && window.Alpine) {
      window.Alpine.cloneNode(from, to);
      if (from._x_teleport && to._x_teleport) {
        context.patch(from._x_teleport, to._x_teleport);
      }
    }
    if (textOrComment(to)) {
      context.patchNodeValue(from, to);
      context.updated(from, to);
      return;
    }
    if (!updateChildrenOnly) {
      context.patchAttributes(from, to);
    }
    context.updated(from, to);`;

const PLANNING_PATCH_BODY = `    if (!context.planning && from.nodeType === 1 && window.Alpine) {
      window.Alpine.cloneNode(from, to);
      if (from._x_teleport && to._x_teleport) {
        context.patch(from._x_teleport, to._x_teleport);
      }
    }
    if (textOrComment(to)) {
      if (!context.planning) {
        context.patchNodeValue(from, to);
        context.updated(from, to);
      }
      return;
    }
    if (!context.planning) {
      if (!updateChildrenOnly) {
        context.patchAttributes(from, to);
      }
      context.updated(from, to);
    }`;

const MORPH_SWAP_ADD = `    if (shouldSkip(context.adding, toCloned))
      return;`;

const PLANNING_SWAP_ADD = `    if (shouldSkip(context.adding, context.planning ? to : toCloned))
      return;`;

const MORPH_ALPINE_BRIDGE = `function src_default(Alpine) {
  Alpine.morph = morph;
  Alpine.morphBetween = morphBetween;
}`;

const PLANNING_ALPINE_BRIDGE = `function src_default(Alpine) {
  Alpine.morph = morph;
  Alpine.morphBetween = morphBetween;
  Alpine._citryPlanBetween = planBetween;
}`;

const replaceExactlyOnce = function (source, before, after, label) {
  const first = source.indexOf(before);
  if (first === -1 || source.indexOf(before, first + before.length) !== -1) {
    throw new Error(`Pinned Alpine ${ALPINE_VERSION} ${label} changed; review Citry's directive instrumentation.`);
  }
  return source.slice(0, first) + after + source.slice(first + before.length);
};

export const instrumentAlpineDirectives = function (source) {
  let instrumented = replaceExactlyOnce(
    source,
    DIRECTIVES_IMPORTS,
    INSTRUMENTED_DIRECTIVES_IMPORTS,
    "directives imports",
  );
  instrumented = replaceExactlyOnce(
    instrumented,
    DIRECTIVE_HANDLER,
    INSTRUMENTED_DIRECTIVE_HANDLER,
    "directive handler",
  );
  return instrumented;
};

export const instrumentAlpineMorphPlanner = function (source) {
  let instrumented = replaceExactlyOnce(
    source,
    MORPH_CONTEXT_ENTRY,
    `${PLANNING_ENTRY}\n${MORPH_CONTEXT_ENTRY}`,
    "morph planner entry",
  );
  instrumented = replaceExactlyOnce(
    instrumented,
    MORPH_CONTEXT_OPTIONS,
    PLANNING_CONTEXT_OPTIONS,
    "morph context options",
  );
  instrumented = replaceExactlyOnce(instrumented, MORPH_KEY_MAP_LOOP, FILTERED_KEY_MAP_LOOP, "morph keyed-map filter");
  instrumented = replaceExactlyOnce(instrumented, MORPH_PATCH_BODY, PLANNING_PATCH_BODY, "morph planning patch body");
  instrumented = replaceExactlyOnce(instrumented, MORPH_ALPINE_BRIDGE, PLANNING_ALPINE_BRIDGE, "morph Alpine bridge");
  instrumented = replaceExactlyOnce(
    instrumented,
    MORPH_SWAP_ADD,
    PLANNING_SWAP_ADD,
    "morph planning swap classification",
  );
  return instrumented;
};

export const alpineDirectiveInstrumentation = {
  name: "citry-alpine-directive-instrumentation",
  setup(build) {
    build.onLoad({ filter: /[\\/]alpinejs[\\/]src[\\/]directives\.js$/ }, async function (args) {
      const source = await readFile(args.path, "utf8");
      return {
        contents: instrumentAlpineDirectives(source),
        loader: "js",
      };
    });
  },
};

export const alpineMorphPlannerInstrumentation = {
  name: "citry-alpine-morph-planner-instrumentation",
  setup(build) {
    build.onLoad({ filter: /[\\/]@alpinejs[\\/]morph[\\/]dist[\\/]module\.esm\.js$/ }, async function (args) {
      const source = await readFile(args.path, "utf8");
      return {
        contents: instrumentAlpineMorphPlanner(source),
        loader: "js",
      };
    });
  },
};

const clientBuildOptions = function (variant, overrides = {}) {
  if (Object.hasOwn(overrides, "define")) {
    throw new Error("The Citry client build owns its fixed Alpine runtime identity.");
  }
  return {
    entryPoints: [fileURLToPath(new URL("src/citry-events.ts", import.meta.url))],
    bundle: true,
    format: "iife",
    platform: "browser",
    target: "es2020",
    tsconfigRaw: {},
    define: {
      ALPINE_VERSION: JSON.stringify(ALPINE_VERSION),
      CITRY_ALPINE_RUNTIME_VARIANT: JSON.stringify(variant),
    },
    banner: { js: GENERATED_BANNER },
    outfile: fileURLToPath(new URL("../../py/citry/citry/ext/events/client/citry-events.js", import.meta.url)),
    plugins: [alpineDirectiveInstrumentation, alpineMorphPlannerInstrumentation],
    ...overrides,
  };
};

export const citryClientBuildOptions = function (overrides = {}) {
  return clientBuildOptions("standard", overrides);
};

export const citryCspClientBuildOptions = function (overrides = {}) {
  if (Object.hasOwn(overrides, "alias")) {
    throw new Error("The Citry CSP client build owns its fixed Alpine entry alias.");
  }
  return clientBuildOptions("csp", {
    alias: { "alpinejs/src/index": "@alpinejs/csp/src/index" },
    banner: { js: CSP_GENERATED_BANNER },
    outfile: fileURLToPath(new URL("../../py/citry/citry/ext/events/client/citry-events-csp.js", import.meta.url)),
    ...overrides,
  });
};

export const citryI18nBuildOptions = function (overrides = {}) {
  return {
    entryPoints: [fileURLToPath(new URL("src/citry-i18n.ts", import.meta.url))],
    bundle: true,
    format: "iife",
    platform: "browser",
    target: "es2020",
    tsconfigRaw: {},
    banner: { js: I18N_GENERATED_BANNER },
    outfile: fileURLToPath(new URL("../../py/citry/citry/ext/i18n/client/citry-i18n.js", import.meta.url)),
    ...overrides,
  };
};
