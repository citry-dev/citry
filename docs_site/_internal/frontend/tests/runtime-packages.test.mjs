import assert from "node:assert/strict";
import test from "node:test";

import { resolvePackageUrl, resolvePackageUrls } from "../src/runtime_packages.js";

test("direct package coordinates resolve relative to the Worker", async () => {
  const url = await resolvePackageUrl(
    { name: "citry-ui", version: "0.2.0", source: "url", url: "./local/citry_ui.whl" },
    { baseUrl: "https://docs.citry.dev/playground/worker.js" },
  );

  assert.equal(url, "https://docs.citry.dev/playground/local/citry_ui.whl");
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
