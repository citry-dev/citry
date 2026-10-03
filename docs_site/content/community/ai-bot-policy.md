---
title: AI bot policy
description: Which AI training and search crawlers may index the Citry documentation, and why the robots file allows them.
---

# AI bot policy

You run an AI crawler or build an AI tool, and want to know whether it may
read the Citry documentation. It may: the docs treat AI and LLM crawlers
the same as every other crawler. This page also shows how an AI tool can
find the pages it needs.

## Allowed crawlers { #which-crawlers-are-allowed }

`robots.txt` starts with a rule that allows every crawler (`User-agent: *`
followed by `Allow: /`). Any crawler that follows `robots.txt` may index
the docs, and there is no list of named bots to keep up to date.

The same `User-agent: *` group also has `Disallow` lines for older
documentation versions, so no crawler, search or AI, indexes those pages.

## Why we allow them

Citry is an open-source, community-maintained framework. When AI search and
AI coding tools can read the docs, people find Citry more easily and write
correct components on the first try.

## How AI tools find docs { #how-ai-tools-find-the-documentation }

Start from the [llms.txt index](/llms.txt){: target="_blank" rel="noopener"}.
It is a short, organized list of the documentation, and each entry links to
a Markdown version of one page. An agent can fetch only the pages that
answer its question.

Every documentation page also points to its own Markdown version and to
the `llms.txt` file that lists it, through standard HTML `<link>` tags.
These links help an agent find readable content. They do not allow or block
crawling; `robots.txt` alone decides that.

The Markdown versions of the generated [API Reference](/reference/) pages
may still contain some HTML, but they leave out the site's header,
navigation, and footer.

The larger [`llms-full.txt`](/llms-full.txt){: target="_blank" rel="noopener"}
file holds all the documentation in one download. It is an extra
convenience, not part of the llms.txt standard.

## Request a change { #requesting-a-change }

To ask for a specific bot to be blocked, or to report a crawler that ignores
`robots.txt`,
[file an issue]({{ repo_issues_url }}){: target="_blank" rel="noopener"}.
