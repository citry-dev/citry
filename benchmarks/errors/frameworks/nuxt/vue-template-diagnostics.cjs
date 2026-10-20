// Print the Vue compiler errors that the Vue - Official extension shows on top
// of TypeScript's, for every .vue file under app/, as `eslint -f json` output
// so the runner's eslint-json parser reads it.
//
// `vue-tsc` reports only TypeScript's diagnostics. The editor extension also
// runs two Vue language service plugins that report the Vue compiler's own
// errors: `vue-sfc` (a broken single-file component block outside the
// template) and `vue-compiler-dom-errors` (a template that does not parse or
// compile, such as an unclosed element). See @vue/language-service 3.3.13,
// lib/plugins/vue-sfc.js and lib/plugins/vue-compiler-dom-errors.js. This
// script calls the @vue/language-core parse and compile functions those
// plugins rely on, with the default options, so that together with vue-tsc
// the editor stage covers what these two plugins show. It was not compared
// against a running editor.
//
// Run it from the app's folder: `node vue-template-diagnostics.cjs`.

const fs = require("node:fs");
const path = require("node:path");
const { createRequire } = require("node:module");

// Resolve the app's own installed packages, not ones next to this script, so
// the pinned @vue/language-core that vue-tsc uses is the one that runs.
const appRequire = createRequire(path.join(process.cwd(), "package.json"));
const { parse: parseSfc } = appRequire("@vue/language-core/lib/utils/parseSfc");
const { compileTemplate } = appRequire("@vue/language-core/lib/template/compile");

function vueFiles(dir) {
  const found = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) found.push(...vueFiles(full));
    else if (entry.name.endsWith(".vue")) found.push(full);
  }
  return found.sort();
}

function lineAt(text, offset) {
  return text.slice(0, offset).split("\n").length;
}

const results = [];
for (const file of vueFiles(path.join(process.cwd(), "app"))) {
  const source = fs.readFileSync(file, "utf8");
  const messages = [];
  const sfc = parseSfc(source);
  const template = sfc.descriptor.template;
  const templateStart = template ? template.loc.start.offset : Infinity;
  const templateEnd = template ? template.loc.end.offset : -Infinity;

  // SFC-level errors outside the template block, reported as errors, as the
  // `vue-sfc` plugin does. Errors inside the template come from the compile
  // step below instead.
  for (const error of sfc.errors) {
    if (!("code" in error)) continue;
    const start = error.loc ? error.loc.start.offset : 0;
    const end = error.loc ? error.loc.end.offset : 0;
    if (end < templateStart || start >= templateEnd) {
      messages.push({ line: lineAt(source, start), severity: 2, ruleId: `vue-sfc/${error.code}`, message: error.message });
    }
  }

  if (template) {
    // language-core passes these options when no plugin listed in
    // `vueCompilerOptions.plugins` changes them, and Nuxt's tsconfigs list none.
    const errors = [];
    const warnings = [];
    try {
      compileTemplate(template.content, {
        onError: (error) => errors.push(error),
        onWarn: (warning) => warnings.push(warning),
        expressionPlugins: ["typescript"],
      });
    } catch (error) {
      errors.push(error);
    }
    for (const [list, severity] of [
      [errors, 2],
      [warnings, 1],
    ]) {
      for (const error of list) {
        const offset = templateStart + (error.loc ? error.loc.start.offset : 0);
        messages.push({
          line: lineAt(source, offset),
          severity,
          ruleId: `vue-compiler-dom-errors/${error.code ?? "exception"}`,
          message: String(error.message),
        });
      }
    }
  }
  results.push({ filePath: file, messages });
}
process.stdout.write(JSON.stringify(results, null, 2));
