import sample from "../samples/citry_component.py";
import * as monaco from "monaco-editor/editor/editor.api.js";
import "monaco-editor/editor/contrib/find/browser/findController.js";
import { conf as cssConfiguration, language as cssLanguage } from "monaco-editor/languages/definitions/css/css.js";
import { conf as htmlConfiguration, language as htmlLanguage } from "monaco-editor/languages/definitions/html/html.js";
import { conf as javascriptConfiguration, language as javascriptLanguage } from "monaco-editor/languages/definitions/javascript/javascript.js";
import { conf as pythonConfiguration, language as pythonLanguage } from "monaco-editor/languages/definitions/python/python.js";
import { wireProofShell } from "./editor-shell.js";

function registerMonarch(id, configuration, language, aliases = []) {
  monaco.languages.register({ id, aliases });
  monaco.languages.setLanguageConfiguration(id, configuration);
  monaco.languages.setMonarchTokensProvider(id, language);
}

registerMonarch("python", pythonConfiguration, pythonLanguage, ["Python"]);
registerMonarch("text/javascript", javascriptConfiguration, javascriptLanguage, ["JavaScript"]);
registerMonarch("text/css", cssConfiguration, cssLanguage, ["CSS"]);

const citryHtmlLanguage = {
  ...htmlLanguage,
  tokenizer: {
    ...htmlLanguage.tokenizer,
    root: [
      [/\{#/, { token: "comment.citry", next: "@citryComment" }],
      [
        /\{\{/,
        {
          token: "delimiter.citry",
          next: "@citryExpression",
          nextEmbedded: "python",
        },
      ],
      ...htmlLanguage.tokenizer.root,
    ],
    otherTag: [
      [
        /(c-[\w$:@.-]+)(\s*)(=)(\s*)(")/,
        [
          "attribute.name.citry",
          "",
          "delimiter",
          "",
          {
            token: "string.quote",
            next: "@citryAttributeDouble",
            nextEmbedded: "python",
          },
        ],
      ],
      [
        /(c-[\w$:@.-]+)(\s*)(=)(\s*)(')/,
        [
          "attribute.name.citry",
          "",
          "delimiter",
          "",
          {
            token: "string.quote",
            next: "@citryAttributeSingle",
            nextEmbedded: "python",
          },
        ],
      ],
      ...htmlLanguage.tokenizer.otherTag,
    ],
    citryComment: [
      [/#\}/, { token: "comment.citry", next: "@pop" }],
      [/./, "comment.citry"],
    ],
    citryExpression: [
      [/\}\}/, { token: "delimiter.citry", next: "@pop", nextEmbedded: "@pop" }],
      [/[^}]+/, ""],
      [/./, ""],
    ],
    citryAttributeDouble: [
      [/"/, { token: "string.quote", next: "@pop", nextEmbedded: "@pop" }],
      [/[^"\\]+/, ""],
      [/\\./, ""],
    ],
    citryAttributeSingle: [
      [/'/, { token: "string.quote", next: "@pop", nextEmbedded: "@pop" }],
      [/[^'\\]+/, ""],
      [/\\./, ""],
    ],
  },
};

registerMonarch("citry-html", htmlConfiguration, citryHtmlLanguage, ["Citry HTML"]);

function embeddedAssignment(name, quote, state, embedded) {
  const escapedQuote = quote === '"""' ? /"""/ : /'''/;
  const source = new RegExp(
    `\\b${name}(?:\\s*:\\s*[^\\s=]+)?\\s*=\\s*${escapedQuote.source}`,
  );
  return [
    source,
    { token: "variable.citry", next: state, nextEmbedded: embedded },
  ];
}

function embeddedBody(quote) {
  const close = quote === '"""' ? /"""/ : /'''/;
  const content = quote === '"""' ? /[^\"]+/ : /[^']+/;
  return [
    [close, { token: "string.quote", next: "@pop", nextEmbedded: "@pop" }],
    [content, ""],
    [/./, ""],
  ];
}

const citryPythonLanguage = {
  ...pythonLanguage,
  tokenizer: {
    ...pythonLanguage.tokenizer,
    root: [
      embeddedAssignment("template", '"""', "@templateDouble", "citry-html"),
      embeddedAssignment("template", "'''", "@templateSingle", "citry-html"),
      embeddedAssignment("js", '"""', "@javascriptDouble", "text/javascript"),
      embeddedAssignment("js", "'''", "@javascriptSingle", "text/javascript"),
      embeddedAssignment("css", '"""', "@cssDouble", "text/css"),
      embeddedAssignment("css", "'''", "@cssSingle", "text/css"),
      ...pythonLanguage.tokenizer.root,
    ],
    templateDouble: embeddedBody('"""'),
    templateSingle: embeddedBody("'''"),
    javascriptDouble: embeddedBody('"""'),
    javascriptSingle: embeddedBody("'''"),
    cssDouble: embeddedBody('"""'),
    cssSingle: embeddedBody("'''"),
  },
};

registerMonarch("citry-python", pythonConfiguration, citryPythonLanguage, ["Citry Python"]);

const model = monaco.editor.createModel(sample, "citry-python");
const isDark = matchMedia("(prefers-color-scheme: dark)").matches;
const editor = monaco.editor.create(document.querySelector("#editor"), {
  model,
  ariaLabel: "Citry Python module",
  accessibilitySupport: "on",
  automaticLayout: true,
  bracketPairColorization: { enabled: true },
  minimap: { enabled: false },
  padding: { top: 10, bottom: 10 },
  scrollBeyondLastLine: false,
  tabSize: 4,
  theme: isDark ? "vs-dark" : "vs",
});

let updateDiagnostic = () => {};

function applyDiagnostic() {
  const source = model.getValue();
  const offset = source.indexOf("BROKEN");
  if (offset < 0) {
    monaco.editor.setModelMarkers(model, "citry-proof", []);
  } else {
    const start = model.getPositionAt(offset);
    const end = model.getPositionAt(offset + "BROKEN".length);
    monaco.editor.setModelMarkers(model, "citry-proof", [
      {
        severity: monaco.MarkerSeverity.Error,
        message: "NameError: BROKEN is not defined",
        startLineNumber: start.lineNumber,
        startColumn: start.column,
        endLineNumber: end.lineNumber,
        endColumn: end.column,
      },
    ]);
  }
  updateDiagnostic();
}

model.onDidChangeContent(applyDiagnostic);

function replaceSource(value = sample) {
  editor.setValue(value);
  editor.setPosition({ lineNumber: 1, column: 1 });
  editor.revealLine(1);
  editor.focus();
}

updateDiagnostic = wireProofShell({
  editorName: "Monaco",
  getValue: () => model.getValue(),
  restore: replaceSource,
  undo: () => {
    editor.trigger("proof", "undo", null);
    editor.focus();
  },
  openSearch: () => editor.trigger("proof", "actions.find", null),
});

function tokenAt(needle) {
  const source = model.getValue();
  const offset = source.indexOf(needle);
  if (offset < 0) return null;
  const position = model.getPositionAt(offset + 1);
  const tokens = monaco.editor.tokenize(source, "citry-python")[position.lineNumber - 1];
  const token = [...tokens].reverse().find((entry) => entry.offset <= position.column - 1);
  return token ? { language: token.language, type: token.type } : null;
}

window.editorProof = {
  name: "Monaco",
  ready: true,
  getValue: () => model.getValue(),
  setValue: replaceSource,
  append(value) {
    editor.executeEdits("proof", [
      {
        range: new monaco.Range(
          model.getLineCount(),
          model.getLineMaxColumn(model.getLineCount()),
          model.getLineCount(),
          model.getLineMaxColumn(model.getLineCount()),
        ),
        text: value,
      },
    ]);
  },
  focus: () => editor.focus(),
  undo: () => editor.trigger("proof", "undo", null),
  openSearch: () => editor.trigger("proof", "actions.find", null),
  tokenAt,
  tokenize: (source) => monaco.editor.tokenize(source, "citry-python"),
  workerRequests: () => globalThis.__monacoWorkerRequests,
  workerExecuted: () => globalThis.__monacoWorkerExecuted,
  markers: () => monaco.editor.getModelMarkers({ resource: model.uri }),
};

applyDiagnostic();
