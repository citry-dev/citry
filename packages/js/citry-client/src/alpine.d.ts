/**
 * Narrow, local type declarations for the pinned AlpineJS 3.15.12 and
 * `@alpinejs/morph` 3.15.12. Neither package ships its own types, so these
 * declare exactly the surface the runtime calls and nothing more; the point
 * is an honest type-check without pretending to type all of Alpine.
 *
 * `addScopeToNode` and `initTree` here plus the `Element._x_dataStack` and
 * `_x_ignore` fields (declared in `citry-events.ts`) are PINNED-VERSION
 * PRIVATE APIs. The pins, reasoning, and canary that trips on drift are
 * described in the header of `src/citry-events.ts`. Keep these declarations
 * in step with what the canary asserts.
 */

declare module "alpinejs" {
  export interface AlpineDirective {
    expression?: string | (() => unknown);
    modifiers?: string[];
    original: string;
    type?: string | null;
    value?: string | null;
  }

  export type AlpineDirectiveCallback = ((el: Element, directive: AlpineDirective, utilities: object) => unknown) & {
    inline?: (el: Element, directive: AlpineDirective, utilities: object) => unknown;
  };

  /**
   * The Alpine object the package default-exports, also installed at
   * `globalThis.Alpine` so morph's bridge and page scripts can reach it.
   */
  export interface AlpineGlobal {
    /** Registers a plugin; Alpine calls it back with this same object. */
    plugin(plugin: (alpine: AlpineGlobal) => void): void;
    /** Adds a selector for roots Alpine walks besides `[x-data]`. */
    addRootSelector(selectorFn: () => string): void;
    /** Runs the callback on each element just before Alpine initializes it. */
    interceptInit(callback: (el: Element) => void): void;
    /** Registers cleanup for one exact Alpine attribute invocation. Pinned private API. */
    onAttributeRemoved(node: Element, name: string, callback: () => void): void;
    /** Registers a `$name` magic; the callback gets the element the expression runs on. */
    magic(name: string, callback: (el: Element) => unknown): void;
    /** Registers a directive and returns its ordering handle. Public plugin API. */
    directive(name: string, callback: AlpineDirectiveCallback): { before(other: string): void };
    /**
     * Evaluates an Alpine expression string against the element's scope stack
     * (the magics and any user `x-data`/`x-for` scopes in play are visible);
     * `extras.scope` adds names the expression can read (e.g. `$event`). A
     * synchronous expression's value is returned directly. Public API.
     */
    evaluate(el: Element, expression: string, extras?: { scope?: object }): unknown;
    /** Wraps the target in Alpine's reactivity proxy. */
    reactive<T extends object>(target: T): T;
    /**
     * Runs the callback now and re-runs it (through Alpine's scheduler) when
     * any reactive value it read changes. Returns the handle `release` takes.
     * Public API; the state-binding effects ride it.
     */
    effect(callback: () => void): object;
    /** Stops a reactive effect created by `effect`. Public API. */
    release(effectReference: object): void;
    /** Boots Alpine: walks the document and initializes every root. */
    start(): void;
    /**
     * PINNED-VERSION PRIVATE API: pushes `scope` onto the element's scope
     * stack, creating `_x_dataStack` (scope first) if the element has none.
     * The isolation mechanism in `attachBoundaryScope` builds on this.
     */
    addScopeToNode(node: Element, scope: object, referenceNode?: Node): () => void;
    /** PINNED-VERSION PRIVATE API: returns the inherited proxy layers for a node. */
    closestDataStack(node: Node): object[];
    /** PINNED-VERSION PRIVATE API: merges Alpine scope layers without copying them. */
    mergeProxies(objects: object[]): object;
    /** PINNED-VERSION PRIVATE API: registers physical element cleanup. */
    onElRemoved(node: Element, callback: () => void): void;
    /** PINNED-VERSION PRIVATE API: walks one element subtree. */
    walk(node: Element, callback: (el: Element) => void): void;
    /** PINNED-VERSION PRIVATE API: initializes a detached morph counterpart from a live source. */
    cloneNode(from: Element, to: Element): void;
    /** PINNED-VERSION PRIVATE API: follows Alpine root and teleport ancestry. */
    closestRoot(node: Element): Element | undefined;
    /**
     * PINNED-VERSION PRIVATE API: initializes one subtree. Citry calls this
     * after releasing a fragment root that was held with `_x_ignore` while
     * its component callback branch settled.
     */
    initTree(node: Element): void;
    /**
     * The raw morph function the `@alpinejs/morph` plugin installs (the
     * package's named export is the installer, WP6 spike F1). `to` may be an
     * HTML string (morph parses it and consumes only the first element) or a
     * pre-parsed element. The hook signature carries a sixth `skipUntil`
     * argument beyond the five the runtime uses (spike finding F10).
     */
    morph(
      from: Element,
      to: string | Element,
      options?: {
        key?(el: Element): string | null | undefined | false;
        updating?(from: Node, to: Node, childrenOnly: () => void, skip: () => void, skipChildren: () => void): void;
      },
    ): Element;
  }

  const Alpine: AlpineGlobal;
  export default Alpine;
}

declare module "@alpinejs/morph" {
  import type { AlpineGlobal } from "alpinejs";

  /**
   * The default export is the plugin INSTALLER, not the raw morph function
   * (WP6 spike F1): register it with `Alpine.plugin(...)` and the raw
   * function becomes `Alpine.morph`.
   */
  const morphPlugin: (alpine: AlpineGlobal) => void;
  export default morphPlugin;
}

declare module "alpinejs/src/index" {
  import type { AlpineGlobal } from "alpinejs";

  const Alpine: AlpineGlobal;
  export default Alpine;
}
