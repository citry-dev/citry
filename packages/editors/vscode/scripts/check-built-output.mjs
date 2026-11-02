// The extension ships the committed `out/extension.js`, and release
// qualification rejects a VSIX whose copy differs from it. `pnpm run check`
// rebuilds `out/` just before this runs. esbuild writes the same bytes from the
// same sources and lockfile, so when none of the bundle's inputs changed, a
// different rebuild means the committed bundle is stale or the local
// node_modules does not match pnpm-lock.yaml. When an input did change, the
// rebuilt bundle is the developer's own uncommitted work, so this only reminds
// them to commit it; CI checks out committed files only, so it always fails.
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const extensionRoot = fileURLToPath(new URL("..", import.meta.url));

function changedFiles(paths) {
	return execFileSync("git", ["status", "--porcelain", "--", ...paths], {
		cwd: extensionRoot,
		encoding: "utf8",
	}).trim();
}

// Only the shipped bundle is compared, the same file release compares. The
// source map and test bundles record pnpm's folder layout, which can differ
// between machines without changing what ships.
const bundleChanged = changedFiles(["out/extension.js"]);
// The files esbuild and tsc read to build the bundle, relative to the extension.
const inputsChanged = changedFiles(["src", "package.json", "tsconfig.json", "../../../pnpm-lock.yaml"]);

if (bundleChanged) {
	const rebuild =
		"Commit the rebuilt files under out/ (from `pnpm run compile` and `pnpm run test`) together with the source change.";
	if (inputsChanged && !process.env.CI) {
		process.stderr.write(`warning: out/extension.js changed with your source edits. ${rebuild}\n`);
	} else {
		process.stderr.write(
			"out/extension.js differs from the committed copy after the rebuild, although none of its inputs changed.\n" +
				"Run `pnpm install --frozen-lockfile`, then `pnpm --dir packages/editors/vscode run compile`. " +
				`If out/extension.js still differs, the committed copy is stale. ${rebuild}\n`,
		);
		process.exit(1);
	}
}
