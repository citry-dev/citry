// The extension ships the committed `out/extension.js`, and release
// qualification rejects a VSIX whose copy differs from it. `pnpm run check`
// rebuilds `out/` just before this runs, so in a clean CI checkout a difference
// here means the committed bundle is out of date with the sources or locked
// dependencies.
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const extensionRoot = fileURLToPath(new URL("..", import.meta.url));
// Only the shipped bundle is compared, the same file release compares. The
// source map and test bundles record pnpm's folder layout, which can differ
// between machines without changing what ships.
const changed = execFileSync("git", ["status", "--porcelain", "--", "out/extension.js"], {
	cwd: extensionRoot,
	encoding: "utf8",
}).trim();

if (changed) {
	const message =
		"out/extension.js differs from the committed copy after the rebuild.\n" +
		"Commit the rebuilt files under out/ (from `pnpm run compile` and `pnpm run test`) " +
		"together with the source change.\n";
	// Locally the rebuilt bundle is usually just not committed yet, so only a
	// clean CI checkout treats the difference as a failure.
	if (process.env.CI) {
		process.stderr.write(message);
		process.exit(1);
	}
	process.stderr.write(`warning: ${message}`);
}
