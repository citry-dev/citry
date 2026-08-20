import path from "node:path";
import { fileURLToPath } from "node:url";
import { runTests } from "@vscode/test-electron";

const here = path.dirname(fileURLToPath(import.meta.url));
const extensionDevelopmentPath = process.env.CITRY_VSCODE_EXTENSION_DIR;
const workspace = process.env.CITRY_VSCODE_SMOKE_WORKSPACE;
const python = process.env.CITRY_VSCODE_SMOKE_PYTHON;
const prettierExtensionPath = process.env.CITRY_VSCODE_PRETTIER_EXTENSION_DIR;

if (!extensionDevelopmentPath || !workspace || !python) {
	throw new Error(
		"CITRY_VSCODE_EXTENSION_DIR, CITRY_VSCODE_SMOKE_WORKSPACE, and CITRY_VSCODE_SMOKE_PYTHON are required",
	);
}

await runTests({
	version: process.env.CITRY_VSCODE_TEST_VERSION ?? "1.101.0",
	extensionDevelopmentPath:
		prettierExtensionPath === undefined
			? path.resolve(extensionDevelopmentPath)
			: [path.resolve(extensionDevelopmentPath), path.resolve(prettierExtensionPath)],
	extensionTestsPath: path.join(here, "suite.cjs"),
	extensionTestsEnv: {
		CITRY_VSCODE_EXTENSION_DIR: path.resolve(extensionDevelopmentPath),
		CITRY_VSCODE_SMOKE_PYTHON: path.resolve(python),
		CITRY_VSCODE_EXPECT_UNAVAILABLE: process.env.CITRY_VSCODE_EXPECT_UNAVAILABLE,
		CITRY_VSCODE_SMOKE_FORMATTING: process.env.CITRY_VSCODE_SMOKE_FORMATTING,
		CITRY_VSCODE_SMOKE_FORMATTING_FIXTURE: process.env.CITRY_VSCODE_SMOKE_FORMATTING_FIXTURE,
	},
	launchArgs: [
		path.resolve(workspace),
		"--disable-workspace-trust",
		"--skip-welcome",
		"--skip-release-notes",
		"--disable-updates",
		"--disable-telemetry",
	],
	reuseMachineInstall: false,
});
