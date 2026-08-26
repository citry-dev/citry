---
title: Web integration
url: https://citry.dev/v/0.4.4/reference/web/
description: "The route table a web framework mounts, and the request/response types handlers use (see citry.contrib)."
---
# Web integration

The route table a web framework mounts, and the request/response types handlers use (see `citry.contrib`).




<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/util/routing.py#L155" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-urlroute" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>URLRoute</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>One framework-neutral route: either a <code>handler</code> or nested <code>children</code>.</p>
<p>A child's full path is the parent's path followed by the child's (plain
concatenation; end a parent path with <code>/</code>). <code>{name}</code> segments in the
path become keyword arguments of the handler.</p>
<p><code>handler_async</code> optionally carries an <code>async def</code> twin of <code>handler</code>
(same signature and behavior). Adapters that run an event loop (ASGI)
serve the route through the twin, awaiting it natively, while the plain
<code>handler</code> stays what the sync hosts (WSGI, sync Django) mount and run.
Only routes that need both worlds carry it; a route table meant solely
for ASGI can simply pass an <code>async def</code> function as <code>handler</code>.</p>
<p>Example::</p>
<pre><code>URLRoute("cache/{class_id}.{script_type}", handler=serve_script, name="citry_cached_script")
URLRoute("ext/", children=[URLRoute("my_ext/status", handler=status)])
</code></pre>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/util/routing.py#L177" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-urlroute-path" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>path</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>path: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/util/routing.py#L183" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-urlroute-handler" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>handler</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>handler: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[..., <a class="doc-type-link" href="/reference/web/#citry-routeresponse">RouteResponse</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Awaitable">Awaitable</a>[<a class="doc-type-link" href="/reference/web/#citry-routeresponse">RouteResponse</a>]] | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/util/routing.py#L184" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-urlroute-handler-async" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>handler_async</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>handler_async: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[..., <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Awaitable">Awaitable</a>[<a class="doc-type-link" href="/reference/web/#citry-routeresponse">RouteResponse</a>]] | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/util/routing.py#L185" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-urlroute-children" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>children</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>children: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/web/#citry-urlroute">URLRoute</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/util/routing.py#L186" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-urlroute-name" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>name</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/util/routing.py#L187" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-urlroute-methods" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>methods</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>methods: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/util/routing.py#L188" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-urlroute-extra" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>extra</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>extra: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/util/routing.py#L84" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-routerequest" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>RouteRequest</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>A framework-neutral view of one HTTP request, passed to route handlers.</p>
<p>Each web adapter (<code>citry.contrib.asgi</code>, <code>citry.contrib.wsgi</code>, the
Django patterns, ...) builds this from its host's request, so a handler
reads the same fields no matter which framework serves it. Anything
host-specific stays reachable through <code>native</code>.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>method</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The HTTP method, uppercase (<code>"GET"</code>, <code>"POST"</code>, ...).
</li>

<li>
<code>path</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The full URL path of the request, including the prefix the
route table is mounted under (e.g. <code>"/citry/citry.js"</code>).
</li>

<li>
<code>query</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, ...]]</code>

- The query-string parameters. Each key maps to all values it
was sent with, in order, so repeated keys are preserved.
</li>

<li>
<code>headers</code>

<code><a class="doc-type-link" href="/reference/web/#citry-routeheaders">RouteHeaders</a></code>

- The HTTP request headers; lookups ignore case.
</li>

<li>
<code>body</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#bytes">bytes</a></code>

- The raw request body. Empty for bodyless methods such as GET.
</li>

<li>
<code>content_type</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The <code>Content-Type</code> header value, or <code>""</code> when the
request names none.
</li>

<li>
<code>native</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code>

- The untouched host request object: the ASGI scope, the WSGI
environ, or Django's <code>HttpRequest</code>.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/util/routing.py#L109" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-routerequest-method" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>method</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>method: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/util/routing.py#L110" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-routerequest-path" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>path</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>path: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/util/routing.py#L111" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-routerequest-query" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>query</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>query: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, ...]]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/util/routing.py#L112" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-routerequest-headers" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>headers</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>headers: <a class="doc-type-link" href="/reference/web/#citry-routeheaders">RouteHeaders</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/util/routing.py#L113" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-routerequest-body" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>body</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>body: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#bytes">bytes</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/util/routing.py#L114" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-routerequest-content-type" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>content_type</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>content_type: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/util/routing.py#L115" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-routerequest-native" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>native</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>native: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/util/routing.py#L126" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-routeresponse" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>RouteResponse</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>What a route handler returns; adapters translate it to the host's response type.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>content</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#bytes">bytes</a></code>

- The response body, as text or raw bytes.
</li>

<li>
<code>content_type</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The <code>Content-Type</code> header value to send.
</li>

<li>
<code>status</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code>

- The HTTP status code.
</li>

<li>
<code>headers</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>], ...]</code>

- Extra response headers, as <code>(name, value)</code> pairs; adapters
send them in addition to <code>Content-Type</code>. A name may repeat (e.g.
two <code>Set-Cookie</code> lines): the ASGI and WSGI adapters send every
pair, while the Django adapter raises <code>ValueError</code> on a repeated
name, because Django's response object holds one value per header
name.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/util/routing.py#L144" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-routeresponse-content" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>content</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>content: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#bytes">bytes</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/util/routing.py#L145" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-routeresponse-content-type" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>content_type</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>content_type: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/util/routing.py#L146" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-routeresponse-status" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>status</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>status: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/util/routing.py#L147" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-routeresponse-headers" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>headers</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>headers: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>], ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/util/routing.py#L150" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-routeresponse-body" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>body</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>body: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#bytes">bytes</a></code></pre>
</div>

<div class="doc-body">
<p>The content as bytes (utf8-encoded when given as a string).</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/util/routing.py#L45" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-routeheaders" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>RouteHeaders</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a></code></p>


<div class="doc-body">
<p>A read-only mapping of HTTP header names to values; lookups ignore case.</p>
<p>Built from <code>(name, value)</code> pairs. Iteration yields the names lowercased,
and a header sent multiple times has its values joined with <code>", "</code> (the
HTTP rule for repeatable headers).</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><pre><code class="language-python">headers = RouteHeaders([(&quot;Content-Type&quot;, &quot;application/json&quot;)])
headers[&quot;content-type&quot;]  # &quot;application/json&quot;
headers[&quot;CONTENT-TYPE&quot;]  # &quot;application/json&quot;
</code></pre></blockquote>





</div>
</div>



