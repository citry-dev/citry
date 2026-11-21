---
title: Hot reload
url: https://citry.dev/v/1.2.0/reference/hot-reload/
description: "The citry.reload module, which watches component files and reloads them in place while you develop (see the hot reload guide)."
---
# Hot reload

The `citry.reload` module, which watches component files and reloads them in place while you develop (see the [hot reload guide](/v/1.2.0/guides/hot-reload/)).




<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.2.0/packages/py/citry/citry/reload.py#L293" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-reload-watch" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>watch</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>watch(engine: <a class="doc-type-link" href="/reference/citry/#citry-citry">Citry</a>, roots: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Iterable">Iterable</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a>] | None = None, watcher: <a class="doc-type-link" href="/reference/hot-reload/#citry-reload-filewatcher">FileWatcher</a> | None = None, on_reload: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#set">set</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a>], <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#list">list</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]]], None] | None = None) -> <a class="doc-type-link" href="/reference/hot-reload/#citry-reload-watchhandle">WatchHandle</a></code></pre>
</div>

<div class="doc-body">
<p>Watch component files and reload them in place when they change.</p>
<p>For each changed file, the watcher calls
<a href="/reference/citry/#citry-citry-invalidate-file"><code>Citry.invalidate_file()</code></a>, so the next
render reads the new template, JavaScript or CSS. The watcher runs on
a background daemon thread, so <code>watch()</code> returns at once, and the
watcher stops when your program exits. Call <code>wait()</code> on the returned
handle to keep a script running.</p>
<p>A change to a file no component has loaded yet does nothing, because
nothing is cached for it. A new component file or a change to Python
code needs a restart, which your web framework's own reloader does.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><pre><code class="language-python">from citry.reload import watch
from myapp import engine

handle = watch(engine)
try:
    handle.wait()
except KeyboardInterrupt:
    handle.stop()
</code></pre></blockquote>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>engine</code>

<code><a class="doc-type-link" href="/reference/citry/#citry-citry">Citry</a></code>

- The Citry instance whose components to reload.
</li>

<li>
<code>roots</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Iterable">Iterable</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a>] | None</code>

- The directories to watch. Defaults to <code>engine.settings.dirs</code>.
</li>

<li>
<code>watcher</code>

<code><a class="doc-type-link" href="/reference/hot-reload/#citry-reload-filewatcher">FileWatcher</a> | None</code>

- The file-watching backend. Defaults to the best one
installed: <a href="/reference/hot-reload/#citry-reload-watchfileswatcher"><code>WatchfilesWatcher</code></a>,
then <a href="/reference/hot-reload/#citry-reload-watchdogwatcher"><code>WatchdogWatcher</code></a>, then
<a href="/reference/hot-reload/#citry-reload-pollingwatcher"><code>PollingWatcher</code></a>.
</li>

<li>
<code>on_reload</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#set">set</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a>], <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#list">list</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]]], None] | None</code>

- A function Citry calls after each batch of changes, with
the set of changed paths (absolute, each listed once) and the
list of component classes it reset.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="/reference/hot-reload/#citry-reload-watchhandle">WatchHandle</a>: A [`WatchHandle`](/v/1.2.0/reference/hot-reload/#citry-reload-watchhandle). Call its `stop()` to</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>ValueError</code> - When none of the directories to watch exists.
</li>

</ul>



</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.2.0/packages/py/citry/citry/reload.py#L224" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-reload-watchhandle" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>WatchHandle</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>A running watcher, returned by <a href="/reference/hot-reload/#citry-reload-watch"><code>watch()</code></a>.</p>
<p>Call <code>stop()</code> to end it, or <code>wait()</code> to block until it stops. The
<code>citry watch</code> command calls <code>wait()</code>, then <code>stop()</code> when you press
Ctrl-C.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.2.0/packages/py/citry/citry/reload.py#L238" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-reload-watchhandle-running" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>running</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>running: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Whether the watcher thread is still alive.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.2.0/packages/py/citry/citry/reload.py#L242" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-reload-watchhandle-wait" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>wait</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>wait() -> None</code></pre>
</div>

<div class="doc-body">
<p>Block the calling thread until the watcher stops.</p>
<p>Polls with a short timeout so a <code>KeyboardInterrupt</code> on the main thread
is delivered promptly rather than swallowed by an un-timed join.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.2.0/packages/py/citry/citry/reload.py#L252" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-reload-watchhandle-stop" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>stop</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>stop(timeout: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#float">float</a> = _DEFAULT_STOP_TIMEOUT) -> None</code></pre>
</div>

<div class="doc-body">
<p>Ask the watcher to stop and wait up to <code>timeout</code> for its thread.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.2.0/packages/py/citry/citry/reload.py#L54" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-reload-filewatcher" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>FileWatcher</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Protocol">Protocol</a></code></p>


<div class="doc-body">
<p>The interface a file-watching backend implements.</p>
<p>Citry calls <code>run()</code> on a background thread. <code>run()</code> blocks and calls
<code>on_change</code> with the set of changed paths for each batch of changes,
until another thread calls <code>stop()</code>. A backend should group the burst
of events one editor save produces into as few <code>on_change</code> calls as it
can, and must return from <code>run()</code> soon after <code>stop()</code> is called.</p>
<p>Citry ships three backends: <a href="/reference/hot-reload/#citry-reload-watchfileswatcher"><code>WatchfilesWatcher</code></a>,
<a href="/reference/hot-reload/#citry-reload-watchdogwatcher"><code>WatchdogWatcher</code></a> and
<a href="/reference/hot-reload/#citry-reload-pollingwatcher"><code>PollingWatcher</code></a>. To use your own,
pass an object with these two methods as <code>watcher=</code> to
<a href="/reference/hot-reload/#citry-reload-watch"><code>watch()</code></a> or
<a href="/reference/contrib/#citry-contrib-asgi-reload-lifespan"><code>reload_lifespan()</code></a>.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.2.0/packages/py/citry/citry/reload.py#L72" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-reload-filewatcher-run" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>run</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>run(roots: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Sequence">Sequence</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a>], on_change: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#set">set</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a>]], None]) -> None</code></pre>
</div>

<div class="doc-body">
<p>Watch <code>roots</code> and call <code>on_change</code> per batch until stopped.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.2.0/packages/py/citry/citry/reload.py#L76" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-reload-filewatcher-stop" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>stop</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>stop() -> None</code></pre>
</div>

<div class="doc-body">
<p>Ask <code>run</code> to return. Safe to call from another thread.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.2.0/packages/py/citry/citry/reload.py#L81" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-reload-watchfileswatcher" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>WatchfilesWatcher</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Watch files with the <code>watchfiles</code> package, the recommended backend.</p>
<p><code>watchfiles</code> listens to your operating system's file-change events. It
needs the <code>watcher-watchfiles</code> extra
(<code>pip install "citry[watcher-watchfiles]"</code>). Citry imports <code>watchfiles</code>
only when the watcher starts, so you can create this class without the
extra installed.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>force_polling</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a></code>

- Check the directories on a timer instead of using
operating system events, for example on a network drive that
sends no events.
</li>

</ul>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.2.0/packages/py/citry/citry/reload.py#L102" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-reload-watchfileswatcher-run" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>run</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>run(roots: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Sequence">Sequence</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a>], on_change: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#set">set</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a>]], None]) -> None</code></pre>
</div>

<div class="doc-body">
<p>Stream <code>watchfiles</code> change batches into <code>on_change</code>.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.2.0/packages/py/citry/citry/reload.py#L114" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-reload-watchfileswatcher-stop" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>stop</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>stop() -> None</code></pre>
</div>

<div class="doc-body">
<p>Signal the <code>watchfiles</code> loop (it watches <code>self._stop</code>).</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.2.0/packages/py/citry/citry/reload.py#L175" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-reload-watchdogwatcher" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>WatchdogWatcher</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Watch files with the <code>watchdog</code> package.</p>
<p>Use it in a project that already depends on <code>watchdog</code>; otherwise prefer
<a href="/reference/hot-reload/#citry-reload-watchfileswatcher"><code>WatchfilesWatcher</code></a>. It needs the
<code>watcher-watchdog</code> extra (<code>pip install "citry[watcher-watchdog]"</code>).
Citry imports <code>watchdog</code> only when the watcher starts, so you can create
this class without the extra installed.</p>
<p><code>watchdog</code> reports one change at a time, so one save can make Citry
drop the same file's cached work more than once. Dropping it again
costs little.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.2.0/packages/py/citry/citry/reload.py#L193" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-reload-watchdogwatcher-run" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>run</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>run(roots: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Sequence">Sequence</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a>], on_change: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#set">set</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a>]], None]) -> None</code></pre>
</div>

<div class="doc-body">
<p>Drive watchdog filesystem events into <code>on_change</code> until stopped.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.2.0/packages/py/citry/citry/reload.py#L219" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-reload-watchdogwatcher-stop" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>stop</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>stop() -> None</code></pre>
</div>

<div class="doc-body">
<p>Stop the watchdog observer loop.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.2.0/packages/py/citry/citry/reload.py#L119" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-reload-pollingwatcher" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>PollingWatcher</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Watch files by checking their modification times on a timer.</p>
<p>It needs nothing installed, but it is slower than
<a href="/reference/hot-reload/#citry-reload-watchfileswatcher"><code>WatchfilesWatcher</code></a>. Citry uses it when
neither <code>watchfiles</code> nor <code>watchdog</code> is installed.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>interval</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#float">float</a></code>

- The seconds between two checks.
</li>

</ul>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.2.0/packages/py/citry/citry/reload.py#L136" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-reload-pollingwatcher-run" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>run</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>run(roots: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Sequence">Sequence</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a>], on_change: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#set">set</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a>]], None]) -> None</code></pre>
</div>

<div class="doc-body">
<p>Re-scan <code>roots</code> every <code>interval</code> seconds and report mtime changes.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@1.2.0/packages/py/citry/citry/reload.py#L147" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-reload-pollingwatcher-stop" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>stop</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>stop() -> None</code></pre>
</div>

<div class="doc-body">
<p>Break the scan loop after the current wait.</p>





</div>
</div>


</div>

</div>
</div>



