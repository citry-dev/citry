import assert from "node:assert/strict";
import test from "node:test";

import {
  resolvePackageUrl,
  resolvePackageUrls,
  validatePyodideManifest,
} from "../src/runtime_packages.js";

const PYODIDE = {
  version: "314.0.3",
  python: "3.14.2",
  index_url: "https://cdn.jsdelivr.net/pyodide/v314.0.3/full/",
  module_url: "https://cdn.jsdelivr.net/pyodide/v314.0.3/full/pyodide.mjs",
};

test("the Pyodide manifest is pinned to the exact approved CDN tree", () => {
  validatePyodideManifest(PYODIDE);
  assert.throws(
    () => validatePyodideManifest({ ...PYODIDE, module_url: "https://example.com/pyodide.mjs" }),
    /invalid Pyodide CDN URLs/,
  );
});

test("direct package coordinates resolve relative to the Worker", async () => {
  const url = await resolvePackageUrl(
    { name: "citry-ui", version: "0.2.0", source: "url", url: "./local/citry_ui.whl" },
    { baseUrl: "https://docs.citry.dev/playground/worker.js" },
  );

  assert.equal(url, "https://docs.citry.dev/playground/local/citry_ui.whl");
});

test("direct package coordinates accept the approved Pyodide CDN origin", async () => {
  const url = await resolvePackageUrl({
    name: "MarkupSafe",
    version: "3.0.3",
    source: "url",
    url: "https://cdn.jsdelivr.net/pyodide/v314.0.3/full/markupsafe.whl",
  }, { pyodide: { version: "314.0.3" } });

  assert.equal(url, "https://cdn.jsdelivr.net/pyodide/v314.0.3/full/markupsafe.whl");
});

test("direct package coordinates reject unapproved or credential-bearing URLs", async () => {
  for (const url of [
    "https://example.com/package.whl",
    "https://user:password@cdn.jsdelivr.net/package.whl",
    "https://cdn.jsdelivr.net/package.whl?redirect=elsewhere",
    "//cdn.jsdelivr.net/pyodide/v314.0.3/full/package.whl",
    "https://cdn.jsdelivr.net",
    "https://cdn.jsdelivr.net/pyodide/v314.0.2/full/package.whl",
  ]) {
    await assert.rejects(
      resolvePackageUrl(
        { name: "package", version: "1.0.0", source: "url", url },
        { pyodide: { version: "314.0.3" } },
      ),
      /unapproved Pyodide runtime URL|unsafe runtime URL/,
    );
  }
});

test("PyPI coordinates accept only the qualified filename and digest", async () => {
  const sha256 = "a".repeat(64);
  const requested = [];
  const url = await resolvePackageUrl(
    {
      name: "citry",
      version: "0.4.7",
      source: "pypi",
      filename: "citry-0.4.7-py3-none-any.whl",
      sha256,
    },
    {
      fetchImpl: async (requestUrl, options) => {
        requested.push([requestUrl, options]);
        return {
          ok: true,
          async json() {
            return {
              urls: [{
                filename: "citry-0.4.7-py3-none-any.whl",
                url: "https://files.pythonhosted.org/packages/aa/citry-0.4.7-py3-none-any.whl",
                digests: { sha256 },
              }],
            };
          },
        };
      },
    },
  );

  assert.equal(url, "https://files.pythonhosted.org/packages/aa/citry-0.4.7-py3-none-any.whl");
  assert.deepEqual(requested, [["https://pypi.org/pypi/citry/0.4.7/json", { cache: "no-cache" }]]);
});

test("PyPI coordinates reject different public bytes", async () => {
  await assert.rejects(
    resolvePackageUrl(
      {
        name: "citry",
        version: "0.4.7",
        source: "pypi",
        filename: "citry-0.4.7-py3-none-any.whl",
        sha256: "a".repeat(64),
      },
      {
        fetchImpl: async () => ({
          ok: true,
          async json() {
            return {
              urls: [{
                filename: "citry-0.4.7-py3-none-any.whl",
                url: "https://files.pythonhosted.org/packages/aa/citry-0.4.7-py3-none-any.whl",
                digests: { sha256: "b".repeat(64) },
              }],
            };
          },
        }),
      },
    ),
    /does not match the qualified SHA-256 digest/,
  );
});

test("the package list fails as one unit when a source is unknown", async () => {
  await assert.rejects(
    resolvePackageUrls([{ name: "citry", version: "0.4.7", source: "mirror" }]),
    /unsupported runtime source/,
  );
});
