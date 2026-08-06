export function wireProofShell({ editorName, getValue, restore, undo, openSearch }) {
  const diagnostic = document.querySelector("#editor-diagnostic");
  const diagnosticText = document.querySelector("#diagnostic-text");

  function updateDiagnostic() {
    const source = getValue();
    const offset = source.indexOf("BROKEN");
    diagnostic.hidden = offset < 0;
    if (offset >= 0) {
      diagnosticText.textContent = `${editorName} proof diagnostic\nNameError: BROKEN is not defined`;
    }
  }

  document.querySelector("#restore-button").addEventListener("click", () => restore());
  document.querySelector("#undo-button").addEventListener("click", () => undo());
  document.querySelector("#search-button").addEventListener("click", () => openSearch());
  document.querySelector("#diagnostic-button").addEventListener("click", () => {
    restore(`${getValue()}\nBROKEN\n`);
  });
  document.querySelector("#copy-diagnostic").addEventListener("click", async () => {
    await navigator.clipboard.writeText(diagnosticText.textContent);
  });

  return updateDiagnostic;
}
