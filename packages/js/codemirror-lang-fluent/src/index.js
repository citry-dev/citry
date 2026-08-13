import { LanguageSupport, StreamLanguage } from "@codemirror/language";
import { tags } from "@lezer/highlight";

const identifier = "[A-Za-z][A-Za-z0-9_-]*";

function startState() {
  return { atLineStart: true, placeableDepth: 0 };
}

function token(stream, state) {
  if (stream.sol()) state.atLineStart = true;
  if (stream.eatSpace()) return null;

  if (state.atLineStart && stream.match(/^#{1,3}.*$/)) {
    state.atLineStart = false;
    return "comment";
  }
  if (state.atLineStart && stream.match(new RegExp(`^\\.${identifier}(?=\\s*=)`))) {
    state.atLineStart = false;
    return "fluentAttribute";
  }
  if (state.atLineStart && stream.match(new RegExp(`^-?${identifier}(?=\\s*=)`))) {
    state.atLineStart = false;
    return stream.current().startsWith("-") ? "fluentTerm" : "fluentMessage";
  }
  state.atLineStart = false;

  if (stream.match(/^->/)) return "operator";
  if (stream.match(/^(?:\*)?\[[^\]\r\n]+\]/)) return "labelName";
  if (stream.match(/^"(?:\\(?:\\|"|u[0-9A-Fa-f]{4}|U[0-9A-Fa-f]{6})|[^"\\])*"?/)) {
    return "string";
  }
  if (stream.match(new RegExp(`^\\$${identifier}`))) return "variableName";
  if (stream.match(new RegExp(`^-?${identifier}(?=\\s*\\()`))) return "variableName.function";
  if (stream.match(new RegExp(`^-?${identifier}(?=\\.${identifier})`))) return "variableName";
  if (stream.match(new RegExp(`^\\.${identifier}`))) return "propertyName";
  if (stream.match(/^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?/)) return "number";
  if (stream.match(/^[{}(),:=]/)) {
    const punctuation = stream.current();
    if (punctuation === "{") state.placeableDepth += 1;
    if (punctuation === "}" && state.placeableDepth > 0) state.placeableDepth -= 1;
    return punctuation === "=" ? "operator" : null;
  }
  if (state.placeableDepth > 0 && stream.match(new RegExp(`^-?${identifier}`))) return "variableName";

  stream.next();
  return null;
}

/**
 * A small, syntax-coloring-only Fluent language for CodeMirror 6.
 *
 * Citry uses this while the Fluent and CodeMirror projects decide whether to
 * maintain a complete Lezer grammar. It deliberately provides no syntax tree
 * API, validation, completion, or formatting contract.
 */
export const fluentLanguage = StreamLanguage.define({
  name: "fluent",
  startState,
  token,
  blankLine(state) {
    state.atLineStart = true;
  },
  tokenTable: {
    fluentMessage: tags.definition(tags.labelName),
    fluentTerm: tags.definition(tags.function(tags.variableName)),
    fluentAttribute: tags.definition(tags.propertyName),
  },
  languageData: {
    commentTokens: { line: "#" },
  },
});

/** Return CodeMirror support for a standalone or embedded Fluent source. */
export function fluent() {
  return new LanguageSupport(fluentLanguage);
}
