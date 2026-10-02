---
title: Community extensions
description: Find independently maintained packages that connect Citry to frameworks and add cross-cutting behavior.
---

# Community extensions

You want Citry to work with your web framework, or to add the same
behavior to many components at once. An extension is a package that does
that. Each package below shows who maintains it: "Citry maintained" or
"Community maintained".

<c-community-packages category="extension" />

## Publish an extension

[Extensions](/advanced/extensions/) explains how to write an extension and
how applications install one.

To get your package listed here, add an entry to
[`community_packages.yml`](https://github.com/citry-dev/citry/edit/main/docs_site/data/community_packages.yml){: target="_blank" rel="noopener"}
and open a pull request. The package name does not need a `citry-` prefix,
but the package must have public source code and state which Citry
versions it supports.

Citry maintainers review every listing. A listing helps people find your
package. It is not a security audit, and it does not mean the Citry
project supports the package.
