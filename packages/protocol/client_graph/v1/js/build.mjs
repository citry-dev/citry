/** Generate the client-graph protocol runtime embedded in the core browser file. */

import { readFile, writeFile } from "node:fs/promises";

import { build, transform } from "esbuild";

import { composeCoreRuntime } from "./build-support.mjs";

const argumentsSet = new Set(process.argv.slice(2));
const knownArguments = new Set(["--check", "--initialize"]);
for (const argument of argumentsSet) {
	if (!knownArguments.has(argument))
		throw new TypeError(`Unknown argument: ${argument}`);
}
if (argumentsSet.has("--check") && argumentsSet.has("--initialize")) {
	throw new TypeError("--check and --initialize cannot be combined");
}

const root = new URL("../../../../../", import.meta.url);
const coreUrl = new URL(
	"packages/py/citry/citry/ext/dependencies/client/citry.js",
	root,
);
const bundle = await build({
	entryPoints: [new URL("src/core-embed.ts", import.meta.url).pathname],
	bundle: true,
	format: "esm",
	platform: "browser",
	target: "es2020",
	write: false,
});
const moduleBody = bundle.outputFiles[0].text.replace(
	/export\s*\{[\s\S]*?\};?\s*$/,
	"",
);
const transformed = await transform(
	`${moduleBody}\nvar CitryClientGraphProtocol = { OWNERSHIP_COMMENT_PREFIX, parseOwnershipComment, ProtocolValueError, assertValidManifest };`,
	{ loader: "js", minify: true, target: "es2020" },
);
const generated = transformed.code.trim();
if (!generated.includes("CitryClientGraphProtocol")) {
	throw new Error(
		"Generated client-graph runtime did not expose its browser API",
	);
}

const current = await readFile(coreUrl, "utf8");
const expected = composeCoreRuntime(current, generated, {
	initialize: argumentsSet.has("--initialize"),
});
if (argumentsSet.has("--check")) {
	if (current !== expected) {
		throw new Error(
			"citry.js has a stale generated client-graph region; run the protocol build",
		);
	}
} else if (current !== expected) {
	await writeFile(coreUrl, expected, "utf8");
}
