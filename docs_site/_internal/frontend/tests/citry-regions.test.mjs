import assert from "node:assert/strict";
import test from "node:test";

import { syntaxTree } from "@codemirror/language";
import { EditorState } from "@codemirror/state";
import { classHighlighter, highlightTree } from "@lezer/highlight";
import { BrowserIdeSession, templateRegions } from "../src/browser_ide.js";
import { citryPython } from "../src/citry_editor.js";
import { citryAssetAt } from "../src/citry_regions.js";

function asset(source, start = source.indexOf('"""'), end = source.lastIndexOf('"""') + 3) {
  return citryAssetAt(
    { name: "String", from: start, to: end },
    (from, to) => source.slice(from, to),
  );
}

test("direct triple-quoted Citry assets expose their exact body", () => {
  const source = 'class Card:\n  template = """<c-if cond="ready"></c-if>"""';
  const result = asset(source);

  assert.deepEqual(result, {
    kind: "template",
    from: source.indexOf('"""') + 3,
    to: source.lastIndexOf('"""'),
    sourceExact: true,
  });
  assert.equal(source.slice(result.from, result.to), '<c-if cond="ready"></c-if>');
});

test("asset discovery distinguishes all Citry assets and ordinary strings", () => {
  const javascript = '  js = """$component(() => ({}))"""';
  const messages = '  messages = """card-title = Card"""';
  const ordinary = '  example = """<c-if></c-if>"""';

  assert.equal(asset(javascript).kind, "js");
  assert.equal(asset(messages).kind, "messages");
  assert.equal(asset(ordinary), null);
});

test("analysis withholds Python literals whose decoded body needs a source map", () => {
  const escaped = '  template = """<p>\\N{SNOWMAN}</p>"""';
  const raw = '  template = r"""<p>\\N{SNOWMAN}</p>"""';

  assert.equal(asset(escaped).sourceExact, false);
  assert.equal(asset(raw, raw.indexOf('r"""')).sourceExact, true);
});

test("the mixed Python tree publishes only authored template bodies", () => {
  const source = `class Card:
  template = """
    <c-if cond="ready"></c-if>
  """
  js = """<c-for></c-for>"""
`;
  const state = EditorState.create({ doc: source, extensions: [citryPython] });

  const regions = templateRegions(state);

  assert.equal(regions.length, 1);
  assert.equal(regions[0].source, '\n    <c-if cond="ready"></c-if>\n  ');
});

test("the mixed Python tree colors component messages as Fluent", () => {
  const source = `class Card:
  messages = """
    # @param {str} $name - Account name.
    account-title = Welcome, { $name }.
  """
`;
  const state = EditorState.create({ doc: source, extensions: [citryPython] });
  const highlighted = [];

  highlightTree(syntaxTree(state), classHighlighter, (from, to, classes) => {
    highlighted.push({ classes, text: source.slice(from, to) });
  });

  assert.ok(highlighted.some(({ classes, text }) => classes === "tok-comment" && text.startsWith("# @param")));
  assert.ok(highlighted.some(({ classes, text }) => classes === "tok-labelName" && text === "account-title"));
  assert.ok(highlighted.some(({ classes, text }) => classes === "tok-variableName" && text === "$name"));
});

test("stale Worker responses resolve to no editor result", async () => {
  const messages = [];
  const worker = {
    onerror: null,
    onmessage: null,
    postMessage(message) { messages.push(message); },
    terminate() {},
  };
  const session = new BrowserIdeSession({ workerFactory: () => worker });
  session.version = 2;
  const pending = session.request(
    "hover",
    { id: "template", source: "<c-if></c-if>" },
    { line: 0, character: 2 },
  );
  const request = messages.at(-1);

  worker.onmessage({
    data: {
      schemaVersion: 1,
      type: "response",
      kind: "hover",
      requestId: request.requestId,
      version: 1,
      value: { stale: true },
    },
  });

  assert.equal(await pending, null);
});

test("Citry completion composes with the nested HTML completion source", () => {
  const worker = {
    onerror: null,
    onmessage: null,
    postMessage() {},
    terminate() {},
  };
  const session = new BrowserIdeSession({ workerFactory: () => worker });
  const source = 'class Card:\n  template = """<di"""';
  const position = source.indexOf("<di") + 3;
  const state = EditorState.create({
    doc: source,
    extensions: [citryPython, ...session.extensions()],
  });

  const sources = state.languageDataAt("autocomplete", position);

  assert.ok(sources.includes(session.completionSource));
  assert.ok(sources.some((sourceProvider) => sourceProvider !== session.completionSource));
  session.destroy();
});

test("runtime catalogs are forwarded only for the exact source generation", () => {
  const messages = [];
  const worker = {
    onerror: null,
    onmessage: null,
    postMessage(message) { messages.push(message); },
    terminate() {},
  };
  const session = new BrowserIdeSession({ workerFactory: () => worker });
  session.version = 4;
  session.source = "current";

  assert.equal(session.versionForSource("stale"), null);
  assert.equal(session.versionForSource("current"), 4);
  assert.equal(session.publishCatalog(3, { schemaVersion: 1, registries: [] }), false);
  assert.equal(session.publishCatalog(4, { schemaVersion: 1, registries: [] }), true);
  assert.deepEqual(messages.at(-1), {
    schemaVersion: 1,
    type: "catalog",
    version: 4,
    snapshot: { schemaVersion: 1, registries: [] },
  });
  session.destroy();
});
