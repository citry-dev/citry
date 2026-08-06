export interface TagCompletionChange {
	startOffset: number;
	removedLength: number;
	insertedText: string;
	history: boolean;
}

export interface TagCompletionRetriggerDecision {
	pendingOffset?: number;
	triggerOffset?: number;
}

const partialTagPattern = /<\/?c-[A-Za-z0-9_.-]*$/;
// Punctuation already has native LSP triggers; recovery is only needed for word characters.
const manualRetriggerCharacterPattern = /^[A-Za-z0-9_]$/;

export function advanceTagCompletionRetrigger(
	postEditSource: string,
	change: TagCompletionChange,
	pendingOffset: number | undefined,
): TagCompletionRetriggerDecision {
	const resultingOffset = change.startOffset + change.insertedText.length;
	const remainsInPartialTag = partialTagPattern.test(postEditSource.slice(0, resultingOffset));
	if (change.history) {
		return remainsInPartialTag ? { triggerOffset: resultingOffset } : {};
	}
	if (change.removedLength > 0 && change.insertedText.length === 0) {
		return remainsInPartialTag ? { pendingOffset: resultingOffset } : {};
	}
	const continuesPendingTag =
		pendingOffset === change.startOffset &&
		change.removedLength === 0 &&
		manualRetriggerCharacterPattern.test(change.insertedText) &&
		remainsInPartialTag;
	return continuesPendingTag ? { triggerOffset: resultingOffset } : {};
}
