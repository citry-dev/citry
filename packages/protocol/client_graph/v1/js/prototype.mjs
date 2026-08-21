/** Report the generated-region size and the current combined browser payload. */

import { readFile } from "node:fs/promises";
import { gzipSync } from "node:zlib";

import { build, transform } from "esbuild";

import {
	composeCoreRuntime,
	REGION_END,
	REGION_START,
} from "./build-support.mjs";

const RAW_GUARD = 649_000;
const GZIP_GUARD = 138_000;
const root = new URL("../../../../../", import.meta.url);
const coreUrl = new URL(
	"packages/py/citry/citry/ext/dependencies/client/citry.js",
	root,
);
const eventsUrl = new URL(
	"packages/py/citry/citry/ext/events/client/citry-events.js",
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
	`${moduleBody}\nvar CitryClientGraphProtocol = { OWNERSHIP_COMMENT_PREFIX, ownershipRevisionAlias, parseOwnershipComment, ProtocolValueError, assertValidManifest };`,
	{ loader: "js", minify: true, target: "es2020" },
);
const generated = transformed.code.trim();
const core = await readFile(coreUrl, "utf8");
if (composeCoreRuntime(core, generated) !== core) {
	throw new Error("citry.js has a stale generated client-graph region");
}
const combined = Buffer.concat([Buffer.from(core), await readFile(eventsUrl)]);
const gzipBytes = gzipSync(combined, { level: 9, mtime: 0 }).length;
const markerStart = core.indexOf(REGION_START);
const markerEnd = core.indexOf(REGION_END) + REGION_END.length;
const report = {
	format: "citry-client-graph-region-prototype/1",
	committedMarkerSpanBytes: Buffer.byteLength(
		core.slice(markerStart, markerEnd),
	),
	combined: {
		rawBytes: combined.length,
		gzipBytes,
	},
	guard: {
		rawBytes: RAW_GUARD,
		gzipBytes: GZIP_GUARD,
		rawHeadroom: RAW_GUARD - combined.length,
		gzipHeadroom: GZIP_GUARD - gzipBytes,
	},
};
console.log(JSON.stringify(report, null, 2));
