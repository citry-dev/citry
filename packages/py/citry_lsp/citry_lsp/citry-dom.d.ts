// Citry's additions to the DOM types for component JavaScript and templates.
//
// A query by CSS selector cannot say which kind of element it finds, so the
// DOM types return `Element`, which lacks `focus()`, `dataset`, `checked`
// and most of what page code reads. TypeScript code fixes that with a cast,
// but a template cannot cast at all, and JavaScript needs a JSDoc cast.
// Citry's editor and `citry check --types` therefore leave the result of a
// selector query untyped (`any`), as it is in plain JavaScript. A query by
// tag name keeps the tag's own type, such as `HTMLInputElement` for "input".
//
// TypeScript lists these overloads before the DOM's own, so they win.

interface ParentNode {
    querySelector<K extends keyof HTMLElementTagNameMap>(selectors: K): HTMLElementTagNameMap[K] | null;
    querySelector<K extends keyof SVGElementTagNameMap>(selectors: K): SVGElementTagNameMap[K] | null;
    querySelector<E extends Element = any>(selectors: string): E | null;
    querySelectorAll<K extends keyof HTMLElementTagNameMap>(selectors: K): NodeListOf<HTMLElementTagNameMap[K]>;
    querySelectorAll<K extends keyof SVGElementTagNameMap>(selectors: K): NodeListOf<SVGElementTagNameMap[K]>;
    querySelectorAll<E extends Element = any>(selectors: string): NodeListOf<E>;
}

interface Element {
    closest<K extends keyof HTMLElementTagNameMap>(selector: K): HTMLElementTagNameMap[K] | null;
    closest<K extends keyof SVGElementTagNameMap>(selector: K): SVGElementTagNameMap[K] | null;
    closest<E extends Element = any>(selectors: string): E | null;
}

// Scripts on the page add their own globals to `window`, such as
// `window.htmx`. No type file describes them, so a name `window` does not
// declare reads as `any` instead of an error. Members the DOM declares keep
// their own types.
interface Window {
    [name: string]: any;
}
