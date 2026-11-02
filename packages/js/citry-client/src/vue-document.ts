/**
 * The `document` that Citry's Vue bundle sees in place of the global one.
 *
 * The Vue build injects this module (`inject` in build-support.mjs), so every free `document`
 * in Vue's code reads this export. Vue keeps a reference to `document` and calls
 * `createElement`, `createTextNode` and `querySelector` on it; through `pageDocument` those
 * calls reach the document's real methods even when the page holds an element named after
 * one of them. Where no document exists (a test run in Node), this stays `undefined`, so
 * Vue's own `typeof document` check still finds no document.
 */
import { pageDocument } from "./page-dom";

export const document: Document | undefined = typeof globalThis.document === "undefined" ? undefined : pageDocument;
