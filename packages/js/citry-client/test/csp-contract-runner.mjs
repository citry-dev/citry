import { readFile } from "node:fs/promises";

const ALPINE_VERSION = "3.16.2";
const FOR_EXPRESSION = /([\s\S]*?)\s+(?:in|of)\s+([\s\S]*)/;

function installDomStubs() {
  // The pinned evaluator snapshots browser globals at module initialization,
  // so the runner installs stable identities before importing its source.
  globalThis.Node ??= class Node {};
  globalThis.CSSStyleDeclaration ??= class CSSStyleDeclaration {};
  globalThis.DOMStringMap ??= class DOMStringMap {};
  globalThis.DOMTokenList ??= class DOMTokenList {};
  globalThis.NamedNodeMap ??= class NamedNodeMap {};
  globalThis.HTMLIFrameElement ??= class HTMLIFrameElement extends globalThis.Node {};
  globalThis.HTMLScriptElement ??= class HTMLScriptElement extends globalThis.Node {};
}

async function pinnedRuntimeFactory() {
  installDomStubs();
  const parserUrl = new URL("../node_modules/@alpinejs/csp/src/parser.js", import.meta.url);
  const source = await readFile(parserUrl, "utf8");
  const moduleUrl = `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
  return (await import(moduleUrl)).generateRuntimeFunction;
}

function scopeFor(testCase) {
  if (testCase.scopeFixture === "computed-call") {
    return { items: [{ id: 7 }], index: 0, save: ({ id }) => id };
  }
  if (testCase.scopeFixture === "save") return { save: () => 1 };
  if (testCase.scopeFixture === "browser-global") return { Math };
  if (testCase.scopeFixture === "dom-assignment") {
    return { $el: new globalThis.Node(), next: "after" };
  }
  return structuredClone(testCase.scope ?? {});
}

function expressionsFor(testCase) {
  if (testCase.transform === "citry-args") return [`(${testCase.source})`];
  if (testCase.transform === "x-model") {
    return [testCase.source, `${testCase.source} = __placeholder`];
  }
  if (testCase.transform === "x-for") {
    const match = testCase.source.match(FOR_EXPRESSION);
    return match === null ? [""] : [match[2].trim()];
  }
  return [testCase.source];
}

function classifyFailure(error, expressionIndex, testCase) {
  if (testCase.transform === "x-model" && expressionIndex === 1) return "derived-expression";
  return String(error?.message).startsWith("CSP Parser Error:") ? "parser" : "evaluator";
}

function runCase(generateRuntimeFunction, testCase) {
  const scope = scopeFor(testCase);
  const expressions = expressionsFor(testCase);
  let value;
  let expressionIndex = 0;
  try {
    for (const [index, expression] of expressions.entries()) {
      expressionIndex = index;
      const expressionScope =
        testCase.transform === "x-model" && index === 1
          ? Object.assign(scope, { __placeholder: testCase.placeholder })
          : scope;
      value = generateRuntimeFunction(expression)({ scope: expressionScope });
    }
    if (testCase.transform === "x-model") value = scope.user?.name ?? scope.count;
    return { id: testCase.id, outcome: "accepted", value };
  } catch (error) {
    return {
      id: testCase.id,
      outcome: "rejected",
      failure: classifyFailure(error, expressionIndex, testCase),
      message: String(error?.message ?? error),
    };
  }
}

export async function runCspContract({ caseIds = null } = {}) {
  const fixtureUrl = new URL("./fixtures/alpine-csp-3.16.2.json", import.meta.url);
  const fixture = JSON.parse(await readFile(fixtureUrl, "utf8"));
  if (fixture.alpineVersion !== ALPINE_VERSION) {
    throw new Error(`CSP corpus ${fixture.alpineVersion} does not match ${ALPINE_VERSION}.`);
  }
  const selected = caseIds === null ? fixture.cases : fixture.cases.filter(({ id }) => caseIds.includes(id));
  const generateRuntimeFunction = await pinnedRuntimeFactory();
  return {
    alpineVersion: ALPINE_VERSION,
    expected: selected.map(({ id, outcome, failure, value }) => ({ id, outcome, failure, value })),
    actual: selected.map((testCase) => runCase(generateRuntimeFunction, testCase)),
  };
}

if (process.env.NODE_TEST_CONTEXT === undefined && process.argv[1] === new URL(import.meta.url).pathname) {
  const caseIndex = process.argv.indexOf("--case");
  const caseIds = caseIndex >= 0 ? [process.argv[caseIndex + 1]] : null;
  const result = await runCspContract({ caseIds });
  process.stdout.write(`${JSON.stringify(result, null, process.argv.includes("--json") ? 0 : 2)}\n`);
}
