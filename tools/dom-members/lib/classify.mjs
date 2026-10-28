// Decides, for every HTML element and lowercase name, which attribute text
// Vue's first client render leaves:
//
// - WritesText: in every supported browser the name is either no member of
//   the element, or a member that mirrors the same-named attribute as a
//   string. Vue's two paths then leave the same text.
// - ReflectBoolean: every supported browser has it as a property that mirrors
//   a boolean attribute, so the attribute is present or absent.
// - Unknown: anything else, or any doubt. The server declines such a name.

import { INTERFACES_WITHOUT_TAG } from "./data.mjs";
import {
  NOT_MIRRORING,
  PRESENCE_ONLY_BOOLEANS,
  PROSE_MIRRORING,
  SUPPORTED_AT_FLOOR,
  UNRECORDED_MEMBERS,
} from "./reviewed.mjs";

/**
 * The oldest browser versions Citry supports. The client already needs them,
 * because it calls `structuredClone` (decided for #346).
 */
export const FLOOR = {
  chrome: "98",
  chrome_android: "98",
  firefox: "94",
  firefox_android: "94",
  safari: "15.4",
  safari_ios: "15.4",
};

/** Tags whose members no table can know, so every name is Unknown. */
export const ALL_UNKNOWN_TAGS = ["embed", "object"];

const UNKNOWN_ELEMENT = "HTMLUnknownElement";

/** Whether the server ever asks the table about this name. */
export function isTableName(name) {
  return /^[a-z][a-z0-9]*$/.test(name);
}

export function classify(data) {
  assertAllClassified(data);
  const base = answersFor(data, UNKNOWN_ELEMENT);
  // A name some browser has that no data records cannot be predicted, so
  // it is Unknown on BASE and, below, on every element.
  for (const name of UNRECORDED_MEMBERS) {
    base[name] = "Unknown";
  }
  const elements = {};
  for (const [tag, name] of [...data.elements].sort(([a], [b]) => byteOrder(a, b))) {
    if (ALL_UNKNOWN_TAGS.includes(tag)) {
      continue;
    }
    let answers = answersFor(data, name);
    // Without this, the element's own chain would answer WritesText for the
    // name and the comparison below would write that over BASE's Unknown.
    for (const unrecorded of UNRECORDED_MEMBERS) {
      answers[unrecorded] = "Unknown";
    }
    // A browser at the floor that lacks this element's interface gives the
    // tag the unknown-element chain, so a name has to agree under both,
    // unless the attribute is listed in PRESENCE_ONLY_BOOLEANS.
    if (!supportedAtFloor(lookupCompat(data.bcd, name, null))) {
      answers = combineAnswers(answers, base, (key) => PRESENCE_ONLY_BOOLEANS.has(`${name}.${key}`));
    }
    const differences = {};
    for (const key of new Set([...Object.keys(answers), ...Object.keys(base)])) {
      const answer = answers[key] ?? "WritesText";
      if (answer !== (base[key] ?? "WritesText")) {
        differences[key] = answer;
      }
    }
    elements[tag] = sortObject(differences);
  }
  return {
    floor: FLOOR,
    allUnknownTags: ALL_UNKNOWN_TAGS,
    base: sortObject(base),
    elements,
  };
}

/** The non-WritesText answers for every lowercase name on one interface's chain. */
function answersFor(data, interfaceName) {
  const chain = interfaceChain(data.idl, interfaceName);
  const occurrences = new Map();
  const add = (name, occurrence) => {
    if (!isTableName(name)) {
      return;
    }
    const list = occurrences.get(name) ?? [];
    list.push(occurrence);
    occurrences.set(name, list);
  };
  for (const { owner, hosts, members } of chain.memberSets) {
    for (const member of members) {
      add(member.name, { member, owner, hosts });
    }
  }
  // Members BCD records that the IDL does not define: non-standard ones, and
  // ones a newer IDL dropped. Their behavior is unknown, so they count as
  // members that do not mirror an attribute.
  for (const interfaceOnChain of chain.interfaces) {
    for (const api of data.bcd.map((copy) => copy.api)) {
      for (const [key, feature] of Object.entries(api[interfaceOnChain] ?? {})) {
        if (key === "__compat") {
          continue;
        }
        if (!occurrences.get(key)?.some((item) => item.member)) {
          add(key, { bcdOnly: true, owner: interfaceOnChain, key });
        }
        // An older or prefixed spelling exists only in the browser versions
        // whose statements name it, so it carries its own support data.
        // An older spelling of a member that mirrors a string attribute
        // (Chrome 101's `fetchpriority` for `fetchPriority`) is the same
        // member, so it mirrors the same attribute.
        const standard = chain.memberSets
          .flatMap((set) => set.members.map((member) => ({ member, owner: set.owner })))
          .find((item) => item.member.name === key);
        const mirrorsAttribute = standard !== undefined && occurrenceKind(standard) === "string-mirror";
        for (const alternative of alternativeNames(key, feature.__compat)) {
          if (!occurrences.get(alternative)?.some((item) => item.member)) {
            // Only the spelling that is the attribute's own name mirrors it.
            const mirrors = mirrorsAttribute && alternative === key.toLowerCase();
            add(alternative, { bcdOnly: true, owner: interfaceOnChain, key, alternative, mirrors });
          }
        }
      }
    }
  }
  const answers = {};
  for (const [name, list] of occurrences) {
    // The server treats every `on*` name as Unknown itself, including the
    // handler properties no data records (Chrome's `onsearch`), so the
    // table leaves them out.
    if (name.startsWith("on")) {
      continue;
    }
    const answer = decide(data, name, list, chain.interfaces);
    if (answer !== "WritesText") {
      answers[name] = answer;
    }
  }
  return answers;
}

/** One name's answer from every place it appears on the chain. */
function decide(data, name, occurrences, interfaces) {
  let booleanMirror = false;
  for (const occurrence of occurrences) {
    const kind = occurrenceKind(occurrence);
    // A member can move between interfaces over time, as `autofocus` moved
    // from each form control to HTMLElement, so its support is read from
    // every interface on the chain that records it.
    let compat = occurrence.member
      ? chainCompat(data.bcd, [...occurrence.hosts, ...interfaces], name)
      : chainCompat(data.bcd, [occurrence.owner], occurrence.key);
    if (occurrence.alternative && compat !== null) {
      compat = onlyStatementsNaming(compat, occurrence.key, occurrence.alternative);
    }
    if (kind === "string-mirror") {
      // Either path leaves the same text, whichever browsers have it.
      continue;
    }
    if (compat === null) {
      // An IDL member with no browser data may ship somewhere, so it is not
      // safe to call absent.
      return "Unknown";
    }
    if (!presentAfterFloor(compat)) {
      continue;
    }
    const reviewedSupport = interfaces.some(
      (owner) =>
        SUPPORTED_AT_FLOOR.has(`${owner}.${name}`) || PRESENCE_ONLY_BOOLEANS.has(`${owner}.${name}`),
    );
    if (kind === "boolean-mirror" && (reviewedSupport || supportedAtFloor(compat))) {
      booleanMirror = true;
      continue;
    }
    return "Unknown";
  }
  return booleanMirror ? "ReflectBoolean" : "WritesText";
}

function occurrenceKind({ member, owner, mirrors }) {
  if (mirrors) {
    return "string-mirror";
  }
  if (!member || member.kind !== "attribute" || member.readonly) {
    return "other";
  }
  if (member.stringLike) {
    if (member.reflect || PROSE_MIRRORING.has(`${owner}.${member.name}`)) {
      return "string-mirror";
    }
    return "other";
  }
  if (member.type === "boolean" && member.reflect === "Reflect") {
    return "boolean-mirror";
  }
  return "other";
}

/**
 * Every settable lowercase string attribute without a reflection marker that
 * neither reviewed list classifies. The generator refuses to run until each
 * one is reviewed, so nothing falls to an answer by accident.
 */
export function collectUnclassified(data) {
  const found = new Set();
  const interfaces = [...data.idl.interfaces.keys(), ...data.idl.mixins.keys()];
  for (const owner of interfaces) {
    const entry = data.idl.interfaces.get(owner) ?? data.idl.mixins.get(owner);
    for (const member of entry.members) {
      if (
        member.kind === "attribute" &&
        !member.readonly &&
        isTableName(member.name) &&
        member.stringLike &&
        !member.reflect
      ) {
        const id = `${owner}.${member.name}`;
        if (!PROSE_MIRRORING.has(id) && !NOT_MIRRORING.has(id) && onAnyElementChain(data, id)) {
          found.add(id);
        }
      }
    }
  }
  return [...found].sort();
}

function assertAllClassified(data) {
  const missing = collectUnclassified(data);
  if (missing.length > 0) {
    throw new Error(
      `unreviewed string members: ${missing.join(", ")}. ` +
        "Add each to PROSE_MIRRORING or NOT_MIRRORING in lib/reviewed.mjs.",
    );
  }
}

function onAnyElementChain(data, id) {
  const owner = id.slice(0, id.indexOf("."));
  for (const name of new Set([...data.elements.values(), ...INTERFACES_WITHOUT_TAG])) {
    if (interfaceChain(data.idl, name).memberSets.some((set) => set.owner === owner)) {
      return true;
    }
  }
  return false;
}

/**
 * The interfaces and member sets an instance of `name` sees: the interface,
 * each one it inherits from, and the mixins each of them includes.
 *
 * `hosts` lists the interfaces a mixin's members appear on, because BCD
 * records a mixin member under the interface that includes it.
 */
export function interfaceChain(idl, name) {
  const interfaces = [];
  const memberSets = [];
  let current = name;
  while (current) {
    const entry = idl.interfaces.get(current);
    if (!entry) {
      throw new Error(`the IDL does not define ${current}`);
    }
    interfaces.push(current);
    memberSets.push({ owner: current, hosts: [current], members: entry.members });
    for (const mixin of idl.includes.get(current) ?? []) {
      const mixinEntry = idl.mixins.get(mixin);
      if (!mixinEntry) {
        throw new Error(`${current} includes ${mixin}, which the IDL does not define`);
      }
      memberSets.push({ owner: mixin, hosts: [current], members: mixinEntry.members });
    }
    current = entry.inherits;
  }
  // `Object.prototype` members are visible through `in` on every element.
  memberSets.push({
    owner: "Object",
    hosts: [],
    members: [{ name: "constructor", kind: "operation" }],
  });
  return { interfaces, memberSets };
}

/**
 * The support data every listed interface records for a member, each from
 * the newest copy that has it, or null when none records it.
 */
function chainCompat(bcd, hosts, member) {
  const found = [];
  for (const host of new Set(hosts)) {
    const support = lookupCompat(bcd, host, member);
    if (support !== null) {
      found.push(support);
    }
  }
  return found.length === 0 ? null : found;
}

/**
 * The newest BCD support data for a member, or for the interface itself when
 * `member` is null. Null when no copy records it.
 */
function lookupCompat(bcd, hosts, member) {
  const names = Array.isArray(hosts) ? hosts : [hosts];
  for (const copy of bcd) {
    for (const host of names) {
      const feature = member === null ? copy.api[host] : copy.api[host]?.[member];
      if (feature?.__compat) {
        return feature.__compat.support;
      }
    }
  }
  return null;
}

/** Keep only the support statements that use one alternative spelling. */
function onlyStatementsNaming(support, key, alternative) {
  return [support].flat().map((entry) =>
    Object.fromEntries(
      Object.entries(entry).map(([browser, statements]) => [
        browser,
        [statements].flat().filter((statement) => spellings(key, statement).includes(alternative)),
      ]),
    ),
  );
}

function spellings(key, statement) {
  const names = [];
  if (statement.alternative_name) {
    names.push(statement.alternative_name);
  }
  if (statement.prefix) {
    names.push(statement.prefix + key[0].toUpperCase() + key.slice(1), statement.prefix + key);
  }
  return names;
}

function alternativeNames(key, compat) {
  const names = new Set();
  for (const statements of Object.values(compat?.support ?? {})) {
    for (const statement of [statements].flat()) {
      for (const name of spellings(key, statement)) {
        names.add(name);
      }
    }
  }
  return [...names];
}

/**
 * Whether some supported browser has the feature at or after the floor.
 *
 * `support` is one BCD support object, or a list of them for the same member
 * on several interfaces.
 */
export function presentAfterFloor(support) {
  if (support === null) {
    return true;
  }
  return Object.keys(FLOOR).some((browser) =>
    statementsFor(support, browser).some((statement) => {
      if (statement.flags) {
        return false;
      }
      const added = readVersion(statement.version_added);
      if (added === null) {
        return false;
      }
      const removed = statement.version_removed;
      if (removed === undefined || removed === true || removed === null) {
        // `true` means "removed at an unknown version", which could be after
        // the floor, so it still counts as present.
        return true;
      }
      const removedVersion = readVersion(removed);
      return removedVersion === null || compareVersions(removedVersion, FLOOR[browser]) > 0;
    }),
  );
}

/** Whether every supported browser has had the feature, unprefixed, since the floor. */
export function supportedAtFloor(support) {
  if (support === null) {
    return false;
  }
  return Object.entries(FLOOR).every(([browser, floor]) =>
    statementsFor(support, browser).some((statement) => {
      if (statement.flags || statement.prefix || statement.alternative_name) {
        return false;
      }
      if (statement.partial_implementation || statement.version_removed !== undefined) {
        return false;
      }
      const added = readVersion(statement.version_added);
      return added !== null && added !== "unknown" && compareVersions(added, floor) <= 0;
    }),
  );
}

/** Every support statement for one browser, across one or several support objects. */
function statementsFor(support, browser) {
  return [support].flat().flatMap((entry) => [entry[browser] ?? []].flat());
}

/** A BCD version as a comparable string, "unknown" for `true`, or null for none. */
export function readVersion(value) {
  if (value === true) {
    return "unknown";
  }
  if (typeof value !== "string" || value === "preview") {
    return null;
  }
  return value.replace(/^≤/, "");
}

export function compareVersions(left, right) {
  if (left === "unknown" || right === "unknown") {
    return 0;
  }
  const a = left.split(".").map(Number);
  const b = right.split(".").map(Number);
  for (let index = 0; index < Math.max(a.length, b.length); index += 1) {
    const difference = (a[index] ?? 0) - (b[index] ?? 0);
    if (difference !== 0) {
      return difference;
    }
  }
  return 0;
}

function combineAnswers(own, base, keepBoolean = () => false) {
  const combined = {};
  for (const key of new Set([...Object.keys(own), ...Object.keys(base)])) {
    const left = own[key] ?? "WritesText";
    const right = base[key] ?? "WritesText";
    // A listed boolean keeps the element's answer (see
    // PRESENCE_ONLY_BOOLEANS).
    const keep = left === "ReflectBoolean" && right === "WritesText" && keepBoolean(key);
    const answer = left === right || keep ? left : "Unknown";
    if (answer !== "WritesText") {
      combined[key] = answer;
    }
  }
  return combined;
}

/**
 * Sort keys by code unit, the order Rust's `str` comparison uses, because the
 * server looks names up with a binary search.
 */
function sortObject(object) {
  return Object.fromEntries(Object.entries(object).sort(([a], [b]) => byteOrder(a, b)));
}

function byteOrder(left, right) {
  return left < right ? -1 : left > right ? 1 : 0;
}
