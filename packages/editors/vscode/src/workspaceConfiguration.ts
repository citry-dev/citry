import path from "node:path";

/** Expand VS Code's folder token and resolve a resource-scoped filesystem setting. */
export function resolveWorkspacePath(
	configured: string,
	workspacePath: string,
	platform: NodeJS.Platform = process.platform,
): string {
	const paths = platform === "win32" ? path.win32 : path.posix;
	const workspaceToken = `$${"{workspaceFolder}"}`;
	return paths.resolve(workspacePath, configured.replaceAll(workspaceToken, workspacePath));
}

/** Compare watched paths using the host filesystem's case contract. */
export function sameWorkspacePath(left: string, right: string, platform: NodeJS.Platform = process.platform): boolean {
	const paths = platform === "win32" ? path.win32 : path.posix;
	const normalizedLeft = paths.normalize(left);
	const normalizedRight = paths.normalize(right);
	return platform === "win32"
		? normalizedLeft.toLocaleLowerCase("en-US") === normalizedRight.toLocaleLowerCase("en-US")
		: normalizedLeft === normalizedRight;
}
