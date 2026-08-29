import assert from "node:assert/strict";
import test from "node:test";

import { resolveWorkspacePath, sameWorkspacePath } from "../out/tests/workspaceConfiguration.mjs";

const workspaceToken = `$${"{workspaceFolder}"}`;

test("workspace paths expand the folder token and relative values", () => {
	assert.equal(resolveWorkspacePath(`${workspaceToken}/.env`, "/work/app", "linux"), "/work/app/.env");
	assert.equal(resolveWorkspacePath("config/citry.env", "/work/app", "linux"), "/work/app/config/citry.env");
	assert.equal(resolveWorkspacePath("/shared/citry.env", "/work/app", "linux"), "/shared/citry.env");
});

test("Windows workspace paths use drive and case-insensitive semantics", () => {
	assert.equal(resolveWorkspacePath(`${workspaceToken}\\.env`, "C:\\Work\\App", "win32"), "C:\\Work\\App\\.env");
	assert.equal(sameWorkspacePath("C:\\Work\\App\\.ENV", "c:\\work\\app\\.env", "win32"), true);
});

test("POSIX watched paths remain case-sensitive", () => {
	assert.equal(sameWorkspacePath("/work/.ENV", "/work/.env", "linux"), false);
});
