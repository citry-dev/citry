// Page markup can hide the document's members behind a named element, so they are read
// through `pageDocument`; `observe()` still gets the real document, which it needs as a node.
import { pageDocument } from "./page-dom";

type VueMount = { protocol: "citry-vue-fragment/1"; appId: string; host: string; prepared: unknown };
type FragmentManifest = { vue?: VueMount };
// The same shape as the prepared runtime's error for a render from another release: the code the
// server gives a State token it no longer accepts, and status 0 for a failure found in the browser.
const pageOutOfDateError = (message: string): Error =>
  Object.assign(new TypeError(message), { status: 0, code: "stale_state" });
const isPageOutOfDate = (error: unknown): boolean =>
  error !== null && typeof error === "object" && (error as { code?: unknown }).code === "stale_state";
export type FragmentManager = { load(manifest: unknown, tag?: HTMLScriptElement): Promise<void> };
export function installFragmentManager(
  publicApi: Record<string, unknown>,
  isManagedDescendant: (node: Element, exceptAppId?: string) => boolean,
  startPrepared: (
    configuration: unknown,
    lifecycle?: { guard: () => void; nonce: string; signal: AbortSignal },
  ) => Promise<{ appId: string; app: { unmount(): void } }>,
  documentNonce = "",
  carriesPageNonce: (block: HTMLScriptElement) => boolean = (block) => block.nonce === documentNonce,
  promptReload: () => void = () => {},
): FragmentManager {
  const processed = new WeakMap<HTMLScriptElement, Promise<void>>();
  const reservedHosts = new Set<Element>();
  const pendingHosts = new Map<Element, { abort: AbortController; guard: () => void }>();
  const trackedHosts = new Map<Element, { appId: string; dispose: () => void }>();
  let pendingAttributeObserver: MutationObserver | null = null;
  let pendingGuardQueued = false;
  const queuePendingGuards = (): void => {
    if (pendingGuardQueued) return;
    pendingGuardQueued = true;
    queueMicrotask(() => {
      pendingGuardQueued = false;
      for (const pending of pendingHosts.values()) {
        try {
          pending.guard();
        } catch (error) {
          pending.abort.abort(error);
        }
      }
    });
  };
  const updatePendingAttributeObserver = (): void => {
    if (pendingHosts.size > 0 && pendingAttributeObserver === null) {
      pendingAttributeObserver = new MutationObserver(queuePendingGuards);
      pendingAttributeObserver.observe(document, { attributes: true, subtree: true });
    } else if (pendingHosts.size === 0 && pendingAttributeObserver !== null) {
      pendingAttributeObserver.disconnect();
      pendingAttributeObserver = null;
    }
  };
  const loadOnce = async (raw: unknown, tag?: HTMLScriptElement): Promise<void> => {
    if (!raw || typeof raw !== "object" || Array.isArray(raw))
      throw new TypeError("[Citry] fragment manifest is not an object.");
    const manifest = raw as FragmentManifest;
    // A fragment written by another release of the app (a newer server during a deploy) can use a
    // field or a protocol this runtime does not know. That is a page to reload, not a broken page.
    const protocol = (manifest.vue as { protocol?: unknown } | null | undefined)?.protocol;
    if (
      Object.keys(manifest).some((key) => key !== "vue") ||
      (typeof protocol === "string" && protocol !== "citry-vue-fragment/1")
    )
      throw pageOutOfDateError("[Citry] this Vue fragment comes from a different version of the app; reload the page.");
    const vue = manifest.vue;
    if (
      !vue ||
      vue.protocol !== "citry-vue-fragment/1" ||
      typeof vue.appId !== "string" ||
      !vue.appId ||
      typeof vue.host !== "string" ||
      !vue.host ||
      !vue.prepared ||
      typeof vue.prepared !== "object" ||
      (vue.prepared as { host?: unknown }).host !== vue.host ||
      (vue.prepared as { manifest?: { appId?: unknown } }).manifest?.appId !== vue.appId
    )
      throw new TypeError("[Citry] fragment manifest has no valid bound Vue mount descriptor.");
    const hosts = pageDocument.querySelectorAll(vue.host);
    if (hosts.length !== 1 || !pageDocument.body.contains(hosts[0]))
      throw new TypeError("[Citry] Vue fragment host must resolve once inside the document body.");
    const host = hosts[0];
    const initialParent = host.parentNode;
    const initialTagParent = tag?.parentNode ?? null;
    if (reservedHosts.has(host)) throw new TypeError("[Citry] Vue fragment host is already mounting.");
    if ((tag && isManagedDescendant(tag)) || isManagedDescendant(host))
      throw new TypeError("[Citry] a Vue fragment cannot be inserted inside a managed Vue host.");
    const guard = (): void => {
      const current = pageDocument.querySelectorAll(vue.host);
      if (
        current.length !== 1 ||
        current[0] !== host ||
        !pageDocument.body.contains(host) ||
        host.parentNode !== initialParent ||
        (tag !== undefined && (!pageDocument.body.contains(tag) || tag.parentNode !== initialTagParent)) ||
        isManagedDescendant(host, vue.appId)
      )
        throw new TypeError("[Citry] Vue fragment host changed while mounting.");
    };
    reservedHosts.add(host);
    const abort = new AbortController();
    pendingHosts.set(host, { abort, guard });
    updatePendingAttributeObserver();
    let mounted: { appId: string; app: { unmount(): void } } | null = null;
    try {
      guard();
      mounted = await startPrepared(vue.prepared, { guard, nonce: documentNonce, signal: abort.signal });
      guard();
      trackedHosts.set(host, { appId: mounted.appId, dispose: () => mounted?.app.unmount() });
    } catch (error) {
      try {
        mounted?.app.unmount();
      } catch (cleanupError) {
        console.error("[Citry] failed to dispose a rejected Vue fragment:", cleanupError);
      }
      throw error;
    } finally {
      pendingHosts.delete(host);
      updatePendingAttributeObserver();
      reservedHosts.delete(host);
    }
  };
  // A fragment the prepared runtime refuses for the same reason (a render compiled by another
  // release) fails with the same code, so both offer the page's one reload prompt. The load still
  // rejects, so a caller of `Citry.fragments.load` sees the failure.
  const load = (raw: unknown, tag?: HTMLScriptElement): Promise<void> =>
    loadOnce(raw, tag).catch((error: unknown) => {
      if (isPageOutOfDate(error)) promptReload();
      throw error;
    });
  const manager: FragmentManager = {
    load(raw, tag) {
      if (tag) {
        const prior = processed.get(tag);
        if (prior) return prior;
        tag.dataset.citryProcessed = "";
        // A data block found in the page could come from injected markup, and the fragment's
        // scripts load with the page's nonce. Under a nonce-based CSP the server stamps the
        // page's nonce on the blocks it writes, and injected markup cannot set it, so a block
        // without it is refused, as startDocument refuses a configuration block. When the
        // runtime's own tag has no nonce there is nothing to compare, and every block starts.
        const promise =
          documentNonce && !carriesPageNonce(tag)
            ? Promise.reject(
                new Error(
                  "[Citry] the Vue fragment's data block does not carry the page's CSP nonce." +
                    " Serialize the fragment with csp_nonce set to the page's nonce.",
                ),
              )
            : load(raw, tag);
        processed.set(tag, promise);
        return promise;
      }
      return load(raw, tag);
    },
  };
  publicApi.fragments = manager;
  const process = (tag: HTMLScriptElement): void => {
    if (processed.has(tag) || !tag.textContent.trim()) return;
    let manifest: unknown;
    try {
      manifest = JSON.parse(tag.textContent);
    } catch (error) {
      console.error("[Citry] failed to parse Vue fragment manifest:", error);
      return;
    }
    void manager.load(manifest, tag).catch((error) => console.error("[Citry] discarded Vue fragment:", error));
  };
  const scan = (node: Node): void => {
    if (!(node instanceof Element)) return;
    // The added node can be a form whose field hides `matches` or `querySelectorAll`, so call the
    // built-in methods.
    if (Element.prototype.matches.call(node, 'script[type="application/json"][data-citry-vue-fragment]'))
      process(node as HTMLScriptElement);
    (
      Element.prototype.querySelectorAll.call(
        node,
        'script[type="application/json"][data-citry-vue-fragment]',
      ) as NodeListOf<HTMLScriptElement>
    ).forEach(process);
  };
  let connectivityQueued = false;
  new MutationObserver((records) => {
    records.forEach((record) => {
      record.addedNodes.forEach(scan);
    });
    if (!connectivityQueued && (pendingHosts.size || trackedHosts.size)) {
      connectivityQueued = true;
      queueMicrotask(() => {
        connectivityQueued = false;
        queuePendingGuards();
        for (const [host, tracked] of trackedHosts) {
          if (host.isConnected) continue;
          trackedHosts.delete(host);
          try {
            tracked.dispose();
          } catch (error) {
            console.error("[Citry] failed to dispose a removed Vue fragment:", error);
          }
        }
      });
    }
  }).observe(document, { childList: true, subtree: true });
  pageDocument
    .querySelectorAll<HTMLScriptElement>('script[type="application/json"][data-citry-vue-fragment]')
    .forEach(process);
  return manager;
}
