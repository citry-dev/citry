# Security policy

## Supported versions

Security fixes ship as a new release of the affected package. Before you
report a problem, please check that it still happens with the newest
release of the affected package, or with a release the table below
lists.

| Package | Releases that get security fixes |
| ------- | -------------------------------- |
| `citry` | The newest 1.x minor release (see below) |
| `citry-core` | The version that a supported `citry` release installs |
| `citry-lsp` | The newest 1.x release |
| VS Code extension (`citry-dev.citry`) | The newest 1.x release |
| `pygments-citry` | The newest 1.x release |
| `citry-ui` | The newest release (0.x, alpha) |

For `citry`, only the newest 1.x minor release gets fixes: once 1.2.0 is
out, a fix arrives as 1.2.1, not as a 1.1.x release. After 2.0.0 comes
out, the last 1.x minor release keeps getting security fixes, but no
other fixes, for 12 months. The 0.x releases get no fixes.

The [Versioning and support](https://citry.dev/about/versioning/) page
explains what each kind of release may change and how long a deprecated
feature keeps working.

## Reporting a vulnerability

**Please do not open a public issue for security problems.**

Report privately through GitHub's [private vulnerability
reporting](https://github.com/citry-dev/citry/security/advisories/new): open the
repository's **Security** tab and choose **Report a vulnerability**. That opens a
private advisory visible only to the maintainers.

Include, as far as you can:

- the affected package and version,
- a description of the issue and its impact,
- steps to reproduce (a minimal component or template is ideal), and
- any known workaround.

## What to expect

- We aim to acknowledge a report within a few days.
- Once the issue is confirmed we will work on a fix, coordinate a release, and
  keep you posted; we are happy to credit you in the release notes.
- Please give us a reasonable window to ship a fix before any public disclosure.

## Past security reviews

Before some changes merge, a separate reviewer checks their security.
[`docs/security/reviews/`](docs/security/reviews/) keeps a short public
record of each such review: what was checked, how, and what was left
untested.
