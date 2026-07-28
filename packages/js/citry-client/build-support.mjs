import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

export const ALPINE_VERSION = "3.15.12";
export const GENERATED_BANNER =
  "/* Citry events client runtime. GENERATED FILE, do not edit: built from packages/js/citry-client/src/citry-events.ts (pnpm run build there). Bundles AlpineJS 3.15.12 + @alpinejs/morph 3.15.12 (MIT). */";

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

export const citryClientBuildOptions = function (overrides = {}) {
  return {
    entryPoints: [fileURLToPath(new URL("src/citry-events.ts", import.meta.url))],
    bundle: true,
    format: "iife",
    platform: "browser",
    target: "es2020",
    tsconfigRaw: {},
    define: { ALPINE_VERSION: JSON.stringify(ALPINE_VERSION) },
    banner: { js: GENERATED_BANNER },
    outfile: fileURLToPath(new URL("../../py/citry/citry/ext/events/client/citry-events.js", import.meta.url)),
    plugins: [alpineDirectiveInstrumentation],
    ...overrides,
  };
};
