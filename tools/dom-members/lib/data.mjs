// Loads the inputs the table is built from: the merged web platform IDL, the
// HTML element-to-interface map, and every pinned copy of MDN's browser
// compatibility data (BCD).

import { readFile } from "node:fs/promises";
import path from "node:path";

/** Element lists from @webref/elements in the HTML namespace. */
const HTML_ELEMENT_FILES = new Set([
  "fenced-frame",
  "geolocation-element",
  "html",
  "html-ruby-extensions",
  "install-element",
  "mediacapture-extensions",
  "model-element",
  "portals",
]);

/**
 * Element lists from @webref/elements in other namespaces (SVG, MathML).
 *
 * Every list must be in one of the two sets, so a new file stops the
 * generator until someone decides which namespace it belongs to. Treating an
 * SVG list as HTML would give its tags HTML answers.
 */
const NON_HTML_ELEMENT_FILES = new Set([
  "SVG11",
  "SVG2",
  "css-masking-1",
  "filter-effects-1",
  "mathml-core",
  "svg-animations",
  "svg-paths",
]);

/**
 * Obsolete elements a browser still gives an interface other than
 * HTMLUnknownElement, which no @webref/elements list names (HTML Standard, "Obsolete features").
 *
 * Without this, a template's `<marquee loop="2">` would be measured as an
 * unknown element, and `loop` would look like a plain attribute.
 */
export const OBSOLETE_ELEMENTS = {
  dir: "HTMLDirectoryElement",
  font: "HTMLFontElement",
  frame: "HTMLFrameElement",
  frameset: "HTMLFrameSetElement",
  listing: "HTMLPreElement",
  marquee: "HTMLMarqueeElement",
  param: "HTMLParamElement",
  xmp: "HTMLPreElement",
};

/**
 * HTML interfaces that belong to no tag, or only to tags listed above.
 *
 * Every `HTML*Element` interface in the IDL must be reachable from a tag or be
 * named here, so a new element interface stops the generator until someone
 * maps it.
 */
export const INTERFACES_WITHOUT_TAG = new Set(["HTMLElement", "HTMLUnknownElement"]);

/** The latest BCD release; older copies are the `bcd-YYYY` aliases. */
const BCD_LATEST = "@mdn/browser-compat-data";

/**
 * How far apart two neighbouring BCD copies may be. MDN may delete a feature
 * two years after every browser removed it, and each copy still lists what
 * was removed up to two years before its own date.
 */
const MAX_COPY_GAP_DAYS = 2 * 365 + 1;

/** Extended attributes that start with "Reflect" and that the generator knows. */
const KNOWN_REFLECT_MARKERS = new Set([
  "Reflect",
  "ReflectDefault",
  "ReflectNonNegative",
  "ReflectPositive",
  "ReflectPositiveWithFallback",
  "ReflectRange",
  "ReflectSetter",
  "ReflectURL",
]);

export async function loadData(require) {
  // Check the installed packages first, so a missing or stale install is
  // reported by name before anything tries to load it.
  const { bcdPackages, versions } = await checkInstalled();
  const webidl2 = require("webidl2");
  const idlPackage = require.resolve("@webref/idl/package.json");
  const idlDirectory = path.dirname(idlPackage);
  const { listAll: listIdl } = require("@webref/idl");
  const idlFiles = await listIdl();
  const idl = {
    interfaces: new Map(),
    mixins: new Map(),
    includes: new Map(),
  };
  for (const [shortname, file] of Object.entries(idlFiles).sort(([a], [b]) => byteOrder(a, b))) {
    let ast;
    try {
      ast = webidl2.parse(await readFile(path.join(idlDirectory, `${shortname}.idl`), "utf8"));
    } catch (error) {
      // A skipped file could hide members, so a file that does not parse
      // stops the generator rather than shrinking the table.
      throw new Error(`could not parse ${file.filename}: ${error.message}`);
    }
    for (const definition of ast) {
      mergeDefinition(idl, definition);
    }
  }

  const { listAll: listElements } = require("@webref/elements");
  const elementLists = await listElements();
  const elements = new Map();
  for (const [shortname, list] of Object.entries(elementLists).sort(([a], [b]) => byteOrder(a, b))) {
    if (NON_HTML_ELEMENT_FILES.has(shortname)) {
      continue;
    }
    if (!HTML_ELEMENT_FILES.has(shortname)) {
      throw new Error(
        `@webref/elements has a new list, ${shortname}; add it to HTML_ELEMENT_FILES or NON_HTML_ELEMENT_FILES`,
      );
    }
    for (const element of list.elements) {
      if (!element.interface) {
        throw new Error(`element <${element.name}> in ${shortname} has no interface`);
      }
      if (elements.has(element.name) && elements.get(element.name) !== element.interface) {
        throw new Error(`element <${element.name}> has two interfaces`);
      }
      elements.set(element.name, element.interface);
    }
  }
  for (const [tag, name] of Object.entries(OBSOLETE_ELEMENTS)) {
    if (!elements.has(tag)) {
      elements.set(tag, name);
    }
  }
  for (const [tag, name] of elements) {
    if (!idl.interfaces.has(name)) {
      throw new Error(`element <${tag}> maps to ${name}, which the IDL does not define`);
    }
  }
  const mapped = new Set(elements.values());
  // An interface others inherit from, such as HTMLMediaElement, is shared by
  // its subclasses and needs no tag of its own.
  const inherited = new Set([...idl.interfaces.values()].map((entry) => entry.inherits));
  for (const name of idl.interfaces.keys()) {
    if (
      /^HTML\w*Element$/.test(name) &&
      !mapped.has(name) &&
      !inherited.has(name) &&
      !INTERFACES_WITHOUT_TAG.has(name)
    ) {
      throw new Error(`${name} belongs to no element; map it in OBSOLETE_ELEMENTS or INTERFACES_WITHOUT_TAG`);
    }
  }

  const bcd = bcdPackages.map((name) => require(name));
  checkCopyGaps(bcdPackages, bcd);
  return { idl, elements, bcd, versions };
}

/**
 * The BCD packages to read, newest first, and the version of every input,
 * after checking each is installed at the version package.json pins.
 */
async function checkInstalled() {
  const manifest = JSON.parse(await readFile(new URL("../package.json", import.meta.url), "utf8"));
  const pins = manifest.devDependencies;
  // The older copies are read from package.json, so a copy that `refresh`
  // adds is used without a code change.
  const copies = Object.keys(pins)
    .filter((name) => /^bcd-\d{4}$/.test(name))
    .sort((a, b) => byteOrder(b, a));
  const bcdPackages = [BCD_LATEST, ...copies];
  const versions = {};
  for (const name of ["@vue/runtime-dom", "@webref/idl", "@webref/elements", "webidl2", ...bcdPackages]) {
    // Read the installed manifest directly: some packages do not export it.
    const installed = new URL(`../node_modules/${name}/package.json`, import.meta.url);
    let version;
    try {
      version = JSON.parse(await readFile(installed, "utf8")).version;
    } catch {
      throw new Error(`${name} is not installed; run \`pnpm --dir tools/dom-members install\``);
    }
    const pinned = pins[name].replace(/^npm:@mdn\/browser-compat-data@/, "");
    if (version !== pinned) {
      // A stale install would build a table that does not match the lockfile.
      throw new Error(`${name} is installed at ${version} but package.json pins ${pinned}; reinstall`);
    }
    versions[name] = version;
  }
  return { bcdPackages, versions };
}

/** Fail when two neighbouring BCD copies are more than two years apart. */
export function checkCopyGaps(names, copies) {
  for (let index = 1; index < copies.length; index += 1) {
    const newer = Date.parse(copies[index - 1].__meta?.timestamp);
    const older = Date.parse(copies[index].__meta?.timestamp);
    if (Number.isNaN(newer) || Number.isNaN(older)) {
      throw new Error(`${names[index - 1]} or ${names[index]} has no release date in __meta.timestamp`);
    }
    if (newer < older) {
      // The aliases are ordered by name, so a misnamed copy shows up here.
      throw new Error(`${names[index]} is newer than ${names[index - 1]}; check the bcd-YYYY alias names`);
    }
    const days = (newer - older) / (1000 * 60 * 60 * 24);
    if (days > MAX_COPY_GAP_DAYS) {
      throw new Error(
        `${names[index - 1]} and ${names[index]} are ${Math.round(days)} days apart, ` +
          "more than two years; run `pnpm --dir tools/dom-members run refresh` to add a copy between them",
      );
    }
  }
}

function byteOrder(left, right) {
  return left < right ? -1 : left > right ? 1 : 0;
}

/**
 * Add one IDL definition, merging partial definitions into the whole.
 * Exported so the tests can feed it IDL text.
 */
export function mergeDefinition(idl, definition) {
  if (definition.type === "includes") {
    const list = idl.includes.get(definition.target) ?? [];
    list.push(definition.includes);
    idl.includes.set(definition.target, list);
    return;
  }
  if (definition.type === "interface" || definition.type === "interface mixin") {
    const table = definition.type === "interface" ? idl.interfaces : idl.mixins;
    const entry = table.get(definition.name) ?? { inherits: null, members: [], extAttrs: [] };
    if (!definition.partial) {
      entry.inherits = definition.inheritance ?? null;
    }
    entry.extAttrs.push(...definition.extAttrs.map((attribute) => attribute.name));
    for (const member of definition.members) {
      entry.members.push(...describeMember(member));
    }
    table.set(definition.name, entry);
  }
}

/** The instance members one IDL member puts on an object, by name. */
function describeMember(member) {
  const extAttrs = member.extAttrs ?? [];
  if (member.special === "static" || member.type === "constructor" || member.type === "const") {
    // Static members live on the interface object, and constants are upper
    // case, so neither is ever a lowercase key on an element.
    return [];
  }
  if (member.type === "attribute") {
    return [
      {
        name: member.name,
        kind: "attribute",
        type: member.idlType.idlType,
        stringLike: isStringLike(member.idlType),
        nullable: member.idlType.nullable,
        readonly: member.readonly,
        reflect: reflectMarker(member.name, extAttrs),
        extAttrs: extAttrs.map((attribute) => attribute.name),
      },
    ];
  }
  if (member.type === "operation") {
    return member.name ? [{ name: member.name, kind: "operation" }] : [];
  }
  if (member.type === "iterable" || member.type === "maplike" || member.type === "setlike") {
    // These declarations add methods with fixed names to every instance.
    const names = ["entries", "forEach", "keys", "values"];
    if (member.type !== "iterable") {
      names.push("has", "size");
      if (!member.readonly) {
        names.push("clear", "delete", member.type === "maplike" ? "set" : "add");
      }
      if (member.type === "maplike") {
        names.push("get");
      }
    }
    return names.map((name) => ({ name, kind: "operation" }));
  }
  return [];
}

/**
 * Whether a value of this type is a string: `DOMString`, `USVString`, or a
 * union of those with Trusted Types (`(TrustedScriptURL or USVString)`).
 * Without Trusted Types enforced, a page passes plain strings, and with them
 * enforced, setting the property and calling `setAttribute` are both blocked,
 * so neither leaves the attribute.
 */
function isStringLike(idlType) {
  if (idlType.union) {
    return idlType.idlType.every(
      (part) => isStringLike(part) || /^Trusted[A-Za-z]+$/.test(part.idlType),
    );
  }
  return idlType.idlType === "DOMString" || idlType.idlType === "USVString";
}

/**
 * Whether the IDL marks an attribute as mirroring the content attribute of
 * the same name, and with which marker.
 */
function reflectMarker(name, extAttrs) {
  // A new marker could mean a new kind of mirroring, so a member with one
  // counts as not mirroring, and is Unknown until someone reviews it.
  const unknown = extAttrs.find(
    (attribute) => attribute.name.startsWith("Reflect") && !KNOWN_REFLECT_MARKERS.has(attribute.name),
  );
  if (unknown) {
    process.stderr.write(`warning: ${name} has an unknown marker [${unknown.name}]\n`);
    return null;
  }
  for (const attribute of extAttrs) {
    if (attribute.name === "Reflect") {
      // `[Reflect="other"]` mirrors a differently named attribute.
      const value = attribute.rhs?.value;
      const target = typeof value === "string" ? value.replace(/^"|"$/g, "") : null;
      if (target === null || target === name.toLowerCase()) {
        return "Reflect";
      }
      return null;
    }
    if (attribute.name === "ReflectSetter" || attribute.name === "ReflectURL") {
      return attribute.name;
    }
  }
  return null;
}
