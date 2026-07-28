(() => {
  "use strict";

  const attributeSnapshot = (element) => ({
    names: element.getAttributeNames(),
    props: element.getAttribute("$c-props"),
    outerHTML: element.outerHTML,
  });

  const selectorProbe = (selector) => {
    try {
      return { count: document.querySelectorAll(selector).length, error: null };
    } catch (error) {
      return { count: null, error: error.name };
    }
  };

  async function rawDomProbe() {
    const host = document.createElement("div");
    host.innerHTML = `
      <section
        id="parsed-direct"
        $c-props="{ count: 1 }"
        c-$c-props="serverExpression"
        $c-on:click.once="save()"
      ></section>
      <section id="parsed-case" $C-PROPS="mixed"></section>
    `;
    const direct = host.querySelector("#parsed-direct");
    const mixedCase = host.querySelector("#parsed-case");

    const parsedDocument = new DOMParser().parseFromString(
      '<main id="dom-parser" $c-props="from-parser"></main>',
      "text/html",
    );
    const parsedByDomParser = parsedDocument.getElementById("dom-parser");

    const adjacentHost = document.createElement("div");
    adjacentHost.insertAdjacentHTML(
      "beforeend",
      '<aside id="adjacent" $c-props="from-adjacent"></aside>',
    );

    const apiElement = document.createElement("div");
    apiElement.id = "api-element";
    const apiResults = {};
    for (const name of ["$c-props", "c-$c-props", "$c-on:click"]) {
      try {
        apiElement.setAttribute(name, `value:${name}`);
        apiResults[name] = {
          error: null,
          value: apiElement.getAttribute(name),
          namedItem: apiElement.attributes.getNamedItem(name)?.value ?? null,
        };
      } catch (error) {
        apiResults[name] = { error: error.name, value: null, namedItem: null };
      }
    }
    document.body.append(apiElement);

    const escapedName = CSS.escape("$c-props");
    const selectors = {
      raw: selectorProbe("[$c-props]"),
      escaped: selectorProbe(`[${escapedName}]`),
      escapedName,
      matchesEscaped: apiElement.matches(`[${escapedName}]`),
    };

    const mutationElement = document.createElement("div");
    mutationElement.setAttribute("$c-props", "v1");
    const mutationRecords = [];
    const observer = new MutationObserver((records) => {
      mutationRecords.push(
        ...records.map((record) => ({
          name: record.attributeName,
          oldValue: record.oldValue,
          currentValue: mutationElement.getAttribute(record.attributeName),
        })),
      );
    });
    observer.observe(mutationElement, { attributes: true, attributeOldValue: true });
    mutationElement.setAttribute("$c-props", "v2");
    mutationElement.removeAttribute("$c-props");
    mutationElement.setAttribute("$c-props", "v3");
    await Promise.resolve();
    observer.disconnect();

    const clone = mutationElement.cloneNode(true);

    const template = document.createElement("template");
    template.innerHTML = '<button id="in-template" $c-props="template"></button>';
    const templateElement = template.content.getElementById("in-template");
    const clonedTemplate = template.content.cloneNode(true);
    const clonedTemplateElement = clonedTemplate.getElementById("in-template");

    return {
      innerHTML: {
        direct: attributeSnapshot(direct),
        mixedCase: attributeSnapshot(mixedCase),
        serializedHost: host.innerHTML.trim(),
      },
      domParser: attributeSnapshot(parsedByDomParser),
      insertAdjacentHTML: attributeSnapshot(adjacentHost.firstElementChild),
      attributeApis: {
        results: apiResults,
        names: apiElement.getAttributeNames(),
        serialized: apiElement.outerHTML,
        afterToggleOff: (() => {
          apiElement.toggleAttribute("$c-props", false);
          return apiElement.hasAttribute("$c-props");
        })(),
      },
      selectors,
      mutation: {
        records: mutationRecords,
        final: attributeSnapshot(mutationElement),
      },
      cloneNode: attributeSnapshot(clone),
      template: {
        source: attributeSnapshot(templateElement),
        clone: attributeSnapshot(clonedTemplateElement),
        serialized: template.innerHTML,
      },
    };
  }

  function contextualParsingProbe() {
    const table = document.createElement("table");
    table.innerHTML = '<tr id="table-row"><td $c-props="cell">cell</td></tr>';
    const tableCell = table.querySelector("td");

    const contextualTable = document.createElement("table");
    contextualTable.innerHTML = "<tbody></tbody>";
    const tbody = contextualTable.tBodies[0];
    const tableRange = document.createRange();
    tableRange.selectNodeContents(tbody);
    const tableFragment = tableRange.createContextualFragment(
      '<tr id="range-row"><td $c-props="range-cell">range</td></tr>',
    );
    tbody.append(tableFragment);
    const rangeCell = tbody.querySelector("#range-row td");

    const select = document.createElement("select");
    select.innerHTML = '<option $c-props="option">One</option>';
    const option = select.options[0];

    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.innerHTML = '<g id="svg-inner" $c-props="group"></g>';
    const svgGroup = svg.querySelector("#svg-inner");
    let svgSetAttributeError = null;
    try {
      svgGroup.setAttribute("$c-model", "state");
    } catch (error) {
      svgSetAttributeError = error.name;
    }

    const svgRange = document.createRange();
    svgRange.selectNodeContents(svg);
    const svgFragment = svgRange.createContextualFragment(
      '<circle id="svg-range" $c-props="circle"></circle>',
    );
    svg.append(svgFragment);
    const svgCircle = svg.querySelector("#svg-range");

    const xml = new DOMParser().parseFromString(
      '<svg xmlns="http://www.w3.org/2000/svg"><g $c-props="xml"/></svg>',
      "image/svg+xml",
    );

    return {
      table: {
        wrapper: table.firstElementChild?.localName ?? null,
        cell: attributeSnapshot(tableCell),
        contextualCell: attributeSnapshot(rangeCell),
      },
      select: attributeSnapshot(option),
      svg: {
        inner: attributeSnapshot(svgGroup),
        innerNamespace: svgGroup.namespaceURI,
        setAttributeError: svgSetAttributeError,
        contextual: attributeSnapshot(svgCircle),
        contextualNamespace: svgCircle.namespaceURI,
        serialized: svg.outerHTML,
      },
      xmlRoundTrip: {
        parserErrors: xml.getElementsByTagName("parsererror").length,
        rootName: xml.documentElement.localName,
      },
    };
  }

  async function alpineProbe() {
    const fixture = document.getElementById("alpine-fixture");
    const count = document.getElementById("alpine-count");
    const scope = Alpine.closestDataStack(fixture)[0];
    scope.count = 2;
    await Alpine.nextTick();

    const objectBind = document.getElementById("alpine-bind-object");
    const argumentBind = document.getElementById("alpine-bind-argument");
    const numericNames = (element) =>
      element.getAttributeNames().filter((name) => /^\d+$/.test(name));

    return {
      version: Alpine.version,
      direct: {
        expression: fixture.getAttribute("$c-props"),
        renderedCount: count.textContent,
        directiveRuns: window.__componentFirstSyntax.directiveRuns,
        intercepted: window.__componentFirstSyntax.intercepted,
      },
      xBindObject: {
        props: objectBind.getAttribute("$c-props"),
        numericNames: numericNames(objectBind),
        outerHTML: objectBind.outerHTML,
      },
      xBindArgument: {
        props: argumentBind.getAttribute("$c-props"),
        numericNames: numericNames(argumentBind),
        outerHTML: argumentBind.outerHTML,
      },
    };
  }

  async function morphProbe() {
    const fixture = document.getElementById("morph-fixture");
    const original = fixture;
    const records = [];
    const observer = new MutationObserver((mutations) => {
      records.push(
        ...mutations
          .filter((mutation) => mutation.type === "attributes")
          .map((mutation) => mutation.attributeName),
      );
    });
    observer.observe(fixture, { attributes: true });

    Alpine.morph(
      fixture,
      '<div id="morph-fixture" x-data="{ value: 1 }" $c-props="v2"><span x-text="value"></span></div>',
    );
    await Alpine.nextTick();
    const changed = fixture.getAttribute("$c-props");

    Alpine.morph(
      fixture,
      '<div id="morph-fixture" x-data="{ value: 1 }"><span x-text="value"></span></div>',
    );
    await Alpine.nextTick();
    const removed = fixture.getAttribute("$c-props");

    Alpine.morph(
      fixture,
      '<div id="morph-fixture" x-data="{ value: 1 }" $c-props="v3"><span x-text="value"></span></div>',
    );
    await Alpine.nextTick();
    const added = fixture.getAttribute("$c-props");
    await Promise.resolve();
    observer.disconnect();

    return {
      sameElement: original === document.getElementById("morph-fixture"),
      changed,
      removed,
      added,
      mutationNames: records,
      finalOuterHTML: fixture.outerHTML,
    };
  }

  window.runComponentFirstSyntaxScenarios = async () => ({
    rawDom: await rawDomProbe(),
    contextualParsing: contextualParsingProbe(),
    alpine: await alpineProbe(),
    morph: await morphProbe(),
  });
})();
