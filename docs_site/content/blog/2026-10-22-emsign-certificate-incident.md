---
title: The emSign certificate incident and Citry
description: What the eMudhra (emSign) certificate incident means for Citry users, what to update, and what we changed in Citry's own builds.
date: 2026-10-22T14:30:00+02:00
author: Juro Oravec
author_url: /community/people/
tags: Security, Project updates
---

On October 20, 2026, the Python Security Developer-in-Residence
[announced](https://discuss.python.org/t/information-for-python-users-regarding-emudhra-emsign-ca-certificate-security-incident/109576){: target="\_blank" rel="noopener"}
that the private keys of several eMudhra (emSign) certificate authorities
can be recovered. Anyone who has those keys and controls part of your
network can pretend to be any HTTPS site, including pypi.org, to a
program that still trusts them.

This post explains what that means if you use Citry, what to update on
your machine and in your CI, and what we changed in Citry.

## The emSign incident

Your computer decides whether to trust an HTTPS site by checking its
certificate against a list of trusted root certificates. The affected
certificate authorities all lead back to one root on that list, "emSign
ECC Root CA - G3". Since their keys are no longer secret, that root is
being removed from every such list.

Several Python tools ship their own copy of the list, so each of them
needs an update:

| Package | Update to |
|---|---|
| pip | 26.2.2 |
| uv | 0.13.5 |
| certifi | 2026.10.19 |

uv 0.13.4 was the first uv without the emSign root; 0.13.5 also rejects
the compromised keys if they appear further down a certificate chain.
Python 3.13.17, 3.14.9, and 3.15.1 bundle pip 26.2.2, so new virtual
environments made with them start with the fixed pip.

pip also reads your operating system's list, and so do Python's own HTTPS
requests. That list needs an update too. Ubuntu 24.04 has one; Debian 12
and 13 do not yet.

Installing from a lock file that records hashes, such as
`uv sync --frozen`, protects the packages the lock lists: uv rejects any
file whose hash does not match. It does not cover the build backend (for
example setuptools) that uv downloads to build your own project. Installs
without hashes, such as `pip install django`, are not protected.

## No Citry upgrade needed

You do not need to upgrade Citry because of this incident. None of the
Citry packages (`citry`, `citry-core`, `citry-ui`, `citry-lsp`, and
`pygments-citry`) depends on certifi, and none of them makes HTTPS
connections while your app runs.

The main risk is in the tools that install packages. If pip or uv
downloads a package through a connection someone has taken over, it can
install code you did not ask for. Your own app is affected too if it makes
HTTPS requests with a library that uses certifi, such as `requests` or
`httpx`. The certifi update below covers that.

## Update your tools

Upgrade pip in each Python installation and virtual environment that has
it:

```sh
python -m pip install --upgrade "pip>=26.2.2"
```

On a network you do not trust, install pip from the URL and checksum
given in the announcement instead, so that pip checks the download itself.

Until your operating system's update removes the emSign root, tell pip
26.2.2 to use only its own list:

```sh
export PIP_USE_DEPRECATED=legacy-certs
```

Set it only in the shell or CI job that runs pip 26.2.2. An older pip in
another environment stops with "invalid choice", and pip with this
setting no longer trusts certificates your company added to the
operating system's list, such as one for a private package index.

Upgrade uv the same way you installed it, then install the Python builds
that come with pip 26.2.2:

```sh
uv self update        # standalone installer
brew upgrade uv       # Homebrew
uv python upgrade
```

If your project lists certifi in a lock file, raise it to 2026.10.19:

```sh
uv lock --upgrade-package certifi
```

If you use Node.js, upgrade to 22.23.4, 24.22.1, or 26.12.1, or a later
release. Earlier releases in those lines still trust the emSign root.

If you publish to PyPI with the `pypa/gh-action-pypi-publish` action,
update it to 1.14.3 or later
([advisory](https://github.com/pypa/gh-action-pypi-publish/security/advisories/GHSA-5xjx-3w67-w9x9){: target="\_blank" rel="noopener"}).

On Ubuntu 24.04, update the operating system's list:

```sh
sudo apt-get update
sudo apt-get install --only-upgrade ca-certificates
```

Rebuild your container images so they pick up the updated packages. An
image based on Debian still trusts emSign through the operating system's
list after a rebuild, so keep `PIP_USE_DEPRECATED=legacy-certs` set there.

## Fix the starter uv pin

If you created your project from a Citry starter or demo, its CI workflow
in `.github/workflows/check.yml` pins uv 0.10.12, which still trusts the
emSign authorities. It also uses setup-uv 7.6.0, which installs any uv
newer than 0.10.10 without checking the download's checksum. Change both,
and keep the cache pruning that setup-uv 10 no longer does by default. The
commit below is setup-uv 10.3.2:

```yaml
- uses: astral-sh/setup-uv@07a047e608db84b3d8c06cd9a7c7dcc9c355c18e
  with:
    prune-cache: true
    version: "0.13.5"
```

The starters now ship with these settings.

## What we changed in Citry

We build, test, and publish Citry on GitHub Actions, so we checked every
place where our builds download or upload packages:

- **The PyPI upload.** We publish to PyPI with the
  `pypa/gh-action-pypi-publish` action. Its earlier versions shipped a
  certifi that still trusts emSign, and they used it for every HTTPS
  connection, including the request for a short-lived upload token and
  the upload itself. Our publish workflows now use version 1.14.3, whose
  certifi no longer trusts emSign.
- **uv.** Our release workflows, our documentation workflows, and the
  starters pinned uv 0.10.12 or used the newest uv. They now pin 0.13.5,
  and a repository check fails if any of them pins a different version.
  Every workflow also uses setup-uv 10.3.2, which checks the uv download
  against uv's published checksum; the older setup-uv skipped that check
  for any uv newer than 0.10.10.
- **pip.** The workflows that test the installed `citry-ui` wheel and the
  VS Code extension used the pip that comes with Python, which can be
  older than 26.2.2. They now install pip 26.2.2 from a URL with a
  checksum before pip downloads anything else, and then use only pip's
  own list.
- **certifi.** Our development and benchmark lock files now use certifi
  2026.10.19.
- **Build backends.** When uv builds a Citry package, it downloads a build
  backend (setuptools or maturin) that the lock file does not cover. These
  downloads must now match hashes we record, and uv stops on a mismatch.
- **Node.js.** Node.js 22.23.4, 24.22.1, and 26.12.1 drop the emSign root.
  The VS Code extension uploads to the Visual Studio Marketplace and Open
  VSX now run on Node.js 22.23.4, with the Open VSX client pinned in our
  lock file. Playwright bundles an older Node.js, so its browser downloads
  now use the runner's updated system list instead.

Most of our installs were already safe, because they come from lock files
with hashes. The exposed steps were the PyPI upload, the VS Code extension
uploads, the Playwright browser downloads, the build backends that uv
downloaded to build our packages, and a few test installs that picked
packages by version only, without hashes.

Two parts remain. The GitHub Actions that download Python, Node.js, and
pnpm run on the runner's own Node.js, which trusts the emSign root until
GitHub ships a runner with Node.js 24.22.1. The action that builds the
`citry-core` wheels downloads maturin without checking a checksum; we have
not replaced it yet.

We checked PyPI against our own releases: every Citry package file there
comes from a release our workflows made, and nothing has been uploaded
since October 19, the day before the announcement.
