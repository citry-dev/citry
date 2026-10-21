/*
 * Citry development checks for the browser.
 *
 * The server sends this script only with Citry(mode="development"), and only on a page whose
 * served HTML Vue hydrates and that has at least one shell with served contents. A shell is an
 * element the server marks with data-allow-mismatch="children": Vue adopts the element itself
 * (keeps the server's node) but builds its children in the browser, because the server cannot
 * write them the way Vue would. The runtime (`_vue/client.js`) removes the served children right
 * before Vue hydrates, so Vue never reports a difference there, not even in its own development
 * build.
 *
 * This script compares what the server sent inside each shell with what Vue's first render
 * built there, and logs one console warning per shell that differs. The usual cause is browser
 * code that changes state before the first render, such as created() reading the window size,
 * so the page jumps when Vue starts. The comparison runs when mount() returns: mounted() hooks
 * have run by then, but a re-render that their state changes ask for waits for Vue's scheduler,
 * so only a direct DOM edit in such a hook is seen.
 *
 * The server writes a shell's contents from the values it knows. It leaves out a list, a text or
 * an attribute that only the browser can compute, and it writes every branch of a condition that
 * only the browser can test. So the comparison is one-sided: it reports a text or an attribute
 * value the server wrote that Vue's first render does not show, and it never reports an element,
 * text or attribute that only one side has.
 */
(function (global) {
  "use strict";

  const SHELL_SELECTOR = '[data-allow-mismatch="children"]';
  const ALLOW_ATTRIBUTE = "data-allow-mismatch";
  // Past this many element pairs in one parent the best-match search would be slow, and pairing
  // in order could pair the wrong two elements, so such a parent's elements are not compared.
  // Only very long lists reach it, not ordinary markup.
  const MAX_ALIGNMENT_CELLS = 40000;
  // Scoring a pair of elements by their whole subtree compares the subtrees too. A shell spends
  // at most this many steps on such scores: each score, the text it reads first, and the nodes
  // and element pairs compared inside it. Past it, pairs score by their own attributes and text
  // only, and two same-tag branches can pair the wrong way.
  const MAX_SUBTREE_CELLS = 40000;
  // Scores nest one level per element level, so very deep markup would run out of stack. Past
  // this depth a score stops and the pair keeps its own attributes-and-text score.
  const MAX_SUBTREE_DEPTH = 64;
  // Vue names a component it registers with `name`; Citry's runtime uses this prefix with the
  // component's type key (its class name plus a short code) when the author gave no name.
  const CITRY_NAME_PREFIX = "CitryComponent_";

  const isElement = node => node !== null && typeof node === "object" && node.nodeType === 1;
  const isText = node => node !== null && typeof node === "object" && node.nodeType === 3;

  // Whitespace never decides a difference: the server and Vue condense it the same way, and the
  // browser's parser merges neighboring text nodes that Vue keeps apart.
  const withoutSpace = text => text.replace(/\s+/g, "");
  const collapsed = text => text.replace(/\s+/g, " ").trim();

  // Follow Vue's own reading of data-allow-mismatch (runtime-core `isMismatchAllowed`): an empty
  // value allows every kind, otherwise a comma-separated list, where "children" also allows text.
  const allowsKind = (value, kind) => {
    if (value === null) return false;
    if (value === "") return true;
    const kinds = value.split(",");
    return kinds.includes(kind) || (kind === "text" && kinds.includes("children"));
  };

  // As in Vue, a text or children difference is decided by the nearest element that carries the
  // attribute, and any other kind only by the element itself. The shell carries the attribute
  // too, so the walk stops before it.
  const allowedHere = (element, kind, boundary) => {
    let current = element;
    if (kind === "text" || kind === "children")
      while (current && current !== boundary && !current.hasAttribute(ALLOW_ATTRIBUTE)) current = current.parentElement;
    if (!current || current === boundary) return false;
    return allowsKind(current.getAttribute(ALLOW_ATTRIBUTE), kind);
  };

  const sameTag = (served, browser) =>
    served.localName === browser.localName && served.namespaceURI === browser.namespaceURI;

  // Group a node list into runs of text that the browser's parser would read as one text node:
  // text nodes with nothing but comments or other text between them. Vue keeps an empty text node
  // at each end of a fragment and a comment where a v-if renders nothing; the server writes
  // neither, so the parse of the served HTML joins what Vue keeps apart.
  const textRuns = nodes => {
    const runs = [];
    let current = null;
    for (const node of nodes) {
      if (isText(node)) {
        if (current === null) {
          current = [];
          runs.push(current);
        }
        if (withoutSpace(node.data)) current.push(node.data);
      } else if (isElement(node)) {
        current = null;
      }
    }
    return runs.filter(run => run.length > 0);
  };

  // Whether a served run of text agrees with a browser run, given as its text pieces. The two
  // legitimate differences go in opposite directions: the server leaves out a text node only the
  // browser can compute, so the served text may be the browser's pieces with some left out; and
  // it writes every branch of a condition only the browser can test, so the served text may hold
  // the browser's pieces, in order, with other text around them.
  const textAgrees = (served, pieces) => {
    let reachable = new Set([0]);
    for (const piece of pieces) {
      const next = new Set(reachable);
      for (const position of reachable) if (served.startsWith(piece, position)) next.add(position + piece.length);
      reachable = next;
    }
    if (reachable.has(served.length)) return true;
    let position = 0;
    for (const piece of pieces) {
      const found = served.indexOf(piece, position);
      if (found < 0) return false;
      position = found + piece.length;
    }
    return true;
  };

  // Find a served text run that contradicts the browser's text. Runs are paired in order where
  // they agree. Between two agreeing pairs, a served run and a browser run in the same position
  // contradict each other only when both sides hold the same number of runs there; otherwise the
  // extra runs are a branch only the server shows or text only the browser knows.
  const textDifference = (servedNodes, browserNodes) => {
    const servedRuns = textRuns(servedNodes).map(run => run.join(""));
    if (!servedRuns.length) return null;
    const browserTexts = textRuns(browserNodes);
    const browserRuns = browserTexts.map(run => run.map(withoutSpace));
    const servedKeys = servedRuns.map(withoutSpace);
    const rows = servedKeys.length, columns = browserRuns.length;
    const score = Array.from({length: rows + 1}, () => new Array(columns + 1).fill(0));
    for (let row = rows - 1; row >= 0; row--)
      for (let column = columns - 1; column >= 0; column--)
        score[row][column] = textAgrees(servedKeys[row], browserRuns[column])
          ? 1 + score[row + 1][column + 1]
          : Math.max(score[row + 1][column], score[row][column + 1]);
    let row = 0, column = 0, gapRow = 0, gapColumn = 0;
    const checkGap = (endRow, endColumn) => {
      if (endRow - gapRow > 0 && endRow - gapRow === endColumn - gapColumn)
        return {kind: "text", served: collapsed(servedRuns[gapRow]), browser: collapsed(browserTexts[gapColumn].join(""))};
      return null;
    };
    while (row < rows && column < columns) {
      if (textAgrees(servedKeys[row], browserRuns[column]) && score[row][column] === 1 + score[row + 1][column + 1]) {
        const gap = checkGap(row, column);
        if (gap) return gap;
        gapRow = ++row;
        gapColumn = ++column;
      } else if (score[row][column] === score[row + 1][column]) {
        row++;
      } else {
        column++;
      }
    }
    return checkGap(rows, columns);
  };

  // A boolean attribute is written as an empty value by the server and by Vue, but a browser may
  // also write the attribute's own name.
  const sameBooleanValue = (name, served, browser) =>
    (served === "" || served === name) && (browser === "" || browser === name);

  // Vue sets some attributes as DOM properties (an input's value, checked, selected, muted), and
  // the browser does not write those back as attributes. Compare the property instead.
  const UNREFLECTED_PROPERTIES = new Set(["value", "checked", "selected", "muted"]);
  const propertyAgrees = (element, name, served) => {
    if (!(name in element)) return false;
    const value = element[name];
    if (typeof value === "boolean") return value === true;
    return value !== null && value !== undefined && String(value) === served;
  };

  const classTokens = value => value.split(/\s+/).filter(Boolean);

  // Compare the attributes the server wrote on one element with Vue's element. The server writes
  // only the parts of a class or style it knows, so each served class and each served style
  // property must appear in the browser, and a browser-only class or property is not a difference.
  const attributeDifference = (served, browser, boundary) => {
    for (const attribute of Array.from(served.attributes)) {
      const name = attribute.name;
      if (name === ALLOW_ATTRIBUTE) continue;
      if (name === "class") {
        if (allowedHere(browser, "class", boundary)) continue;
        const present = new Set(classTokens(browser.getAttribute("class") || ""));
        const missing = classTokens(attribute.value).filter(token => !present.has(token));
        if (missing.length)
          return {kind: "attribute", name, served: attribute.value, browser: browser.getAttribute("class")};
        continue;
      }
      if (name === "style") {
        if (allowedHere(browser, "style", boundary)) continue;
        const servedStyle = served.style, browserStyle = browser.style;
        if (!servedStyle || !browserStyle) continue;
        for (let index = 0; index < servedStyle.length; index++) {
          const property = servedStyle[index];
          // A v-show only the browser can test leaves the served element's own display in
          // place, and Vue then hides it, so a browser-only `display: none` is not a difference.
          if (property === "display" && browserStyle.getPropertyValue(property) === "none") continue;
          if (servedStyle.getPropertyValue(property) !== browserStyle.getPropertyValue(property))
            return {kind: "attribute", name, served: attribute.value, browser: browser.getAttribute("style")};
        }
        continue;
      }
      if (allowedHere(browser, "attribute", boundary)) continue;
      // Look the attribute up by its written name: the parser puts `xmlns` and `xlink:href` in
      // their XML namespaces, while Vue may set the same name without one.
      const browserValue = browser.getAttribute(name);
      if (browserValue === attribute.value) continue;
      if (browserValue === null && propertyAgrees(browser, attribute.localName, attribute.value)) continue;
      if (browserValue !== null && sameBooleanValue(name, attribute.value, browserValue)) continue;
      // Vue sets these as DOM properties, which the browser never writes back as attributes, so
      // "no checked" would misdescribe the page: name the property's value instead.
      const property = attribute.localName;
      if (browserValue === null && UNREFLECTED_PROPERTIES.has(property) && property in browser)
        return {kind: "attribute", name, served: attribute.value, browser: browser[property], property: true};
      return {kind: "attribute", name, served: attribute.value, browser: browserValue};
    }
    return null;
  };

  // Elements whose children are not plain markup to compare: a template's contents live in a
  // separate fragment, a textarea's text is its value, which Vue sets as a property, and the text
  // of a script or noscript is not markup Vue renders.
  const OPAQUE_CHILDREN = new Set(["template", "textarea", "script", "noscript"]);

  // Own attributes plus the text directly inside: what two elements show without looking at
  // their child elements. Pairing uses it to rule a pair out cheaply, and on its own for a tag
  // the served side has no more of than the browser, or once the shell's budget for
  // whole-subtree scores is spent.
  const shallowDifference = (served, browser, boundary) =>
    attributeDifference(served, browser, boundary) ||
    (OPAQUE_CHILDREN.has(browser.localName) || allowedHere(browser, "text", boundary)
      ? null
      : textDifference(Array.from(served.childNodes), Array.from(browser.childNodes)));

  // One comparison of a shell's served contents with Vue's first render.
  const createComparison = boundary => {
    // The first difference between a served element and a browser element, subtree included,
    // keyed by both elements. Pairing scores some candidate pairs with it (see pairElements),
    // and the walk reuses those results instead of comparing the pair again.
    const known = new Map();
    // Each element's subtree text without whitespace, as one string and as its text pieces in
    // order, read once per element.
    const subtreeTexts = new Map();
    const subtreeText = element => {
      let value = subtreeTexts.get(element);
      if (value === undefined) {
        const pieces = [];
        const stack = [element];
        while (stack.length) {
          const node = stack.pop();
          if (isText(node)) {
            const piece = withoutSpace(node.data);
            if (piece) pieces.push(piece);
          } else if (isElement(node) && !OPAQUE_CHILDREN.has(node.localName)) {
            const children = node.childNodes;
            for (let index = children.length - 1; index >= 0; index--) stack.push(children[index]);
          }
        }
        value = {whole: pieces.join(""), pieces};
        subtreeTexts.set(element, value);
        // Reading the text costs about one step per piece, paid once per element.
        subtreeCellsLeft -= pieces.length;
      }
      return value;
    };
    // Whether two subtrees' text could agree, given that either side may hold text the other
    // leaves out: the server writes every branch of a browser-only condition, and the browser
    // shows text only it can compute. Most pairs that differ fail here, at a fraction of a full
    // score's cost. It misses agreement only when both sides hold text the other lacks.
    const textCouldAgree = (served, browser) => {
      const servedText = subtreeText(served), browserText = subtreeText(browser);
      return textAgrees(servedText.whole, browserText.pieces) || textAgrees(browserText.whole, servedText.pieces);
    };
    // What whole-subtree scores may still spend, in scores and element pairs; see
    // MAX_SUBTREE_CELLS. `subtreeDepth` counts the scores in progress, so the pairs compared
    // inside them are charged too.
    let subtreeCellsLeft = MAX_SUBTREE_CELLS;
    let subtreeDepth = 0;
    // Thrown when a whole-subtree score runs past the budget; the score in progress then falls
    // back to the pair's own attributes and text, and keeps nothing it had not finished.
    const OUT_OF_BUDGET = {};

    const elementDifference = (served, browser) => {
      let row = known.get(served);
      if (row === undefined) {
        row = new Map();
        known.set(served, row);
      }
      if (row.has(browser)) return row.get(browser);
      const own = attributeDifference(served, browser, boundary);
      const difference = own
        ? {...own, element: browser}
        : OPAQUE_CHILDREN.has(browser.localName)
          ? null
          : childrenDifference(Array.from(served.childNodes), Array.from(browser.childNodes), browser);
      row.set(browser, difference);
      return difference;
    };

    // Pair served elements with browser elements of the same tag, keeping both orders, so the
    // most pairs agree. The served side can hold extra elements (every branch of a condition
    // only the browser can test) and the browser side can hold extra ones (a list only the
    // browser knows), so an element left without a partner is not a difference.
    const pairElements = (servedElements, browserElements) => {
      const rows = servedElements.length, columns = browserElements.length;
      if (rows === 0 || columns === 0) return [];
      if (rows * columns > MAX_ALIGNMENT_CELLS) {
        // Inside a score, a list this long is a cost the budget cannot pay.
        if (subtreeDepth > 0) throw OUT_OF_BUDGET;
        return [];
      }
      if (subtreeDepth > 0) {
        // Pairs compared inside a whole-subtree score are part of that score's cost.
        subtreeCellsLeft -= rows * columns;
        if (subtreeCellsLeft < 0) throw OUT_OF_BUDGET;
      }
      // Two branches of a browser-only v-if can share a tag and attributes and differ only
      // further down, and the browser's branch must pair with its own served copy, not with the
      // first one. That needs the whole subtree, but only for a tag the served side has more of.
      // When the served side has no more of a tag than the browser, the pairing treats the
      // elements as the same ones, possibly moved or changed, and scores them by their own
      // attributes and text so such a change stays visible. Browser-only elements of the same
      // tag can hide a served-only branch from this count, and then the branches can pair the
      // wrong way.
      const extra = new Set();
      const counts = new Map();
      for (const element of servedElements) {
        const tag = element.namespaceURI + " " + element.localName;
        counts.set(tag, (counts.get(tag) || 0) + 1);
      }
      for (const element of browserElements) {
        const tag = element.namespaceURI + " " + element.localName;
        counts.set(tag, (counts.get(tag) || 0) - 1);
      }
      for (const [tag, count] of counts) if (count > 0) extra.add(tag);
      const differs = (served, browser) => {
        // A difference in the pair's own attributes or text is also one in its subtree, and
        // costs far less to find, so only a pair that agrees there may be compared further.
        if (shallowDifference(served, browser, boundary) !== null) return true;
        if (!extra.has(served.namespaceURI + " " + served.localName) || subtreeCellsLeft <= 0) return false;
        if (subtreeDepth >= MAX_SUBTREE_DEPTH) return false;
        subtreeCellsLeft--;
        if (!textCouldAgree(served, browser)) return true;
        if (subtreeCellsLeft <= 0) return false;
        subtreeDepth++;
        try {
          return elementDifference(served, browser) !== null;
        } catch (error) {
          if (error !== OUT_OF_BUDGET) throw error;
          // The own attributes and text agree, which is all a shallow score would read.
          return false;
        } finally {
          subtreeDepth--;
        }
      };
      // A pair of the same tag scores 2, and 1 more when the two agree, so of two candidates
      // the agreeing one wins, while a differing pair still beats leaving both unpaired.
      const weights = servedElements.map(served =>
        browserElements.map(browser => (sameTag(served, browser) ? (differs(served, browser) ? 2 : 3) : 0)),
      );
      const score = Array.from({length: rows + 1}, () => new Array(columns + 1).fill(0));
      for (let row = rows - 1; row >= 0; row--)
        for (let column = columns - 1; column >= 0; column--) {
          const paired = weights[row][column];
          score[row][column] = Math.max(
            score[row + 1][column],
            score[row][column + 1],
            paired ? paired + score[row + 1][column + 1] : 0,
          );
        }
      const pairs = [];
      let row = 0, column = 0;
      while (row < rows && column < columns) {
        const paired = weights[row][column];
        if (paired && score[row][column] === paired + score[row + 1][column + 1]) {
          pairs.push([servedElements[row++], browserElements[column++]]);
        } else if (score[row][column] === score[row + 1][column]) {
          row++;
        } else {
          column++;
        }
      }
      return pairs;
    };

    // Find the first difference between served nodes and browser nodes under one parent, depth
    // first, as {kind, name?, served, browser, element}. `element` is the browser element the
    // difference belongs to (the parent, for a text difference).
    const childrenDifference = (servedNodes, browserNodes, browserParent) => {
      if (browserParent !== boundary && allowedHere(browserParent, "children", boundary)) return null;
      if (subtreeDepth > 0) {
        // Comparing the text runs inside a score is part of its cost, about one step per pair of
        // nodes.
        subtreeCellsLeft -= (servedNodes.length + 1) * (browserNodes.length + 1);
        if (subtreeCellsLeft < 0) throw OUT_OF_BUDGET;
      }
      if (!allowedHere(browserParent, "text", boundary)) {
        const text = textDifference(servedNodes, browserNodes);
        if (text) return {...text, element: browserParent};
      }
      for (const [served, browser] of pairElements(servedNodes.filter(isElement), browserNodes.filter(isElement))) {
        const difference = elementDifference(served, browser);
        if (difference) return difference;
      }
      return null;
    };

    return childrenDifference;
  };

  // Compare the served nodes and browser nodes directly inside `browserParent`, within the
  // shell `boundary`; see createComparison.
  const childrenDifference = (servedNodes, browserNodes, browserParent, boundary) =>
    createComparison(boundary)(servedNodes, browserNodes, browserParent);

  // Map each element Vue created to the vnode that created it, by walking the rendered vnode
  // tree from the host. The production build keeps `el`, `component`, `subTree` and `ctx` on
  // vnodes; `ctx` is the component whose template wrote the vnode, which for slot content is the
  // component that filled the slot, not the one that rendered it.
  const indexVNodes = root => {
    const index = new Map();
    const stack = root ? [root] : [];
    while (stack.length) {
      const vnode = stack.pop();
      if (!vnode || typeof vnode !== "object") continue;
      if (vnode.component) {
        stack.push(vnode.component.subTree);
        continue;
      }
      if (typeof vnode.type === "string" && isElement(vnode.el)) index.set(vnode.el, vnode);
      if (Array.isArray(vnode.children)) for (const child of vnode.children) stack.push(child);
    }
    return index;
  };

  const componentName = instance => {
    const name = instance?.type?.name || instance?.type?.__name;
    if (typeof name !== "string" || !name) return "a component";
    return name.startsWith(CITRY_NAME_PREFIX) ? name.slice(CITRY_NAME_PREFIX.length) : name;
  };

  const ownerName = (element, index, boundary) => {
    for (let current = element; current; current = current.parentElement) {
      const vnode = index.get(current);
      if (vnode?.ctx) return componentName(vnode.ctx);
      if (current === boundary) break;
    }
    return componentName(index.get(boundary)?.ctx);
  };

  const describeElement = element => {
    const id = element.getAttribute("id");
    if (id) return "<" + element.localName + ' id="' + id + '">';
    const firstClass = classTokens(element.getAttribute("class") || "")[0];
    if (firstClass) return "<" + element.localName + ' class="' + firstClass + '">';
    return "<" + element.localName + ">";
  };

  const quoted = value => (value === null ? "nothing" : JSON.stringify(value));

  const describeDifference = difference => {
    const where = describeElement(difference.element);
    if (difference.kind === "text")
      return "In " + where + ", the server sent the text " + quoted(difference.served) +
        " and the browser shows " + quoted(difference.browser) + ".";
    const shown = difference.property
      ? "the " + difference.name + " property as " + JSON.stringify(difference.browser)
      : difference.browser === null
        ? "no " + difference.name
        : difference.name + "=" + quoted(difference.browser);
    return "On " + where + ", the server sent " + difference.name + "=" + quoted(difference.served) +
      " and the browser shows " + shown + ".";
  };

  // The data-allow-mismatch value that accepts exactly this kind of difference.
  const allowValue = difference =>
    difference.kind === "text" ? "text" : ["class", "style"].includes(difference.name) ? difference.name : "attribute";

  const warningText = (component, difference) =>
    "[Citry] " + component + ": Vue's first render in the browser differs from the HTML the server sent, " +
    "so the page changes as Vue starts. " + describeDifference(difference) + " The usual cause is browser " +
    "code that sets state before the first render, such as created() reading window.matchMedia: set that " +
    "state in mounted() instead. " +
    // The check cannot tell that cause from a deliberate change, such as a mounted() hook that edits
    // the page directly, so the advice names both.
    "If the difference is deliberate, such as a mounted() hook that edits the page, add " +
    "data-allow-mismatch=\"" + allowValue(difference) + "\" to " + describeElement(difference.element) +
    ". Citry runs this check only with Citry(mode=\"development\").";

  // Keep each shell's served children before the runtime removes them. Called by the runtime in
  // the same task as the mount, so the page cannot change in between.
  const captureShells = host => {
    const captured = [];
    // A bug here must never stop the page either; without the served contents there is simply
    // nothing to compare.
    try {
      for (const shell of Array.from(host.querySelectorAll(SHELL_SELECTOR))) {
        // A shell inside another shell's served contents is rebuilt with the outer one; the
        // server never writes one there, so this is only a guard.
        if (shell.parentElement?.closest(SHELL_SELECTOR)) continue;
        const served = Array.from(shell.childNodes);
        // A shell the server sent empty (its contents would run twice, the parser would move
        // them, or they were too large) has nothing to compare.
        if (!served.some(node => isElement(node) || (isText(node) && withoutSpace(node.data)))) continue;
        captured.push({shell, served});
      }
    } catch (error) {
      captured.length = 0;
      console.error("[Citry] the development check of server-rendered HTML failed:", error);
    }
    return {
      compare() {
        // A bug here must never stop the page, so every failure becomes a console message.
        try {
          if (!captured.length) return;
          const index = indexVNodes(host._vnode);
          for (const {shell, served} of captured) {
            // Vue replaced the shell itself (a mismatch it reports on its own), so there is no
            // first render of its children to compare.
            if (!shell.isConnected) continue;
            const difference = childrenDifference(served, Array.from(shell.childNodes), shell, shell);
            if (difference) console.warn(warningText(ownerName(difference.element, index, shell), difference));
          }
        } catch (error) {
          console.error("[Citry] the development check of server-rendered HTML failed:", error);
        }
      },
    };
  };

  global.CitryVueDevChecks = Object.freeze({captureShells, childrenDifference, warningText});
})(globalThis);
