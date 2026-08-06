// src/formatting.ts
function documentVersionIsCurrent(requestedVersion, currentVersion) {
  return requestedVersion === currentVersion;
}
async function applyVersionedEdit(application) {
  const prepared = await prepareVersionedEdit(application);
  if (prepared.kind !== "ready") {
    return prepared.kind;
  }
  return await application.apply(prepared.edit) ? "applied" : "not-applied";
}
async function prepareVersionedEdit(preparation) {
  if (!documentVersionIsCurrent(preparation.requestedVersion, preparation.currentVersion())) {
    return { kind: "stale" };
  }
  if (!preparation.validate(preparation.protocolEdit)) {
    return { kind: "invalid" };
  }
  const edit = await preparation.convert(preparation.protocolEdit);
  if (!documentVersionIsCurrent(preparation.requestedVersion, preparation.currentVersion())) {
    return { kind: "stale" };
  }
  return { kind: "ready", edit };
}
function formattingFailureDelivery(message, quiet, previousQuietFailure) {
  return {
    appendToOutput: !quiet || previousQuietFailure !== message,
    showWarning: !quiet,
    nextQuietFailure: quiet ? message : previousQuietFailure
  };
}
function sourceFormattingAction(resource) {
  return {
    title: "Format Citry document",
    command: "citry.formatDocument",
    arguments: [resource, true],
    isPreferred: true
  };
}
function workspaceOwnsDocument(workspaceUri, selectedWorkspaceUri) {
  return workspaceUri === selectedWorkspaceUri;
}
export {
  applyVersionedEdit,
  documentVersionIsCurrent,
  formattingFailureDelivery,
  prepareVersionedEdit,
  sourceFormattingAction,
  workspaceOwnsDocument
};
