---
title: Rendering
url: https://citry.dev/v/0.4.4/reference/rendering/
description: "The render pipeline, its output structs, and Citry's trusted-HTML marker. citry.Markup is exactly markupsafe.Markup. Markup(value) trusts the complete..."
---
# Rendering

The render pipeline, its output structs, and Citry's trusted-HTML marker. `citry.Markup` is exactly [`markupsafe.Markup`](https://markupsafe.palletsprojects.com/en/stable/escaping/#markupsafe.Markup). `Markup(value)` trusts the complete value without sanitizing or validating anything.




<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_element.py#L63" target="_blank" rel="noopener">
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

- The final source-ordered <code>$c-props</code>, Alpine event,
and Citry event contributions captured from a component tag. They
are framework metadata, not Python kwargs.
</li>

<li>
<code>ownership_invocation_id</code>

- The render-local component call record that
this element will bind to its concrete component instance.
</li>

<li>
<code>ownership_graph</code>

- The render-local graph that allocated
<code>ownership_invocation_id</code>. Retained explicitly so a lazy value
invoked during another root render cannot bind a graph-local ID
against the wrong graph.
</li>

<li>
<code>element_morph_metadata</code>

- Private metadata materialized only by the
dynamic ordinary-element built-in.
</li>

<li>
<code>forward_ownership_invocation</code>

- Whether this element is the transparent
dynamic selector and must forward the invocation to its selected
target instead of consuming it.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_element.py#L121" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_element.py#L122" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_element.py#L123" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_element.py#L124" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_element.py#L125" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citryelement-ownership-invocation-id" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>ownership_invocation_id</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_element.py#L126" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citryelement-ownership-graph" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>ownership_graph</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_element.py#L127" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_element.py#L128" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citryelement-forward-ownership-invocation" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>forward_ownership_invocation</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_element.py#L130" target="_blank" rel="noopener">
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
<pre><code>render(template_globals: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None = None, provides: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None = None) -> <a class="doc-type-link" href="/reference/rendering/#citry-citryrender">CitryRender</a></code></pre>
</div>

<div class="doc-body">
<p>Render this component into a <code>CitryRender</code>.</p>
<p>Each call mints fresh per-instance state (render_id, etc.), so the same
CitryElement can be rendered multiple times with distinct identities.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>template_globals</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None</code>

- Template variables added for this render. They
reach the whole tree, sit above the Citry instance's globals,
and sit below each component's own <code>template_data</code>.
</li>

<li>
<code>provides</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None</code>

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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L186" target="_blank" rel="noopener">
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

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code>

- True only for the render that is a component's whole
output (produced by the render pipeline, one per component
instance). Interior renders (a <code>&lt;c-if&gt;</code>/<code>&lt;c-for&gt;</code> block, a
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L216" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L217" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L218" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L221" target="_blank" rel="noopener">
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
<pre><code>is_component_root: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Whether this render is the whole output frame of one component.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L225" target="_blank" rel="noopener">
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
<pre><code>serialize(deps_strategy: <a class="doc-type-link" href="/reference/rendering/#citry-depsstrategy">DepsStrategy</a> = &#x27;document&#x27;, deps_position: <a class="doc-type-link" href="/reference/rendering/#citry-depsposition">DepsPosition</a> = &#x27;smart&#x27;, csp_nonce: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None = None, security_csp: <a class="doc-type-link" href="/reference/citry/#citry-securitycspmode">SecurityCspMode</a> | None = None, security_javascript: <a class="doc-type-link" href="/reference/citry/#citry-securityjavascriptmode">SecurityJavascriptMode</a> | None = None, security_script_integrity: <a class="doc-type-link" href="/reference/citry/#citry-securityscriptintegritymode">SecurityScriptIntegrityMode</a> | None = None) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Turn this render into a final HTML string.</p>
<p>Each component's root element(s) get a <code>data-cid-&lt;id&gt;</code> marker so the
rendered HTML records which component produced which part of the page,
and the JS/CSS collected from the rendered components is placed into the
output per the chosen strategy and position.</p>
<p>Raises <code>RuntimeError</code> if any child component was left unrendered (a
<code>DeferredComponent</code> still in the parts), which can only happen if this
render did not come from <code>render()</code>.</p>
<p>CSP warning mode reports incompatibilities without changing the
standard-runtime output. Strict mode selects the CSP runtime and
rejects incompatible reached-tree or final HTML. JavaScript warning
mode inventories client requirements, omit removes Citry-managed
executable output while retaining HTML and CSS, and forbid rejects a
rendered subtree that requires client behavior.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>deps_strategy</code>

<code><a class="doc-type-link" href="/reference/rendering/#citry-depsstrategy">DepsStrategy</a></code>

- <p>How to handle the collected JS/CSS.</p>
<ul>
<li><code>"document"</code> (default): emit the tags, plus the
client-side dependency manager and the page manifest when
a component needs per-instance browser behavior, including
<code>js_data()</code> scope seeding and <code>$component</code> callbacks.</li>
<li><code>"simple"</code>: the tags only, no JavaScript runtime. For
static pages and emails; per-instance JS does not run
(CSS variables still work, they are pure CSS).</li>
<li><code>"fragment"</code>: HTML meant to be inserted into an
already-loaded page (an HTMX swap, <code>fetch</code> +
<code>innerHTML</code>, ...): nothing is inlined; the output ends
with a JSON manifest of URLs the client-side manager
fetches, each once per page however many fragments need
it. Requires a mounted web integration.</li>
<li><code>"ignore"</code>: no tags inserted.</li>
</ul>
</li>

<li>
<code>deps_position</code>

<code><a class="doc-type-link" href="/reference/rendering/#citry-depsposition">DepsPosition</a></code>

- <p>Where the tags go (<code>document</code>/<code>simple</code> only).</p>
<ul>
<li><code>"smart"</code> (default): into the <code>&lt;c-js&gt;</code>/<code>&lt;c-css&gt;</code>
placeholders when present, else CSS before the first
<code>&lt;/head&gt;</code> and JS before the last <code>&lt;/body&gt;</code>, else
CSS is prepended and JS appended.</li>
<li><code>"prepend"</code> / <code>"append"</code>: all tags before/after the
whole output.</li>
</ul>
</li>

<li>
<code>csp_nonce</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

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

- Override this render's engine-level
script integrity policy.
</li>

</ul>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L298" target="_blank" rel="noopener">
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
<pre><code>serialize_result(deps_strategy: <a class="doc-type-link" href="/reference/rendering/#citry-depsstrategy">DepsStrategy</a> = &#x27;document&#x27;, deps_position: <a class="doc-type-link" href="/reference/rendering/#citry-depsposition">DepsPosition</a> = &#x27;smart&#x27;, csp_nonce: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None = None, security_csp: <a class="doc-type-link" href="/reference/citry/#citry-securitycspmode">SecurityCspMode</a> | None = None, security_javascript: <a class="doc-type-link" href="/reference/citry/#citry-securityjavascriptmode">SecurityJavascriptMode</a> | None = None, security_script_integrity: <a class="doc-type-link" href="/reference/citry/#citry-securityscriptintegritymode">SecurityScriptIntegrityMode</a> | None = None) -> <a class="doc-type-link" href="/reference/rendering/#citry-serializedrender">SerializedRender</a></code></pre>
</div>

<div class="doc-body">
<p>Return final HTML together with security metadata for those exact bytes.</p>
<p>Arguments and validation match :meth:<code>serialize</code>; this richer method
exposes the host-facing metadata while :meth:<code>serialize</code> returns only
<code>result.html</code>.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L126" target="_blank" rel="noopener">
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





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L130" target="_blank" rel="noopener">
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
<pre><code>html: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L131" target="_blank" rel="noopener">
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


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L112" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L122" target="_blank" rel="noopener">
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
<pre><code>scripts: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/rendering/#citry-serializedscriptsecurity">SerializedScriptSecurity</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L123" target="_blank" rel="noopener">
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
<pre><code>csp_script_hashes: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L95" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L105" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L106" target="_blank" rel="noopener">
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
<pre><code>url: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L107" target="_blank" rel="noopener">
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
<pre><code>digests: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L108" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L109" target="_blank" rel="noopener">
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
<pre><code>origin_class_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_context.py#L62" target="_blank" rel="noopener">
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
output). Read by nodes when evaluating expressions.
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
collected JS/CSS dependency records). Top-level keys are
namespaced by owner; see the module docstring.
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_context.py#L106" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_context.py#L107" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_context.py#L108" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_context.py#L109" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrycontext-ownership" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>ownership</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_context.py#L110" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_context.py#L111" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_context.py#L116" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_template.py#L46" target="_blank" rel="noopener">
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

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The template string, after <code>on_template_loaded</code> hooks ran.
</li>

<li>
<code>origin</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

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

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[], <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[BodyItem]] | None</code>

- Internal. The compiled body-generating function; calling it
yields a fresh node list. <code>None</code> until the render pipeline
compiles the template on first render.
</li>

<li>
<code>used_vars</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#frozenset">frozenset</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>]</code>

- Internal. Every variable name the template uses, including
in nested tags (the parse-time <code>Template.used_variables</code>). Empty
until compiled. The <code>Const</code> optimization keys its cache only on
these.
</li>

<li>
<code>declared_slots</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[DeclaredSlot, ...]</code>

- Internal. The <code>&lt;c-slot&gt;</code> tags the template declares
(static names only), used to check the component against its
<code>Slots</code> schema. Empty until compiled.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_template.py#L72" target="_blank" rel="noopener">
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
<pre><code>source: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_template.py#L73" target="_blank" rel="noopener">
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
<pre><code>origin: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_template.py#L74" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_template.py#L75" target="_blank" rel="noopener">
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
<pre><code>template_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_template.py#L76" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_template.py#L79" target="_blank" rel="noopener">
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
<pre><code>generate: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[], <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[BodyItem]] | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_template.py#L80" target="_blank" rel="noopener">
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
<pre><code>used_vars: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#frozenset">frozenset</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_template.py#L81" target="_blank" rel="noopener">
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
<pre><code>declared_slots: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[DeclaredSlot, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_template.py#L82" target="_blank" rel="noopener">
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
<pre><code>foreign_spans: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_template.py#L83" target="_blank" rel="noopener">
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
<pre><code>foreign_provider_metadata: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_template.py#L84" target="_blank" rel="noopener">
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
<pre><code>foreign_compile_contexts: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_template.py#L85" target="_blank" rel="noopener">
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
<pre><code>foreign_prepared: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_template.py#L86" target="_blank" rel="noopener">
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
<pre><code>source_offset: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_template.py#L87" target="_blank" rel="noopener">
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
<pre><code>root_source: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_template.py#L88" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_template.py#L89" target="_blank" rel="noopener">
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
<pre><code>standalone_bodies: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.html#collections.OrderedDict">OrderedDict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]]</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/host_templates.py#L20" target="_blank" rel="noopener">
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





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/host_templates.py#L71" target="_blank" rel="noopener">
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
<pre><code>render_compiled_body(body: <a class="doc-type-link" href="/reference/rendering/#citry-compiledbody">CompiledBody</a>, context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>, variables_overlay: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None = None) -> <a class="doc-type-link" href="/reference/rendering/#citry-citryrender">CitryRender</a></code></pre>
</div>

<div class="doc-body">
<p>Render a protected compiled body with a live host-variable overlay.</p>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/host_templates.py#L99" target="_blank" rel="noopener">
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
<pre><code>collect_compiled_body_fills(body: <a class="doc-type-link" href="/reference/rendering/#citry-compiledbody">CompiledBody</a>, context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>, sink: FillSink, variables_overlay: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None = None) -> None</code></pre>
</div>

<div class="doc-body">
<p>Collect fills from a host-selected compiled body against a live overlay.</p>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L404" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L428" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L141" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L154" target="_blank" rel="noopener">
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





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L158" target="_blank" rel="noopener">
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
<pre><code>render_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L159" target="_blank" rel="noopener">
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
<pre><code>class_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L160" target="_blank" rel="noopener">
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
<pre><code>class_name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L161" target="_blank" rel="noopener">
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
<pre><code>is_component_root: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L162" target="_blank" rel="noopener">
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
<pre><code>root_markers: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L164" target="_blank" rel="noopener">
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
<pre><code>from_context(context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>, is_component_root: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a>) -> <a class="doc-type-link" href="/reference/rendering/#citry-renderframe">RenderFrame</a></code></pre>
</div>

<div class="doc-body">
<p>Snapshot the identity-bearing portion of one live render context.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L149" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L89" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry_render.py#L92" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/constness.py#L145" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/constness.py#L151" target="_blank" rel="noopener">
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
<pre><code>is_const(value: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Return <code>True</code> if <code>value</code> is marked <code>Const</code>.</p>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/constness.py#L156" target="_blank" rel="noopener">
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
<p>Return the underlying value if <code>value</code> is <code>Const</code>, else <code>value</code>.</p>





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

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></p>


<div class="doc-body">
<p><code>citry.Markup</code> is exactly <a href="https://markupsafe.palletsprojects.com/en/stable/escaping/#markupsafe.Markup"><code>markupsafe.Markup</code></a>, re-exported unchanged. <code>Markup(value)</code> trusts the complete value without sanitizing, validating, or escaping anything.</p>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry_core/citry_core/safe_eval/eval.py#L15" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-securityerror" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>SecurityError</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/library/exceptions.html#Exception">Exception</a></code></p>


<div class="doc-body">
<p>An expression attempted an operation blocked by the evaluator's sandbox.</p>
<p>The evaluator raises this at evaluation time when a checked variable,
attribute, key, callable, or assignment is unsafe.</p>





</div>
</div>



