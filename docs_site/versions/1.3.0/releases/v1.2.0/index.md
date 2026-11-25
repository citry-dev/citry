---
title: v1.2.0
url: https://citry.dev/v/1.3.0/releases/v1.2.0/
description: "What changed in citry v1.2.0."
---
# v1.2.0

Citry 1.2.0 adds Experimental APIs for host integrations such as
citry-django: CSRF names set in Python, the CSP nonce for fragments
that a host's own requests load, and `CitryRender.needs_csrf_token()`.
It still requires citry-core 2.1.2.

## Added

- Experimental: you can now name your CSRF cookie and header in Python,
  with `_csrf_cookie` and `_csrf_header` in
  `extensions_defaults["events"]`, and Citry's browser code uses them.
  Integrations that embed Citry in another framework, such as
  citry-django, no longer need a script that calls `Citry.configure()`
  for this, except on a page without a CSP nonce that only gets
  fragments. See
  [CSRF cookie and header](https://citry.dev/security/#csrf-names).
- Experimental: a fragment that your own code loads, with htmx or
  `fetch()`, can now carry the CSP nonce of the tab that asked for it,
  even with several tabs open. Send `Citry.pageNonce()` in the
  `X-Citry-Page-Nonce` header and pass
  `page_nonce_from_headers(request.headers)` as `csp_nonce`; an Events
  `Render` uses the header on its own. Integrations such as citry-django
  can stop keeping the nonce in the session. See
  [Nonces in fragments](https://citry.dev/security/#html-fragments).
- You can now ask a render, before you serialize it, whether the
  browser may send Citry's CSRF token from it, with the Experimental
  `CitryRender.needs_csrf_token()`. It covers Events calls and the
  i18n message requests of a locale switch. It is for host integrations
  such as citry-django, which can use it to set the CSRF cookie only on
  pages that need it. `CitryRender.has_server_events()` answers for
  Events calls alone. See
  [Find renders that need the CSRF token](https://citry.dev/advanced/asset-placement/#find-renders-that-need-the-csrf-token).