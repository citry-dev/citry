import { PROTOCOL, revisionForManifest } from "./canonical";
import { OWNERSHIP_COMMENT_PREFIX } from "./comments";
import {
	firstUnknown,
	hasOwn,
	isPlainObject,
	ProtocolValueError,
	pointer,
	type ValidationIssue,
	validateStrictJson,
} from "./issue";
import { validateGraph } from "./records";
import { validateRelationships } from "./relationships";
import type { ClientGraphManifest } from "./types";

const REVISION = /^[0-9a-f]{64}$/;
const MANIFEST_FIELDS = new Set([
	"protocol",
	"revision",
	"mode",
	"graphs",
	"delimiters",
]);
const REQUIRED_MANIFEST_FIELDS = [
	"protocol",
	"revision",
	"mode",
	"graphs",
	"delimiters",
] as const;
const DELIMITER_FIELDS = new Set(["format"]);

const validateManifestShape = (
	value: unknown,
	path: string,
): ValidationIssue | null => {
	const jsonIssue = validateStrictJson(value, path);
	if (jsonIssue) return jsonIssue;
	if (!isPlainObject(value)) {
		return {
			path,
			category: "type",
			message: "The client-graph manifest must be an object.",
		};
	}
	for (const required of REQUIRED_MANIFEST_FIELDS) {
		if (!hasOwn(value, required)) {
			return {
				path: pointer(path, required),
				category: "required",
				message: `The manifest requires '${required}'.`,
			};
		}
	}
	const unknown = firstUnknown(value, MANIFEST_FIELDS);
	if (unknown !== null) {
		return {
			path: pointer(path, unknown),
			category: "unknown_field",
			message: "The manifest has an unknown field.",
		};
	}
	if (value.protocol !== PROTOCOL) {
		return {
			path: pointer(path, "protocol"),
			category: typeof value.protocol === "string" ? "enum" : "type",
			message: `The manifest protocol must be ${PROTOCOL}.`,
		};
	}
	if (typeof value.revision !== "string") {
		return {
			path: pointer(path, "revision"),
			category: "type",
			message: "The manifest revision must be a string.",
		};
	}
	if (!REVISION.test(value.revision)) {
		return {
			path: pointer(path, "revision"),
			category: "pattern",
			message: "The manifest revision must be lowercase SHA-256.",
		};
	}
	if (typeof value.mode !== "string") {
		return {
			path: pointer(path, "mode"),
			category: "type",
			message: "The manifest mode must be a string.",
		};
	}
	if (value.mode !== "production" && value.mode !== "development") {
		return {
			path: pointer(path, "mode"),
			category: "enum",
			message: "The manifest mode must be production or development.",
		};
	}
	if (!Array.isArray(value.graphs)) {
		return {
			path: pointer(path, "graphs"),
			category: "type",
			message: "The manifest graphs must be an array.",
		};
	}
	for (let index = 0; index < value.graphs.length; index += 1) {
		const issue = validateGraph(
			value.graphs[index],
			pointer(pointer(path, "graphs"), index),
			false,
		);
		if (issue) return issue;
	}
	const delimiterPath = pointer(path, "delimiters");
	if (!isPlainObject(value.delimiters)) {
		return {
			path: delimiterPath,
			category: "type",
			message: "The manifest delimiters must be an object.",
		};
	}
	if (!hasOwn(value.delimiters, "format")) {
		return {
			path: pointer(delimiterPath, "format"),
			category: "required",
			message: "The manifest delimiters require 'format'.",
		};
	}
	const delimiterUnknown = firstUnknown(value.delimiters, DELIMITER_FIELDS);
	if (delimiterUnknown !== null) {
		return {
			path: pointer(delimiterPath, delimiterUnknown),
			category: "unknown_field",
			message: "The manifest delimiters have an unknown field.",
		};
	}
	if (value.delimiters.format !== OWNERSHIP_COMMENT_PREFIX) {
		return {
			path: pointer(delimiterPath, "format"),
			category: typeof value.delimiters.format === "string" ? "enum" : "type",
			message: `The ownership-comment prefix must be ${OWNERSHIP_COMMENT_PREFIX}.`,
		};
	}
	return null;
};

export const validateRevision = (
	value: unknown,
	path = "",
): ValidationIssue | null => {
	if (
		!isPlainObject(value) ||
		typeof value.revision !== "string" ||
		!REVISION.test(value.revision)
	)
		return null;
	return revisionForManifest(value) === value.revision
		? null
		: {
				path: pointer(path, "revision"),
				category: "correlation",
				message: "The revision does not match the canonical unsigned manifest.",
			};
};

/** Return the first structural, revision, or relationship issue. */
export const validateManifest = (
	value: unknown,
	path = "",
): ValidationIssue | null => {
	const shapeIssue = validateManifestShape(value, path);
	if (shapeIssue) return shapeIssue;
	const revisionIssue = validateRevision(value, path);
	if (revisionIssue) return revisionIssue;
	return validateRelationships(value as unknown as ClientGraphManifest, path);
};

/** Return one valid manifest or throw its protocol issue. */
export const assertValidManifest = (value: unknown): ClientGraphManifest => {
	const issue = validateManifest(value);
	if (issue) throw new ProtocolValueError(issue);
	return value as ClientGraphManifest;
};
