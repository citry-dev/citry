// Tests for the pure parts of the generator (lib/classify.mjs) against small
// hand-built inputs. They run without the data packages: no IDL, element
// list or browser data is read from node_modules.
//
// The reviewed lists in lib/reviewed.mjs are module constants, so every
// member name below is made up (`zz...`) and cannot meet an entry on them.
// The exception is `Element.id`, which the unreviewed-member test uses on
// purpose because the PROSE_MIRRORING list names it. UNRECORDED_MEMBERS
// (`cue`, `cuebackground`) is Unknown in every classified table, whatever the
// input, and one test checks that.

import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { describe, it, mock } from "node:test";

import {
  FLOOR,
  classify,
  collectUnclassified,
  compareVersions,
  presentAfterFloor,
  readVersion,
  supportedAtFloor,
} from "../lib/classify.mjs";
import { checkCopyGaps, mergeDefinition } from "../lib/data.mjs";

// webidl2 is the parser `loadData` uses; the tests feed it IDL text so the
// members come out exactly as the generator builds them.
const webidl2 = createRequire(import.meta.url)("webidl2");

const BROWSERS = Object.keys(FLOOR);

/** A support object that gives every supported browser the same statement. */
function everywhere(statement) {
  return Object.fromEntries(BROWSERS.map((browser) => [browser, statement]));
}

/** A support object with a plain statement at each browser's floor version. */
function atFloor() {
  return Object.fromEntries(
    BROWSERS.map((browser) => [browser, { version_added: FLOOR[browser] }]),
  );
}

describe("readVersion", () => {
  it("returns a version string as it is", () => {
    assert.equal(readVersion("98"), "98");
    assert.equal(readVersion("15.4"), "15.4");
  });

  it("drops the 'at most' marker, keeping the bound", () => {
    assert.equal(readVersion("≤18"), "18");
  });

  it("reads true as an unknown version", () => {
    assert.equal(readVersion(true), "unknown");
  });

  it("reads false, null and preview as never shipped", () => {
    assert.equal(readVersion(false), null);
    assert.equal(readVersion(null), null);
    assert.equal(readVersion("preview"), null);
  });
});

describe("compareVersions", () => {
  it("compares dotted parts as numbers, not text", () => {
    assert.ok(compareVersions("100", "99") > 0);
    assert.ok(compareVersions("15.4", "15.10") < 0);
    assert.ok(compareVersions("15.5", "15.4") > 0);
  });

  it("treats a missing part as zero", () => {
    assert.equal(compareVersions("98", "98.0"), 0);
    assert.equal(compareVersions("98", "98"), 0);
  });

  it("calls an unknown version equal to anything", () => {
    assert.equal(compareVersions("unknown", "98"), 0);
    assert.equal(compareVersions("1", "unknown"), 0);
  });
});

describe("presentAfterFloor", () => {
  it("treats a member with no data as possibly present", () => {
    assert.equal(presentAfterFloor(null), true);
  });

  it("finds a member one browser added after the floor", () => {
    assert.equal(presentAfterFloor({ chrome: { version_added: "120" } }), true);
  });

  it("finds a member present at the floor", () => {
    assert.equal(presentAfterFloor(atFloor()), true);
  });

  it("finds nothing in a member that never shipped", () => {
    assert.equal(presentAfterFloor(everywhere({ version_added: false })), false);
    assert.equal(presentAfterFloor(everywhere({ version_added: "preview" })), false);
    assert.equal(presentAfterFloor({}), false);
  });

  it("finds nothing in a member removed before the floor", () => {
    const support = { chrome: { version_added: "50", version_removed: "90" } };
    assert.equal(presentAfterFloor(support), false);
    // The 'at most' marker keeps its bound.
    assert.equal(
      presentAfterFloor({ chrome: { version_added: "50", version_removed: "≤80" } }),
      false,
    );
  });

  it("finds a member removed after the floor", () => {
    const support = { chrome: { version_added: "50", version_removed: "120" } };
    assert.equal(presentAfterFloor(support), true);
  });

  it("counts a member removed at an unknown version as present", () => {
    const support = { chrome: { version_added: "50", version_removed: true } };
    assert.equal(presentAfterFloor(support), true);
  });

  it("ignores support behind a flag", () => {
    const support = { chrome: { version_added: "99", flags: [{ type: "preference", name: "x" }] } };
    assert.equal(presentAfterFloor(support), false);
  });

  it("counts a partial implementation as present", () => {
    const support = { chrome: { version_added: "99", partial_implementation: true } };
    assert.equal(presentAfterFloor(support), true);
  });

  it("looks through every statement in an array", () => {
    const flagged = { version_added: "99", flags: [{ type: "preference", name: "x" }] };
    assert.equal(
      presentAfterFloor({ chrome: [flagged, { version_added: false }] }),
      false,
    );
    assert.equal(
      presentAfterFloor({ chrome: [flagged, { version_added: "110" }] }),
      true,
    );
  });

  it("looks through a list of support objects for one member on two interfaces", () => {
    const gone = { chrome: { version_added: "50", version_removed: "90" } };
    const later = { firefox: { version_added: "120" } };
    assert.equal(presentAfterFloor([gone]), false);
    assert.equal(presentAfterFloor([gone, later]), true);
  });

  it("ignores a browser the floor does not list", () => {
    assert.equal(presentAfterFloor({ opera: { version_added: "10" } }), false);
  });
});

describe("supportedAtFloor", () => {
  it("is false without data", () => {
    assert.equal(supportedAtFloor(null), false);
  });

  it("accepts support from the floor version in every browser", () => {
    assert.equal(supportedAtFloor(atFloor()), true);
    // The 'at most' marker still bounds the version below the floor.
    assert.equal(supportedAtFloor(everywhere({ version_added: "≤10" })), true);
  });

  it("rejects one browser that added the member after the floor", () => {
    const support = atFloor();
    support.safari = { version_added: "15.5" };
    assert.equal(supportedAtFloor(support), false);
  });

  it("rejects a browser with no statement", () => {
    const support = atFloor();
    delete support.firefox_android;
    assert.equal(supportedAtFloor(support), false);
  });

  it("rejects an unknown or missing version", () => {
    assert.equal(supportedAtFloor(everywhere({ version_added: true })), false);
    assert.equal(supportedAtFloor(everywhere({ version_added: false })), false);
  });

  it("rejects a member removed at any version", () => {
    const support = atFloor();
    support.chrome = { version_added: "50", version_removed: "200" };
    assert.equal(supportedAtFloor(support), false);
    support.chrome = { version_added: "50", version_removed: true };
    assert.equal(supportedAtFloor(support), false);
  });

  it("rejects flagged, prefixed, renamed and partial support", () => {
    for (const extra of [
      { flags: [{ type: "preference", name: "x" }] },
      { prefix: "webkit" },
      { alternative_name: "zzold" },
      { partial_implementation: true },
    ]) {
      const support = atFloor();
      support.chrome = { version_added: "50", ...extra };
      assert.equal(supportedAtFloor(support), false, JSON.stringify(extra));
    }
  });

  it("accepts an array when some statement is plain support", () => {
    const support = atFloor();
    support.chrome = [
      { version_added: "50", prefix: "webkit" },
      { version_added: "90" },
    ];
    assert.equal(supportedAtFloor(support), true);
    // Without the plain statement the prefixed one is not enough.
    support.chrome = [{ version_added: "50", prefix: "webkit" }];
    assert.equal(supportedAtFloor(support), false);
  });

  it("combines a list of support objects for one member on two interfaces", () => {
    const desktop = Object.fromEntries(
      ["chrome", "firefox", "safari"].map((browser) => [browser, { version_added: FLOOR[browser] }]),
    );
    const mobile = Object.fromEntries(
      ["chrome_android", "firefox_android", "safari_ios"].map((browser) => [
        browser,
        { version_added: FLOOR[browser] },
      ]),
    );
    assert.equal(supportedAtFloor([desktop]), false);
    assert.equal(supportedAtFloor([desktop, mobile]), true);
  });
});

/** A BCD feature node for a member. */
function feature(support) {
  return { __compat: { support } };
}

/** An attribute the way `describeMember` in lib/data.mjs returns it. */
function attribute(name, options = {}) {
  return {
    name,
    kind: "attribute",
    type: options.type ?? "DOMString",
    stringLike: options.stringLike ?? (options.type ?? "DOMString") === "DOMString",
    nullable: false,
    readonly: options.readonly ?? false,
    reflect: options.reflect ?? null,
    extAttrs: [],
  };
}

function operation(name) {
  return { name, kind: "operation" };
}

function booleanReflect(name) {
  return attribute(name, { type: "boolean", reflect: "Reflect" });
}

/**
 * A small web platform shaped like what `loadData` returns.
 *
 *   Element
 *   HTMLElement  (includes ZzMixin)
 *   HTMLUnknownElement
 *   HTMLZzElement  (tag <zz>, interface supported at the floor)
 *   HTMLYyElement  (tag <yy>, interface missing from BCD)
 */
function makeData() {
  const idl = {
    interfaces: new Map([
      ["Element", { inherits: null, extAttrs: [], members: [attribute("id")] }],
      [
        "HTMLElement",
        {
          inherits: "Element",
          extAttrs: [],
          members: [
            // A string member marked as mirroring its attribute.
            attribute("zzmirror", { reflect: "Reflect" }),
            booleanReflect("zzflag"),
            // A boolean that Safari added after the floor.
            booleanReflect("zzlate"),
            // A boolean member with no browser data at all.
            booleanReflect("zznodata"),
            operation("zzmethod"),
          ],
        },
      ],
      ["HTMLUnknownElement", { inherits: "HTMLElement", extAttrs: [], members: [] }],
      ["HTMLZzElement", { inherits: "HTMLElement", extAttrs: [], members: [booleanReflect("zzown")] }],
      ["HTMLYyElement", { inherits: "HTMLElement", extAttrs: [], members: [booleanReflect("yyown")] }],
    ]),
    mixins: new Map([["ZzMixin", { inherits: null, extAttrs: [], members: [booleanReflect("zzmixed")] }]]),
    includes: new Map([["HTMLElement", ["ZzMixin"]]]),
  };
  const elements = new Map([
    ["zz", "HTMLZzElement"],
    ["yy", "HTMLYyElement"],
    // `object` is always Unknown, so it gets no entry whatever its members.
    ["object", "HTMLElement"],
  ]);
  const bcd = [
    {
      api: {
        HTMLElement: {
          zzflag: feature(atFloor()),
          zzlate: feature({ ...atFloor(), safari: { version_added: "16" } }),
          zzmethod: feature(atFloor()),
          zzmixed: feature(atFloor()),
          // BCD knows these, and the IDL does not.
          zzbcdonly: feature(atFloor()),
          zznever: feature(everywhere({ version_added: false })),
        },
        HTMLZzElement: {
          __compat: { support: atFloor() },
          zzown: feature(atFloor()),
        },
        HTMLYyElement: {
          // No interface-level __compat: some supported browser may lack it.
          yyown: feature(atFloor()),
        },
      },
    },
  ];
  return { idl, elements, bcd, versions: {} };
}

describe("classify", () => {
  it("returns the floor, the always-unknown tags and sorted answers", () => {
    const table = classify(makeData());
    assert.deepEqual(table.floor, FLOOR);
    assert.deepEqual(table.allUnknownTags, ["embed", "object"]);
    // Names come out in code-unit order for the server's binary search.
    assert.deepEqual(Object.keys(table.base), [...Object.keys(table.base)].sort());
  });

  it("answers for names inherited through the chain and a mixin", () => {
    const { base } = classify(makeData());
    // `zzflag` lives on HTMLElement, below the unknown-element chain's top.
    assert.equal(base.zzflag, "ReflectBoolean");
    // `zzmixed` lives on a mixin HTMLElement includes; BCD files it under
    // the including interface.
    assert.equal(base.zzmixed, "ReflectBoolean");
  });

  it("leaves a string member that mirrors its attribute out of the table", () => {
    const { base } = classify(makeData());
    assert.equal("zzmirror" in base, false);
    // `Element.id` has no marker; the reviewed prose list vouches for it.
    assert.equal("id" in base, false);
  });

  it("calls a method Unknown", () => {
    assert.equal(classify(makeData()).base.zzmethod, "Unknown");
  });

  it("calls a boolean added after the floor, or with no data, Unknown", () => {
    const { base } = classify(makeData());
    assert.equal(base.zzlate, "Unknown");
    assert.equal(base.zznodata, "Unknown");
  });

  it("writes a listed boolean by presence even where the floor lacks its member", () => {
    // `inert` arrived after the floor, and `<dialog>` is missing at the floor
    // in one browser. Both are in PRESENCE_ONLY_BOOLEANS, so they stay
    // booleans, while an unlisted late boolean (`zzlate`) stays Unknown.
    const data = makeData();
    data.idl.interfaces.get("HTMLElement").members.push(booleanReflect("inert"));
    data.idl.interfaces.set("HTMLDialogElement", {
      inherits: "HTMLElement",
      extAttrs: [],
      members: [booleanReflect("open")],
    });
    data.elements.set("dialog", "HTMLDialogElement");
    data.bcd[0].api.HTMLElement.inert = feature({ ...atFloor(), safari: { version_added: "15.5" } });
    data.bcd[0].api.HTMLDialogElement = {
      __compat: { support: { ...atFloor(), firefox: { version_added: "98" } } },
      open: feature({ ...atFloor(), firefox: { version_added: "98" } }),
    };
    const table = classify(data);
    assert.equal(table.base.inert, "ReflectBoolean");
    assert.equal(table.elements.dialog.open, "ReflectBoolean");
    assert.equal(table.base.zzlate, "Unknown");
  });

  it("answers Unknown for a name no data records, on BASE and every element", () => {
    const { base, elements } = classify(makeData());
    assert.equal(base.cue, "Unknown");
    assert.equal(base.cuebackground, "Unknown");
    for (const answers of Object.values(elements)) {
      assert.equal("cue" in answers, false);
      assert.equal("cuebackground" in answers, false);
    }
  });

  it("calls a member only BCD knows Unknown", () => {
    assert.equal(classify(makeData()).base.zzbcdonly, "Unknown");
  });

  it("leaves out a BCD member that never shipped", () => {
    assert.equal("zznever" in classify(makeData()).base, false);
  });

  it("records an element's own member as a difference from the base", () => {
    const { elements } = classify(makeData());
    assert.deepEqual(elements.zz, { zzown: "ReflectBoolean" });
  });

  it("makes a name Unknown when the element's interface may be missing", () => {
    const { elements } = classify(makeData());
    // BCD has no record of HTMLYyElement, so a browser at the floor may give
    // `<yy>` the unknown-element chain, where `yyown` is no member. The two
    // chains disagree, so the answer is Unknown.
    assert.deepEqual(elements.yy, { yyown: "Unknown" });
  });

  it("gives no entry to a tag whose every name is Unknown", () => {
    assert.equal("object" in classify(makeData()).elements, false);
  });

  it("throws when an unmarked string member is on neither reviewed list", () => {
    const data = makeData();
    data.idl.interfaces.get("HTMLElement").members.push(attribute("zzunmarked"));
    assert.throws(() => classify(data), /HTMLElement\.zzunmarked/);
  });

  it("names a bad interface in the chain", () => {
    const data = makeData();
    data.idl.interfaces.get("HTMLZzElement").inherits = "Missing";
    assert.throws(() => classify(data), /the IDL does not define Missing/);
  });
});

describe("collectUnclassified", () => {
  it("is empty when every string member is marked or reviewed", () => {
    assert.deepEqual(collectUnclassified(makeData()), []);
  });

  it("lists unmarked settable string members on an interface and a mixin, sorted", () => {
    const data = makeData();
    data.idl.mixins.get("ZzMixin").members.push(attribute("zzmixstr"));
    data.idl.interfaces.get("HTMLElement").members.push(attribute("zzunmarked"));
    assert.deepEqual(collectUnclassified(data), ["HTMLElement.zzunmarked", "ZzMixin.zzmixstr"]);
  });

  it("skips members that need no review", () => {
    const data = makeData();
    const members = data.idl.interfaces.get("HTMLElement").members;
    members.push(
      // Read-only, so Vue's assignment cannot reach it.
      attribute("zzreadonly", { readonly: true }),
      // Not a string.
      attribute("zznumber", { type: "long" }),
      // Mixed case is never a lowercase key.
      attribute("zzCamel"),
      // A marked string mirror.
      attribute("zzmarked", { reflect: "ReflectURL" }),
    );
    assert.deepEqual(collectUnclassified(data), []);
  });

  it("skips an interface that no element chain reaches", () => {
    const data = makeData();
    data.idl.interfaces.set("ZzOrphan", {
      inherits: null,
      extAttrs: [],
      members: [attribute("zzorphan")],
    });
    assert.deepEqual(collectUnclassified(data), []);
  });
});

/** A fresh IDL store with the given IDL text merged in, as `loadData` does. */
function mergeIdl(text, idl = { interfaces: new Map(), mixins: new Map(), includes: new Map() }) {
  for (const definition of webidl2.parse(text)) {
    mergeDefinition(idl, definition);
  }
  return idl;
}

describe("mergeDefinition", () => {
  it("adds a member that only a partial definition declares", () => {
    const idl = mergeIdl(`
      interface ZzBase {};
      interface ZzThing : ZzBase { attribute DOMString zza; };
      partial interface ZzThing { [Reflect] attribute boolean zzb; };
    `);
    const entry = idl.interfaces.get("ZzThing");
    assert.deepEqual(entry.members.map((member) => member.name), ["zza", "zzb"]);
    // The partial definition must not reset the parent.
    assert.equal(entry.inherits, "ZzBase");
  });

  it("keeps the parent when the partial definition comes first", () => {
    const idl = mergeIdl(`
      partial interface ZzThing { [Reflect] attribute boolean zzb; };
      interface ZzThing : ZzBase { attribute DOMString zza; };
    `);
    const entry = idl.interfaces.get("ZzThing");
    assert.deepEqual(entry.members.map((member) => member.name).sort(), ["zza", "zzb"]);
    assert.equal(entry.inherits, "ZzBase");
  });

  it("records includes statements and mixin members", () => {
    const idl = mergeIdl(`
      interface mixin ZzMix { [Reflect] attribute boolean zzm; };
      ZzThing includes ZzMix;
    `);
    assert.deepEqual(idl.includes.get("ZzThing"), ["ZzMix"]);
    assert.deepEqual(idl.mixins.get("ZzMix").members.map((member) => member.name), ["zzm"]);
  });

  it("reaches the table through a partial definition", () => {
    const data = makeData();
    mergeIdl("partial interface HTMLElement { [Reflect] attribute boolean zzpartial; };", data.idl);
    data.bcd[0].api.HTMLElement.zzpartial = feature(atFloor());
    assert.equal(classify(data).base.zzpartial, "ReflectBoolean");
  });

  it("counts a union with Trusted Types as a string", () => {
    const idl = mergeIdl(`
      interface ZzThing {
        [Reflect] attribute (TrustedHTML or DOMString) zzunion;
        [Reflect] attribute (Node or DOMString) zznode;
      };
    `);
    const [union, node] = idl.interfaces.get("ZzThing").members;
    assert.equal(union.stringLike, true);
    assert.equal(union.reflect, "Reflect");
    // A union with a type that is no string is not a string.
    assert.equal(node.stringLike, false);
  });

  it("leaves a marked string union out of the table, and an unmarked one for review", () => {
    const data = makeData();
    const stringUnion = {
      ...attribute("zzunion", { type: "union", stringLike: true, reflect: "Reflect" }),
    };
    const members = data.idl.interfaces.get("HTMLElement").members;
    members.push(stringUnion);
    // A string mirror needs no browser data: either path leaves the text.
    assert.equal("zzunion" in classify(data).base, false);
    // The same member with no marker waits for review, like any string.
    members.pop();
    members.push({ ...stringUnion, name: "zzunmarkedunion", reflect: null });
    assert.deepEqual(collectUnclassified(data), ["HTMLElement.zzunmarkedunion"]);
  });

  it("reads a Reflect marker for another attribute name as not mirroring", () => {
    const idl = mergeIdl(`
      interface ZzThing {
        [Reflect="other"] attribute DOMString zzrenamed;
        [Reflect="zzsame"] attribute DOMString zzsame;
      };
    `);
    const [renamed, same] = idl.interfaces.get("ZzThing").members;
    assert.equal(renamed.reflect, null);
    assert.equal(same.reflect, "Reflect");
  });

  it("warns about a Reflect marker it does not know and counts it as not mirroring", () => {
    const write = mock.method(process.stderr, "write", () => true);
    try {
      const idl = mergeIdl("interface ZzThing { [ReflectZzNew] attribute boolean zzq; };");
      assert.equal(idl.interfaces.get("ZzThing").members[0].reflect, null);
      assert.match(String(write.mock.calls[0].arguments[0]), /zzq has an unknown marker \[ReflectZzNew\]/);
    } finally {
      write.mock.restore();
    }
  });
});

describe("older BCD copies", () => {
  /** A copy of the data after the first, holding only what `api` lists. */
  function olderCopy(api) {
    return { api: { HTMLElement: api } };
  }

  it("reads a member's support from an older copy when the newest lacks it", () => {
    const data = makeData();
    data.idl.interfaces.get("HTMLElement").members.push(booleanReflect("zzold"));
    // With only the newest copy the boolean has no data, so it is Unknown.
    assert.equal(classify(data).base.zzold, "Unknown");
    data.bcd.push(olderCopy({ zzold: feature(atFloor()) }));
    assert.equal(classify(data).base.zzold, "ReflectBoolean");
  });

  it("finds a member only an older copy records", () => {
    const data = makeData();
    data.bcd.push(olderCopy({ zzoldonly: feature(atFloor()) }));
    assert.equal(classify(data).base.zzoldonly, "Unknown");
  });

  it("prefers the newest copy's statement over an older one", () => {
    const data = makeData();
    // The newest copy says the boolean arrived in Safari 16, after the
    // floor; the older copy's floor-time statement must not override it.
    data.bcd.push(olderCopy({ zzlate: feature(atFloor()) }));
    assert.equal(classify(data).base.zzlate, "Unknown");
  });
});

describe("alternative spellings", () => {
  /** A string member that mirrors its attribute, with BCD statements. */
  function withMirror(name, support) {
    const data = makeData();
    data.idl.interfaces.get("HTMLElement").members.push(attribute(name, { reflect: "Reflect" }));
    data.bcd[0].api.HTMLElement[name] = feature(support);
    return classify(data).base;
  }

  it("treats a live older spelling as an unknown member", () => {
    const base = withMirror("zzmirrorb", {
      ...atFloor(),
      chrome: [{ version_added: "98", alternative_name: "zzoldname" }, { version_added: "110" }],
    });
    assert.equal(base.zzoldname, "Unknown");
  });

  it("gives the spelling only the statements that name it", () => {
    // Chrome dropped `zzoldname` before the floor, and the plain name
    // arrived at the floor, so no supported browser has the old spelling.
    const base = withMirror("zzmirrorc", {
      ...atFloor(),
      chrome: [
        { version_added: "50", version_removed: "90", alternative_name: "zzoldname" },
        { version_added: "90" },
      ],
    });
    assert.equal("zzoldname" in base, false);
  });

  it("reads a prefixed spelling the same way", () => {
    const live = withMirror("zzmirrord", {
      ...atFloor(),
      chrome: [{ version_added: "50", prefix: "webkit" }, { version_added: "90" }],
    });
    assert.equal(live.webkitzzmirrord, "Unknown");
    const gone = withMirror("zzmirrore", {
      ...atFloor(),
      chrome: [
        { version_added: "50", version_removed: "80", prefix: "webkit" },
        { version_added: "90" },
      ],
    });
    assert.equal("webkitzzmirrore" in gone, false);
  });

  it("lets only the lowercase spelling of the attribute's own name mirror it", () => {
    // `zzMirrorf` mirrors the attribute `zzmirrorf`; Chrome once spelled it
    // in lowercase, which is the same attribute and so the same text.
    const data = makeData();
    data.idl.interfaces.get("HTMLElement").members.push(attribute("zzMirrorf", { reflect: "Reflect" }));
    data.bcd[0].api.HTMLElement.zzMirrorf = feature({
      ...atFloor(),
      chrome: [
        { version_added: "98", alternative_name: "zzmirrorf" },
        { version_added: "98", alternative_name: "zzotherf" },
      ],
    });
    const { base } = classify(data);
    assert.equal("zzmirrorf" in base, false);
    // A different old name is not that attribute, whatever the member does.
    assert.equal(base.zzotherf, "Unknown");
  });
});

describe("event handler names", () => {
  it("never puts an on* name in the table", () => {
    const data = makeData();
    // An IDL member and a BCD-only member would both be Unknown otherwise.
    data.idl.interfaces.get("HTMLElement").members.push(operation("onzzfoo"));
    data.bcd[0].api.HTMLElement.onzzbar = feature(atFloor());
    const { base } = classify(data);
    assert.equal("onzzfoo" in base, false);
    assert.equal("onzzbar" in base, false);
    // A method that does not start with "on" is still there.
    assert.equal(base.zzmethod, "Unknown");
  });
});

describe("checkCopyGaps", () => {
  const copy = (timestamp) => ({ __meta: { timestamp } });

  it("passes for copies a year apart", () => {
    checkCopyGaps(
      ["latest", "bcd-2025", "bcd-2024"],
      [copy("2026-06-01T00:00:00.000Z"), copy("2025-06-01T00:00:00.000Z"), copy("2024-06-01T00:00:00.000Z")],
    );
  });

  it("throws and names the pair for copies three years apart", () => {
    assert.throws(
      () =>
        checkCopyGaps(
          ["latest", "bcd-2023"],
          [copy("2026-06-01T00:00:00.000Z"), copy("2023-06-01T00:00:00.000Z")],
        ),
      /latest and bcd-2023 are 1096 days apart/,
    );
  });

  it("passes for a single copy", () => {
    checkCopyGaps(["latest"], [copy("2026-06-01T00:00:00.000Z")]);
  });
});
