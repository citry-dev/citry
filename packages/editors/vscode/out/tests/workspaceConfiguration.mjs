// src/workspaceConfiguration.ts
import path from "node:path";
function resolveWorkspacePath(configured, workspacePath, platform = process.platform) {
  const paths = platform === "win32" ? path.win32 : path.posix;
  const workspaceToken = `$${"{workspaceFolder}"}`;
  return paths.resolve(workspacePath, configured.replaceAll(workspaceToken, workspacePath));
}
function sameWorkspacePath(left, right, platform = process.platform) {
  const paths = platform === "win32" ? path.win32 : path.posix;
  const normalizedLeft = paths.normalize(left);
  const normalizedRight = paths.normalize(right);
  return platform === "win32" ? normalizedLeft.toLocaleLowerCase("en-US") === normalizedRight.toLocaleLowerCase("en-US") : normalizedLeft === normalizedRight;
}
export {
  resolveWorkspacePath,
  sameWorkspacePath
};
