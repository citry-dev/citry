import { createHash } from "node:crypto";
import { readdir, readFile, writeFile, mkdir } from "node:fs/promises";
import { createRequire } from "node:module";
import { basename, dirname, join, relative, resolve, sep } from "node:path";

const require = createRequire(import.meta.url);
const packages = {
  vue: ["dist/vue.d.mts", "dist/vue.d.ts"],
  "@vue/shared": ["dist/shared.d.ts"],
  "@vue/compiler-core": ["dist/compiler-core.d.ts"],
  "@vue/compiler-dom": ["dist/compiler-dom.d.ts"],
  "@vue/reactivity": ["dist/reactivity.d.ts"],
  "@vue/runtime-core": ["dist/runtime-core.d.ts"],
  "@vue/runtime-dom": ["dist/runtime-dom.d.ts"],
  "@babel/types": ["lib/index.d.ts"],
  "@babel/parser": ["typings/babel-parser.d.ts"],
  csstype: ["index.d.ts"],
};
const expectedVueVersion = "3.5.42";
const outputRoot = resolve(import.meta.dirname, "../../py/citry_lsp/citry_lsp/types/node_modules");
const checking = process.argv.includes("--check");

const vuePackage = require.resolve("vue/package.json");
const vueRequire = createRequire(vuePackage);
const expectedTargets = new Set();

const inventory = [];
for (const [name, declarations] of Object.entries(packages)) {
  const packageJson = name === "vue" ? vuePackage : vueRequire.resolve(`${name}/package.json`);
  const packageRoot = dirname(packageJson);
  const metadata = JSON.parse(await readFile(packageJson, "utf8"));
  if (name === "vue" && metadata.version !== expectedVueVersion)
    throw new Error(`Expected Vue ${expectedVueVersion}, found ${metadata.version}.`);
  const targetRoot = join(outputRoot, ...name.split("/"));
  const licenseNames = (await readdir(packageRoot)).filter((entry) => /^licen[cs]e(?:\..*)?$/i.test(entry));
  const files = ["package.json", ...licenseNames, ...declarations].map((path) => join(packageRoot, path)).sort();
  const licenseFiles = files.filter((path) => /^licen[cs]e(?:\..*)?$/i.test(basename(path)));
  if (licenseFiles.length === 0) throw new Error(`${name}@${metadata.version} has no packaged license file.`);
  for (const source of files) {
    const target = join(targetRoot, relative(packageRoot, source));
    expectedTargets.add(resolve(target));
    const content = await readFile(source);
    if (checking) {
      let current;
      try {
        current = await readFile(target);
      } catch {
        throw new Error(`Missing generated Vue declaration artifact ${target}.`);
      }
      if (!current.equals(content)) throw new Error(`Stale generated Vue declaration artifact ${target}.`);
    } else {
      await mkdir(dirname(target), { recursive: true });
      await writeFile(target, content);
    }
  }
  inventory.push({
    name,
    version: metadata.version,
    files: files.map((path) => relative(packageRoot, path).split(sep).join("/")),
    sha256: createHash("sha256")
      .update(Buffer.concat(await Promise.all(files.map((path) => readFile(path)))))
      .digest("hex"),
  });
}

const inventoryPath = resolve(outputRoot, "../inventory.json");
expectedTargets.add(inventoryPath);
const inventoryText = `${JSON.stringify({ vue: expectedVueVersion, packages: inventory }, null, 2)}\n`;
if (checking) {
  if ((await readFile(inventoryPath, "utf8")) !== inventoryText)
    throw new Error(`Stale generated Vue declaration inventory ${inventoryPath}.`);
} else {
  await mkdir(dirname(inventoryPath), { recursive: true });
  await writeFile(inventoryPath, inventoryText);
}

const actualTargets = [];
async function collect(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) await collect(path);
    else actualTargets.push(resolve(path));
  }
}
await collect(resolve(outputRoot, ".."));
const extras = actualTargets.filter((path) => !expectedTargets.has(path));
if (extras.length > 0) throw new Error(`Unexpected stale Vue declaration artifacts: ${extras.join(", ")}.`);
