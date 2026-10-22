/**
 * The development check that compares a shell's served HTML with Vue's first render. These tests
 * run the minified `citry/_vue/dev_checks.min.js` that development pages inline, built from the
 * readable `citry/_vue/dev_checks.js`, so they also catch a minification that changes behavior.
 * The comparison runs over a small fake DOM here; the browser tests in
 * `tests/e2e/test_vue_dev_checks_e2e.py` run it on real pages.
 */
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

const source = await readFile(new URL("../../../py/citry/citry/_vue/dev_checks.min.js", import.meta.url), "utf8");

function devChecks() {
  const context = { console };
  context.globalThis = context;
  vm.runInNewContext(source, context);
  return context.CitryVueDevChecks;
}

// Just enough of the DOM for the comparison: elements with attributes, a parsed style, and
// parent links, text nodes and comments.
function element(tag, attributes = {}, children = []) {
  const node = {
    nodeType: 1,
    localName: tag,
    namespaceURI: "http://www.w3.org/1999/xhtml",
    parentElement: null,
    attributes: Object.entries(attributes).map(([name, value]) => ({
      name,
      localName: name,
      value,
      namespaceURI: null,
    })),
    childNodes: children,
    getAttribute(name) {
      return this.attributes.find((attribute) => attribute.name === name)?.value ?? null;
    },
    hasAttribute(name) {
      return this.getAttribute(name) !== null;
    },
    getAttributeNS(_namespace, name) {
      return this.getAttribute(name);
    },
  };
  const declarations = (attributes.style || "")
    .split(";")
    .map((part) => part.split(":").map((value) => value.trim()))
    .filter(([name]) => name);
  node.style = Object.assign(
    declarations.map(([name]) => name),
    { getPropertyValue: (name) => declarations.find(([key]) => key === name)?.[1] ?? "" },
  );
  for (const child of children) if (child.nodeType === 1) child.parentElement = node;
  return node;
}
const text = (data) => ({ nodeType: 3, data });
const comment = (data) => ({ nodeType: 8, data });

// Compare served children with browser children inside a shell element, as the runtime does.
function differenceOf(served, browser) {
  const shell = element("section", { "data-allow-mismatch": "children" }, browser);
  return devChecks().childrenDifference(served, browser, shell, shell);
}

test("identical served and browser contents give no difference", () => {
  const make = () => [
    element("button", { type: "button", "aria-expanded": "false" }, [text(" Details ")]),
    element("p", { class: "status" }, [text("Status: "), element("span", {}, [text("closed")])]),
  ];
  assert.equal(differenceOf(make(), make()), null);
});

test("an attribute value the server wrote and the browser changed is a difference", () => {
  const served = [element("button", { "aria-expanded": "false" }, [text("Details")])];
  const browser = [element("button", { "aria-expanded": "true" }, [text("Details")])];
  const difference = differenceOf(served, browser);
  assert.equal(difference.kind, "attribute");
  assert.equal(difference.name, "aria-expanded");
  assert.equal(difference.served, "false");
  assert.equal(difference.browser, "true");
  assert.equal(difference.element, browser[0]);
});

test("an attribute the server wrote that the browser removed is a difference", () => {
  const served = [element("button", { disabled: "" })];
  const browser = [element("button")];
  const difference = differenceOf(served, browser);
  assert.equal(difference.name, "disabled");
  assert.equal(difference.browser, null);
});

test("server text that the browser shows differently is a difference", () => {
  const served = [element("span", {}, [text("closed")])];
  const browser = [element("span", {}, [text("open")])];
  const difference = differenceOf(served, browser);
  assert.equal(difference.kind, "text");
  assert.equal(difference.served, "closed");
  assert.equal(difference.browser, "open");
});

test("parts only the browser knows are not differences", () => {
  // The server leaves out an attribute, a text node, and list items it cannot compute.
  const served = [
    element("article", { class: "card" }, [element("h2"), text("Static ")]),
    element("ol"),
    element("span", {}, []),
  ];
  const browser = [
    element("article", { class: "card", title: "Hello" }, [
      element("h2", {}, [text("Hello")]),
      text("Static "),
      text("HELLO"),
    ]),
    element("ol", {}, [text(""), element("li", {}, [text("aa")]), element("li", {}, [text("bb")]), text("")]),
    element("span", {}, [text("browser only")]),
  ];
  assert.equal(differenceOf(served, browser), null);
});

test("every branch of a browser-only condition in the served HTML is not a difference", () => {
  // The server writes both branches; the browser shows the second, with a comment where the
  // first would be.
  const served = [element("p", { class: "wide" }, [text("big")]), element("p", { class: "narrow" }, [text("small")])];
  const browser = [comment("v-if"), element("p", { class: "narrow" }, [text("small")])];
  assert.equal(differenceOf(served, browser), null);
});

test("same-tag branches of a browser-only condition pair by what is inside them", () => {
  // The server writes both branches of `v-if`/`v-else` with the same wrapper tag and
  // attributes, and the browser shows the second one. Each case pairs the browser's branch
  // with its own served copy, so none of them is a difference.
  const cases = [
    // Text further down: <div v-if="wide"><b>Wide</b></div><div v-else><b>Narrow</b></div>
    [
      [
        element("div", {}, [element("b", {}, [text("Wide")])]),
        element("div", {}, [element("b", {}, [text("Narrow")])]),
      ],
      [comment("v-if"), element("div", {}, [element("b", {}, [text("Narrow")])])],
    ],
    // An attribute further down.
    [
      [
        element("div", {}, [element("span", { class: "a" }, [text("x")])]),
        element("div", {}, [element("span", { class: "b" }, [text("x")])]),
      ],
      [comment("v-if"), element("div", {}, [element("span", { class: "b" }, [text("x")])])],
    ],
    // A list in each branch.
    [
      [element("ul", {}, [element("li", {}, [text("A")])]), element("ul", {}, [element("li", {}, [text("B")])])],
      [comment("v-if"), element("ul", {}, [element("li", {}, [text("B")])])],
    ],
    // Wrappers with the same class, and a button whose type differs in each branch.
    [
      [
        element("div", { class: "panel" }, [element("button", { type: "button" }, [text("Log out")])]),
        element("div", { class: "panel" }, [element("button", { type: "submit" }, [text("Log in")])]),
      ],
      [comment("v-if"), element("div", { class: "panel" }, [element("button", { type: "submit" }, [text("Log in")])])],
    ],
  ];
  for (const [served, browser] of cases) assert.equal(differenceOf(served, browser), null);
});

test("the shown second branch pairs with its own copy before a browser-only list of its tag", () => {
  // <div v-if="wide" class="wide"> and <div v-else class="narrow">, then a browser-only
  // <div v-for>. The browser's branch must pair with its own served copy, even though pairing
  // each branch with a list row would pair more elements. With the first branch shown, the
  // check still warns, a documented limit.
  const served = [
    element("div", { class: "wide" }, [element("b", {}, [text("Wide")])]),
    element("div", { class: "narrow" }, [element("b", {}, [text("Narrow")])]),
  ];
  const browser = [
    comment("v-if"),
    element("div", { class: "narrow" }, [element("b", {}, [text("Narrow")])]),
    element("div", {}, [element("i", {}, [text("one")])]),
    element("div", {}, [element("i", {}, [text("two")])]),
  ];
  assert.equal(differenceOf(served, browser), null);
});

test("a branch with a nested condition and browser-only text pairs with its own served copy", () => {
  // The shown branch holds a nested browser-only v-if, whose two branches the server both
  // wrote, and an <em v-text> only the browser fills. Its served copy then holds text the
  // browser lacks and lacks text the browser holds, as does the other branch.
  const served = [
    element("div", {}, [element("span", {}, [text("Alpha")]), element("em")]),
    element("div", {}, [element("span", {}, [text("X")]), element("span", {}, [text("Y")]), element("em")]),
  ];
  const browser = (shown) => [
    comment("v-if"),
    element("div", {}, [comment("v-if"), element("span", {}, [text(shown)]), element("em", {}, [text("Z")])]),
  ];
  assert.equal(differenceOf(served, browser("Y")), null);
  // A static <div> beside the branches agrees with the browser's branch too, since served text
  // the browser lacks is allowed. The branch must still pair with its own served copy.
  const intro = () => element("div", {}, [text("Intro")]);
  assert.equal(differenceOf([intro(), ...served], [intro(), ...browser("Y")]), null);
  // A nested branch the browser shows differently is still reported.
  const difference = differenceOf(served, browser("Q"));
  assert.equal(difference.kind, "text");
  assert.equal(difference.browser, "Q");
});

test("a branch the browser changed before the first render is still a difference", () => {
  // The server wrote one branch, and created() made the browser show the other.
  const served = [element("div", {}, [element("b", {}, [text("Wide")])])];
  const browser = [element("div", {}, [element("b", {}, [text("Narrow")])])];
  const difference = differenceOf(served, browser);
  assert.equal(difference.kind, "text");
  assert.equal(difference.served, "Wide");
  assert.equal(difference.browser, "Narrow");
});

test("a large nested shell stays fast and still finds a deep difference", () => {
  // Three levels of same-tag elements, with one served-only element at each level, as the
  // server writes for a browser-only v-if. Comparing every pair by its whole subtree would
  // compare millions of pairs.
  const size = 16;
  const tree = (extra, leaf) =>
    Array.from({ length: size + extra }, (_, outer) =>
      element(
        "section",
        {},
        Array.from({ length: size + extra }, (_, middle) =>
          element(
            "div",
            {},
            Array.from({ length: size + extra }, (_, inner) => element("span", {}, [text(leaf(outer, middle, inner))])),
          ),
        ),
      ),
    );
  const same = (outer, middle, inner) => `${outer}-${middle}-${inner}`;
  const started = Date.now();
  assert.equal(differenceOf(tree(1, same), tree(0, same)), null);
  // About a quarter of a second here: most pairs differ in their text, so the quick text check
  // rules them out without a full comparison. The limit only catches a large slowdown.
  assert.ok(Date.now() - started < 5000);
  const changed = (outer, middle, inner) =>
    outer === 0 && middle === 0 && inner === 0 ? "changed" : same(outer, middle, inner);
  // The served side has the same element count here, so the change cannot be a served-only
  // branch and is reported.
  const difference = differenceOf(tree(0, same), tree(0, changed));
  assert.equal(difference.kind, "text");
  assert.equal(difference.served, "0-0-0");
  assert.equal(difference.browser, "changed");
});

test("whole-subtree scores stay within the budget when children never pair", () => {
  // One served-only <div> makes every <div> pair a candidate for a whole-subtree score, and
  // each such score pairs 150 by 150 children. The budget stops those scores early.
  const divs = (count, tag) =>
    Array.from({ length: count }, () =>
      element(
        "div",
        {},
        Array.from({ length: 150 }, () => element(tag)),
      ),
    );
  const started = Date.now();
  assert.equal(differenceOf(divs(61, "span"), divs(60, "b")), null);
  // Well under a second here; without the budget it takes several seconds.
  assert.ok(Date.now() - started < 2000);
});

test("a long table does not use up the budget that same-tag branches need", () => {
  const table = () =>
    element(
      "table",
      {},
      Array.from({ length: 60 }, (_, row) =>
        element(
          "tr",
          {},
          Array.from({ length: 5 }, (_, cell) => element("td", {}, [text(`r${row}c${cell}`)])),
        ),
      ),
    );
  const served = [
    table(),
    element("div", {}, [element("b", {}, [text("Wide")])]),
    element("div", {}, [element("b", {}, [text("Narrow")])]),
  ];
  const browser = [table(), element("div", {}, [element("b", {}, [text("Narrow")])])];
  assert.equal(differenceOf(served, browser), null);
});

test("many similar cards before same-tag branches leave budget for the branches", () => {
  // Cards that differ in their text are told apart by that text, without a full comparison
  // of each pair, so 80 of them do not use up the shell's budget.
  const card = (index) =>
    element("div", { class: "card" }, [
      element("h3", {}, [text(`T${index}`)]),
      element("p", {}, [text(`body ${index}`)]),
      element(
        "ul",
        {},
        [0, 1, 2].map((item) => element("li", {}, [text(`${index}.${item}`)])),
      ),
    ]);
  const cards = (extra) => [
    ...Array.from({ length: 80 }, (_, index) => card(index)),
    ...(extra ? [element("div", { class: "card" }, [element("b", {}, [text("Loading")])])] : []),
  ];
  const served = [
    element("section", {}, cards(true)),
    element("section", {}, [
      element("div", {}, [element("b", {}, [text("Wide")])]),
      element("div", {}, [element("b", {}, [text("Narrow")])]),
    ]),
  ];
  const browser = [
    element("section", {}, cards(false)),
    element("section", {}, [comment("v-if"), element("div", {}, [element("b", {}, [text("Narrow")])])]),
  ];
  assert.equal(differenceOf(served, browser), null);
});

test("text compared inside whole-subtree scores counts against the budget", () => {
  // Code blocks with many highlighted spans between text, beside one served-only block. The
  // blocks hold the same text, so the cheap text check passes and every pair of blocks gets a
  // full comparison, which compares hundreds of text runs.
  const block = (index) =>
    element("div", {}, [
      element(
        "pre",
        {},
        Array.from({ length: 210 }, (_, item) => [element("span", {}, [text(`t${item}`)]), text(` op${item} `)]).flat(),
      ),
    ]);
  const started = Date.now();
  const served = [...Array.from({ length: 20 }, (_, index) => block(index)), element("div", {}, [text("extra")])];
  const browser = Array.from({ length: 20 }, (_, index) => block(index));
  assert.equal(differenceOf(served, browser), null);
  // About half a second here; charging nothing for the text took about ten seconds.
  assert.ok(Date.now() - started < 5000);
});

test("searching the text of a pair counts against the budget", () => {
  // Thousands of one-letter text pieces, and one piece the served side lacks, make the search
  // for how the two texts line up try every position for every piece: millions of steps if
  // nothing stops it. Count the steps through String.prototype.startsWith, which that search
  // calls once per position, so the test does not depend on the machine's speed.
  const context = { console, steps: 0 };
  context.globalThis = context;
  vm.createContext(context);
  vm.runInContext(
    "const startsWith = String.prototype.startsWith;" +
      "String.prototype.startsWith = function (...args) { globalThis.steps++; return startsWith.apply(this, args); };",
    context,
  );
  vm.runInContext(source, context);
  const letters = (count, last) =>
    element("div", {}, [
      ...Array.from({ length: count }, () => element("i", {}, [text("a")])),
      ...(last ? [element("i", {}, [text(last)])] : []),
    ]);
  const served = [letters(6000), element("div", {}, [text("other")])];
  const browser = [letters(6000, "b")];
  const shell = element("section", { "data-allow-mismatch": "children" }, browser);
  assert.equal(context.CitryVueDevChecks.childrenDifference(served, browser, shell, shell), null);
  // The shell's budget is 200,000 steps; an unbounded search takes about 18 million.
  assert.ok(context.steps < 400000, `${context.steps} steps`);
});

test("a list that browser code reorders before the first render is a difference", () => {
  // The rows' text sits below each row element, and both sides hold the same rows.
  const row = (value) => element("li", {}, [element("span", {}, [text(value)])]);
  const served = ["A", "B", "C", "D"].map(row);
  const browser = ["B", "C", "D", "A"].map(row);
  const difference = differenceOf(served, browser);
  assert.equal(difference.kind, "text");
  assert.equal(difference.served, "A");
  assert.equal(difference.browser, "B");
});

test("text branches of a browser-only condition are not a difference", () => {
  // The browser's parser joins the two served branches into one text node.
  const servedJoined = [element("span", {}, [text("WideNarrow")])];
  const browserOne = [element("span", {}, [text(""), text("Narrow"), text("")])];
  assert.equal(differenceOf(servedJoined, browserOne), null);
  // Branches separated by an element leave an extra served run of text.
  const servedRuns = [element("span", {}, [text("A"), element("b"), text("B")])];
  const browserRun = [element("span", {}, [comment("v-if"), text("B")])];
  assert.equal(differenceOf(servedRuns, browserRun), null);
});

test("text the browser keeps in several nodes matches the served text node", () => {
  const served = [element("p", {}, [text("Status: open now")])];
  const browser = [element("p", {}, [text("Status: "), comment("v-if"), text("open"), text(" now")])];
  assert.equal(differenceOf(served, browser), null);
});

test("served classes and style properties must be present in the browser", () => {
  const served = [element("div", { class: "card", style: "color: red" })];
  const agreeing = [element("div", { class: "card card--open", style: "color: red; display: none" })];
  assert.equal(differenceOf(served, agreeing), null);
  const missingClass = [element("div", { class: "panel", style: "color: red" })];
  assert.equal(differenceOf(served, missingClass).name, "class");
  const changedStyle = [element("div", { class: "card", style: "color: blue" })];
  assert.equal(differenceOf(served, changedStyle).name, "style");
});

test("boolean attributes and values Vue sets as properties agree with the served attribute", () => {
  const served = [element("input", { checked: "", value: "Ada" }), element("option", { selected: "selected" })];
  const browserInput = element("input");
  browserInput.checked = true;
  browserInput.value = "Ada";
  const browser = [browserInput, element("option", { selected: "" })];
  assert.equal(differenceOf(served, browser), null);
  browserInput.value = "Grace";
  assert.equal(differenceOf(served, browser).name, "value");
});

test("a value Vue holds only as a DOM property is named with that value", () => {
  const served = [element("input", { type: "checkbox", checked: "" })];
  const input = element("input", { type: "checkbox" });
  input.checked = false;
  const difference = differenceOf(served, [input]);
  assert.equal(difference.name, "checked");
  const message = devChecks().warningText("Form_1", difference);
  assert.match(message, /the server sent checked="" and the browser shows the checked property as false\./);
  const textInput = element("input");
  textInput.value = "Grace";
  const valueMessage = devChecks().warningText(
    "Form_1",
    differenceOf([element("input", { value: "Ada" })], [textInput]),
  );
  assert.match(valueMessage, /the server sent value="Ada" and the browser shows the value property as "Grace"\./);
});

test("data-allow-mismatch silences the kinds it names, as in Vue", () => {
  const served = () => [element("p", { title: "a" }, [element("time", {}, [text("10:00")])])];
  const browser = (allow) => [
    element("p", { title: "b", "data-allow-mismatch": allow }, [element("time", {}, [text("10:01")])]),
  ];
  assert.equal(differenceOf(served(), browser("")), null);
  // "attribute" covers the element's own attributes, not text further down.
  assert.equal(differenceOf(served(), browser("attribute")).kind, "text");
  // "children" covers text and attributes below the element, not its own attributes.
  assert.equal(differenceOf(served(), browser("children")).name, "title");
  assert.equal(differenceOf(served(), browser("children,attribute")), null);
});

test("the warning names the component, the difference, and the fix", () => {
  const browser = element("button", { "aria-expanded": "true" });
  const message = devChecks().warningText("Details_1138d1", {
    kind: "attribute",
    name: "aria-expanded",
    served: "false",
    browser: "true",
    element: browser,
  });
  assert.match(message, /^\[Citry\] Details_1138d1: /);
  assert.match(
    message,
    /On <button>, the server sent aria-expanded="false" and the browser shows aria-expanded="true"\./,
  );
  // The advice fits both causes: state set too early, and a deliberate change.
  assert.match(message, /set that state in mounted\(\) instead\./);
  assert.match(message, /If the difference is deliberate, such as a mounted\(\) hook that edits the page, add /);
  assert.match(message, /data-allow-mismatch/);
});

test("a browser-only display: none from v-show is not a difference", () => {
  // The server keeps the element's own display when only the browser can test its v-show.
  const served = [element("div", { style: "display: flex" })];
  assert.equal(differenceOf(served, [element("div", { style: "display: none" })]), null);
  assert.equal(differenceOf(served, [element("div", { style: "display: grid" })]).name, "style");
});

test("the nearest data-allow-mismatch decides a text difference, as in Vue", () => {
  const served = [element("div", {}, [element("p", {}, [text("10:00")])])];
  const browser = [
    element("div", { "data-allow-mismatch": "text" }, [
      element("p", { "data-allow-mismatch": "class" }, [text("10:01")]),
    ]),
  ];
  // The <p> carries the attribute without "text", so the outer "text" does not apply.
  assert.equal(differenceOf(served, browser).kind, "text");
});

test("the warning names the data-allow-mismatch value that accepts the difference", () => {
  const checks = devChecks();
  const paragraph = element("p", { class: "status" });
  const textMessage = checks.warningText("Status_1", {
    kind: "text",
    served: "closed",
    browser: "open",
    element: paragraph,
  });
  assert.match(textMessage, /add data-allow-mismatch="text" to <p class="status">/);
  const classMessage = checks.warningText("Status_1", {
    kind: "attribute",
    name: "class",
    served: "a",
    browser: "b",
    element: paragraph,
  });
  assert.match(classMessage, /data-allow-mismatch="class"/);
});

test("a failure while keeping the served contents is logged and never thrown", () => {
  const errors = [];
  const context = { console: { error: (...args) => errors.push(args), warn() {} } };
  context.globalThis = context;
  vm.runInNewContext(source, context);
  const host = {
    querySelectorAll() {
      throw new Error("broken host");
    },
  };
  const check = context.CitryVueDevChecks.captureShells(host);
  check.compare();
  assert.equal(errors.length, 1);
  assert.match(String(errors[0][0]), /development check/);
});

test("a failure while comparing is logged and never thrown", () => {
  const errors = [];
  const context = { console: { error: (...args) => errors.push(args), warn() {} } };
  context.globalThis = context;
  vm.runInNewContext(source, context);
  const shell = element("section", { "data-allow-mismatch": "children" }, [element("p", {}, [text("x")])]);
  shell.parentElement = { closest: () => null };
  const host = { querySelectorAll: () => [shell] };
  Object.defineProperty(host, "_vnode", {
    get() {
      throw new Error("broken vnode");
    },
  });
  shell.isConnected = true;
  context.CitryVueDevChecks.captureShells(host).compare();
  assert.equal(errors.length, 1);
});
