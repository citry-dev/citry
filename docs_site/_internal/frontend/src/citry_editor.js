import { autocompletion, closeBrackets, closeBracketsKeymap } from "@codemirror/autocomplete";
import { defaultKeymap, history, historyKeymap, indentWithTab } from "@codemirror/commands";
import { css, cssLanguage } from "@codemirror/lang-css";
import { html, htmlLanguage } from "@codemirror/lang-html";
import { javascript, javascriptLanguage } from "@codemirror/lang-javascript";
import { python, pythonLanguage } from "@codemirror/lang-python";
import { fluent, fluentLanguage } from "@citry/codemirror-lang-fluent";
import {
  HighlightStyle,
  LanguageSupport,
  bracketMatching,
  foldGutter,
  indentOnInput,
  syntaxHighlighting,
} from "@codemirror/language";
import { highlightSelectionMatches, searchKeymap } from "@codemirror/search";
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
import { parseMixed } from "@lezer/common";
import { tags } from "@lezer/highlight";
import { citryAssetAt } from "./citry_regions.js";

// Parse the Python module normally, then switch parsers only inside Citry's
// triple-quoted template, JavaScript, and CSS class fields.
const embeddedParsers = {
  template: htmlLanguage.parser,
  js: javascriptLanguage.parser,
  css: cssLanguage.parser,
  messages: fluentLanguage.parser,
};

function mixedCitryRegion(node, input) {
  const asset = citryAssetAt(node, (from, to) => input.read(from, to));
  if (asset === null) return null;
  return {
    parser: embeddedParsers[asset.kind],
    overlay: [{ from: asset.from, to: asset.to }],
  };
}

export const citryPython = new LanguageSupport(
  pythonLanguage.configure({ wrap: parseMixed(mixedCitryRegion) }, "Citry Python"),
  [python().support, html().support, javascript().support, css().support, fluent().support],
);

// Lezer understands the embedded languages, while these marks add Citry-only
// names and interpolation delimiters that do not belong to ordinary HTML.
function citryDecorations(view) {
  const ranges = [];
  const patterns = [
    { regexp: /(?:<\/?)(c-[\w-]+)/g, group: 1, className: "cm-citry-name" },
    { regexp: /\b(c-[\w$:@.-]+)(?=\s*=)/g, group: 1, className: "cm-citry-name" },
    { regexp: /\{\{|\}\}/g, group: 0, className: "cm-citry-interpolation" },
  ];
  for (const { from, to } of view.visibleRanges) {
    const text = view.state.sliceDoc(from, to);
    for (const pattern of patterns) {
      pattern.regexp.lastIndex = 0;
      for (let match; (match = pattern.regexp.exec(text)); ) {
        const value = match[pattern.group];
        const offset = pattern.group ? match[0].lastIndexOf(value) : 0;
        const start = from + match.index + offset;
        ranges.push(Decoration.mark({ class: pattern.className }).range(start, start + value.length));
      }
    }
  }
  return Decoration.set(ranges, true);
}

const citryDecorationPlugin = ViewPlugin.fromClass(
  class {
    constructor(view) {
      this.decorations = citryDecorations(view);
    }

    update(update) {
      if (update.docChanged || update.viewportChanged) this.decorations = citryDecorations(update.view);
    }
  },
  { decorations: (plugin) => plugin.decorations },
);

const citryHighlightStyle = HighlightStyle.define([
  { tag: tags.meta, class: "cm-citry-meta" },
  { tag: tags.link, textDecoration: "underline" },
  { tag: tags.heading, textDecoration: "underline", fontWeight: "bold" },
  { tag: tags.emphasis, fontStyle: "italic" },
  { tag: tags.strong, fontWeight: "bold" },
  { tag: tags.strikethrough, textDecoration: "line-through" },
  { tag: tags.keyword, class: "cm-citry-keyword" },
  { tag: [tags.atom, tags.bool, tags.url, tags.contentSeparator, tags.labelName], class: "cm-citry-constant" },
  { tag: [tags.literal, tags.inserted], class: "cm-citry-literal" },
  {
    tag: [
      tags.function(tags.variableName),
      tags.function(tags.definition(tags.variableName)),
      tags.function(tags.local(tags.variableName)),
    ],
    class: "cm-citry-function",
  },
  { tag: [tags.string, tags.deleted], class: "cm-citry-string" },
  { tag: [tags.regexp, tags.escape, tags.special(tags.string)], class: "cm-citry-special-string" },
  { tag: tags.definition(tags.variableName), class: "cm-citry-definition" },
  { tag: tags.local(tags.variableName), class: "cm-citry-local" },
  { tag: [tags.typeName, tags.namespace, tags.className], class: "cm-citry-type" },
  { tag: [tags.special(tags.variableName), tags.macroName], class: "cm-citry-special-name" },
  { tag: tags.definition(tags.propertyName), class: "cm-citry-definition" },
  { tag: tags.tagName, class: "cm-citry-tag" },
  { tag: tags.attributeName, class: "cm-citry-attribute" },
  { tag: tags.comment, class: "cm-citry-comment" },
  { tag: tags.invalid, class: "cm-citry-invalid" },
]);

const citryTheme = EditorView.theme({
  "&": { height: "100%", backgroundColor: "var(--c-bg)", color: "var(--c-fg)" },
  "&.cm-focused": { outline: "none" },
  ".cm-content": { paddingBlock: "0.6rem", caretColor: "var(--c-fg)" },
  ".cm-cursor, .cm-dropCursor": { borderLeftColor: "var(--c-fg)" },
  ".cm-selectionBackground, &.cm-focused .cm-selectionBackground": {
    backgroundColor: "color-mix(in oklch, var(--c-link) 8%, transparent)",
  },
});

// Both playground consumers use this small adapter so CodeMirror lifecycle and
// keyboard behavior stay out of their run-state coordinators.
export function createCitryEditor({ parent, initialSource, onChange, onRun, ide = null }) {
  const view = new EditorView({
    parent,
    state: EditorState.create({
      doc: initialSource,
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
        syntaxHighlighting(citryHighlightStyle),
        bracketMatching(),
        closeBrackets(),
        autocompletion(),
        rectangularSelection(),
        highlightActiveLine(),
        highlightSelectionMatches(),
        citryPython,
        citryDecorationPlugin,
        citryTheme,
        ...(ide?.extensions() || []),
        EditorView.contentAttributes.of({
          "aria-label": "Citry Python module",
          spellcheck: "false",
        }),
        EditorView.updateListener.of((update) => {
          if (!update.docChanged) return;
          ide?.update(update.state);
          onChange();
        }),
        keymap.of([
          { key: "Mod-Enter", run: () => { onRun(); return true; } },
          ...closeBracketsKeymap,
          ...defaultKeymap,
          ...searchKeymap,
          ...historyKeymap,
          indentWithTab,
        ]),
      ],
    }),
  });
  ide?.attach(view);

  return {
    getSource: () => view.state.doc.toString(),
    setSource(source, focus = true) {
      view.dispatch({
        changes: { from: 0, to: view.state.doc.length, insert: source },
        selection: { anchor: 0 },
        scrollIntoView: true,
      });
      if (focus) view.focus();
    },
    focus: () => view.focus(),
    setCursor(position) {
      if (!Number.isSafeInteger(position) || position < 0 || position > view.state.doc.length) return false;
      view.dispatch({ selection: { anchor: position }, scrollIntoView: true });
      view.focus();
      return true;
    },
    destroy() {
      ide?.destroy();
      view.destroy();
    },
  };
}
