// Page markup can hide the document's members behind a named element, so they are read
// through `pageDocument`; `observe()` still gets the real document, which it needs as a node.
import { pageDocument } from "./page-dom";

type VueMount = { protocol: "citry-vue-fragment/1"; appId: string; host: string; prepared: unknown };
type FragmentManifest = { vue?: VueMount };
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
  const load = async (raw: unknown, tag?: HTMLScriptElement): Promise<void> => {
    if (!raw || typeof raw !== "object" || Array.isArray(raw))
      throw new TypeError("[Citry] fragment manifest is not an object.");
    const manifest = raw as FragmentManifest;
    if (Object.keys(manifest).some((key) => key !== "vue"))
      throw new TypeError("[Citry] Vue fragments cannot carry legacy dependency state.");
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
