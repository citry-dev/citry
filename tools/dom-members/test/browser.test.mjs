// Checks the generated table against real browsers.
//
// The table says, for each HTML element and lowercase name, what Vue's first
// client render leaves in the attribute. This test creates every element in
// each browser Playwright installs and runs Vue's own `patchProp` on it, so a
// name the table calls `WritesText` that a browser treats differently fails
// here. Run it with `pnpm --dir tools/dom-members run test:browser`; set
// BROWSERS to a comma-separated list (default: chromium) to pick browsers.

import assert from "node:assert/strict";
import { createRequire } from "node:module";
import path from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

import { chromium, firefox, webkit } from "playwright";

import { classify } from "../lib/classify.mjs";
import { loadData } from "../lib/data.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.join(here, "../generate.mjs"));
const VUE_BUNDLE = path.join(here, "../node_modules/@vue/runtime-dom/dist/runtime-dom.global.js");
const ENGINES = { chromium, firefox, webkit };

const table = classify(await loadData(require));
const browsers = (process.env.BROWSERS ?? "chromium").split(",").map((name) => name.trim());

for (const name of browsers) {
  // A hanging browser launch or page should fail within two minutes.
  test(`the table matches ${name}`, { timeout: 120_000 }, async () => {
    const engine = ENGINES[name];
    assert.ok(engine, `unknown browser ${name}`);
    const browser = await engine.launch();
    try {
      const page = await browser.newPage();
      await page.goto("about:blank");
      await page.addScriptTag({ path: VUE_BUNDLE });
      // An unknown tag uses the answers every element starts from.
      const tags = [...Object.keys(table.elements), "citrynotatag"];
      const problems = await page.evaluate(checkInPage, { table, tags });
      if (process.env.PROBLEMS_FILE) {
        const { writeFile } = await import("node:fs/promises");
        await writeFile(process.env.PROBLEMS_FILE, problems.join("\n"));
      }
      assert.deepEqual(summarize(name, problems), []);
    } finally {
      await browser.close();
    }
  });
}

/**
 * One line per name, value and result, saying which browser reported it and
 * on which elements, so a name a browser adds to every element reads as one
 * finding rather than one line per tag. Every element is listed, because CI
 * keeps no other record of which ones drifted.
 */
function summarize(browser, problems) {
  const groups = new Map();
  const other = [];
  for (const problem of problems) {
    const match = /^([a-z0-9-]+)\.([a-z0-9]+=[^:]*): (.*)$/.exec(problem);
    if (!match) {
      other.push(`${browser}: ${problem}`);
      continue;
    }
    const [, tag, nameAndValue, result] = match;
    const key = `${nameAndValue}: ${result}`;
    groups.set(key, [...(groups.get(key) ?? []), tag]);
  }
  const lines = [...groups].map(([key, tags]) => `${browser}: ${key} (on ${tags.join(", ")})`);
  return [...lines, ...other];
}

/**
 * Runs in the page. Returns one line per name whose behavior differs from
 * the table.
 */
function checkInPage({ table, tags }) {
  const { patchProp, render, h } = window.VueRuntimeDOM;
  const values = ["text", "", 7, true, false, null, undefined];
  const problems = [];
  // The server treats every name starting with `on` as Unknown itself
  // (`dom_answer` in server_render.rs), whatever the table says.
  const answerFor = (tag, name) =>
    name.startsWith("on")
      ? "Unknown"
      : (table.elements[tag]?.[name] ?? table.base[name] ?? "WritesText");
  // What the attribute holds after one call, as a comparable string.
  const attributeAfter = (tag, key, value) => {
    const element = document.createElement(tag);
    try {
      patchProp(element, key, null, value);
    } catch (error) {
      return `threw ${error.name}`;
    }
    const name = key.replace(/^\^/, "");
    return element.hasAttribute(name) ? `=${JSON.stringify(element.getAttribute(name))}` : "absent";
  };
  for (const tag of tags) {
    if (table.allUnknownTags.includes(tag)) {
      continue;
    }
    // Every lowercase name `key in el` can see on this element.
    const names = new Set();
    for (let object = document.createElement(tag); object; object = Object.getPrototypeOf(object)) {
      for (const name of Object.getOwnPropertyNames(object)) {
        if (/^[a-z][a-z0-9]*$/.test(name)) {
          names.add(name);
        }
      }
    }
    for (const name of names) {
      const answer = answerFor(tag, name);
      for (const value of values) {
        // Vue's `^` prefix forces its setAttribute path, which is what
        // `WritesText` promises the property path matches.
        const viaVue = attributeAfter(tag, name, value);
        if (answer === "WritesText") {
          const viaAttribute = attributeAfter(tag, `^${name}`, value);
          if (viaVue !== viaAttribute) {
            problems.push(`${tag}.${name}=${String(value)}: property ${viaVue}, attribute ${viaAttribute}`);
          }
        } else if (answer === "ReflectBoolean") {
          const expected = value === "" || Boolean(value) ? '=""' : "absent";
          if (viaVue !== expected) {
            problems.push(`${tag}.${name}=${String(value)}: ${viaVue}, expected ${expected}`);
          }
        }
      }
    }
  }
  // A form's controls become properties of the form, which the server's
  // form check relies on: a key with no prototype member then misses the
  // attribute, while an unrelated control name leaves it alone.
  const container = document.createElement("div");
  const formAttribute = (key, controlName) => {
    render(h("form", { [key]: "v" }, [h("input", { name: controlName })]), container);
    const form = container.firstElementChild;
    const result = form.hasAttribute(key) ? form.getAttribute(key) : null;
    render(null, container);
    return result;
  };
  if (formAttribute("action", "q") !== "v") {
    problems.push("form action with an unrelated control did not keep its attribute");
  }
  for (const key of ["foo", "data-x"]) {
    if (formAttribute(key, key) === "v") {
      problems.push(`form ${key} with a control of that name kept its attribute; the form check may be unnecessary`);
    }
  }
  // A null `action` beside a control named `action`: the control makes
  // `typeof form.action` an object, so Vue takes the property path and
  // writes "null". This is the case the server's form check declines.
  render(h("form", { action: null }, [h("input", { name: "action" })]), container);
  const nullAction = container.firstElementChild.getAttribute("action");
  render(null, container);
  if (nullAction !== "null") {
    problems.push(`form action=null with a control named action left ${JSON.stringify(nullAction)}, expected "null"`);
  }
  return problems;
}
