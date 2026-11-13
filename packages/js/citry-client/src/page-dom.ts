/**
 * Read Citry's own objects and the document's members in a way page markup cannot change.
 *
 * A browser turns some elements into properties of `window` and `document`. An element with
 * an `id` becomes a property of `window` when `window` has no own property of that name, and a
 * `form`, `img`, `iframe`, `embed` or `object` with a `name` becomes a property of `document`
 * that hides the document's built-in member of that name (`<form name="createElement">` makes
 * `document.createElement` that form). When data chooses such an `id` or `name`, a plain
 * lookup gets an element instead of the function or object Citry's browser code expects, and
 * the runtime stops working on that page. The helpers here read past those elements.
 *
 * `_vue/client.js` is hand-written JavaScript that ships without a bundler, so it carries its
 * own copy of `ownGlobal`, `builtInMember` and `documentMembers`; keep the two in step.
 */

const hasOwn = Object.prototype.hasOwnProperty;

/**
 * Read a global that Citry's scripts define, such as `__citryRuntime` or `Citry`.
 *
 * Every script that defines one assigns it to `window`, which makes it an own property. An
 * element's `id` is never an own property of `window` (the browser finds it on an object
 * further up the prototype chain), so an element with that id reads as `undefined` here.
 */
export const ownGlobal = (name: string): unknown =>
  hasOwn.call(globalThis, name) ? (globalThis as Record<string, unknown>)[name] : undefined;

/**
 * The built-in member named `key` of `target`, or undefined when no prototype defines it.
 *
 * A named element shows up as an own data property (on `document`, or a named field on a
 * `form`), so own data properties are passed over. An own getter or setter can only come from a
 * script (a test's stub, a polyfill, the real document's `location`), so it is kept.
 */
export const builtInMember = (target: object, key: PropertyKey): PropertyDescriptor | undefined => {
  const own = Object.getOwnPropertyDescriptor(target, key);
  if (own !== undefined && (own.get !== undefined || own.set !== undefined)) return own;
  for (let proto = Object.getPrototypeOf(target); proto !== null; proto = Object.getPrototypeOf(proto)) {
    const descriptor = Object.getOwnPropertyDescriptor(proto, key);
    if (descriptor !== undefined) return descriptor;
  }
  return undefined;
};

/**
 * Return a stand-in for the document whose members are always the browser's built-in ones.
 *
 * Each read finds the member through {@link builtInMember}, calls a getter with the real
 * document, and binds a method to it. A name no prototype defines falls back to an ordinary
 * read, which serves a test's plain-object document. The document is read again on every
 * access, because tests swap `globalThis.document` after this module loads.
 *
 * Use the real `document` where it is passed to a DOM call (`observer.observe(document)`) or
 * compared (`target === document`): the browser rejects this proxy as an argument, and it never
 * equals the document.
 */
export const documentMembers = (currentDocument: () => Document): Document => {
  // One bound copy per method and document, so a hot path such as Vue creating elements does
  // not build a new function on every call.
  const bound = new WeakMap<object, { target: object; method: unknown }>();
  const bind = (method: (...args: unknown[]) => unknown, target: object): unknown => {
    const cached = bound.get(method);
    if (cached !== undefined && cached.target === target) return cached.method;
    const boundMethod = method.bind(target);
    bound.set(method, { target, method: boundMethod });
    return boundMethod;
  };
  return new Proxy({} as Document, {
    get(_shell, key) {
      const target = currentDocument();
      const descriptor = builtInMember(target, key);
      let value: unknown;
      if (descriptor === undefined) value = Reflect.get(target, key);
      else if (descriptor.get !== undefined) return descriptor.get.call(target);
      else if (descriptor.set !== undefined) return undefined;
      else value = descriptor.value;
      return typeof value === "function" ? bind(value as (...args: unknown[]) => unknown, target) : value;
    },
    set(_shell, key, value) {
      const target = currentDocument();
      const descriptor = builtInMember(target, key);
      // A setter such as `cookie` runs on the real document; anything else is written to it.
      if (descriptor?.set !== undefined) {
        descriptor.set.call(target, value);
        return true;
      }
      return Reflect.set(target, key, value);
    },
  });
};

/** The page's document read through {@link documentMembers}. */
export const pageDocument: Document = documentMembers(() => globalThis.document);

/**
 * The page's origin, or null outside a browser.
 *
 * It is `window.origin`, which is "null" in a document sandboxed without `allow-same-origin`
 * even when its address is real, so such a document never matches any URL's origin.
 */
export const pageOrigin = (): string | null => {
  const scope = globalThis as { location?: { origin?: unknown }; origin?: unknown };
  if (scope.location === undefined) return null;
  return typeof scope.origin === "string" ? scope.origin : String(scope.location.origin);
};

/** Whether `target` is on the page's own origin; never true for an opaque ("null") origin. */
export const onPageOrigin = (target: URL): boolean => {
  const origin = pageOrigin();
  return origin !== null && target.origin !== "null" && target.origin === origin;
};

/**
 * Resolve a URL that Citry's browser code requests or navigates to against the page's own address.
 *
 * The browser resolves a relative URL against `document.baseURI`, which a `<base href>` element in
 * the page sets, so a request or navigation resolved that way could go to the site the element
 * names. Resolving against `location.href` keeps a relative URL on the page that the server
 * wrote it for. A document whose address cannot serve as a base, such as `about:srcdoc` or
 * `about:blank`, takes its base URL from the page that created it, so there the base URL is
 * used, and only when it is on the document's own origin; otherwise this throws.
 *
 * Returns null outside a browser (no `location`), where there is no page to resolve against.
 * `_vue/client.js` keeps a copy of this rule for the redirect and URL actions; keep the two in step.
 */
export const resolveOnPage = (url: string): URL | null => {
  const location = (globalThis as { location?: { href?: unknown } }).location;
  if (location === undefined || typeof location.href !== "string") return null;
  try {
    return new URL(url, location.href);
  } catch {
    let inherited: URL;
    try {
      inherited = new URL(url, pageDocument.baseURI);
    } catch {
      throw new Error(`Citry cannot resolve the URL ${JSON.stringify(url.slice(0, 80))}.`);
    }
    if (!onPageOrigin(inherited)) throw new Error("Citry refused a URL that does not resolve to this page's origin.");
    return inherited;
  }
};
