---
title: Rendering
url: https://citry.dev/v/1.3.0/reference/rendering/
description: "The render pipeline, its output structs, Citry's trusted-HTML marker, and the Secret marker that keeps a value out of the data sent to the browser...."
---
# Rendering

The render pipeline, its output structs, Citry's trusted-HTML marker, and the `Secret` marker that keeps a value out of the data sent to the browser. `citry.Markup` is exactly [`markupsafe.Markup`](https://markupsafe.palletsprojects.com/en/stable/escaping/#markupsafe.Markup). `Markup(value)` trusts the complete value without sanitizing or validating anything. `safe_eval` runs an expression in the sandbox, `unsafe` marks a function that sandboxed expressions must not call, and `SecurityError` is what a blocked access raises. Four parts of this page are experimental and may change in a minor release: `RenderFrame`; the asset tags that `deps_position="separate"` returns (`SerializedAssets`, `SerializedAssetEntry`, the asset fields of `SerializedRender`, `CitryRender.needs_browser_runtime()`, `combine_assets()`, and `OutsideSlotContentError`); the API for embedding Citry tags in another template engine (`CompiledBody`, `render_compiled_body` and `collect_compiled_body_fills`); and `page_nonce_from_headers()`, which reads the page's CSP nonce from a request, with the `PAGE_NONCE_HEADER` name it reads.




<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_element.py#L96" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-citryelement" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>CitryElement</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Intermediate representation of a component invocation.</p>
<p>Created by <code>Component()</code>. Holds the component class and the
kwargs/slots that were passed. Rendering is deferred until
<code>.render()</code> is called.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>comp_cls</code>

- The Component subclass to render.
</li>

<li>
<code>kwargs</code>

- The keyword arguments passed to the component.
</li>

<li>
<code>slots</code>

- The slot fills passed to the component. Filled from either
channel: the reserved <code>slots=</code> kwarg when composing from Python
(<code>MyComp(title="x", slots={...})</code>), or the collected <code>&lt;c-fill&gt;</code>
tags / implicit default body when composed by a parent template.
Values are raw inputs here (strings, functions, elements, Slots);
they normalize to <code>Slot</code> instances when the component instance is
created at render time.
</li>

<li>
<code>component_tag_client_bindings</code>

- The final source-ordered bindings
captured from a component tag, including native Vue props and event
listeners and Citry server events. They are framework metadata,
not Python kwargs.
</li>

<li>
<code>element_morph_metadata</code>

- Private metadata materialized only by the
dynamic ordinary-element built-in.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_element.py#L142" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citryelement-comp-cls" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>comp_cls</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_element.py#L143" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citryelement-kwargs" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>kwargs</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_element.py#L144" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citryelement-slots" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>slots</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_element.py#L145" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citryelement-component-tag-client-bindings" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_tag_client_bindings</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_element.py#L146" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citryelement-element-morph-metadata" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>element_morph_metadata</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_element.py#L147" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citryelement-prepared-call-metadata" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>prepared_call_metadata</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_element.py#L149" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citryelement-render" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>render</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>render(template_globals: RenderTemplateGlobals | None = None, provides: RenderProvides | None = None) -> <a class="doc-type-link" href="/reference/rendering/#citry-citryrender">CitryRender</a></code></pre>
</div>

<div class="doc-body">
<p>Render this component into a <code>CitryRender</code>.</p>
<p>Each call mints fresh per-instance state (render_id, etc.), so the same
CitryElement can be rendered multiple times with distinct identities.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>template_globals</code>

<code>RenderTemplateGlobals | None</code>

- Template variables added for this render. They
reach the whole tree, sit above the Citry instance's globals,
and sit below each component's own <code>template_data</code>.
</li>

<li>
<code>provides</code>

<code>RenderProvides | None</code>

- Values the root component and its rendered descendants
may read with <code>inject()</code>. A nested direct <code>render()</code> call
starts a new root and must pass its required values again.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="/reference/rendering/#citry-citryrender">CitryRender</a>: A ``CitryRender`` with the complete rendered tree. Call</p>




</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L691" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-citryrender" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>CitryRender</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>The result of rendering a <code>CitryElement</code> (the render-phase output).</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Experimental</p><p>The <code>frame</code> attribute, the <code>frame=</code> argument and the
<a href="/reference/rendering/#citry-renderframe"><code>RenderFrame</code></a> class they use are
experimental. They may change in a minor release without a
deprecation period. The rest of <code>CitryRender</code> is stable.</p></blockquote>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>parts</code>

- Ordered list of <code>str</code> or nested <code>CitryRender</code> fragments.
</li>

<li>
<code>context</code>

- The <code>CitryContext</code> used to produce this render.
</li>

<li>
<code>is_component_root</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a></code>

- True for a nontransparent component's whole output.
Transparent whole outputs and interior renders (a <code>&lt;c-if&gt;</code>/<code>&lt;c-for&gt;</code> block, a
nested template, slot-fill content rendered in the enclosing
scope) are False. Serialization uses this to tell a completed
child-component subtree (which becomes its own marked frame) from
content that joins into the surrounding frame; the component on
the context cannot tell these apart, because slot-fill content
carries the context of the component that wrote it, not the one
it renders inside.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L729" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citryrender-parts" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>parts</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L730" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citryrender-context" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>context</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L734" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citryrender-owner-citry" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>owner_citry</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L735" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citryrender-frame" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>frame</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L742" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citryrender-render-target" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>render_target</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L745" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citryrender-is-component-root" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>is_component_root</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>is_component_root: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Whether this render is the whole output frame of one component.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L749" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citryrender-needs-browser-runtime" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>needs_browser_runtime</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>needs_browser_runtime() -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Whether this render has browser behavior that needs Citry's browser runtime.</p>
<p>It returns <code>True</code> when a component in this render uses
<code>js_data()</code>, a Vue binding such as <code>@click</code> or <code>:title</code>,
component JavaScript, or server events. Then <code>serialize()</code> with
the <code>"document"</code> or <code>"fragment"</code> strategy puts the HTML in an
element that Vue mounts on, and adds the runtime. It returns
<code>False</code> when the serialized HTML works without Citry's
JavaScript.</p>
<p>The answer depends only on what was rendered, not on the
<code>serialize()</code> arguments: with <code>security_javascript="omit"</code> or
<code>"forbid"</code>, serialize still leaves out the runtime or refuses the
render.</p>
<p>Code that combines Citry renders with HTML from another template
engine can use it to pick which child renders become their own Vue
apps. A child component's render may be serialized on its own
before its parent is serialized. It becomes a separate Vue app with
its own assets, and the parent's render does not change, so the
parent can still be serialized afterwards. This works only when the
child holds no slot content that a component outside it wrote, such
as text the parent passed between the child's tags; serializing such
a child on its own raises
<a href="/reference/rendering/#citry-outsideslotcontenterror"><code>OutsideSlotContentError</code></a>, a
<code>TypeError</code>.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Experimental</p><p>This method may change in a minor release without a deprecation
period.</p></blockquote>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><pre><code class="language-python">rendered = Page().render()
apps = [
    part.serialize_result(deps_position=&quot;separate&quot;)
    for part in rendered.parts
    if isinstance(part, CitryRender)
    and part.is_component_root
    and part.needs_browser_runtime()
]
</code></pre></blockquote>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a>: Whether this render needs Citry&#x27;s browser runtime.</p>




</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L806" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citryrender-has-server-events" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>has_server_events</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>has_server_events() -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Whether this render has a component with server events.</p>
<p>It returns <code>True</code> when a component in this render declares
<code>class Events</code>. Then <code>serialize()</code> gives the browser what it
needs to call that component's event handlers. It returns
<code>False</code> when no event call can come from this render. It answers
from what Citry recorded while rendering, so you can call it before
<code>serialize()</code>, and it does not change the render.</p>
<p>To decide whether a page needs the CSRF cookie, use
<a href="/reference/rendering/#citry-citryrender-needs-csrf-token"><code>needs_csrf_token()</code></a>, which
also covers the other browser requests that send the token.</p>
<p>Like <a href="/reference/rendering/#citry-citryrender-needs-browser-runtime"><code>needs_browser_runtime()</code></a>,
the answer depends only on what was rendered, not on the
<code>serialize()</code> arguments. It can return <code>True</code> even when
<code>security_javascript="omit"</code> or <code>"forbid"</code> makes
<code>serialize()</code> leave the event handlers out or refuse the render.
A child component's render answers for that child alone, which is
what serializing it on its own gives.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Experimental</p><p>This method may change in a minor release without a deprecation
period.</p></blockquote>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><pre><code class="language-python">rendered = Page().render()
if rendered.has_server_events():
    ...  # the page can call server event handlers
</code></pre></blockquote>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a>: Whether serializing this render lets the browser call a server</p>




</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L854" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citryrender-needs-csrf-token" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>needs_csrf_token</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>needs_csrf_token() -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Whether the browser may send Citry's CSRF token from this render.</p>
<p>It returns <code>True</code> when serializing this render lets the browser
send a request that carries the page's CSRF token, which the
host's CSRF check, such as Django's <code>CsrfViewMiddleware</code>, then
verifies.
Citry's browser code sends the token on these requests:</p>
<ul>
<li>an Events call to a component's event handlers, a <code>POST</code> to
the events route, when
<a href="/reference/rendering/#citry-citryrender-has-server-events"><code>has_server_events()</code></a>
returns <code>True</code>;</li>
<li>a request for translated messages, a <code>POST</code> to
<code>ext/i18n/messages</code>, which the browser sends when it needs a
locale the page did not include, such as on
<code>$i18n.switchLocale()</code>. Citry sends it only when its routes are
mounted, from a render that has a <code>&lt;c-i18n client&gt;</code> provider or
that is rendered into one.</li>
</ul>
<p>It returns <code>False</code> when neither can come from this render.</p>
<p>Host integrations such as citry-django use it to set the CSRF
cookie only on pages that need it, because the cookie keeps shared
caches from storing the page. It answers from what Citry recorded
while rendering, so you can call it before <code>serialize()</code>, and it
does not change the render.</p>
<p>It does not cover requests that your own code sends. A form you
write that posts to an event URL needs your framework's CSRF
field, and a browser plugin from a third-party extension that adds
<code>csrfHeaders()</code> to its own requests needs the cookie too.</p>
<p>Like <a href="/reference/rendering/#citry-citryrender-has-server-events"><code>has_server_events()</code></a>,
the answer depends only on what was rendered, not on the
<code>serialize()</code> arguments, and a child component's render answers
for that child alone. It may return <code>True</code> when serialization
writes no such request, which only costs a cookie the page did not
need.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Experimental</p><p>This method may change in a minor release without a deprecation
period.</p></blockquote>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><pre><code class="language-python">rendered = Page().render()
if rendered.needs_csrf_token():
    get_token(request)  # Django sets the CSRF cookie
html = rendered.serialize()
</code></pre></blockquote>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a>: Whether serializing this render lets the browser send Citry&#x27;s</p>




</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L930" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citryrender-serialize" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>serialize</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>serialize(deps_strategy: <a class="doc-type-link" href="/reference/rendering/#citry-depsstrategy">DepsStrategy</a> = &#x27;document&#x27;, deps_position: <a class="doc-type-link" href="/reference/rendering/#citry-depsposition">DepsPosition</a> = &#x27;smart&#x27;, csp_nonce: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None = None, security_csp: <a class="doc-type-link" href="/reference/citry/#citry-securitycspmode">SecurityCspMode</a> | None = None, security_javascript: <a class="doc-type-link" href="/reference/citry/#citry-securityjavascriptmode">SecurityJavascriptMode</a> | None = None, security_script_integrity: <a class="doc-type-link" href="/reference/citry/#citry-securityscriptintegritymode">SecurityScriptIntegrityMode</a> | None = None, ssr: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a> | None = None) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Turn this render into a final HTML string.</p>
<p>In static output, each component's root element gets a
<code>data-cid-&lt;id&gt;</code> attribute. When a rendered component needs Vue in
the browser, Citry keeps the surrounding page markup, puts the
rendered content (the page body, for a full document) in one element
where Vue mounts, and adds the data and scripts Vue needs to mount
it. Citry places the collected JS/CSS according to
<code>deps_strategy</code> and <code>deps_position</code>.</p>
<p>With <code>security_csp="warn"</code>, Citry reports content that would break
under a Content Security Policy but leaves the output unchanged. With
<code>"strict"</code>, it raises instead of warning, and it requires
<code>csp_nonce</code> when Citry emits an executable script or a <code>&lt;style&gt;</code>
element.
With <code>security_javascript="warn"</code>, it reports which components need
JavaScript; <code>"omit"</code> drops Citry's scripts but keeps the HTML and
CSS; <code>"forbid"</code> raises when a rendered component needs browser
behavior.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>deps_strategy</code>

<code><a class="doc-type-link" href="/reference/rendering/#citry-depsstrategy">DepsStrategy</a></code>

- <p>How to handle the collected JS/CSS.</p>
<ul>
<li><code>"document"</code> (default): emit the tags, plus Citry's
Vue browser runtime and the data it needs to mount the
page when a component needs per-instance browser
behavior, such as <code>js_data()</code> values on its Vue
instance or <code>$component</code> callbacks.</li>
<li><code>"simple"</code>: the tags only, no JavaScript runtime. For
static pages and emails; per-instance JS does not run
(CSS variables still work, they are pure CSS).</li>
<li><code>"fragment"</code>: HTML meant to be inserted into an
already-loaded page (an HTMX swap, <code>fetch</code> +
<code>innerHTML</code>, ...). A fragment without browser behavior
carries its tags directly. An interactive fragment
carries a script that loads Citry's browser runtime if
the page does not have it yet, plus JSON that tells the
runtime which assets to load before it mounts the
fragment. A fragment that carries JS, CSS, or browser
behavior requires a mounted web integration.</li>
<li><code>"ignore"</code>: no tags inserted.</li>
</ul>
</li>

<li>
<code>deps_position</code>

<code><a class="doc-type-link" href="/reference/rendering/#citry-depsposition">DepsPosition</a></code>

- <p>Where the tags go (<code>document</code>/<code>simple</code> only;
<code>"separate"</code> also accepts <code>ignore</code>).</p>
<ul>
<li><code>"smart"</code> (default): into the <code>&lt;c-js&gt;</code>/<code>&lt;c-css&gt;</code>
placeholders when present, else CSS before the first
<code>&lt;/head&gt;</code> and JS before the last <code>&lt;/body&gt;</code>, else
CSS is prepended and JS appended.</li>
<li><code>"prepend"</code> / <code>"append"</code>: all tags before/after the
whole output.</li>
<li><code>"separate"</code> (<strong>Experimental</strong>): no tags in the HTML.
<code>serialize_result()</code> returns them in the asset fields
of <a href="/reference/rendering/#citry-serializedrender"><code>SerializedRender</code></a>, so a
page that combines several renders can write each shared
tag once. Vue adopts the server HTML as it does with
<code>"smart"</code>. <code>serialize()</code> returns only the HTML and
drops the tags, so use <code>serialize_result()</code>.</li>
</ul>
</li>

<li>
<code>csp_nonce</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None</code>

- Raw request nonce to add to structured scripts and
inline styles. The host owns nonce generation and the matching
Content-Security-Policy response header.
</li>

<li>
<code>security_csp</code>

<code><a class="doc-type-link" href="/reference/citry/#citry-securitycspmode">SecurityCspMode</a> | None</code>

- Override this render's engine-level CSP policy.
</li>

<li>
<code>security_javascript</code>

<code><a class="doc-type-link" href="/reference/citry/#citry-securityjavascriptmode">SecurityJavascriptMode</a> | None</code>

- Override this render's engine-level
JavaScript delivery policy.
</li>

<li>
<code>security_script_integrity</code>

<code><a class="doc-type-link" href="/reference/citry/#citry-securityscriptintegritymode">SecurityScriptIntegrityMode</a> | None</code>

- Override
<a href="/reference/citry/#citry-citrysettings-security-script-integrity"><code>security_script_integrity</code></a>
for this render.
</li>

<li>
<code>ssr</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a> | None</code>

- Override the engine's initial Vue HTML hydration setting.
<code>None</code> uses the <a href="/reference/citry/#citry-citrysettings-ssr"><code>ssr</code></a> setting.
</li>

</ul>



<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>RuntimeError</code> - If a child component was left unrendered, which can
only happen when this render did not come from <code>render()</code>;
if the same render is placed more than once in the output;
if <code>deps_strategy="fragment"</code> needs a mounted web
integration and none is mounted; or if, with
<code>deps_position="separate"</code>, an extension's
<code>on_serialize</code> hook changed one of the asset tags.
</li>

<li>
<code>ValueError</code> - If an argument is invalid, such as
<code>deps_position="separate"</code> with a <code>deps_strategy</code> other
than <code>"document"</code>, <code>"simple"</code> or <code>"ignore"</code>; if
<code>security_csp="strict"</code> rejects the output or the output
needs <code>csp_nonce</code> and none was given; or if
<code>security_javascript="forbid"</code> finds a component that
needs browser behavior; or if a component uses <code>Events</code>
and no web integration is mounted.
</li>

<li>
<code>TypeError</code> - If <code>ssr</code> is not a bool or <code>None</code>.
</li>

<li>
<code>OutsideSlotContentError</code> - If this render is a child component's
render that needs Vue and holds slot content that a
component outside it wrote. It subclasses <code>TypeError</code>.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L1043" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citryrender-serialize-result" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>serialize_result</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>serialize_result(deps_strategy: <a class="doc-type-link" href="/reference/rendering/#citry-depsstrategy">DepsStrategy</a> = &#x27;document&#x27;, deps_position: <a class="doc-type-link" href="/reference/rendering/#citry-depsposition">DepsPosition</a> = &#x27;smart&#x27;, csp_nonce: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None = None, security_csp: <a class="doc-type-link" href="/reference/citry/#citry-securitycspmode">SecurityCspMode</a> | None = None, security_javascript: <a class="doc-type-link" href="/reference/citry/#citry-securityjavascriptmode">SecurityJavascriptMode</a> | None = None, security_script_integrity: <a class="doc-type-link" href="/reference/citry/#citry-securityscriptintegritymode">SecurityScriptIntegrityMode</a> | None = None, ssr: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a> | None = None) -> <a class="doc-type-link" href="/reference/rendering/#citry-serializedrender">SerializedRender</a></code></pre>
</div>

<div class="doc-body">
<p>Return final HTML together with security metadata for those exact bytes.</p>
<p>Arguments and validation match
<a href="/reference/rendering/#citry-citryrender-serialize"><code>serialize()</code></a>; this method also returns
the security metadata a host needs, while <code>serialize()</code> returns only
<code>result.html</code>.</p>
<p>With <code>deps_position="separate"</code>, the result's <code>html</code> holds no
asset tags, and its <code>runtime_assets</code>, <code>app_assets</code> and
<code>component_assets</code> hold them instead. Each group's
<code>css_entries</code> and <code>js_entries</code> say which components declared
each tag. See
<a href="/advanced/asset-placement/#combine-several-renders">Combine several renders</a>
and <a href="/advanced/asset-placement/#find-a-tags-components">Find a tag's components</a>.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><pre><code class="language-python">result = Widget().render().serialize_result(
    deps_position=&quot;separate&quot;,
)
groups = [
    result.runtime_assets,
    result.component_assets,
    result.app_assets,
]
head = &quot;&quot;.join(tag for g in groups for tag in g.css)
end_of_body = &quot;&quot;.join(tag for g in groups for tag in g.js)
</code></pre></blockquote>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L430" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-serializedrender" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>SerializedRender</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Final HTML plus host-facing security metadata for those exact bytes.</p>
<p>The asset fields are empty unless the render was serialized with
<code>deps_position="separate"</code>. Then <code>html</code> holds none of the tags
Citry places (tags that another extension's <code>on_serialize</code> hook adds
stay in it), and the tags are split into three groups so a page that
combines several renders can write each shared tag once. <code>security</code>
covers the HTML and the tags in these groups.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>html</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code>

- The serialized HTML.
</li>

<li>
<code>security</code>

<code><a class="doc-type-link" href="/reference/rendering/#citry-serializedsecurity">SerializedSecurity</a></code>

- Security metadata, such as the hashes a Content Security
Policy needs, for <code>html</code> and the asset groups below.
</li>

<li>
<code>runtime_assets</code>

<code><a class="doc-type-link" href="/reference/rendering/#citry-serializedassets">SerializedAssets</a></code>

- <strong>Experimental.</strong> Citry's own code that every Vue
app on a page shares: the browser runtime, the scripts that
extensions add to it, preload hints, and, when no web
integration is mounted, the compiled component code. Write the
first of each set of identical tags and skip the rest.
</li>

<li>
<code>app_assets</code>

<code><a class="doc-type-link" href="/reference/rendering/#citry-serializedassets">SerializedAssets</a></code>

- <strong>Experimental.</strong> The tags of this render's one Vue
app: its stylesheets, its configuration data and its start
script. Write every one of them, or pass this group from
every render to <a href="/reference/rendering/#citry-combine-assets"><code>combine_assets()</code></a>,
which writes one stylesheet tag for the apps that share it.
</li>

<li>
<code>component_assets</code>

<code><a class="doc-type-link" href="/reference/rendering/#citry-serializedassets">SerializedAssets</a></code>

- <strong>Experimental.</strong> The other tags: component CSS
and JavaScript when no component needs Vue, dependency files,
and tags added by <code>on_dependencies</code> hooks. Write the first of
each set of identical tags and skip the rest.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L463" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-serializedrender-html" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>html</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>html: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L464" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-serializedrender-security" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>security</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>security: <a class="doc-type-link" href="/reference/rendering/#citry-serializedsecurity">SerializedSecurity</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L465" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-serializedrender-runtime-assets" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>runtime_assets</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>runtime_assets: <a class="doc-type-link" href="/reference/rendering/#citry-serializedassets">SerializedAssets</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L466" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-serializedrender-app-assets" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>app_assets</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>app_assets: <a class="doc-type-link" href="/reference/rendering/#citry-serializedassets">SerializedAssets</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L467" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-serializedrender-component-assets" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_assets</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component_assets: <a class="doc-type-link" href="/reference/rendering/#citry-serializedassets">SerializedAssets</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L257" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-serializedassets" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>SerializedAssets</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>One group of asset tags that <code>deps_position="separate"</code> returns instead of inserting.</p>
<p>Each item is one complete tag, written exactly as Citry would have
inserted it, with the same <code>nonce</code>, <code>integrity</code> and other attributes.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Experimental</p><p><code>SerializedAssets</code>, <code>deps_position="separate"</code> and the asset fields
of <code>SerializedRender</code> are experimental. They may change in a minor
release without a deprecation period.</p></blockquote>



<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>ValueError</code> - When you create the group and <code>css_entries</code> or
<code>js_entries</code> is not empty and does not hold the same tags as
<code>css</code> or <code>js</code>, in the same order.
</li>

</ul>


<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>css</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, ...]</code>

- The tags that belong where <a href="/advanced/asset-placement/#mark-where-the-tags-go"><code>&lt;c-css /&gt;</code></a>
would put them, usually in <code>&lt;head&gt;</code>: stylesheets and preload hints,
in the order to write them.
</li>

<li>
<code>js</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, ...]</code>

- The scripts that belong where <code>&lt;c-js /&gt;</code> would put them, usually
at the end of <code>&lt;body&gt;</code>, in the order they must run.
</li>

<li>
<code>css_entries</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/rendering/#citry-serializedassetentry">SerializedAssetEntry</a>, ...]</code>

- <strong>Experimental.</strong> The same tags as <code>css</code>, in the same
order, each as a <a href="/reference/rendering/#citry-serializedassetentry"><code>SerializedAssetEntry</code></a>
that says which components declared it. Empty when the group
was built without them.
</li>

<li>
<code>js_entries</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/rendering/#citry-serializedassetentry">SerializedAssetEntry</a>, ...]</code>

- <strong>Experimental.</strong> The same for <code>js</code>.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L289" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-serializedassets-css" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>css</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>css: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L290" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-serializedassets-js" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>js</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>js: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L291" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-serializedassets-css-entries" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>css_entries</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>css_entries: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/rendering/#citry-serializedassetentry">SerializedAssetEntry</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L292" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-serializedassets-js-entries" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>js_entries</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>js_entries: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/rendering/#citry-serializedassetentry">SerializedAssetEntry</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L215" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-serializedassetentry" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>SerializedAssetEntry</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>One asset tag, with the components that declared it.</p>
<p>Citry fills these fields from what it recorded while it rendered each
component. So code that bundles or caches tags can decide what to do
with a tag without reading its attributes.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Experimental</p><p><code>SerializedAssetEntry</code> and the <code>css_entries</code> and <code>js_entries</code>
fields of <code>SerializedAssets</code> are experimental. They may change in a
minor release without a deprecation period.</p></blockquote>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>tag</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code>

- The complete tag, the same string as in <code>css</code> or <code>js</code>.
</li>

<li>
<code>class_ids</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, ...]</code>

- The <a href="/reference/component/#citry-component-class-id"><code>class_id</code></a> of each
component that declared this tag, in the order the render
first used them. There is more than one when components
declare the same file or the same CSS text. It is empty for
Citry's own tags, such as the browser runtime, preload hints
and a Vue app's data and start script, and usually for a Vue
app's stylesheets, whose components the app tracks itself. A
tag that an <code>on_dependencies</code> hook added or rebuilt names only
its own <code>origin_class_id</code>, or nothing when the hook set none.
</li>

<li>
<code>instance</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a></code>

- <code>True</code> when the tag may hold data from one render, so
it may differ between renders: a stylesheet with one
instance's <code>css_data()</code> values, every tag in <code>app_assets</code>, and
any tag that Citry cannot show is the same on every render,
such as one an <code>on_dependencies</code> hook added or rebuilt. Do not
put such a tag into a file that other pages share. <code>False</code>
only for the tags in <code>runtime_assets</code> and for a component's
own or <code>Dependencies</code> tags, which are the same wherever the
component is used.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L252" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-serializedassetentry-tag" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>tag</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>tag: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L253" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-serializedassetentry-class-ids" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>class_ids</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>class_ids: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L254" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-serializedassetentry-instance" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>instance</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>instance: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L309" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-combine-assets" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>combine_assets</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>combine_assets(groups: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Iterable">Iterable</a>[<a class="doc-type-link" href="/reference/rendering/#citry-serializedassets">SerializedAssets</a>]) -> <a class="doc-type-link" href="/reference/rendering/#citry-serializedassets">SerializedAssets</a></code></pre>
</div>

<div class="doc-body">
<p>Combine the same group of asset tags from several renders, writing each shared tag once.</p>
<p>Pass one group from every render, such as each result's
<code>app_assets</code>, and write the returned tags in place of theirs. Call it
once per group, so the tags of one group never move into another.</p>
<ul>
<li>Identical tags are kept once, where they first appear.</li>
<li>Stylesheet tags of several Vue apps that serve the same file become
one tag that names every one of those apps, so the browser runtime
lets each app use it. Each app's configuration data and start script
stay as they are, because they differ per app.</li>
<li>Every other tag is kept as it is, with its <code>nonce</code> and <code>integrity</code>.</li>
<li>When every group that has <code>css</code> tags also has <code>css_entries</code>, the
result has them too, and the same for <code>js</code>. A merged tag's entry
lists the components of every tag it replaced, and has
<code>instance=True</code> when any of them does. A group that has tags but
no entries leaves the result without entries for that kind.</li>
</ul>
<p>The tags come in the order of the groups you pass, and within a group
in the order the render gave them. A tag several renders share stays
where it first appears, so a later render's stylesheets can end up in
a different order than that render alone would write them.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Experimental</p><p><code>combine_assets</code> is experimental. It may change in a minor release
without a deprecation period.</p></blockquote>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><pre><code class="language-python">results = [
    Widget().render().serialize_result(
        deps_position=&quot;separate&quot;,
    ),
    Chart().render().serialize_result(
        deps_position=&quot;separate&quot;,
    ),
]
apps = combine_assets(
    result.app_assets for result in results
)
</code></pre></blockquote>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>groups</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Iterable">Iterable</a>[<a class="doc-type-link" href="/reference/rendering/#citry-serializedassets">SerializedAssets</a>]</code>

- The same group, such as <code>app_assets</code>, from each
<a href="/reference/rendering/#citry-serializedrender"><code>SerializedRender</code></a> that
<code>serialize_result(deps_position="separate")</code> returned.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="/reference/rendering/#citry-serializedassets">SerializedAssets</a>: One [`SerializedAssets`](/v/1.3.0/reference/rendering/#citry-serializedassets) with the combined</p>




</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L195" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-outsideslotcontenterror" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>OutsideSlotContentError</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/exceptions.html#TypeError">TypeError</a></code></p>


<div class="doc-body">
<p>Raised when a child render that holds slot content from outside it is serialized on its own as a Vue app.</p>
<p>A child component's render may be serialized on its own before its
parent, and it then becomes its own Vue app. That fails when the child
holds slot content that a component outside it wrote, such as text the
parent passed between the child's tags, because nothing in the new app
owns that content. Serialize the component that wrote the slot content
instead.</p>
<p>It subclasses <code>TypeError</code>, so <code>except TypeError</code> also catches it.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Experimental</p><p><code>OutsideSlotContentError</code> is experimental. It may change in a minor
release without a deprecation period.</p></blockquote>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L181" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-serializedsecurity" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>SerializedSecurity</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Security contributions produced by one serialization call.</p>
<p><code>csp_script_hashes</code> is the deduplicated document-order tuple of quoted
hash sources that a host can add to <code>script-src</code>. It and <code>scripts</code> are
empty when digest-producing security features are disabled.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L191" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-serializedsecurity-scripts" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>scripts</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>scripts: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/rendering/#citry-serializedscriptsecurity">SerializedScriptSecurity</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L192" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-serializedsecurity-csp-script-hashes" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>csp_script_hashes</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>csp_script_hashes: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L164" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-serializedscriptsecurity" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>SerializedScriptSecurity</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Security metadata for one structured script in serialized output.</p>
<p><code>digests</code> uses the unquoted SRI form, such as <code>"sha384-..."</code>.
<code>provenance</code> states whether Citry computed or verified those bytes.
<code>origin_class_id</code> identifies the component class when one owns the tag.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L174" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-serializedscriptsecurity-location" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>location</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>location: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;inline&#x27;, &#x27;external&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L175" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-serializedscriptsecurity-url" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>url</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>url: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L176" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-serializedscriptsecurity-digests" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>digests</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>digests: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L177" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-serializedscriptsecurity-provenance" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>provenance</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>provenance: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;citry-computed&#x27;, &#x27;declared-verified&#x27;, &#x27;declared-unverified&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L178" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-serializedscriptsecurity-origin-class-id" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>origin_class_id</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>origin_class_id: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/_page_nonce.py#L48" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-page-nonce-from-headers" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>page_nonce_from_headers</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>page_nonce_from_headers(headers: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>]) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Return the CSP nonce a request says its page has, or <code>None</code>.</p>
<p>Under a nonce-based Content Security Policy, the browser starts a Vue
fragment only when it carries the nonce of the page it lands in. When
page code loads a fragment with its own request (htmx, <code>fetch()</code>), it
sends that nonce in the <code>X-Citry-Page-Nonce</code> header, from
<code>Citry.pageNonce()</code> in the browser. Pass the result as <code>csp_nonce</code> when
you serialize the fragment, so it carries the nonce of the tab that
asked for it.</p>
<p>The answer depends on the header, so list <code>X-Citry-Page-Nonce</code> in its
<code>Vary</code> header, and when the result is not <code>None</code> also send
<code>Cache-Control: no-store</code>. A shared cache could otherwise give one
visitor's nonce to another.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Experimental</p><p>The header name and this function may change in a 1.x minor
release without a deprecation period.</p></blockquote>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><pre><code class="language-python">nonce = page_nonce_from_headers(request.headers)
html = card.render().serialize(
    deps_strategy=&quot;fragment&quot;,
    csp_nonce=nonce,
)
</code></pre></blockquote>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>headers</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>]</code>

- The request headers, such as Django's <code>request.headers</code>.
Header names match without regard to case.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None: The header&#x27;s value when it has the shape of a CSP nonce (letters,</p>




</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/_page_nonce.py#L30" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-page-nonce-header" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>PAGE_NONCE_HEADER</code>
</span>
<span class="doc-kind">attribute</span>
</h2>


<div class="doc-body">
<p>The request header that carries the CSP nonce of the page that sent the request.</p>
<p>Experimental: the name and the rules for reading it may change in a 1.x
minor release.</p>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_context.py#L60" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-citrycontext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>CitryContext</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Render-scoped state for a single component render.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>variables</code>

- The per-component template variables (the <code>template_data</code>
output). Read by nodes when evaluating expressions. Values are
ordinary Python objects; the private mapping stores any Const
promise separately by variable name.
</li>

<li>
<code>component</code>

- The <code>Component</code> instance currently rendering. Gives a node
access to the component tree (its <code>citry</code> registry for resolving
child component names, and its <code>parent</code>/<code>root</code> linkage). The
current component is stored on the context, so each component render
gets its own <code>CitryContext</code>.
</li>

<li>
<code>extra</code>

- Tree-wide scratch space for extensions (for example the
collected JS/CSS dependency records). Citry does not copy these
entries itself: when a child render is placed into its parent,
Citry calls the <code>on_render_context_merge</code> hook, and each
extension copies its own entries from the child's <code>extra</code> into
the parent's. By convention, each extension stores its data
under a top-level key named after itself
(<code>extra["dependencies"]</code>). Citry uses some other top-level keys
too, so choose a distinctive name.
</li>

<li>
<code>provides</code>

- The provide/inject entries active at this point of the
render. Entries may hold a direct caller value, a frozen keyword-
field payload, or a private blocked marker. Read-only by convention;
<code>Component.provide</code> and <code>Component.unprovide</code> build a new
mapping rather than mutating this one.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_context.py#L113" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrycontext-variables" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>variables</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_context.py#L120" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrycontext-extra" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>extra</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_context.py#L121" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrycontext-js-data" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>js_data</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>js_data: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_context.py#L122" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrycontext-component" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_context.py#L123" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrycontext-template-record" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>template_record</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_context.py#L125" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrycontext-provides" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>provides</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_context.py#L130" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrycontext-sandboxed" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>sandboxed</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_template.py#L46" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-citrytemplate" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>CitryTemplate</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>A component's loaded template: the source string, its origin, and its
compiled form (once first rendered).</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>source</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code>

- The template string, after <code>on_template_loaded</code> hooks ran.
</li>

<li>
<code>origin</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code>

- Where the template came from, for error messages and debugging.
The absolute file path for a file template, or
<code>"&lt;module file&gt;::&lt;ClassName&gt;"</code> for an inline one.
</li>

<li>
<code>filepath</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a> | None</code>

- The resolved template file, or <code>None</code> when the template
was inlined on the class.
</li>

<li>
<code>generate</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[], <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#list">list</a>[BodyItem]] | None</code>

- Internal. The compiled body-generating function; calling it
yields a fresh node list. <code>None</code> until the render pipeline
compiles the template on first render.
</li>

<li>
<code>prepared_generate</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[], <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#list">list</a>[BodyItem]] | None</code>

- Internal. The separate typed-output generator used
only by the private Vue preparation path.
</li>

<li>
<code>used_vars</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#frozenset">frozenset</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>]</code>

- Internal. Every variable name the template uses, including
in nested tags (the parse-time <code>Template.used_variables</code>). Empty
until compiled. The <code>Const</code> optimization keys its cache only on
these.
</li>

<li>
<code>declared_slots</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#tuple">tuple</a>[DeclaredSlot, ...]</code>

- Internal. The <code>&lt;c-slot&gt;</code> tags the template declares
(static names only), used to check the component against its
<code>Slots</code> schema. Empty until compiled.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_template.py#L74" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrytemplate-source" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>source</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>source: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_template.py#L75" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrytemplate-origin" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>origin</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>origin: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_template.py#L76" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrytemplate-filepath" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>filepath</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>filepath: <a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_template.py#L77" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrytemplate-template-id" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>template_id</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>template_id: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_template.py#L78" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrytemplate-kind" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>kind</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>kind: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;primary&#x27;, &#x27;standalone&#x27;, &#x27;nested&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_template.py#L81" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrytemplate-generate" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>generate</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>generate: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[], <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#list">list</a>[BodyItem]] | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_template.py#L82" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrytemplate-prepared-generate" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>prepared_generate</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>prepared_generate: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[], <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#list">list</a>[BodyItem]] | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_template.py#L83" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrytemplate-used-vars" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>used_vars</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>used_vars: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#frozenset">frozenset</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_template.py#L84" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrytemplate-declared-slots" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>declared_slots</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>declared_slots: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#tuple">tuple</a>[DeclaredSlot, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_template.py#L85" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrytemplate-foreign-spans" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>foreign_spans</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>foreign_spans: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_template.py#L86" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrytemplate-foreign-provider-metadata" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>foreign_provider_metadata</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>foreign_provider_metadata: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_template.py#L87" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrytemplate-foreign-compile-contexts" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>foreign_compile_contexts</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>foreign_compile_contexts: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_template.py#L88" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrytemplate-foreign-prepared" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>foreign_prepared</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>foreign_prepared: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_template.py#L89" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrytemplate-source-offset" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>source_offset</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>source_offset: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#int">int</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_template.py#L90" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrytemplate-root-source" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>root_source</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>root_source: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_template.py#L93" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrytemplate-compile-lock" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>compile_lock</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>compile_lock: <a class="doc-type-link" href="https://docs.python.org/3.13/library/threading.html#threading.RLock">RLock</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_template.py#L94" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrytemplate-standalone-bodies" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>standalone_bodies</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>standalone_bodies: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.html#collections.OrderedDict">OrderedDict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#object">object</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#list">list</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_template.py#L95" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrytemplate-prepared-standalone-bodies" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>prepared_standalone_bodies</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>prepared_standalone_bodies: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.html#collections.OrderedDict">OrderedDict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#object">object</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#list">list</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]]</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/host_templates.py#L21" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-compiledbody" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>CompiledBody</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Opaque handle to one already-compiled independent Citry body list.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Experimental</p><p>Part of the experimental API for embedding Citry tags in another
template engine. It may change in a minor release without a
deprecation period.</p></blockquote>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/host_templates.py#L79" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-render-compiled-body" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>render_compiled_body</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>render_compiled_body(body: <a class="doc-type-link" href="/reference/rendering/#citry-compiledbody">CompiledBody</a>, context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>, variables_overlay: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None = None) -> <a class="doc-type-link" href="/reference/rendering/#citry-citryrender">CitryRender</a></code></pre>
</div>

<div class="doc-body">
<p>Render a protected compiled body with a live host-variable overlay.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Experimental</p><p>Part of the experimental API for embedding Citry tags in another
template engine. It may change in a minor release without a
deprecation period.</p></blockquote>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/host_templates.py#L111" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-collect-compiled-body-fills" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>collect_compiled_body_fills</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>collect_compiled_body_fills(body: <a class="doc-type-link" href="/reference/rendering/#citry-compiledbody">CompiledBody</a>, context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>, sink: FillSink, variables_overlay: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None = None) -> None</code></pre>
</div>

<div class="doc-body">
<p>Collect fills from a host-selected compiled body against a live overlay.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Experimental</p><p>Part of the experimental API for embedding Citry tags in another
template engine. It may change in a minor release without a
deprecation period.</p></blockquote>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L1162" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-placeholder" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>Placeholder</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>A spot in the output whose final text is supplied at serialize time.</p>
<p>Rendered output is normally text and nested renders, fixed once rendered.
A Placeholder marks a position whose content is only known when the whole
page is serialized: the <code>&lt;c-js&gt;</code> / <code>&lt;c-css&gt;</code> built-ins render one
each, and the dependencies extension fills them with the collected
script/style tags via the <code>on_serialize</code> hook.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>key</code>

- What belongs at this spot (e.g. <code>"deps:js"</code>). The serializer
reports each occurrence to the <code>on_serialize</code> hook under this
key plus a counter and a private per-serialization identity. An
extension that knows the key supplies the text; an occurrence no
extension fills serializes to nothing. The private identity keeps
cleanup from matching an authored <code>&lt;template c-render-id&gt;</code> with
the same key and counter.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L1186" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-placeholder-key" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>key</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L481" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-renderreplacement" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>RenderReplacement</code>
</span>
<span class="doc-kind">attribute</span>
</h2>


<div class="doc-signature highlight">
<pre><code>RenderReplacement: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.TypeAlias">TypeAlias</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L600" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-renderframe" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>RenderFrame</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Immutable identity needed to traverse and serialize one render frame.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Experimental</p><p><code>RenderFrame</code>, the <code>CitryRender.frame</code> attribute and the <code>frame=</code>
argument of <code>CitryRender</code> are experimental. They may change in a
minor release without a deprecation period.</p></blockquote>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L611" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-renderframe-render-id" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>render_id</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>render_id: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L612" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-renderframe-class-id" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>class_id</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>class_id: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L613" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-renderframe-class-name" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>class_name</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>class_name: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L614" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-renderframe-is-component-root" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>is_component_root</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>is_component_root: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L615" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-renderframe-root-markers" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>root_markers</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>root_markers: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L616" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-renderframe-is-transparent-root" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>is_transparent_root</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>is_transparent_root: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>True for a transparent component's whole output, excluding caller-owned interiors.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L618" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-renderframe-prepared-occurrence" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>prepared_occurrence</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>prepared_occurrence: PreparedOccurrenceMetadata | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L620" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-renderframe-from-context" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>from_context</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>from_context(context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>, is_component_root: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a>, is_transparent_root: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a> = False) -> <a class="doc-type-link" href="/reference/rendering/#citry-renderframe">RenderFrame</a></code></pre>
</div>

<div class="doc-body">
<p>Snapshot the identity-bearing portion of one live render context.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L489" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-onrendergenerator" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>OnRenderGenerator</code>
</span>
<span class="doc-kind">attribute</span>
</h2>


<div class="doc-signature highlight">
<pre><code>OnRenderGenerator: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.TypeAlias">TypeAlias</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L151" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-depsstrategy" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>DepsStrategy</code>
</span>
<span class="doc-kind">attribute</span>
</h2>


<div class="doc-signature highlight">
<pre><code>DepsStrategy: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.TypeAlias">TypeAlias</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/citry_render.py#L156" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-depsposition" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>DepsPosition</code>
</span>
<span class="doc-kind">attribute</span>
</h2>


<div class="doc-signature highlight">
<pre><code>DepsPosition: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.TypeAlias">TypeAlias</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/constness.py#L206" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-const" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>Const</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>Const(wrapped: _T) -> _T</code></pre>
</div>

<div class="doc-body">






</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/constness.py#L212" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-is-const" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>is_const</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>is_const(value: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Return <code>True</code> if <code>value</code> is marked <code>Const</code>.</p>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/constness.py#L248" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-const-value" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>const_value</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>const_value(value: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code></pre>
</div>

<div class="doc-body">
<p>Unwrap outer marker layers; leave plain values unchanged and reject marker cycles.</p>





</div>
</div>






<div class="doc-object">

<h2 id="citry-markup" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>Markup</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></p>


<div class="doc-body">
<p><code>citry.Markup</code> is exactly <a href="https://markupsafe.palletsprojects.com/en/stable/escaping/#markupsafe.Markup"><code>markupsafe.Markup</code></a>, re-exported unchanged. <code>Markup(value)</code> trusts the complete value without sanitizing, validating, or escaping anything.</p>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/secret.py#L18" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-secret" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>Secret</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Generic">Generic</a></code></p>


<div class="doc-body">
<p>Wrap a server-only value, such as an API token, so Citry never sends it to the browser.</p>
<p>Citry sends everything <a href="/reference/component/#citry-component-js-data"><code>Component.js_data()</code></a>
returns to the browser, where anyone can read it in the page source.
Wrap a value in <code>Secret</code> to have Citry refuse to send it.</p>
<p>Rendering a component raises a <code>TypeError</code> that names the component and
the key, before any HTML is sent, when a <code>Secret</code> is anywhere in the
dicts and lists <code>js_data()</code> returns. A <code>Secret</code> in a
<a href="/reference/component/#citry-component-css-data"><code>Component.css_data()</code></a> value or a State
field raises <code>ValueError</code>, whether or not the component has CSS.
<code>citry --app ... check</code> also warns when it can see the <code>Secret</code>: a
module-level <code>Secret</code> that <code>js_data()</code> puts in its result, such as
<code>{"token": API_TOKEN}</code>, or reads from an attribute stored on a module
or a plain class, such as <code>config.API_TOKEN</code> (not through a property or
a lazy settings object), or a <code>JsData</code> field annotated <code>Secret[str]</code>.</p>
<p>A <code>Secret</code> that <code>js_data()</code> returns in another place, such as inside a
dataclass instance nested in the result, as a dict key, or in a set, is
refused too, but by the <code>TypeError</code> for any value JSON cannot carry,
which does not name the key.</p>
<p>On the server a <code>Secret</code> keeps its value hidden. Call
<a href="/reference/rendering/#citry-secret-get-secret-value"><code>get_secret_value()</code></a> where you need the
value, for example to call an API in an event handler. Everywhere Python
turns it into text it shows <code>***</code> instead: <code>str()</code>, <code>repr()</code>, f-strings,
logs, and <code>{{ token }}</code> in a template. So passing a <code>Secret</code> to a
template or to a child component's <code>Kwargs</code> is allowed and never prints
the value.</p>
<p>A child that uses the render cache cannot take a <code>Secret</code> this way.
Without <code>Cache.vary()</code>, its cache key is built from all of its kwargs,
and a <code>Secret</code> cannot be part of a key, so rendering raises
<a href="/reference/cache-keys/#citry-ext-cache-cachekeyerror"><code>CacheKeyError</code></a>. Return values that are
not secret, such as a user id, from that child's <code>Cache.vary()</code>, or
leave the child uncached.</p>
<p>Annotate a <code>Kwargs</code> or <code>TemplateData</code> field as <code>Secret[str]</code> (or
<code>Secret[bytes]</code>, and so on) so a plain value passed there is rejected.
The type in brackets is only for type checkers:
<a href="/reference/citry/#citry-lintsettings"><code>check_input_types</code></a> tests that the value is a
<code>Secret</code>, not what it holds. When <code>Kwargs</code> is a Pydantic model,
Pydantic's own error for a plain value prints that value; add
<code>model_config = ConfigDict(hide_input_in_errors=True)</code> to the model to
keep it out of the message.</p>
<p>A <code>Secret</code> never equals a plain value: <code>API_TOKEN == sent</code> is always
<code>False</code>. To check a value a user sent, use <code>hmac.compare_digest</code>, which
takes the same time however much of the input matches:</p>
<pre><code class="language-python">token = API_TOKEN.get_secret_value().encode()
# An unset variable gives an empty token, which an empty
# input would match, so refuse it first.
if not token:
    raise RuntimeError(&quot;API_TOKEN is not set&quot;)
matches = hmac.compare_digest(token, sent.encode())
</code></pre>
<p>Compare bytes, as here: <code>compare_digest</code> raises <code>TypeError</code> for text
that is not ASCII. Two secrets are equal when their values are equal.
When both values are <code>str</code>, or both are <code>bytes</code>, they are compared with
<code>hmac.compare_digest</code>. Any other values are compared with <code>==</code>.</p>
<p>A <code>Secret</code> cannot be changed after it is created. It can be a dict key
when its value is hashable, and equal secrets hash alike. <code>bool()</code> is
the truth value of the wrapped value, so <code>if token:</code> tells whether a
token is set. Copying or pickling a <code>Secret</code> keeps the value, so a
pickle still holds it in readable form.</p>
<p>Citry detects only values you wrap. A secret kept in a plain <code>str</code> is
sent like any other string.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><p>Read a token on the server, and send the browser only the result:</p>
<pre><code class="language-citry">import os

from citry import Component, Secret

API_TOKEN = Secret(os.environ[&quot;API_TOKEN&quot;])


class Board(Component):
    def template_data(self, kwargs, slots):
        token = API_TOKEN.get_secret_value()
        return {&quot;rows&quot;: load_rows(token)}

    def js_data(self, kwargs, slots):
        # Returning API_TOKEN here raises TypeError.
        return {&quot;apiBase&quot;: &quot;/api&quot;}

    template = '''
      &lt;ul&gt;
        &lt;c-for each=&quot;row in rows&quot;&gt;
          &lt;li&gt;{{ row }}&lt;/li&gt;
        &lt;/c-for&gt;
      &lt;/ul&gt;
    '''
</code></pre></blockquote>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>value</code>

<code>T</code>

- The value to keep on the server. Any type works.
</li>

</ul>



<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>TypeError</code> - When <code>value</code> is already a <code>Secret</code>. Pass that <code>Secret</code> on
as it is instead of wrapping it again.
</li>

</ul>



<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry/citry/secret.py#L147" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-secret-get-secret-value" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>get_secret_value</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>get_secret_value() -> T</code></pre>
</div>

<div class="doc-body">
<p>Return the wrapped value.</p>
<p>Call it only in server code that needs the value itself. Returning
the result from <code>js_data()</code>, or writing it into a template, sends it
to the browser as an ordinary value.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><pre><code class="language-python">token = API_TOKEN.get_secret_value()
</code></pre></blockquote>


<p class="doc-section">Returns</p>
<p class="doc-returns">T: The value given to `Secret(...)`.</p>




</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry_core/citry_core/safe_eval/eval.py#L19" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-securityerror" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>SecurityError</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/exceptions.html#Exception">Exception</a></code></p>


<div class="doc-body">
<p>An expression attempted an operation blocked by the evaluator's sandbox.</p>
<p>The evaluator raises this at evaluation time when a checked variable,
attribute, key, callable, or assignment is unsafe.</p>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry_core/citry_core/safe_eval/eval.py#L28" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-safe-eval" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>safe_eval</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>safe_eval(source: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, validate_variable: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>], <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a>] | None = None, validate_attribute: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[<a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>], <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a>] | None = None, validate_subscript: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[<a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>], <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a>] | None = None, validate_callable: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[<a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>], <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a>] | None = None, validate_assign: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>], <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a>] | None = None) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[<a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]], <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">
<p>Compile a Python expression into a function that runs it inside the sandbox Citry uses for template expressions. Call the result with a mapping of the names the expression may read. A blocked call, attribute, or name raises <a href="/reference/rendering/#citry-securityerror"><code>SecurityError</code></a> when the expression runs. Pass only expression text that you or the template author wrote, never text from a request or from stored user data, because the sandbox does not block everything. See <a href="/security/#sandbox-python-template-expressions">Sandbox template code</a> for what the sandbox blocks and what it misses.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>source</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code>

- The Python expression string to transform.
</li>

<li>
<code>validate_variable</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>], <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a>] | None</code>

- Optional extra validation for variable lookups.
</li>

<li>
<code>validate_attribute</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[<a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>], <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a>] | None</code>

- Optional extra validation for attribute access.
</li>

<li>
<code>validate_subscript</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[<a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>], <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a>] | None</code>

- Optional extra validation for subscript access.
</li>

<li>
<code>validate_callable</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[<a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>], <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a>] | None</code>

- Optional extra validation for function calls. It also receives
every function or class passed as an argument to a call, because the receiving function
may call it.
</li>

<li>
<code>validate_assign</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>], <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a>] | None</code>

- Optional extra validation for variable assignments.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[<a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]], <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]: A compiled function that takes a context mapping and evaluates the expression.</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>SyntaxError</code> - If the input is not valid Python syntax, contains forbidden constructs,
or nests too deeply (more than about 97 chained operators or 65 nested brackets).
</li>

</ul>



</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.3.0/packages/py/citry_core/citry_core/safe_eval/sandbox.py#L222" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-unsafe" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>unsafe</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>unsafe(f: F) -> F</code></pre>
</div>

<div class="doc-body">
<p>Mark a function or method so that sandboxed expressions cannot call it. While the expression sandbox is on (the default), a template that calls it fails with <a href="/reference/rendering/#citry-securityerror"><code>SecurityError</code></a>. See <a href="/security/#marking-your-own-functions-unsafe">Block your functions</a>.</p>





</div>
</div>



