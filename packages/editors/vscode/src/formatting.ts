export interface FormattingFailureDelivery {
	appendToOutput: boolean;
	showWarning: boolean;
	nextQuietFailure: string | undefined;
}

export interface SourceFormattingAction<Resource> {
	title: string;
	command: "citry.formatDocument";
	arguments: [Resource, true];
	isPreferred: true;
}

export type VersionedEditOutcome = "applied" | "invalid" | "not-applied" | "stale";
export type PreparedVersionedEdit<EditorEdit> =
	| { kind: "ready"; edit: EditorEdit }
	| { kind: "invalid" }
	| { kind: "stale" };

export interface VersionedEditApplication<ProtocolEdit, EditorEdit> {
	requestedVersion: number;
	currentVersion: () => number;
	protocolEdit: ProtocolEdit;
	validate: (edit: ProtocolEdit) => boolean;
	convert: (edit: ProtocolEdit) => PromiseLike<EditorEdit>;
	apply: (edit: EditorEdit) => PromiseLike<boolean>;
}

export type VersionedEditPreparation<ProtocolEdit, EditorEdit> = Omit<
	VersionedEditApplication<ProtocolEdit, EditorEdit>,
	"apply"
>;

export function documentVersionIsCurrent(requestedVersion: number, currentVersion: number): boolean {
	return requestedVersion === currentVersion;
}

export async function applyVersionedEdit<ProtocolEdit, EditorEdit>(
	application: VersionedEditApplication<ProtocolEdit, EditorEdit>,
): Promise<VersionedEditOutcome> {
	const prepared = await prepareVersionedEdit(application);
	if (prepared.kind !== "ready") {
		return prepared.kind;
	}
	return (await application.apply(prepared.edit)) ? "applied" : "not-applied";
}

export async function prepareVersionedEdit<ProtocolEdit, EditorEdit>(
	preparation: VersionedEditPreparation<ProtocolEdit, EditorEdit>,
): Promise<PreparedVersionedEdit<EditorEdit>> {
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

export function formattingFailureDelivery(
	message: string,
	quiet: boolean,
	previousQuietFailure: string | undefined,
): FormattingFailureDelivery {
	return {
		appendToOutput: !quiet || previousQuietFailure !== message,
		showWarning: !quiet,
		nextQuietFailure: quiet ? message : previousQuietFailure,
	};
}

export function sourceFormattingAction<Resource>(resource: Resource): SourceFormattingAction<Resource> {
	return {
		title: "Format Citry document",
		command: "citry.formatDocument",
		arguments: [resource, true],
		isPreferred: true,
	};
}

export function workspaceOwnsDocument(workspaceUri: string, selectedWorkspaceUri: string | undefined): boolean {
	return workspaceUri === selectedWorkspaceUri;
}
