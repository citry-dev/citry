// src/completionRetrigger.ts
var partialTagPattern = /<\/?c-[A-Za-z0-9_.-]*$/;
var manualRetriggerCharacterPattern = /^[A-Za-z0-9_]$/;
function advanceTagCompletionRetrigger(postEditSource, change, pendingOffset) {
  const resultingOffset = change.startOffset + change.insertedText.length;
  const remainsInPartialTag = partialTagPattern.test(postEditSource.slice(0, resultingOffset));
  if (change.history) {
    return remainsInPartialTag ? { triggerOffset: resultingOffset } : {};
  }
  if (change.removedLength > 0 && change.insertedText.length === 0) {
    return remainsInPartialTag ? { pendingOffset: resultingOffset } : {};
  }
  const continuesPendingTag = pendingOffset === change.startOffset && change.removedLength === 0 && manualRetriggerCharacterPattern.test(change.insertedText) && remainsInPartialTag;
  return continuesPendingTag ? { triggerOffset: resultingOffset } : {};
}
export {
  advanceTagCompletionRetrigger
};
