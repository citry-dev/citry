import sample from "../samples/citry_component.py";
import { autocompletion, closeBrackets, closeBracketsKeymap } from "@codemirror/autocomplete";
import {
  defaultKeymap,
  history,
  historyKeymap,
  indentWithTab,
  undo as undoCommand,
} from "@codemirror/commands";
import { css, cssLanguage } from "@codemirror/lang-css";
import { html, htmlLanguage } from "@codemirror/lang-html";
import { javascript, javascriptLanguage } from "@codemirror/lang-javascript";
import { python, pythonLanguage } from "@codemirror/lang-python";
import {
  HighlightStyle,
  LanguageSupport,
  bracketMatching,
  defaultHighlightStyle,
  foldGutter,
  indentOnInput,
  syntaxHighlighting,
  syntaxTree,
} from "@codemirror/language";
import { lintGutter, linter } from "@codemirror/lint";
import {
  highlightSelectionMatches,
  openSearchPanel,
  searchKeymap,
} from "@codemirror/search";
import { EditorState } from "@codemirror/state";
import {
  Decoration,
  EditorView,
  ViewPlugin,
  drawSelection,
  dropCursor,
  highlightActiveLine,
  highlightActiveLineGutter,
  highlightSpecialChars,
  keymap,
  lineNumbers,
  rectangularSelection,
} from "@codemirror/view";
import { tags } from "@lezer/highlight";
import { parseMixed } from "@lezer/common";
import { wireProofShell } from "./editor-shell.js";

const embeddedParsers = {
  template: htmlLanguage.parser,
  js: javascriptLanguage.parser,
  css: cssLanguage.parser,
};

function mixedCitryRegion(node, input) {
  if (node.name !== "String") return null;

  const prefix = input.read(Math.max(0, node.from - 180), node.from);
  const currentLine = prefix.slice(prefix.lastIndexOf("\n") + 1);
  const assignment = currentLine.match(
    /\b(template|js|css)(?:\s*:\s*[^=\n]+)?\s*=\s*$/,
  );
  if (!assignment) return null;

  const quoted = input.read(node.from, node.to);
  const opener = quoted.startsWith('"""') ? '"""' : quoted.startsWith("'''") ? "'''" : null;
  if (!opener || !quoted.endsWith(opener) || node.to - node.from < 6) return null;

  return {
    parser: embeddedParsers[assignment[1]],
    overlay: [{ from: node.from + 3, to: node.to - 3 }],
  };
}

const citryPythonLanguage = pythonLanguage.configure(
  { wrap: parseMixed(mixedCitryRegion) },
  "Citry Python",
);
const pythonSupport = python();
const citryPython = new LanguageSupport(citryPythonLanguage, [
  pythonSupport.support,
  html().support,
  javascript().support,
  css().support,
]);

function citryDecorations(view) {
  const decorations = [];
  const patterns = [
    {
      regexp: /(?:<\/?)(c-[\w-]+)/g,
      range(match, base) {
        const nameOffset = match[0].lastIndexOf(match[1]);
        return [base + match.index + nameOffset, base + match.index + nameOffset + match[1].length];
      },
      className: "cm-citry-name",
    },
    {
      regexp: /\b(c-[\w$:@.-]+)(?=\s*=)/g,
      range(match, base) {
        return [base + match.index, base + match.index + match[1].length];
      },
      className: "cm-citry-name",
    },
    {
      regexp: /\{\{|\}\}/g,
      range(match, base) {
        return [base + match.index, base + match.index + match[0].length];
      },
      className: "cm-citry-punctuation cm-citry-interpolation",
    },
  ];

  for (const { from, to } of view.visibleRanges) {
    const text = view.state.sliceDoc(from, to);
    for (const pattern of patterns) {
      pattern.regexp.lastIndex = 0;
      for (let match; (match = pattern.regexp.exec(text)); ) {
        const [start, end] = pattern.range(match, from);
        decorations.push(Decoration.mark({ class: pattern.className }).range(start, end));
      }
    }
  }

  return Decoration.set(decorations, true);
}

const citryDecorationPlugin = ViewPlugin.fromClass(
  class {
    constructor(view) {
      this.decorations = citryDecorations(view);
    }

    update(update) {
      if (update.docChanged || update.viewportChanged) {
        this.decorations = citryDecorations(update.view);
      }
    }
  },
  { decorations: (plugin) => plugin.decorations },
);

const brokenLinter = linter((view) => {
  const source = view.state.doc.toString();
  const from = source.indexOf("BROKEN");
  return from < 0
    ? []
    : [
        {
          from,
          to: from + "BROKEN".length,
          severity: "error",
          message: "NameError: BROKEN is not defined",
        },
      ];
});

const isDark = matchMedia("(prefers-color-scheme: dark)").matches;
const proofTheme = EditorView.theme(
  {
    "&": {
      height: "100%",
      color: isDark ? "#f5f6f8" : "#181a1f",
      backgroundColor: isDark ? "#191b22" : "#ffffff",
    },
    ".cm-scroller": {
      fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
      fontSize: "0.9rem",
      lineHeight: "1.55",
    },
    ".cm-content": { paddingBlock: "0.6rem" },
    ".cm-gutters": {
      color: isDark ? "#b7bdc9" : "#5c6370",
      backgroundColor: isDark ? "#242730" : "#f1f2f4",
      borderInlineEndColor: isDark ? "#454a57" : "#c9ccd2",
    },
    "&.cm-focused": { outline: "none" },
  },
  { dark: isDark },
);

const proofHighlightStyle = HighlightStyle.define([
  { tag: tags.keyword, color: isDark ? "#ff7ab2" : "#a626a4" },
  { tag: tags.string, color: isDark ? "#a8cc8c" : "#407026" },
  { tag: tags.tagName, color: isDark ? "#82d2ce" : "#006d68" },
  { tag: tags.attributeName, color: isDark ? "#ffca85" : "#986801" },
  { tag: tags.comment, color: isDark ? "#8b93a5" : "#66707d" },
]);

let updateDiagnostic = () => {};
const view = new EditorView({
  parent: document.querySelector("#editor"),
  state: EditorState.create({
    doc: sample,
    extensions: [
      lineNumbers(),
      highlightActiveLineGutter(),
      highlightSpecialChars(),
      history(),
      foldGutter(),
      drawSelection(),
      dropCursor(),
      EditorState.allowMultipleSelections.of(true),
      indentOnInput(),
      syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
      syntaxHighlighting(proofHighlightStyle),
      bracketMatching(),
      closeBrackets(),
      autocompletion(),
      rectangularSelection(),
      highlightActiveLine(),
      highlightSelectionMatches(),
      lintGutter(),
      brokenLinter,
      citryPython,
      citryDecorationPlugin,
      proofTheme,
      EditorView.contentAttributes.of({
        "aria-label": "Citry Python module",
        spellcheck: "false",
      }),
      EditorView.updateListener.of((update) => {
        if (update.docChanged) updateDiagnostic();
      }),
      keymap.of([
        ...closeBracketsKeymap,
        ...defaultKeymap,
        ...searchKeymap,
        ...historyKeymap,
        indentWithTab,
      ]),
    ],
  }),
});

function replaceSource(value = sample) {
  view.dispatch({
    changes: { from: 0, to: view.state.doc.length, insert: value },
    selection: { anchor: 0 },
    scrollIntoView: true,
  });
  view.focus();
}

updateDiagnostic = wireProofShell({
  editorName: "CodeMirror 6",
  getValue: () => view.state.doc.toString(),
  restore: replaceSource,
  undo: () => {
    undoCommand(view);
    view.focus();
  },
  openSearch: () => {
    openSearchPanel(view);
    view.focus();
  },
});

window.editorProof = {
  name: "CodeMirror 6",
  ready: true,
  getValue: () => view.state.doc.toString(),
  setValue: replaceSource,
  append(value) {
    view.dispatch({ changes: { from: view.state.doc.length, insert: value } });
  },
  focus: () => view.focus(),
  undo: () => undoCommand(view),
  openSearch: () => openSearchPanel(view),
  syntaxAt(needle) {
    const position = view.state.doc.toString().indexOf(needle);
    return position < 0 ? null : syntaxTree(view.state).resolveInner(position + 1, 1).name;
  },
  citryDecorationCount: () => document.querySelectorAll(".cm-citry-name, .cm-citry-punctuation").length,
  workerResources: () => performance.getEntriesByType("resource").filter((entry) => /worker/i.test(entry.name)).length,
};

updateDiagnostic();
