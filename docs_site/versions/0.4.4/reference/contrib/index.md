---
title: Contrib integrations
url: https://citry.dev/v/0.4.4/reference/contrib/
description: "Adapters mounting citry into web frameworks, and cache adapters for shared stores (the citry.contrib.<name> modules)."
---
# Contrib integrations

Adapters mounting citry into web frameworks, and cache adapters for shared stores (the `citry.contrib.<name>` modules).




<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/contrib/fastapi.py#L32" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-contrib-fastapi-mount" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>mount</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>mount(app: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>, citry_instance: <a class="doc-type-link" href="/reference/citry/#citry-citry">Citry</a>, prefix: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> = &#x27;/citry&#x27;) -> None</code></pre>
</div>

<div class="doc-body">
<p>Mount <code>citry_instance</code>'s routes into a FastAPI/Starlette <code>app</code> at
<code>prefix</code>, and record the prefix on the instance.</p>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/contrib/flask.py#L35" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-contrib-flask-mount" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>mount</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>mount(app: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>, citry_instance: <a class="doc-type-link" href="/reference/citry/#citry-citry">Citry</a>, prefix: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> = &#x27;/citry&#x27;) -> None</code></pre>
</div>

<div class="doc-body">
<p>Mount <code>citry_instance</code>'s routes into a Flask <code>app</code> at <code>prefix</code>, and
record the prefix on the instance.</p>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/contrib/django.py#L132" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-contrib-django-urlpatterns" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>urlpatterns</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>urlpatterns(citry_instance: <a class="doc-type-link" href="/reference/citry/#citry-citry">Citry</a>, prefix: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None = None) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">
<p><code>Citry.urls</code> as Django URL patterns, for <code>include()</code>-ing.</p>
<p>Pass <code>prefix</code> (where you include the patterns, e.g. <code>"/citry"</code>) to
also record it on the instance, so URL building (fragment manifests, the
runtime <code>src</code>) points at the right place; leaving it <code>None</code> means you
call <code>set_mounted_prefix</code> yourself.</p>
<p>The generated views are synchronous, so every route handler must be a
plain function; an <code>async def</code> handler raises <code>TypeError</code> here,
pointing at the ASGI adapter as the fix.</p>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/contrib/django.py#L178" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-contrib-django-enable-hot-reload" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>enable_hot_reload</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>enable_hot_reload(citry_instance: <a class="doc-type-link" href="/reference/citry/#citry-citry">Citry</a>, mode: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;hot&#x27;, &#x27;restart&#x27;] = &#x27;hot&#x27;) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[..., <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a> | None]</code></pre>
</div>

<div class="doc-body">
<p>Reload changed component files in development, using Django's autoreloader.</p>
<p>Connects a receiver to Django's <code>file_changed</code> autoreload signal. When a
watched file changes, the receiver clears the caches of the components that
loaded it (<code>Citry.invalidate_file</code>). With <code>mode="hot"</code> (the default) the
change is handled in place and the server keeps running; with
<code>mode="restart"</code> the process restart is left to Django (the same thing
Django does for a Python edit). Files that back no loaded component fall
through to Django's normal handling either way.</p>
<p>Call once at startup, e.g. from your <code>AppConfig.ready()</code>. Django watches
its template and static directories, so this needs no watcher of its own.
Returns the connected receiver (disconnect it via <code>file_changed.disconnect</code>
if you ever need to).</p>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/contrib/django.py#L221" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-contrib-django-secret" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>secret</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>secret() -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Django's <code>SECRET_KEY</code>, for passing as <code>Citry(secret=...)</code>.</p>
<p>Citry signs values with the engine-level
<a href="/reference/citry/#citry-citrysettings-secret"><code>secret</code></a> setting. In a Django project the
natural signing key is the one the project already manages, so pass it
through::</p>
<pre><code>from citry import Citry
from citry.contrib.django import secret

app = Citry(secret=secret())
</code></pre>
<p>The key is read when this is called, so Django settings must be configured
by then (in a normal Django startup they already are).</p>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>: The ``SECRET_KEY`` of the active Django settings.</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>RuntimeError</code> - When Django settings are not configured; the message
names the fix.
</li>

<li>
<code>django.core.exceptions.ImproperlyConfigured</code> - When settings are
configured but the <code>SECRET_KEY</code> itself is unusable (for example
empty); Django's own message explains the problem.
</li>

</ul>



</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/contrib/django.py#L271" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-contrib-django-djangocache" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>DjangoCache</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Adapt a Django cache (<code>django.core.cache.caches[...]</code>) to citry's
<code>CitryCache</code> protocol, so citry's stored scripts live in whatever cache
backend the Django project already runs (Redis, Memcached, database, ...).</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/contrib/django.py#L281" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-contrib-django-djangocache-get" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>get</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>get(key: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/contrib/django.py#L285" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-contrib-django-djangocache-set" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>set</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>set(key: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, value: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, ttl: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#float">float</a> | None = None) -> None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/contrib/django.py#L295" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-contrib-django-djangocache-delete" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>delete</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>delete(key: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/contrib/django.py#L298" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-contrib-django-djangocache-has" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>has</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>has(key: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/contrib/asgi.py#L113" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-contrib-asgi-asgi-app" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>asgi_app</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>asgi_app(citry_instance: <a class="doc-type-link" href="/reference/citry/#citry-citry">Citry</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[Scope, Receive, Send], <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Awaitable">Awaitable</a>[None]]</code></pre>
</div>

<div class="doc-body">
<p>Build the ASGI application serving <code>citry_instance.urls</code>.</p>
<p>The returned app handles lifespan events (so it also works served
standalone), routes each http request to the matched citry handler
(preferring a route's <code>handler_async</code> twin when it carries one),
translates the scope into a <code>RouteRequest</code> (<code>_build_request</code>),
dispatches it (<code>call_maybe_sync</code>: async handlers are awaited, sync
ones run in a worker thread), and translates the returned
<code>RouteResponse</code> into ASGI messages (<code>_send_response</code>).</p>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/contrib/asgi.py#L182" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-contrib-asgi-reload-lifespan" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>reload_lifespan</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>reload_lifespan(engine: <a class="doc-type-link" href="/reference/citry/#citry-citry">Citry</a>, roots: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Iterable">Iterable</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a>] | None = None, watcher: FileWatcher | None = None, on_reload: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#set">set</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a>], <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]]], None] | None = None) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[<a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>], <a class="doc-type-link" href="https://docs.python.org/3.13/library/contextlib.html#contextlib.AbstractAsyncContextManager">AbstractAsyncContextManager</a>[None]]</code></pre>
</div>

<div class="doc-body">
<p>A Starlette/FastAPI <code>lifespan</code> that hot-reloads component files while the
app runs.</p>
<p>Compose it into the app's root lifespan::</p>
<pre><code>from contextlib import asynccontextmanager
from citry.contrib.asgi import reload_lifespan

watch_lifespan = reload_lifespan(citry_instance)

@asynccontextmanager
async def lifespan(app):
    citry_instance.initialize()
    async with watch_lifespan(app):
        yield

app = FastAPI(lifespan=lifespan)   # or Starlette(...)
</code></pre>
<p>It starts the :mod:<code>citry.reload</code> watcher on startup and stops it on
shutdown, so editing a component's template/JS/CSS shows up on the next
render without restarting. It manages only the watcher and does not call
<a href="/reference/citry/#citry-citry-initialize"><code>Citry.initialize()</code></a>; the root lifespan owns
initialization. For development; in production simply do not add it. If you
already have a lifespan, nest this one inside yours. The keyword arguments
mirror :func:<code>citry.reload.watch</code>.</p>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/contrib/wsgi.py#L78" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-contrib-wsgi-wsgi-app" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>wsgi_app</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>wsgi_app(citry_instance: <a class="doc-type-link" href="/reference/citry/#citry-citry">Citry</a>) -> WSGIApp</code></pre>
</div>

<div class="doc-body">
<p>Build the WSGI application serving <code>citry_instance.urls</code>.</p>
<p>The returned app routes each request to the matched citry handler,
translates the environ into a <code>RouteRequest</code> (<code>_build_request</code>),
calls the handler, and translates the returned <code>RouteResponse</code> back
into the WSGI shape (<code>respond</code>). Async handlers are rejected with a
pointed error up front: WSGI is synchronous.</p>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/contrib/caches.py#L37" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-contrib-caches-rediscache" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>RedisCache</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Adapt a Redis client (<code>redis.Redis</code> or compatible) to citry's
<code>CitryCache</code> protocol. Values are stored as UTF-8 strings; <code>ttl</code>
becomes the key's expiry (<code>ex</code>).</p>
<p><code>prefix</code> is prepended to every key, for sharing a Redis database with
other uses. (Citry's own keys already start with <code>citry:</code>.)</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/contrib/caches.py#L51" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-contrib-caches-rediscache-get" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>get</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>get(key: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/contrib/caches.py#L57" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-contrib-caches-rediscache-set" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>set</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>set(key: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, value: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, ttl: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#float">float</a> | None = None) -> None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/contrib/caches.py#L67" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-contrib-caches-rediscache-delete" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>delete</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>delete(key: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/contrib/caches.py#L70" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-contrib-caches-rediscache-has" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>has</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>has(key: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/contrib/caches.py#L74" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-contrib-caches-diskcache" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>DiskCache</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Adapt a <code>diskcache.Cache</code> (or compatible) to citry's <code>CitryCache</code>
protocol. The store is a directory on disk, shared by every worker
process on the host.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/contrib/caches.py#L84" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-contrib-caches-diskcache-get" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>get</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>get(key: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/contrib/caches.py#L88" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-contrib-caches-diskcache-set" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>set</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>set(key: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, value: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, ttl: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#float">float</a> | None = None) -> None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/contrib/caches.py#L95" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-contrib-caches-diskcache-delete" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>delete</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>delete(key: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/contrib/caches.py#L98" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-contrib-caches-diskcache-has" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>has</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>has(key: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>



