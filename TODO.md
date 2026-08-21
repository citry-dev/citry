# TODO

-----

We have both the editor-agnostic LSP and a working VS Code extension. The remaining major gap is PyCharm validation and packaging.

## Installation state

Nothing else needs to be added to the LSP runtime package. Installing citry-lsp installs:

- citry[analysis-ty]>=0.4.1,<0.5
- pygls==2.1.1
- The citry-lsp console command

pytest and pytest-lsp are development dependencies only.

Citry 0.4.2, citry-core 1.5.1, and citry-lsp 0.1.1 are published. Install and
start the server in the project environment:

python -m pip install citry-lsp
citry-lsp

Citry for VS Code 0.1.0 is published to Visual Studio Marketplace and Open VSX.
The matching GitHub Release carries the exact qualified VSIX.

## Testing the VS Code integration

Build and install the current VSIX:

cd /Users/mac/repos/citry
pnpm install
pnpm --dir packages/editors/vscode run package
code --install-extension packages/editors/vscode/dist/citry.vsix --force

In VS Code, select the repository’s .venv Python interpreter. If automatic interpreter discovery does not find it, configure:

{
"citry.python": "/Users/mac/repos/citry/.venv/bin/python",
"citry.app": "your_module:your_citry_instance"
}

Then verify:

- Run Citry: Show Language Server Status. It should report registry, the selected interpreter, your app spec, Citry 0.4.2, and protocol 1.
- Open a component’s Python file. Its template, js, and css multiline strings should be highlighted.
- Introduce an unmatched or malformed tag and check for a precise diagnostic.
- Type <c- and check component completion.
- Inside a component tag, check input completion and hover.
- Inside <c-fill name="...">, check slot completion.
- Use go-to-definition on a component tag and a loop-local variable.
- Open the document outline and check template symbols.
- Open a registered template_file; registry mode should analyze it even when it is ordinary HTML.
- Run Citry: Restart Language Server after modifying component registrations.

To test degradation, remove citry.app. The status should explicitly become syntax only: parser diagnostics continue, but component names, inputs, slots, and catalog navigation
disappear.

The built artifact is packages/editors/vscode/dist/citry.vsix.

## LSP versus VS Code extension

Both are implemented:

- packages/py/citry_lsp/README.md:1 is the editor-independent stdio language server.
- The packages/editors/vscode/README.md:1 supplies:
    - Python-string and standalone-template highlighting
    - One LSP client per workspace folder
    - Interpreter resolution
    - citry.app configuration
    - Status and restart commands

The LSP is deliberately not bundled into the VSIX. The extension launches python -m citry_lsp from the selected project environment so it can import that project and its
dependencies.

## PyCharm state

PyCharm integration is not ready or supported yet.

What exists:

- The generic LSP server PyCharm could eventually launch.
- A proposed LSP4IJ route.

What is still missing:

- Testing against a real PyCharm installation.
- Verification that LSP4IJ can attach a second language server to .py files already owned by PyCharm’s Python support.
- The importable LSP4IJ configuration JSON.
- JetBrains setup documentation.
- Inline Citry highlighting inside Python strings.
- An official JetBrains plugin.

A manual LSP4IJ experiment could point at the environment’s citry-lsp command, but it should be treated as an unverified experiment. In particular, diagnostics and completion
inside .py files may conflict with or be rejected by PyCharm’s existing Python ownership.

The next PyCharm step should be the attach spike described in the docs/design/ide_integration.md:528. If that succeeds, we can ship the LSP4IJ template and setup docs. Inline
highlighting would still require a native JetBrains plugin.
