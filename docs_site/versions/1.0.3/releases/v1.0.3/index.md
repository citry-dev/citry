---
title: v1.0.3
url: https://citry.dev/v/1.0.3/releases/v1.0.3/
description: "What changed in citry v1.0.3."
---
# v1.0.3

Citry 1.0.3 is a security release. It requires citry-core 2.1.2, which
installs with it.

## Fixes

- Security: template text can no longer read private attributes
  through a string's `format` method, or run a method marked `@unsafe`
  or `alters_data` by passing it to another function, such as the `key`
  of `list.sort`. The fix is in citry-core 2.1.2; its changelog lists
  what the sandbox now refuses. See
  [GHSA-c42m-36vw-xvm3](https://github.com/citry-dev/citry/security/advisories/GHSA-c42m-36vw-xvm3).