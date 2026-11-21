---
title: v1.0.0
url: https://citry.dev/v/1.2.0/releases/v1.0.0/
description: "What changed in citry v1.0.0."
---
# v1.0.0

Citry 1.0.0 is the first stable release. Code that uses what the docs
describe keeps working in every 1.x release, apart from experimental
features and security fixes, so you can allow any 1.x with
`citry>=1.0.0,<2`.
[Versioning and support](https://citry.dev/about/versioning/) says what
this covers, what is experimental, which versions get fixes, and how
deprecations work.

The upgrade from 0.9.x is small. Most apps notice two changes: the
signed State token that Citry sends to the page now expires after 24
hours, and in production Citry no longer asks visitors to reload an
out-of-date page, so add your own message for them.

If you use citry-lsp or the VS Code extension, upgrade them to 1.0.0
together with Citry, because an older extension refuses citry-lsp 1.x.
After that,
any citry-lsp 1.x works with any Citry 1.x, so you can upgrade either
one first. citry-ui 0.6.0 is released alongside and needs Citry 1.0.0
or later.

## Upgrading from 0.9.x

If you are on a release older than 0.9.x, upgrade to 0.9.x before you
start. [Upgrade to Citry 1.0.0](https://citry.dev/guides/upgrading-to-1-0-0/)
lists the steps in order.

- **State sent to the page now expires after 24 hours by default:**
  Citry sends each component's State to the page as a signed string, the
  State token. The token of a component whose `State` sets no
  `_max_age` used to work until you changed the signing secret. Now it
  stops working 24 hours after Citry issues it, as server-stored State
  already did. Citry issues a new token when it renders the component
  and after a call that changes State, so the pages affected are those
  whose State has not changed for more than 24 hours. A call with an
  expired token does not run its handler: it gets a `stale_state` error
  (see the next entry). Tokens issued before
  the upgrade also expire 24 hours after Citry issued them. No setting turns
  expiry off; to keep a token working for longer, set a longer
  `_max_age`:

    ```python
    from datetime import timedelta

    class State:
        _max_age = timedelta(days=7)
    ```

- **Citry no longer asks visitors to reload an out-of-date page in
  production:** when a call fails with `stale_state`, most often because
  the page's State token expired, a visitor whose call failed got a
  confirm dialog asking whether to reload, once per page. Now only a page that
  `Citry(mode="development")` rendered asks. In production Citry asks
  nothing, never reloads by itself, and writes one console warning per
  page, so calls from that component keep failing until the visitor
  reloads the page. Show your own message from a listener, as
  [Handle out-of-date pages](https://citry.dev/reference/browser-apis/#out-of-date-pages)
  shows:

    ```js
    document.addEventListener("citry:events:stale", (event) => {
      if (event.detail.reason !== "version") return;
      event.preventDefault();
      showReloadBanner();
    });
    document.addEventListener("citry:fragments:stale", (event) => {
      event.preventDefault();
      showReloadBanner();
    });
    ```

- **`State._max_age` must be at least one second:** a shorter value,
  including `timedelta(0)`, made every token expire as soon as Citry
  issued it, and now raises `ValueError` when the class is defined.

- **A `c-bind` key may not use an attribute name Citry reserves:** on
  an HTML element, a key such as `c-render-id`, `data-cid-x`,
  `data-ccss-x`, or `data-citry-key` now raises `ValueError`, in any
  letter case. Citry uses these names to find its own elements and
  placeholders in the page, so a name taken from request data could
  make the server copy another component's HTML into the page.
  `<c-element>` with `c-is` or `c-bind` refuses them even when you write
  them in the template. Rename such an attribute to a `data-` name of
  your own; the full list is under
  [Names Citry reserves](https://citry.dev/advanced/html-attributes/#names-citry-reserves).

## Fixes

- When the installed `citry-lsp` does not match your citry release,
  `citry check --types` now names the `citry-lsp` versions to install,
  rather than always asking you to upgrade it.
- With `security_javascript="omit"`, Citry now drops a `Script` or
  `Style` dependency whose URL is a `javascript:` URL written as `Markup`
  with a character reference, such as
  `Style(url=Markup("java&#115;cript:x"))`, and removes such a URL from
  a dependency's attributes, as it already did for a plain string. Before,
  Citry reported it but left it on the page.
- **Server-stored State works on PyPy:** a component whose State sets
  `_storage = "server"` no longer fails to render on PyPy when the cache
  is an `InMemoryCache`, including the default cache. The error was a
  `TypeError` from `sys.getsizeof`. CPython is unchanged.
- **Pydantic classes work with Events on PyPy:** with Pydantic 2.13.0
  or newer installed, Events now accepts Pydantic State and event data
  classes on PyPy. Before, it refused every one of them with "Events
  needs Pydantic 2.13.0 or newer".
- **Lookalike `javascript:` letters are no longer reported:**
  `security_csp`, `security_javascript` and `citry check` no longer
  report a link that spells `javascript:` with `ſ`, `ı` or `İ`, such as
  `href="java&#383;cript:x"`. Browsers read such a link as a relative URL
  and run nothing.

## Added

- You can now find out when the page gets a Vue fragment from another
  Citry release: the page fires the new `citry:fragments:stale` event and
  does not start the fragment. Before, the fragment failed with only a
  console error.

## Changed

- If a later Citry release changes the State token format, a page from
  the other release gets `stale_state` (409) during a deploy, and Citry
  fires `citry:events:stale`. Before, it got `invalid_state`
  (403) and an error.
- During a later deploy, a page that Citry 1.0.0 rendered now fails an
  event call with `stale_state`, as an expired State token does, when
  the response comes from another release and the page's browser code
  cannot read it. Before, the call failed with a plain error.