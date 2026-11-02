// Generates crates/citry_vue_compiler/src/dom_members.rs.
//
// Citry's Vue server renderer has to predict the attribute text Vue's first
// client render leaves on an element. Vue sets `el[key] = value` when
// `key in el` is true and calls `setAttribute` otherwise. For most names both
// paths leave the same text, so the server can write it. This script works out,
// for every HTML element and every lowercase name, whether that holds in every
// supported browser, from the web platform IDL (@webref/idl) and MDN's browser
// compatibility data (BCD). The design is in issue #346.
//
// Usage:
//   node generate.mjs           write the Rust table
//   node generate.mjs --check   fail if the committed table differs
//   node generate.mjs --json    print the table as JSON (for the browser test)
//   node generate.mjs --unclassified
//                               list unmarked string members that neither
//                               reviewed list classifies

import { readFile, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { classify, collectUnclassified } from "./lib/classify.mjs";
import { loadData } from "./lib/data.mjs";
import { renderRust } from "./lib/render.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const OUTPUT = path.join(here, "../../crates/citry_vue_compiler/src/dom_members.rs");

async function main() {
  const mode = process.argv[2] ?? "--write";
  if (!["--write", "--check", "--json", "--unclassified"].includes(mode)) {
    throw new Error(`unknown option ${mode}`);
  }
  const data = await loadData(require);
  if (mode === "--unclassified") {
    const names = collectUnclassified(data);
    process.stdout.write(names.map((item) => `${item}\n`).join(""));
    // A non-empty list fails, so the refresh stops until someone looks at it.
    process.exitCode = names.length === 0 ? 0 : 1;
    return;
  }
  const table = classify(data);
  if (mode === "--json") {
    process.stdout.write(`${JSON.stringify(table, null, 2)}\n`);
    return;
  }
  const rust = renderRust(table, data.versions);
  if (mode === "--check") {
    const committed = await readFile(OUTPUT, "utf8").catch(() => "");
    if (committed !== rust) {
      process.stderr.write(
        `${path.relative(process.cwd(), OUTPUT)} is out of date. ` +
          "Run `pnpm --dir tools/dom-members run generate` and commit the result.\n",
      );
      process.exitCode = 1;
    }
    return;
  }
  await writeFile(OUTPUT, rust);
}

main().catch((error) => {
  process.stderr.write(`${error.stack ?? error}\n`);
  process.exitCode = 1;
});
