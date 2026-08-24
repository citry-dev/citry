---
title: AI bot policy
description: Which AI training and search crawlers may index the Citry documentation, and why the robots file allows them.
---

# AI bot policy

The Citry documentation allows AI and LLM crawlers through the same wildcard
policy as every other crawler.

## Which crawlers are allowed

`robots.txt` starts with an allow-all rule (`User-agent: *` followed by
`Allow: /`), so any well-behaved crawler may index the docs. There is no list of
named bots to keep current. The wildcard group also carries the generated
exclusions for older documentation versions, so that policy applies uniformly
to search and AI crawlers.

## How AI tools find the documentation

The [llms.txt index](/llms.txt){: target="_blank" rel="noopener"} gives agents
a short, organized list of the documentation. Its entries lead directly to
page-level Markdown companions, so an agent can fetch only the pages relevant
to a question. Authored pages contain expanded Markdown. Generated Reference
pages may retain HTML-rich fragments from the reference renderer, but omit the
surrounding site chrome.

Every documentation page also identifies its own Markdown version and the
covering `llms.txt` file through standard HTML link relations. These discovery
links help an agent choose readable content. They do not grant or deny crawler
access; `robots.txt` carries that separate policy.

The larger [`llms-full.txt`](/llms-full.txt){: target="_blank" rel="noopener"}
file remains available as a nonstandard bulk-download convenience. It is not
part of the llms.txt v2 discovery contract.

## Why we allow them

Citry is an open-source, community-maintained framework. The more discoverable
the docs are to AI-based search and AI-based authoring tools, the easier it is
for people to find Citry and write components correctly the first time.

## Requesting a change

We update the allow-list on a rolling basis as new well-behaved crawlers appear.
To request that a specific bot be added or removed,
[file an issue]({{ repo_issues_url }}){: target="_blank" rel="noopener"}.
