// Imports every module of this checkout's Citry and Citry UI in Pyodide and
// renders two components, so a change that only breaks on Pyodide fails the
// pull request.
// Citry 0.8.0 read `time.thread_time` when it was imported, Pyodide has no
// such function, and nothing ran this checkout's Python under Pyodide until
// a release.
//
// Usage: node smoke.mjs <wheel-dir>
//
// <wheel-dir> holds one `citry` wheel and one `citry-ui` wheel built from this
// checkout (`uv build --wheel`). Everything else comes from the playground's
// committed runtime.json, as it does in the browser: the Pyodide version, the
// packages Pyodide ships, and the published Citry Core wheel. Citry Core is
// the Rust extension. Building it for Pyodide takes minutes and needs
// Emscripten, so this check uses the published wheel, and the release
// qualification of citry-core tests the new build.

import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { loadPyodide } from "pyodide";

// The playground's own package resolver, so this check installs the pins the
// way the browser does, including its comparison of each PyPI wheel's SHA-256
// with the one PyPI lists for that file.
import {
  resolvePackageUrls,
  validatePyodideManifest,
} from "../../docs_site/_internal/frontend/src/runtime_packages.js";

const toolDir = path.dirname(fileURLToPath(import.meta.url));
const runtimePath = path.resolve(toolDir, "../../docs_site/static/playground/runtime.json");

// The two distributions built from this checkout. They replace the published
// Citry and Citry UI that runtime.json pins.
const WORKSPACE_DISTRIBUTIONS = ["citry", "citry-ui"];

function normalized(name) {
  return name.toLowerCase().replace(/[-_.]+/g, "-");
}

// Returns the one wheel for a distribution. Zero or two would mean the build
// step went wrong, and installing "whichever came first" would test the wrong
// code without saying so.
async function findWheel(wheelDir, distribution) {
  // A wheel's file name starts with its distribution name, with `-` written
  // as `_`, then `-` and the version.
  const prefix = `${distribution.replaceAll("-", "_")}-`;
  const names = (await readdir(wheelDir)).filter(
    (name) => name.startsWith(prefix) && name.endsWith(".whl"),
  );
  if (names.length !== 1) {
    const found = names.length > 0 ? names.join(", ") : "none";
    throw new Error(`Expected one ${distribution} wheel in ${wheelDir}, found ${found}.`);
  }
  return names[0];
}

function versionOfWheel(filename) {
  return filename.split("-")[1];
}

async function main(wheelDir) {
  const runtime = JSON.parse(await readFile(runtimePath, "utf8"));
  if (runtime.schema_version !== 1 || !Array.isArray(runtime.packages)) {
    throw new Error(`${runtimePath} is not a version 1 playground runtime.`);
  }
  validatePyodideManifest(runtime.pyodide);

  const wheels = new Map();
  for (const distribution of WORKSPACE_DISTRIBUTIONS) {
    wheels.set(distribution, await findWheel(wheelDir, distribution));
  }

  // The pnpm lockfile in this directory picks the Pyodide build that runs, and
  // runtime.json picks the one the playground serves. They must be the same
  // build, or this check would test a different Pyodide than the browser gets.
  const pyodide = await loadPyodide();
  if (pyodide.version !== runtime.pyodide.version) {
    throw new Error(
      `The pyodide package is ${pyodide.version}, but runtime.json pins Pyodide `
        + `${runtime.pyodide.version}. Set the pyodide version in tools/pyodide-smoke/package.json `
        + "to match, then run `pnpm install` in that directory.",
    );
  }
  const python = pyodide.runPython(
    "import sys; '.'.join(str(part) for part in sys.version_info[:3])",
  );
  if (python !== runtime.pyodide.python) {
    throw new Error(`Pyodide runs Python ${python}, but runtime.json pins ${runtime.pyodide.python}.`);
  }

  // Install every pin except the two this checkout replaces.
  const pinned = runtime.packages.filter(
    (entry) => !WORKSPACE_DISTRIBUTIONS.includes(normalized(entry.name)),
  );
  const pinnedUrls = await resolvePackageUrls(pinned, { pyodide: runtime.pyodide });

  // In Node, Pyodide reads a package URL that is not an http(s) URL as a path
  // on this machine, so the local wheels need no copy into Pyodide's files.
  const localPaths = [...wheels.values()].map((name) => path.join(wheelDir, name));
  // Pyodide reports an install that failed through this callback and still
  // resolves. Without the check below, the failure would first show up as a
  // missing package further on, with no hint at the cause.
  const failures = [];
  await pyodide.loadPackage([...pinnedUrls, ...localPaths], {
    errorCallback: (message) => failures.push(message),
  });
  if (failures.length > 0) {
    throw new Error(`Pyodide could not install every package:\n${failures.join("\n")}`);
  }

  // Fail here, with the versions, if an install resolved to the wrong wheel.
  // A published Citry that replaced this checkout's would pass every check
  // below.
  const installed = JSON.parse(
    pyodide.runPython(`
import importlib.metadata
import json
json.dumps({
    name: importlib.metadata.version(name)
    for name in ("citry", "citry-core", "citry-ui")
})
    `),
  );
  const core = runtime.packages.find((entry) => normalized(entry.name) === "citry-core");
  if (!core) throw new Error("runtime.json pins no citry-core package.");
  const expected = {
    citry: versionOfWheel(wheels.get("citry")),
    "citry-core": core.version,
    "citry-ui": versionOfWheel(wheels.get("citry-ui")),
  };
  if (JSON.stringify(installed) !== JSON.stringify(expected)) {
    throw new Error(
      `Installed versions ${JSON.stringify(installed)} differ from the expected `
        + `${JSON.stringify(expected)}.`,
    );
  }
  console.log(`Installed ${JSON.stringify(installed)} on Python ${python}.`);

  // The Python file raises, with the failing output in the message, when an
  // import or a render goes wrong; Pyodide carries that traceback into the
  // error thrown here.
  pyodide.runPython(await readFile(path.join(toolDir, "render_components.py"), "utf8"));
  console.log(pyodide.runPython("main()"));
  console.log("Pyodide smoke check passed.");
}

try {
  const wheelDir = process.argv[2];
  if (!wheelDir) throw new Error("Usage: node smoke.mjs <wheel-dir>");
  await main(path.resolve(wheelDir));
} catch (error) {
  console.error(String(error?.message ?? error));
  // Node's fetch reports every network failure as "fetch failed" and keeps the
  // reason (a DNS or TLS error, say) in `cause`, so print it to tell a flaky
  // download from a code failure.
  if (error?.cause) console.error(`Cause: ${error.cause?.stack ?? error.cause}`);
  process.exit(1);
}
