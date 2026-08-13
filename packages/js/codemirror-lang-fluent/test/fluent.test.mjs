import assert from "node:assert/strict";
import test from "node:test";
import { fluentLanguage } from "../src/index.js";

function tokenNames(source) {
  const cursor = fluentLanguage.parser.parse(source).cursor();
  const result = [];
  do {
    if (cursor.name !== "Document") {
      result.push({ name: cursor.name, text: source.slice(cursor.from, cursor.to) });
    }
  } while (cursor.next());
  return result;
}

test("colors the Fluent constructs used by component messages", () => {
  const source = `### Account copy
# @param {str} $name - User name.
account-title = Welcome, { $name }.
    .aria-label = Account actions for { $name }
-brand = Citry
choice = { $count ->
   [one] One item
  *[other] { NUMBER($count, profile: "compact") } items from { -brand }
}
`;
  const tokens = tokenNames(source);

  assert.ok(tokens.some(({ name, text }) => name === "comment" && text === "### Account copy"));
  assert.ok(tokens.some(({ name, text }) => name === "fluentMessage" && text === "account-title"));
  assert.ok(tokens.some(({ name, text }) => name === "fluentAttribute" && text === ".aria-label"));
  assert.ok(tokens.some(({ name, text }) => name.includes("variableName") && text === "$name"));
  assert.ok(tokens.some(({ name, text }) => name.includes("variableName") && text === "-brand"));
  assert.ok(tokens.some(({ name, text }) => name.includes("variableName") && text === "NUMBER"));
  assert.ok(tokens.some(({ name, text }) => name === "labelName" && text === "*[other]"));
  assert.ok(tokens.some(({ name, text }) => name === "string" && text === '"compact"'));
});

test("keeps prose with an equals sign out of the definition style", () => {
  const source = "notice = Two plus two = four\n    continued prose = still prose";
  const tokens = tokenNames(source);
  const definitions = tokens.filter(({ name }) => name === "fluentMessage");

  assert.deepEqual(
    definitions.map(({ text }) => text),
    ["notice"],
  );
});

test("accepts incomplete source without throwing", () => {
  assert.doesNotThrow(() => fluentLanguage.parser.parse('message = { $count ->\n  [one] "unfinished'));
});
