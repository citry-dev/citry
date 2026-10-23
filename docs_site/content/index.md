---
title: Citry
description: Build checked, isolated web components in Python with server-rendered HTML and optional browser behavior.
layout: landing
boost: 2
---

<section class="landing-hero" markdown="1">
<div class="landing-hero__grid" markdown="1">
<div class="landing-hero__copy" markdown="1">
# The complete Python frontend engineered for AI agents.

<p class="landing-hero__lede">
Citry is a free, open source <strong>HTML-first frontend framework</strong> for Python web
applications.
</p>
<p class="landing-hero__lede">
Everything is typed and checked, so AI agents catch their own mistakes.
</p>
<p class="landing-hero__lede">
No NPM, no NodeJS build, no server-browser API
hassle.
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

<!-- TODO: Add "Used by" belt -->

<section class="landing-sponsor-belt" aria-labelledby="landing-sponsor-title">
  <h2 id="landing-sponsor-title">Development sponsored by</h2>
  <ul>
    <li>
      <a href="https://www.ohne-makler.net/" target="_blank" rel="noopener">
        <img
          src="/static/img/sponsors/ohne-makler.svg"
          alt="Ohne Makler"
        />
      </a>
    </li>
  </ul>
</section>

<!-- Both charts read their numbers from docs_site/data/ through the components
the Benchmarks page uses, so a new benchmark run redraws the bars on both pages.
Their options draw the shorter landing version; docs_site/scripts/benchmark_images.py
draws the README images of both charts with the same options.
The README repeats these two sections. Each <c-benchmark-text> prints a
sentence from docs_site/scripts/benchmark_readme.py, which the README block
uses too, so the counts and versions follow the data. The headings must match
HEADINGS there; the readme_benchmark_charts check fails when they differ.
The rest is typed by hand and nothing checks it, so recheck it after a new
run of either benchmark: "Citry catches more errors than other Python
frameworks" rests on the error counts, the speed chart's title types the
1,400 entries, and the heading "As fast as Next.js" rests on Citry's
second load being no slower than Next.js's.
-->

<div class="landing-benchmarks" id="benchmarks" markdown="1">
<section class="landing-benchmark" markdown="1">
## Catch mistakes early

<p class="landing-section__intro">
<c-benchmark-text part="errors-intro" />
</p>

<p class="landing-section__intro">
Citry catches more errors than other Python frameworks and reports them earlier.
</p>

<div class="landing-benchmark-card" markdown="1">

<p class="landing-benchmark-card__hint"><c-benchmark-text part="errors-hint" /></p>

<c-error-benchmark-chart
  title="Mistakes reported before the app runs, out of those that apply"
  sort="share"
  scale="applicable"
  short_names
  compact
/>

<p class="landing-benchmark-card__note">
<c-benchmark-text part="errors-note" />
<a href="/about/benchmarks/#errors-how-we-measured">How we measured</a>
</p>
</div>
</section>

<section class="landing-benchmark" markdown="1">
## As fast as Next.js

<p class="landing-section__intro">
<c-benchmark-text part="speed-intro" />
</p>

<div class="landing-benchmark-card" markdown="1">

<c-benchmark-chart
  load="second"
  title="Second load: time until usable, 1,400 entries"
  sort="total"
  c-phases="False"
  compact
  c-show_table="False"
/>

<p class="landing-benchmark-card__note">
<c-benchmark-text part="speed-note" />
<a href="/about/benchmarks/#how-the-numbers-were-taken">How we measured</a>
</p>
</div>
</section>
</div>

<!-- TODO: Overview video how it all works (incl VSCode, UI Lib, etc)
-->

<section class="landing-section landing-section--band" id="crash-course" markdown="1">
## Watch the tutorial

<c-youtube-video
  video_id="d3nPqvDdNB0"
  title="50-minute Citry and Django code-along"
/>

</section>

<section class="landing-section" id="proof" markdown="1">
## One file holds the entire component end-to-end.

<p class="landing-section__intro">
Inputs, slots, markup, translated messages, server events and state, browser behavior, and
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

See the [web framework integrations](/advanced/web-frameworks/) and
[server events](/events/).

<c-landing-hosts />

</section>

<section class="landing-section" id="reliability" markdown="1">
## No silent failures.

<!-- Every message below is the real one. Building this page applies each mistake
to the component above, renders it, and prints back exactly what Citry raised.
If a mistake stops being reported, or the report loses its detail, this page
fails to build. -->

<p class="landing-section__intro">
Citry was born out of frustration with Django's silent coercions and leaky
isolations.
</p>

<p class="landing-section__intro">
In Citry, what you see (in your component) is what you get:
</p>

<ul class="landing-section__intro" style="margin: 1.4rem 0;">
  <li>Variables NEVER leak to other components.</li>
  <li>Data passing is ALWAYS explicit contracts.</li>
  <li>Missing values are ALWAYS an error in Citry.</li>
</ul>

Read about [inputs and validation](/concepts/inputs-and-validation/),
[error boundaries](/concepts/error-boundaries/), and
[testing components](/advanced/testing/).

<c-landing-diagnostic />

</section>

<section class="landing-section landing-section--band" id="editor" markdown="1">
## Your editor understands the whole component.

<p class="landing-section__intro">
Citry's VSCode extension connects all parts of the component - Py, HTML, JS, CSS. Surface errors or trace values across the languages. Add completions, diagnostics, and hover hints.
</p>

Install the [VS Code extension](/ide/vscode/).

<c-landing-editor-demo />

</section>

<section class="landing-section" id="capabilities" markdown="1">
## Build fast with 70+ ready-made components.

<p class="landing-section__intro">
<a href="/ui-library/">Citry UI</a>
gives you accessible, themeable components for layout, forms, actions,
navigation, feedback, and data display.
<a href="/ui-library/installation/">Install here.</a>
</p>

<c-landing-composer />

</section>

<section class="landing-section" id="depth" markdown="1">
## Grow without a rewrite.

<p class="landing-section__intro">
A product that works starts running into different problems. None of them need a different framework.
</p>

Read about [caching](/performance/caching/),
[extensions](/advanced/extensions/),
[internationalization](/i18n/),
[CSRF protection](/security/#protect-event-posts-from-csrf),
[strict CSP](/security/#choose-a-csp-compatibility-mode),
[HTML fragments](/advanced/html-fragments/),
[component libraries](/advanced/component-libraries/), and
[performance](/performance/).

<c-landing-depth />

</section>

<section class="landing-section" id="people" markdown="1">
## Built in public by people who care about Python and the web.

<p class="landing-section__intro">
Citry is the successor to
<a href="https://github.com/django-components/django-components" target="_blank" rel="noopener">django-components</a>
(1.5k stars), distilling years of experience into an elegant and powerful framework.
</p>

<div class="landing-human-grid" markdown="1">

<div markdown="1">

<p style="margin-bottom: 0; margin-top: 0.5rem;">
This project would be nothing without its community. The people below have contributed to Citry or django-components:
</p>

<c-people group="contributors" avatars />

## Fund the work

Citry is built in the open with funding from its sponsors. They get the roadmap
early, a direct line to the maintainer, and a say in what gets built next.

### [Sponsor Citry]({{ repo_sponsors_url }}){: target="_blank" rel="noopener"}

</div>
<div markdown="1">

<div class="landing-maintainer">
<div class="landing-maintainer__portrait">
<c-people group="maintainers" avatars />
</div>
<div class="landing-maintainer__identity">
<p class="landing-maintainer__name"><a href="/community/people/">Juro Oravec</a></p>
<p class="landing-maintainer__role">Creator and maintainer of Citry</p>
</div>
</div>

<div class="landing-human-links">
  <a href="/community/people/">Meet the people building Citry</a>
  <a href="/community/help/">Ask a question</a>
  <a href="/community/contributing/">Help improve Citry</a>
</div>
</div>
</div>
</section>

<section class="landing-final" markdown="1">
## Discover safer and faster frontend.

<div class="landing-actions">
  <a class="landing-button landing-button--primary" href="/getting-started/installation/">
    Start the tutorial
    <svg class="landing-button__arrow" viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h11M9 4l4 4-4 4"/></svg>
  </a>
  <a class="landing-button" href="/examples/">Explore examples</a>
</div>

<div class="landing-install">
  <code>pip install citry</code>
  <button class="landing-copy" type="button" data-copy-install>Copy</button>
</div>
</section>
