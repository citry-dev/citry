/** The data carried by one canonical client-graph ownership comment. */
export interface OwnershipComment {
	revisionAlias: string;
	graphId: string;
	kind: "i" | "r";
	recordId: string;
	side: "s" | "e";
	key: string;
}

/** The physical range key and side used by the core DOM reader. */
export interface OwnershipRangeComment {
	key: string;
	side: "s" | "e";
}

export const OWNERSHIP_COMMENT_PREFIX = "citry:g1";
export const REVISION_ALIAS_LENGTH = 8;

const REVISION_RE = /^[0-9a-f]{64}$/;
const OWNERSHIP_COMMENT_RE =
	/^citry:g1:([0-9a-f]{8}):([0-9]+):([ir]):([0-9]+):([se])$/;

/** Derive the readable comment alias from one validated graph revision. */
export const ownershipRevisionAlias = (revision: string): string => {
	if (!REVISION_RE.test(revision)) {
		throw new TypeError("The client-graph revision must be lowercase SHA-256.");
	}
	return revision.slice(0, REVISION_ALIAS_LENGTH);
};

/** Match the five variable fields without converting their decimal text. */
export const matchOwnershipComment = (value: string): RegExpExecArray | null =>
	OWNERSHIP_COMMENT_RE.exec(value.trim());

/** Parse only the fields the DOM range reader needs. */
export const parseOwnershipRangeComment = (
	value: string,
): OwnershipRangeComment | null => {
	const match = matchOwnershipComment(value);
	if (match === null) return null;
	return {
		key: `${OWNERSHIP_COMMENT_PREFIX}:${match[1]}:${match[2]}:${match[3]}:${match[4]}`,
		side: match[5] as "s" | "e",
	};
};

/** Parse one ownership comment without interpreting its decimal identifiers. */
export const parseOwnershipComment = (
	value: string,
): OwnershipComment | null => {
	const match = matchOwnershipComment(value);
	if (match === null) return null;
	const [, revisionAlias, graphId, kind, recordId, side] = match;
	return {
		revisionAlias,
		graphId,
		kind: kind as "i" | "r",
		recordId,
		side: side as "s" | "e",
		key: `${OWNERSHIP_COMMENT_PREFIX}:${revisionAlias}:${graphId}:${kind}:${recordId}`,
	};
};
