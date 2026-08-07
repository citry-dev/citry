---
title: Citry
description: Build checked, isolated web components in Python with server-rendered HTML and optional browser behavior.
layout: landing
boost: 2
---

<section class="landing-hero" markdown="1">
<div class="landing-hero__grid" markdown="1">
<div class="landing-hero__copy" markdown="1">
# The complete frontend stack for Python.

<p class="landing-hero__lede">
Citry is a free, open source <strong>HTML-first component framework</strong> for Python web
applications. From server-rendered HTML to browser behavior and back to a Python
handler, one component holds all of it. No second application, no separate build.
</p>

<div class="landing-actions">
  <a class="landing-button landing-button--primary" href="/docs/">
    Start building
    <svg class="landing-button__arrow" viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h11M9 4l4 4-4 4"/></svg>
  </a>
  <a class="landing-button" href="/playground/">Try the playground</a>
</div>

<div class="landing-install">
  <code>pip install citry</code>
  <button class="landing-copy" type="button" data-copy-install>Copy</button>
</div>

<c-social-links variant="landing-social" />

</div>

<div class="landing-code landing-hero__code" markdown="1">
<div class="landing-code__bar">
  <span class="landing-code__dot"></span>
  <span>product_card.py</span>
</div>

<c-include-file
  path="docs_site/snippets/landing/product_card.py"
  language="citry"
/>
</div>
</div>
</section>

<section class="landing-section" id="proof" markdown="1">
## One file holds the whole component end-to-end.

<p class="landing-section__intro">
Inputs, slots, server state, Python handlers, markup, browser behavior, and
styles live together. No context switching.
</p>

Point at any marked line below to see what it does:

<c-landing-tour />
</section>

<section class="landing-section" id="reliability" markdown="1">
## Catch mistakes early.

<!-- Every message below is the real one. Building this page applies each mistake
to the component above, renders it, and prints back exactly what Citry raised.
If a mistake stops being reported, or the report loses its detail, this page
fails to build. -->

<p class="landing-section__intro">
Explicit component inputs and isolated contexts turn silent UI
failures into loud ERRORS.
</p>

<p class="landing-section__intro">
Iterate faster than ever before. Errors give critical context to your AI coding agents.
</p>

Read about [inputs and validation](/concepts/inputs-and-validation/),
[error boundaries](/concepts/error-boundaries/), and
[testing components](/advanced/testing/).

<c-landing-diagnostic />

</section>

<section class="landing-section landing-section--band" id="integrated" markdown="1">
## Use with any web server.

<p class="landing-section__intro">
Citry serves its own component assets, fragments, and events, so it needs a
route on your application. Your routes, database, authentication, and deployment do not move.
</p>

<p class="landing-section__intro">
Two lines of code and you're all set. 
</p>

See the [web framework integrations](/web-frameworks/) and
[server events](/events/).

<c-landing-hosts />

</section>

<section class="landing-section" id="capabilities" markdown="1">
## Start small. Keep the same model as the interface grows.

<p class="landing-section__intro">
One component can be a button, a dashboard region, or the page around them.
The primitives compose without forcing every project into a new application
architecture.
</p>

<ul class="landing-capabilities">
  <li>
    <strong>Compose</strong>
    <span>Checked inputs, slots, provide and inject, and dynamic components.</span>
  </li>
  <li>
    <strong>Interact</strong>
    <span>Scoped Alpine behavior, state, forms, events, and loading states.</span>
  </li>
  <li>
    <strong>Deliver</strong>
    <span>Assets, caching, HTML fragments, host adapters, and extensions.</span>
  </li>
  <li>
    <strong>Verify</strong>
    <span>Plain Python tests, executable examples, loud failures, and tracing.</span>
  </li>
</ul>

Explore the [component concepts](/concepts/components/),
[interactive examples](/examples/), and [advanced guides](/advanced/testing/).
</section>

<section class="landing-section" id="depth" markdown="1">
## Grow without a rewrite.

<p class="landing-section__intro">
A product that works starts running into different problems. None of them need a different framework.
</p>

Read about [caching](/advanced/caching/),
[`Const` optimization](/advanced/const-optimization/),
[extensions](/advanced/extensions/),
[HTML fragments](/advanced/html-fragments/), and
[component libraries](/advanced/component-libraries/).

<c-landing-depth />

</section>

<section class="landing-section" id="people" markdown="1">
## Built in public by people who care about Python and the web.

<div class="landing-human-grid" markdown="1">
<div class="landing-human-note">
  <blockquote>
    “Python teams should not have to choose between loose template fragments
    and maintaining a second application just to build a serious interface.”
  </blockquote>
  <footer>Juro Oravec · Citry maintainer</footer>
</div>

<div markdown="1">
Citry grows from
[django-components](https://github.com/django-components/django-components)
and the work of its contributors. The project is young, the decisions are open,
and useful questions are contributions too.

The people below have merged work into Citry or django-components. Recognition
follows the whole history of both projects, not a launch-day count.

<c-people group="contributors" avatars />

### Who funds the work

Citry is built in the open and paid for by organizations that run it. Sponsors
get the roadmap early, a direct line to the maintainer, and a say in what gets
built next.

<ul class="landing-sponsors">
  <li><a href="https://www.ohnemakler.net/" target="_blank" rel="noopener">Ohne Makler</a></li>
</ul>

[Sponsor Citry]({{ repo_sponsors_url }}) if your product depends
on this layer and you want it moving faster.

<div class="landing-human-links">
  <a href="/community/people/">Meet the people building Citry</a>
  <a href="/community/help/">Ask a question</a>
  <a href="/community/contributing/">Help improve Citry</a>
  <a href="/blog/">Read the build notes</a>
</div>
</div>
</div>
</section>

<section class="landing-section landing-section--plain" id="trust" markdown="1">
## Open source, inspectable, and honest about its stage.

<div class="landing-trust-grid" markdown="1">
<div class="landing-trust-card" markdown="1">
### What is available now

- free and open source under the MIT license;
- CPython 3.10 through 3.14;
- FastAPI, Starlette, Flask, Django, ASGI, and WSGI adapters;
- server rendering, scoped browser behavior, events, forms, and fragments; and
- source, tests, examples, and benchmark method in the public repository.
</div>

<div class="landing-trust-card" markdown="1">
### What we will not pretend

Citry is a pre-1.0 project. APIs can still change, the community is still
forming, and the future IDE linter is not shipped yet. Use the compatibility,
security, and release notes to make a decision with the current facts.

[Compatibility](/about/compatibility/) · [Security](/security/) ·
[Benchmarks](/about/benchmarks/) · [Source]({{ repo_url }})
</div>
</div>
</section>

<section class="landing-final" markdown="1">
## Build your first component.

Start with plain Python and HTML. Add composition, browser behavior, and Python
events when the interface asks for them.

<div class="landing-actions">
  <a class="landing-button landing-button--primary" href="/docs/">
    Read the docs
    <svg class="landing-button__arrow" viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h11M9 4l4 4-4 4"/></svg>
  </a>
  <a class="landing-button" href="/examples/">Explore examples</a>
</div>

<div class="landing-install">
  <code>pip install citry</code>
  <button class="landing-copy" type="button" data-copy-install>Copy</button>
</div>
</section>
