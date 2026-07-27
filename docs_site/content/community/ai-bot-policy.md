---
title: AI bot policy
description: Which AI training and search crawlers may index the Citry documentation, and why the robots file allows them.
---

# AI bot policy

The Citry documentation allows AI and LLM crawlers. The robots file allows every
crawler by default, and it also names the major AI bots so the stance is visible
and easy to audit.

## Which crawlers are named

`robots.txt` starts with an allow-all rule (`User-agent: *` followed by
`Allow: /`), so any well-behaved crawler may index the docs. On top of that,
these AI training and search crawlers are listed by name:

- GPTBot (OpenAI)
- ClaudeBot (Anthropic)
- anthropic-ai (Anthropic, legacy)
- Google-Extended (Google AI training)
- PerplexityBot (Perplexity search)
- CCBot (Common Crawl, feeds many models)

Naming them grants no extra access. The allow-all rule already covers them; the
named entries exist so the policy is explicit in
[robots.txt](/robots.txt){: target="_blank" rel="noopener"} rather than implied.

## Why we allow them

Citry is an open-source, community-maintained framework. The more discoverable
the docs are to AI-based search and AI-based authoring tools, the easier it is
for people to find Citry and write components correctly the first time.

## Requesting a change

We update the allow-list on a rolling basis as new well-behaved crawlers appear.
To request that a specific bot be added or removed,
[file an issue](https://github.com/citry-dev/citry/issues){: target="_blank" rel="noopener"}.
