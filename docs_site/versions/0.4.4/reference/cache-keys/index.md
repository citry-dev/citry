---
title: Render cache keys
url: https://citry.dev/v/0.4.4/reference/cache-keys/
description: "Exact key helpers and errors for component and named-fragment render caches."
---
# Render cache keys

Exact key helpers and errors for component and named-fragment render caches.




<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/cache/config.py#L25" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-cacheconfig" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>CacheConfig</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/extensions/#citry-extensionconfig">ExtensionConfig</a></code></p>


<div class="doc-body">
<p>Typed runtime view of one component's <code>Cache</code> declaration.</p>
<p>Citry creates this value from the component's nested <code>Cache</code> class. Read
it through <code>component.cache</code> while the component is rendering.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>enabled</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code>

- Whether Citry may cache this component's rendered output.
</li>

<li>
<code>ttl</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#float">float</a> | None</code>

- How many seconds an entry remains valid, or <code>None</code> for no
expiry.
</li>

<li>
<code>version</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- An application-controlled value included in the cache key.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/cache/config.py#L40" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-cacheconfig-enabled" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>enabled</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>enabled: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/cache/config.py#L41" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-cacheconfig-ttl" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>ttl</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>ttl: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#float">float</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/cache/config.py#L42" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-cacheconfig-version" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>version</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>version: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/cache/errors.py#L39" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-cache-cachekeyerror" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>CacheKeyError</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/library/exceptions.html#ValueError">ValueError</a></code></p>


<div class="doc-body">
<p>A value cannot be represented safely in a render-cache key.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>path</code>

- Location of the rejected value within the semantic variation.
</li>

<li>
<code>reason</code>

- Human-readable reason the value was rejected.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/cache/errors.py#L50" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-cache-cachekeyerror-path" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>path</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/cache/errors.py#L51" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-cache-cachekeyerror-reason" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>reason</code>
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/cache/extension.py#L80" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-cache-oncomponentcachehitcontext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>OnComponentCacheHitContext</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Notify an observer after one cached component subtree was replayed.</p>
<p><code>component</code> is the live boundary from the current call, never an
archived object. <code>key_digest</code> is exactly 64 lowercase hexadecimal
characters without a backend-key prefix. <code>artifact_bytes</code> is the
stored value's validated UTF-8 size, and <code>frame_count</code> includes the
boundary frame. <code>kind</code> distinguishes a <code>Component.Cache</code> hit from a
transparent <code>&lt;c-cache&gt;</code> fragment hit. For a fragment, <code>component</code> is
the live built-in Cache boundary from the current call. Return values and
observer failures do not alter the committed hit.</p>
<p>The dataclass is shallowly frozen. Observers should copy the scalar fields
they need instead of retaining the live component through this context.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/cache/extension.py#L98" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-cache-oncomponentcachehitcontext-citry" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>citry</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>citry: <a class="doc-type-link" href="/reference/citry/#citry-citry">Citry</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/cache/extension.py#L99" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-cache-oncomponentcachehitcontext-component" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component: <a class="doc-type-link" href="/reference/component/#citry-component">Component</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/cache/extension.py#L100" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-cache-oncomponentcachehitcontext-kind" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>kind</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>kind: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;component&#x27;, &#x27;fragment&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/cache/extension.py#L101" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-cache-oncomponentcachehitcontext-key-digest" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>key_digest</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>key_digest: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/cache/extension.py#L102" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-cache-oncomponentcachehitcontext-artifact-bytes" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>artifact_bytes</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>artifact_bytes: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/cache/extension.py#L103" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-cache-oncomponentcachehitcontext-frame-count" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>frame_count</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>frame_count: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/cache/keys.py#L55" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-cache-component-cache-key" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>component_cache_key</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>component_cache_key(component: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>], vary: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>, version: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> = 1) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Build the exact physical key for one component variation.</p>
<p>This helper does not construct the component, run input hooks, or call a
component's <code>Cache.vary()</code> method. Callers supply the already-computed semantic
variation value.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>component</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code>

- Component class whose stable class ID identifies the entry.
</li>

<li>
<code>vary</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a></code>

- Semantic variation accepted by Citry's canonical key encoder.
</li>

<li>
<code>version</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Author-controlled exact integer or non-empty string version.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>: A short ASCII key suitable for deleting one exact backend entry.</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>TypeError</code> - If <code>component</code> is not a Component class.
</li>

<li>
<code>ValueError</code> - If <code>version</code> is invalid.
</li>

<li>
<code>CacheKeyError</code> - If <code>vary</code> cannot be encoded safely.
</li>

</ul>



</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/cache/keys.py#L95" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-cache-fragment-cache-key" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>fragment_cache_key</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>fragment_cache_key(citry: <a class="doc-type-link" href="/reference/citry/#citry-citry">Citry</a>, key: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, vary: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a> = (), version: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> = 1) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Build the exact physical key for one named fragment variation.</p>
<p>Like <code>&lt;c-cache&gt;</code>, this unwraps an outer <code>Const</code> marker from <code>key</code>,
<code>vary</code>, and <code>version</code> before validation and encoding.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>citry</code>

<code><a class="doc-type-link" href="/reference/citry/#citry-citry">Citry</a></code>

- Engine whose cache scope and local revision apply.
</li>

<li>
<code>key</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Exact non-empty semantic fragment name.
</li>

<li>
<code>vary</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a></code>

- Semantic variation accepted by Citry's canonical key encoder.
</li>

<li>
<code>version</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Author-controlled exact integer or non-empty string version.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>: A short ASCII key suitable for deleting one exact backend entry.</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>TypeError</code> - If <code>citry</code> is not a Citry instance.
</li>

<li>
<code>ValueError</code> - If <code>key</code> or <code>version</code> is invalid.
</li>

<li>
<code>CacheKeyError</code> - If <code>vary</code> cannot be encoded safely.
</li>

</ul>



</div>
</div>



