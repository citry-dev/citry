// Reviewed decisions the generator cannot make from the IDL and browser data.
// The first two lists cover settable lowercase string attributes whose IDL
// carries no reflection marker. Each entry is `Interface.member`, and the
// generator refuses to run while such a member is on neither list. The later
// lists each explain their own case.
//
// A member mirrors when setting it to a string leaves that same string in the
// content attribute of the same name. The browser test checks each lowercase
// PROSE_MIRRORING entry that a current browser has; NOT_MIRRORING entries lead
// to Unknown, which needs no check.

/** Members whose spec says, in prose, that they mirror the same-named attribute. */
export const PROSE_MIRRORING = new Set([
  "Element.id",
  "Element.slot",
  "HTMLElement.dir",
  "HTMLElement.popover",
  "HTMLFencedFrameElement.allow",
  "HTMLFencedFrameElement.height",
  "HTMLFencedFrameElement.width",
  "HTMLFormElement.autocomplete",
  "HTMLFormElement.enctype",
  "HTMLFormElement.method",
  "HTMLIFrameElement.csp",
  "HTMLIFrameElement.loading",
  "HTMLIFrameElement.srcdoc",
  "HTMLImageElement.decoding",
  "HTMLImageElement.loading",
  "HTMLInputElement.capture",
  "HTMLInputElement.type",
  "HTMLLinkElement.as",
  "HTMLMediaElement.loading",
  "HTMLMediaElement.preload",
  "HTMLPortalElement.src",
  "HTMLScriptElement.src",
  "HTMLTableCellElement.scope",
  "HTMLTrackElement.kind",
  // Camel-case members whose older lowercase spelling (Chrome 101's
  // `fetchpriority`) shipped too: the old spelling mirrors the same
  // attribute, which the generator reads from these entries.
  "HTMLImageElement.fetchPriority",
  "HTMLLinkElement.fetchPriority",
  "HTMLScriptElement.fetchPriority",
]);

/** Members that do not leave the same string in the same-named attribute. */
export const NOT_MIRRORING = new Set([
  // Setting these changes the element's text, not an attribute.
  "HTMLAnchorElement.text",
  "HTMLOptionElement.text",
  "HTMLScriptElement.text",
  "HTMLTitleElement.text",
  // `value` holds the control's current value, separate from its attribute.
  "HTMLInputElement.value",
  "HTMLOutputElement.value",
  "HTMLSelectElement.value",
  "HTMLTextAreaElement.value",
  // These mirror a differently named attribute (`enctype`, `char`).
  "HTMLFormElement.encoding",
  "HTMLTableCellElement.ch",
  "HTMLTableColElement.ch",
  "HTMLTableRowElement.ch",
  "HTMLTableSectionElement.ch",
  // `nonce` keeps the value in an internal slot and hides the attribute.
  "HTMLOrSVGOrMathMLElement.nonce",
  // These rewrite part of `href`.
  "HyperlinkElementUtils.hash",
  "HyperlinkElementUtils.host",
  "HyperlinkElementUtils.hostname",
  "HyperlinkElementUtils.password",
  "HyperlinkElementUtils.pathname",
  "HyperlinkElementUtils.port",
  "HyperlinkElementUtils.protocol",
  "HyperlinkElementUtils.search",
  "HyperlinkElementUtils.username",
]);

/**
 * Boolean members an interface has had since before the floor, where BCD
 * records that support only as a partial implementation of a member that
 * later moved. Each entry is `Interface.member`.
 *
 * `autofocus` moved from the form controls to HTMLElement (Chrome 79,
 * Firefox 110, Safari 15.4). BCD lists the controls' older support as a
 * partial implementation of HTMLElement.autofocus, so without these entries
 * `<input autofocus>` would count as unsupported at the floor.
 */
export const SUPPORTED_AT_FLOOR = new Set([
  // Safari on iOS lets the property be set without disabling the group
  // (WebKit bug 227042). BCD marks that as partial, but the property still
  // mirrors the attribute, which is all the table needs.
  "HTMLOptGroupElement.disabled",
  "HTMLButtonElement.autofocus",
  "HTMLInputElement.autofocus",
  "HTMLSelectElement.autofocus",
  "HTMLTextAreaElement.autofocus",
]);

/**
 * Boolean attributes whose meaning depends only on being present, written by
 * the server as present or absent, as Vue's own server renderer does, even
 * though some browser at the floor lacks the member.
 *
 * Where a browser lacks the member, Vue writes the attribute with
 * `setAttribute`, so `true` leaves `open="true"` and `false` leaves
 * `open="false"`. For `true` and `""`, every browser ends with the attribute
 * present. For `false` in such a browser, Vue's browser path leaves the
 * attribute present while the server leaves it out. Hydration re-applies a
 * dynamic binding, so the page then ends as Vue builds it; a static or
 * constant value keeps the server's version, which is what the author asked
 * for. The hand list before #444 wrote these the same way.
 *
 * - `open` on `<dialog>`: `<dialog>` arrived in Firefox 98. Before it,
 *   `<dialog>` is an unknown element, but the built-in stylesheet still hides
 *   `dialog:not([open])`.
 * - `inert` arrived in Safari 15.5 and Firefox 112.
 * - `autofocus` on any element arrived in Firefox 110; before it the
 *   attribute is ignored outside the form controls.
 */
export const PRESENCE_ONLY_BOOLEANS = new Set([
  "HTMLDialogElement.open",
  "HTMLElement.inert",
  "HTMLElement.autofocus",
]);

/**
 * Names a browser build exposes on every HTML element although no IDL or
 * browser data records them, so the generator cannot know them. Each is
 * Unknown everywhere, so the server leaves an element that uses one to the
 * browser, and the browser test does not check them.
 *
 * - `cue` and `cuebackground`: the WebKit build Playwright 1.64.1 installs
 *   (WebKit 27.2) has them as boolean properties on every element. Their
 *   names suggest WebKit's work on WebVTT cues; whether a shipping Safari
 *   has them is not recorded anywhere the generator reads.
 */
export const UNRECORDED_MEMBERS = new Set(["cue", "cuebackground"]);
