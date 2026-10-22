---
title: The emSign certificate incident and Citry
description: What the eMudhra (emSign) certificate incident means for Citry users, what to update, and what we changed in Citry's own builds.
date: 2026-10-22T16:00:00+02:00
author: Juro Oravec
author_url: /community/people/
tags: Security, Project updates
---

On October 20, 2026, the Python Security Developer-in-Residence
[announced](https://discuss.python.org/t/information-for-python-users-regarding-emudhra-emsign-ca-certificate-security-incident/109576){: target="\_blank" rel="noopener"}
that the private keys of the eMudhra (emSign) certificate authorities can
be recovered. Anyone who has those keys can pretend to be any HTTPS site,
including pypi.org, to a program that still trusts those authorities.

This post explains what that means if you use Citry, what to update on
your machine and in your CI, and what we changed in Citry.

## What happened

Your computer decides whether to trust an HTTPS site by checking its
certificate against a list of trusted certificate authorities. The emSign
authorities were on that list. Since their keys are no longer secret, they
have been removed from the lists that Python tools use.

Several Python tools ship their own copy of the list instead of using the
one in your operating system, so each of them needs an update:

| Tool | Fixed in |
|---|---|
| pip | 26.2.2 |
| uv | 0.13.4 |
| certifi | 2026.10.19 |

Python 3.13.17, 3.14.9, and 3.15.1 were released with the fix as well.

## Citry's packages are fine

You do not need to upgrade Citry because of this incident. None of the
Citry packages (`citry`, `citry-core`, `citry-ui`, `citry-lsp`, and
`pygments-citry`) depends on certifi, and none of them makes HTTPS
connections while your app runs.

The risk is in the tools that install packages. If pip or uv downloads a
package through a connection someone has taken over, it can install code
you did not ask for.

## Update your tools

Upgrade pip in each Python installation and virtual environment that has
it:

```sh
python -m pip install --upgrade "pip>=26.2.2"
```

The announcement also shows how to install pip from a URL with a checksum,
so that pip checks the download itself even on an untrusted connection.
Use that method if you work on a network you do not trust.

Upgrade uv the same way you installed it:

```sh
uv self update        # the standalone installer
brew upgrade uv       # Homebrew
```

If your project lists certifi in a lock file, raise it to 2026.10.19:

```sh
uv lock --upgrade-package certifi
```

Finally, rebuild your container images so they pick up the current
certificate list from the base image and your package manager.

Installs from a lock file that records hashes, such as `uv sync --frozen`,
were already protected: uv rejects any file whose hash does not match the
lock. Installs without hashes, such as `pip install django`, were not.

## Update a starter's uv pin

If you created your project from a Citry starter or demo, its CI workflow
in `.github/workflows/check.yml` pins uv 0.10.12, which still trusts the
emSign authorities. Change the pin to 0.13.5:

```yaml
- uses: astral-sh/setup-uv@37802adc94f370d6bfd71619e3f0bf239e1f3b78 # v7
  with:
    version: "0.13.5"
    python-version: "3.14"
```

The starters now ship with this pin.

## What we changed in Citry

We build, test, and publish Citry on GitHub Actions, so we checked every
place where our own builds download packages:

- **The PyPI upload.** We publish to PyPI with the
  `pypa/gh-action-pypi-publish` action. Its earlier versions shipped a
  certifi that still trusts emSign, and it uses that list when it asks
  PyPI for a short-lived upload token
  ([advisory](https://github.com/pypa/gh-action-pypi-publish/security/advisories/GHSA-5xjx-3w67-w9x9){: target="\_blank" rel="noopener"}).
  Our publish workflows now use version 1.14.3, which drops it.
- **uv.** Our release and documentation workflows pinned uv 0.10.12. They
  now pin 0.13.5, and a repository check fails if any of them or any
  starter uses a different version.
- **pip.** The workflows that test the installed `citry-ui` wheel and the
  VS Code extension use the pip that comes with Python, which can be
  older than 26.2.2. They now install pip 26.2.2 from a URL with a
  checksum before they download anything else.
- **certifi.** Our development and benchmark lock files now use certifi
  2026.10.19.

Most of our installs were already safe, because they come from lock files
with hashes. The exposed steps were the PyPI upload and a few installs of
test tools by version only. We have no sign that anyone used this
weakness against Citry's builds.

If you publish your own packages with `pypa/gh-action-pypi-publish`,
update it to 1.14.3 or later.
