// Updates the data the table is built from, then regenerates the table.
//
// Run it when Citry upgrades Vue (the validator in
// scripts/validators/generated_copies.py fails until the table names the new
// Vue version), or whenever the browser data should be brought up to date:
//
//   pnpm --dir tools/dom-members run refresh
//
// It updates the IDL, element and browser-data packages to their latest
// releases, pins `@vue/runtime-dom` to the version `citry-client` uses, and
// adds an older copy of the browser data when one is due (see below). The old
// copies themselves are never updated.

import { execFileSync } from "node:child_process";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const BCD = "@mdn/browser-compat-data";

// MDN may delete a feature two years after every browser removed it. Each
// pinned copy still lists what was removed up to two years before its date,
// so the copies must stay at most two years apart. A new copy is added when
// the newest one is more than 18 months older than the latest release, which
// leaves room before the gap reaches two years.
const ADD_COPY_AFTER_MONTHS = 18;
const MAX_GAP_MONTHS = 24;

function run(command, args) {
  return execFileSync(command, args, { cwd: here, encoding: "utf8", stdio: ["ignore", "pipe", "inherit"] });
}

function releaseDates() {
  return JSON.parse(run("npm", ["view", BCD, "time", "--json"]));
}

function monthsBetween(earlier, later) {
  return (new Date(later) - new Date(earlier)) / (1000 * 60 * 60 * 24 * 30.44);
}

async function main() {
  const manifest = JSON.parse(await readFile(path.join(here, "package.json"), "utf8"));
  const vue = JSON.parse(
    await readFile(path.join(here, "../../packages/js/citry-client/package.json"), "utf8"),
  ).dependencies.vue;

  // The copies are the `bcd-YYYY` aliases, newest first.
  const copies = Object.entries(manifest.devDependencies)
    .filter(([name]) => /^bcd-\d{4}$/.test(name))
    .map(([name, spec]) => ({ name, version: spec.replace(`npm:${BCD}@`, "") }))
    .sort((a, b) => (a.name < b.name ? 1 : a.name > b.name ? -1 : 0));
  const dates = releaseDates();
  const versions = Object.keys(dates).filter((version) => /^\d+\.\d+\.\d+$/.test(version));
  const latest = versions.reduce((best, version) => (dates[version] > dates[best] ? version : best));

  const updates = [
    "@webref/idl@latest",
    "@webref/elements@latest",
    "webidl2@latest",
    `${BCD}@${latest}`,
    `@vue/runtime-dom@${vue}`,
  ];
  const newest = copies[0];
  if (newest && monthsBetween(dates[newest.version], dates[latest]) > ADD_COPY_AFTER_MONTHS) {
    // Pin the newest release that is still within two years of the newest
    // copy, so no gap between neighbouring copies exceeds two years.
    const candidates = versions.filter(
      (version) =>
        dates[version] > dates[newest.version] &&
        monthsBetween(dates[newest.version], dates[version]) <= MAX_GAP_MONTHS,
    );
    if (candidates.length === 0) {
      throw new Error(`no ${BCD} release within two years of ${newest.name} (${newest.version})`);
    }
    const pick = candidates.reduce((best, version) => (dates[version] > dates[best] ? version : best));
    const alias = `bcd-${dates[pick].slice(0, 4)}`;
    if (copies.some((copy) => copy.name === alias)) {
      throw new Error(`a copy named ${alias} already exists; rename one before adding ${pick}`);
    }
    updates.push(`${alias}@npm:${BCD}@${pick}`);
    process.stdout.write(`adding ${alias} (${BCD} ${pick}, ${dates[pick].slice(0, 10)})\n`);
  }

  // Exact versions keep the lockfile, and so the generated table, repeatable.
  run("pnpm", ["add", "--save-dev", "--save-exact", ...updates]);
  try {
    run("node", ["generate.mjs", "--unclassified"]);
  } catch (error) {
    // A list on stdout means new members need a review before the table can
    // be generated; any other failure (a gap between copies, a stale
    // install) is reported as it is.
    if (error.stdout) {
      throw new Error(`unreviewed string members; add each to lib/reviewed.mjs:\n${error.stdout}`);
    }
    throw error;
  }
  run("node", ["generate.mjs"]);
  process.stdout.write("Regenerated crates/citry_vue_compiler/src/dom_members.rs\n");
}

main().catch((error) => {
  process.stderr.write(`${error.stack ?? error}\n`);
  process.exitCode = 1;
});
