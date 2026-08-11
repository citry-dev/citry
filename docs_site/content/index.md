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

<!-- TODO: Social-proof - companies/orgs/projects
           that use Citry.
           Also mention Sponsors
-->

<!-- TODO: Overview video how it all works (incl VSCode, UI Lib, etc)
-->

<section class="landing-section" id="proof" markdown="1">
## One file holds the entire component end-to-end.

<p class="landing-section__intro">
Inputs, slots, markup, server events and state, browser behavior, and
styles, all live together. No context switching.
</p>

<c-landing-tour />
</section>

<section class="landing-section landing-section--band" id="integrated" markdown="1">
## Use with any web server <br/>or standalone.

<p class="landing-section__intro">
Citry's server-side events need a route on your application.
Two lines of code and you're all set. If you don't need events,
you can use Citry without a server.
</p>

See the [web framework integrations](/web-frameworks/) and
[server events](/events/).

<c-landing-hosts />

</section>

<section class="landing-section" id="reliability" markdown="1">
## Catch mistakes early.

<!-- Every message below is the real one. Building this page applies each mistake
to the component above, renders it, and prints back exactly what Citry raised.
If a mistake stops being reported, or the report loses its detail, this page
fails to build. -->

<p class="landing-section__intro">
Citry was born out of frustration with Django's silent coerctions and leaky
isolations.
</p>

<p class="landing-section__intro">
In Citry, what you see (in your component) is what you get:
</p>

<ul class="landing-section__intro" style="margin: 1.4rem 0;">
  <li>Variables NEVER leak to other components.</li>
  <li>Data passing is ALWAYS explicit contracts.</li>
  <li>Missing values are ALWAYS error in Citry.</li>
</ul>

Read about [inputs and validation](/concepts/inputs-and-validation/),
[error boundaries](/concepts/error-boundaries/), and
[testing components](/advanced/testing/).

<c-landing-diagnostic />

</section>

<section class="landing-section landing-section--band" id="editor" markdown="1">
## Your editor understands the whole component.

<p class="landing-section__intro">
Citry's VSCode extension connects all parts of the component. Surface errors or trace values across the file. Add completions, diagnostics, and hover hints.
</p>

Install the [VS Code extension](/ide/vscode/).

<c-landing-editor-demo />

</section>

<section class="landing-section" id="capabilities" markdown="1">
## A component library for real interfaces.

<p class="landing-section__intro">
Citry UI gives you accessible, themeable components for layout, forms, actions,
navigation, feedback, and data display. Browse the collection below, then drag
a few onto the sample page to see how naturally they fit together.
</p>

Explore the [component concepts](/concepts/components/),
[interactive examples](/examples/), and [advanced guides](/advanced/testing/).

<c-landing-composer />

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
Citry is the successor to
[django-components](https://github.com/django-components/django-components) (1.5k stars), distilling years of experience into an elegant and powerful framework.

This project would be nothing without its community. The people below have contributes into Citry or django-components:

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
