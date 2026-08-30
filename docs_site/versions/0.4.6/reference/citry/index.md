---
title: Citry instance and config
url: https://citry.dev/v/0.4.6/reference/citry/
description: "The Citry instance that scopes components, settings, and caches."
---
# Citry instance and config

The `Citry` instance that scopes components, settings, and caches.




<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L130" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-citry" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>Citry</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Global instance that scopes all component state.</p>
<p>A Citry instance owns:</p>
<ul>
<li>A private component-name registry reached through the engine's methods</li>
<li>Settings (to be expanded as the engine grows)</li>
<li>Transient rendering state</li>
</ul>
<p>All Component classes are assigned to a Citry instance at class
definition time. If no instance is specified, the default instance
is used.</p>
<p>Call :meth:<code>initialize</code> after startup-time registration and before a
server starts request threads. Lazy initialization remains available, but
a thread that encounters lifecycle work owned by another thread receives
<a href="/reference/citry/#citry-citrylifecycleinprogress"><code>CitryLifecycleInProgress</code></a>.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L177" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-settings" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>settings</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L205" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-template-globals" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>template_globals</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>template_globals: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L210" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-mode" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>mode</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>mode: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;production&#x27;, &#x27;development&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L216" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-cache" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>cache</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>cache: <a class="doc-type-link" href="/reference/citry/#citry-citrycache">CitryCache</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L220" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-id-generator" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>id_generator</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>id_generator: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[], <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>] | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L317" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-extensions" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>extensions</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L329" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-render-template" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>render_template</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>render_template(source: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, variables: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None = None, slots: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None = None, template_globals: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None = None, provides: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None = None, foreign_compile_contexts: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Sequence">Sequence</a>[<a class="doc-type-link" href="/reference/extensions/#citry-foreigncompilecontext">ForeignCompileContext</a>] = (), origin: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> = &#x27;&lt;render_template&gt;&#x27;) -> <a class="doc-type-link" href="/reference/rendering/#citry-citryrender">CitryRender</a></code></pre>
</div>

<div class="doc-body">
<p>Render trusted standalone Citry template source through the normal pipeline.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L443" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-engine-id" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>engine_id</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>engine_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Return this engine's opaque process-lifetime identity token.</p>
<p>The value is stable for this <code>Citry</code> instance, including across
<a href="/reference/citry/#citry-citry-clear"><code>clear()</code></a>, and differs for another instance in the
same process. Component-introspection consumers combine it with
<a href="/reference/component/#citry-component-class-id"><code>Component.class_id</code></a> and
<a href="/reference/component/#citry-component-definition-id"><code>Component.definition_id</code></a> when they
need to confirm that retained metadata still describes an exact live
component generation.</p>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>: A non-time-derived token intended only for same-process identity</p>




</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L555" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-atomic-registration" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>atomic_registration</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>atomic_registration() -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Iterator">Iterator</a>[None]</code></pre>
</div>

<div class="doc-body">
<p>Publish a group of component registrations together.</p>
<p>Component classes defined inside the block register normally and fire
the normal class and registration hooks. If the block raises, Citry
restores its component names, class-ID and file indexes, tag rules,
and discovery state to their values at entry. Another thread receives
<a href="/reference/citry/#citry-citrylifecycleinprogress"><code>CitryLifecycleInProgress</code></a> rather
than observing or changing the group before it commits.</p>
<p>This context manager is additive: it publishes new classes and aliases;
<a href="/reference/citry/#citry-citry-unregister"><code>unregister()</code></a> rejects removals inside the
block. Start the block outside other component lifecycle operations;
nested atomic-registration blocks are rejected. Ordinary component
definitions and their hooks remain reentrant inside the block.</p>
<p>Rollback covers the Citry registration and installation indexes listed
above. Rendered-output caches, side effects that extension hooks or
ordinary Python write elsewhere, and registrations made to another
Citry instance are outside the transaction.</p>
<p class="doc-section">Yields</p><ul class="doc-list"><li>None - None. Component factories return their own created classes; the</li><li>None - context manager only owns publication and rollback.</li></ul>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><pre><code class="language-python">with app.atomic_registration():
    class AcmeButton(Component):
        citry = app
</code></pre></blockquote>



<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>CitryLifecycleInProgress</code> - If another thread owns component
lifecycle work for this Citry instance.
</li>

<li>
<code>RuntimeError</code> - If called inside another component lifecycle
operation on the same thread.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L607" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-register-library" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>register_library</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>register_library(library: <a class="doc-type-link" href="/reference/component-libraries/#citry-componentlibrary">ComponentLibrary</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/types.html#types.ModuleType">ModuleType</a>) -> <a class="doc-type-link" href="/reference/component-libraries/#citry-libraryinstallation">LibraryInstallation</a></code></pre>
</div>

<div class="doc-body">
<p>Materialize and publish an engine-neutral component library.</p>
<p>A library package may be passed directly when it exposes its manifest
as <code>__citry_library__</code>. Registration creates a distinct concrete
Component class for every definition and this Citry instance. The
classes and immutable installation record become visible together.</p>
<p>Repeating the same manifest and exact definition generation returns the
existing installation without rerunning component hooks. Clear the
Citry instance before installing a reloaded or changed manifest with
the same library name.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><pre><code class="language-python">import citry_ui
from citry import Citry

app = Citry()
installed = app.register_library(citry_ui)
</code></pre></blockquote>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>library</code>

<code><a class="doc-type-link" href="/reference/component-libraries/#citry-componentlibrary">ComponentLibrary</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/types.html#types.ModuleType">ModuleType</a></code>

- A <a href="/reference/component-libraries/#citry-componentlibrary"><code>ComponentLibrary</code></a> or imported
package exposing one as <code>__citry_library__</code>.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="/reference/component-libraries/#citry-libraryinstallation">LibraryInstallation</a>: The exact active [`LibraryInstallation`](/v/0.4.6/reference/component-libraries/#citry-libraryinstallation).</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>LibraryManifestChanged</code> - If the library name is already associated
with another manifest or definition generation.
</li>

<li>
<code>LibraryInstallationStale</code> - If internal registry mutation damaged an
active installation.
</li>

<li>
<code>ValueError</code> - If a required extension is not installed or a component
identity collides with existing state.
</li>

<li>
<code>AlreadyRegistered</code> - If a registry name is already occupied.
</li>

<li>
<code>CitryLifecycleInProgress</code> - If another thread owns lifecycle work.
</li>

<li>
<code>RuntimeError</code> - If registration is attempted recursively.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L732" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-get-library-installation" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>get_library_installation</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>get_library_installation(name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="/reference/component-libraries/#citry-libraryinstallation">LibraryInstallation</a></code></pre>
</div>

<div class="doc-body">
<p>Return one exact active component-library installation.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>name</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The manifest's case-sensitive library name.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="/reference/component-libraries/#citry-libraryinstallation">LibraryInstallation</a>: The current immutable installation handle.</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>LibraryNotInstalled</code> - If no library with <code>name</code> is active.
</li>

<li>
<code>LibraryInstallationStale</code> - If private registry mutation damaged the
installation record.
</li>

<li>
<code>CitryLifecycleInProgress</code> - If another thread owns lifecycle work.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L897" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-register" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>register</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>register(comp_cls: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>], name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None = None) -> None</code></pre>
</div>

<div class="doc-body">
<p>Register an additional name for a component owned by this instance.</p>
<p>Component classes register automatically when they are defined. This
method supports same-engine aliases and re-registering a class after it
was removed. A class owned by another <code>Citry</code> instance is rejected.</p>
<p>Fires <code>on_component_registered</code> once per call, after the registry
accepts the class.</p>



<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>AlreadyRegistered</code> - If the requested name or class ID belongs to a
different component, or the name is reserved.
</li>

<li>
<code>ValueError</code> - If the component belongs to another Citry instance, is
a retired built-in generation, or the requested name is invalid.
</li>

<li>
<code>CitryLifecycleInProgress</code> - If another thread is changing component
lifecycle state.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L1007" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-unregister" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>unregister</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>unregister(comp_cls_or_name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>] | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> None</code></pre>
</div>

<div class="doc-body">
<p>Unregister one name or all names for a component owned by this instance.</p>
<p>Fires <code>on_component_unregistered</code> once per call, after the registry
removes the class.</p>



<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>NotRegistered</code> - If the requested class or name is not registered.
</li>

<li>
<code>ValueError</code> - If asked to remove a built-in's canonical name or
unregister the built-in class.
</li>

<li>
<code>CitryLifecycleInProgress</code> - If another thread is changing component
lifecycle state.
</li>

<li>
<code>RuntimeError</code> - If called inside <code>atomic_registration()</code> on this
thread; atomic registration is additive.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L1103" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-get" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>get</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>get(name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">
<p>Look up a component by name.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>name</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Registered component name, matched case-insensitively.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]: The registered component class.</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>NotRegistered</code> - If no component has this name after discovery.
</li>

<li>
<code>CitryLifecycleInProgress</code> - If another thread is changing component
lifecycle state.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L1128" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-has" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>has</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>has(name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Check whether a component name is registered.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>name</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Registered component name, matched case-insensitively.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a>: Whether the name is registered after discovery.</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>CitryLifecycleInProgress</code> - If another thread is changing component
lifecycle state.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L1153" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-components" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>components</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>components: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]]</code></pre>
</div>

<div class="doc-body">
<p>All registered components as a name-to-class mapping.</p>



<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>CitryLifecycleInProgress</code> - If another thread is changing component
lifecycle state.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L1170" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-inspect-components" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>inspect_components</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>inspect_components(include_builtins: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a> = False, resolve_assets: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a> = False, include_default_values: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a> = False, include_extensions: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Iterable">Iterable</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>] = ()) -> <a class="doc-type-link" href="/reference/component-introspection/#citry-componentcatalog">ComponentCatalog</a></code></pre>
</div>

<div class="doc-body">
<p>Return an immutable catalog of the currently registered components.</p>
<p>The method completes normal lazy discovery and built-in creation, then
copies the registry once. Schema and asset metadata are built from that
copy after lifecycle coordination is released. Asset inspection never
reads source content or changes render and hot-reload caches.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>include_builtins</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code>

- Include Citry's framework component classes.
</li>

<li>
<code>resolve_assets</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code>

- Check declared asset paths on the filesystem and
report resolved, missing, and searched paths.
</li>

<li>
<code>include_default_values</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code>

- Copy portable literal schema defaults into
field metadata. Default factories are never called.
</li>

<li>
<code>include_extensions</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Iterable">Iterable</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>]</code>

- Installed extensions whose versioned component
metadata inspectors should run. Names are deduplicated and
sorted; no inspector runs unless explicitly requested.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="/reference/component-introspection/#citry-componentcatalog">ComponentCatalog</a>: A canonically ordered [`ComponentCatalog`](/v/0.4.6/reference/component-introspection/#citry-componentcatalog)</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>TypeError</code> - If a boolean option is not a bool or
<code>include_extensions</code> is a string or non-iterable.
</li>

<li>
<code>ComponentIntrospectionError</code> - If a requested extension is missing,
unsupported, fails, or publishes invalid metadata.
</li>

<li>
<code>CitryLifecycleInProgress</code> - If another thread is changing component
lifecycle state.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L1223" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-inspect-component" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>inspect_component</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>inspect_component(component: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>], resolve_assets: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a> = False, include_default_values: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a> = False, include_extensions: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Iterable">Iterable</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>] = ()) -> <a class="doc-type-link" href="/reference/component-introspection/#citry-componentinfo">ComponentInfo</a></code></pre>
</div>

<div class="doc-body">
<p>Inspect one component selected from a copied registry snapshot.</p>
<p>A string is matched case-insensitively as a registered component name.
A class must be owned by this engine and present under at least one
name. Looking up an alias does not change the record's deterministic
primary name.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>component</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code>

- A registered name or exact registered component class.
</li>

<li>
<code>resolve_assets</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code>

- Check declared asset paths on the filesystem.
</li>

<li>
<code>include_default_values</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code>

- Copy portable literal schema defaults.
</li>

<li>
<code>include_extensions</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Iterable">Iterable</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>]</code>

- Installed extensions whose versioned metadata
inspectors should run. Names are deduplicated and sorted.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="/reference/component-introspection/#citry-componentinfo">ComponentInfo</a>: A value-only [`ComponentInfo`](/v/0.4.6/reference/component-introspection/#citry-componentinfo) record.</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>TypeError</code> - If <code>component</code> is neither a string nor a class, a
boolean option is not a bool, or <code>include_extensions</code> is a
string or non-iterable.
</li>

<li>
<code>NotRegistered</code> - If the name or exact class is absent from the copied
registry snapshot.
</li>

<li>
<code>ComponentIntrospectionError</code> - If a requested extension is missing,
unsupported, fails, or publishes invalid metadata.
</li>

<li>
<code>CitryLifecycleInProgress</code> - If another thread is changing component
lifecycle state.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L1291" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-inspect-component-graph" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>inspect_component_graph</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>inspect_component_graph(include_builtins: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a> = False) -> <a class="doc-type-link" href="/reference/component-graph/#citry-componentgraph">ComponentGraph</a></code></pre>
</div>

<div class="doc-body">
<p>Return authored component dependencies from one registry snapshot.</p>
<p>Citry copies the complete name-to-class registry once, then reads each
selected component's effective primary template without rendering or
running template-load transforms. The graph includes direct dependency
and reverse-reference queries plus explicit unresolved targets and
source problems.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><pre><code class="language-python">graph = app.inspect_component_graph()

for dependency in graph.dependencies(&quot;account-page&quot;):
    print(dependency.name)

for dependent in graph.dependents(&quot;avatar&quot;):
    print(dependent.name)
</code></pre></blockquote>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Note</p><p>The graph covers component tags in authored primary templates. It
does not claim to find components composed from Python, inserted by
a transform, or chosen by a dynamic selector.</p></blockquote>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>include_builtins</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code>

- Include Citry's framework component definitions
and references to them.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="/reference/component-graph/#citry-componentgraph">ComponentGraph</a>: A versioned [`ComponentGraph`](/v/0.4.6/reference/component-graph/#citry-componentgraph) containing</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>TypeError</code> - If <code>include_builtins</code> is not a bool.
</li>

<li>
<code>CitryLifecycleInProgress</code> - If another thread is changing component
lifecycle state.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L1354" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-initialize" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>initialize</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>initialize() -> None</code></pre>
</div>

<div class="doc-body">
<p>Prepare component registration state before starting worker threads.</p>
<p>This imports configured component modules when autodiscovery is enabled,
creates Citry's built-in components, and builds the current parse-time
tag rules. Component template, JavaScript, and CSS asset files remain
lazy and are loaded when rendering needs them.</p>
<p>Call this after startup-time component registration and before a server
begins handling requests concurrently. Repeated successful calls are
safe; a later registration invalidates tag rules, and another call
rebuilds them.</p>
<p>Initialization is retryable rather than globally transactional. If a
module import fails, components from earlier successful module imports
may remain registered, while the incomplete work is retried later.</p>


<p class="doc-section">Returns</p>
<p class="doc-returns">None: None.</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>CitryLifecycleInProgress</code> - If another thread is changing component
lifecycle state.
</li>

<li>
<code>RuntimeError</code> - If called recursively from an active lifecycle hook
or initialization on this thread.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L1385" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-template-analysis" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>template_analysis</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>template_analysis() -> <a class="doc-type-link" href="/reference/template-analysis/#citry-templateanalysis">TemplateAnalysis</a></code></pre>
</div>

<div class="doc-body">
<p>Capture the complete component contracts used to analyze templates.</p>
<p>The method completes normal component discovery and built-in
registration under the engine's lifecycle guard. The returned snapshot
keeps normalized registered names and parse-time input and slot rules
together, so tooling cannot observe a partial registry. Call it again
after component registration or reload to capture the new state.</p>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="/reference/template-analysis/#citry-templateanalysis">TemplateAnalysis</a>: An immutable [`TemplateAnalysis`](/v/0.4.6/reference/template-analysis/#citry-templateanalysis) snapshot.</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>CitryLifecycleInProgress</code> - If another thread is changing component
lifecycle state.
</li>

<li>
<code>RuntimeError</code> - If discovery or component initialization fails.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L1415" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-autodiscover" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>autodiscover</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>autodiscover(dirs: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Sequence">Sequence</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a>] | None = None) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>]</code></pre>
</div>

<div class="doc-body">
<p>Import this instance's component modules so their classes register.</p>
<p>With no argument, imports every component module under the instance's
<code>dirs</code> - the same scan the <code>autodiscover</code> setting performs
automatically on first use - and marks that automatic scan done, so it
will not run again. Pass <code>dirs</code> to import an extra set of directories
on demand without affecting the automatic scan.</p>
<p>The directories must be importable: each one (or a parent of it) is on
<code>sys.path</code>/<code>PYTHONPATH</code>, which is how a component file is mapped to
the import name Python uses for it. A directory that holds component
modules but is not importable raises <code>ValueError</code>.</p>
<p>Returns the dotted import paths of the modules that were imported. Safe
to call more than once: an already-imported module has its components
re-registered directly, so a call after <code>clear()</code> rebuilds the
registry and a call that changes nothing is a no-op.</p>
<p>A scan is marked complete only after every module imports successfully.
If one module raises, registrations it made to this <code>Citry</code> instance
during that import are rolled back, and a later call can retry it.
Earlier modules and dependency modules that imported successfully
remain registered. Python side effects and registrations made to
another <code>Citry</code> instance are outside this rollback. Calling
<code>autodiscover()</code> recursively from a component module raises
<code>RuntimeError</code>.</p>



<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>CitryLifecycleInProgress</code> - If another thread is changing component
lifecycle state.
</li>

<li>
<code>RuntimeError</code> - If a component module starts another autodiscovery
scan on the same instance.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L1464" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-urls" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>urls</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>urls: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/web/#citry-urlroute">URLRoute</a>, ...]</code></pre>
</div>

<div class="doc-body">
<p>This instance's HTTP route table (framework-neutral <code>URLRoute</code>s).</p>
<p>The web-integration adapters (<code>citry.contrib.asgi</code> and friends)
mount these into the host application; the routes serve cached
component JS/CSS, the client runtime, and extension endpoints.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L1475" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-commands" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>commands</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>commands: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/extensions/#citry-extensioncommand">ExtensionCommand</a>], ...]]</code></pre>
</div>

<div class="doc-body">
<p>This instance's CLI commands, keyed by extension name.</p>
<p>Each registered extension contributes the commands it declares in
<code>Extension.commands</code>; the <code>citry</code> command-line tool reaches one as
<code>citry ext run &lt;extension name&gt; &lt;command name&gt;</code>. See
<code>ExtensionManager.commands</code> for ordering and the uniqueness guarantee.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L1487" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-mounted-prefix" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>mounted_prefix</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>mounted_prefix: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Where this instance's routes are mounted (e.g. <code>"/citry"</code>), or <code>None</code> when nothing is mounted.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L1491" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-set-mounted-prefix" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>set_mounted_prefix</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>set_mounted_prefix(prefix: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> None</code></pre>
</div>

<div class="doc-body">
<p>Record where this instance's routes are mounted in the host app.</p>
<p>The adapters' <code>mount()</code> call this; call it directly only in a
process that builds URLs without mounting the routes itself (for
example a worker that renders fragments served by another process).
<code>prefix</code> must start with <code>/</code>; a trailing <code>/</code> is dropped.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L1505" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-build-url" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>build_url</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>build_url(path: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>An absolute URL path for one of this instance's routes.</p>
<p><code>path</code> is the route's full path (no leading slash), e.g.
<code>"cache/Table_a1b2c3.js"</code>. Raises <code>RuntimeError</code> when no web
integration is mounted, since the URL would point nowhere.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L1522" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-get-component-by-class-id" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>get_component_by_class_id</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>get_component_by_class_id(class_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">
<p>Look up a registered component class by its <code>class_id</code>.</p>
<p><code>class_id</code> is the stable identifier (<code>MyComp.class_id</code>) used in
cache keys and script URLs. Raises <code>KeyError</code> when no registered
class has that id.</p>



<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>KeyError</code> - If no registered component has this class ID.
</li>

<li>
<code>CitryLifecycleInProgress</code> - If another thread is changing component
lifecycle state.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L1688" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-get-components-for-file" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>get_components_for_file</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>get_components_for_file(path: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]]</code></pre>
</div>

<div class="doc-body">
<p>The component classes whose assets resolved to <code>path</code>.</p>
<p>Most callers want :meth:<code>invalidate_file</code>, which both finds these
classes and resets them. This lower-level lookup is for a caller that
wants the classes without resetting (a custom hot-reload handler, a
test). Dead weakrefs are pruned on read.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L1713" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-invalidate-file" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>invalidate_file</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>invalidate_file(path: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]]</code></pre>
</div>

<div class="doc-body">
<p>Drop cached template/JS/CSS for every component that loaded an asset
from <code>path</code>, so the next render re-reads it from disk.</p>
<p>Returns the component classes it reset. An empty list means the file
backs no loaded component, which a hot-reload handler can read as "not
mine" and, if it wants, fall through to a full restart. This is the
host-neutral call a file watcher drives; see the watcher in
:mod:<code>citry.reload</code> and <code>docs/design/hot_reload.md</code>.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L1733" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-invalidate-all" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>invalidate_all</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>invalidate_all() -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]]</code></pre>
</div>

<div class="doc-body">
<p>Reset cached template/JS/CSS for every component that has loaded a file,
so the next render re-reads them all from disk. Returns the reset classes
(in first-seen order).</p>
<p>For when a change cannot be mapped to a single path: a bulk edit, a
branch switch, or a custom watcher reporting an event it cannot resolve
to one file. Unlike :meth:<code>clear</code>, this leaves the registry and
autodiscovery untouched.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py#L1759" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citry-clear" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>clear</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>clear() -> None</code></pre>
</div>

<div class="doc-body">
<p>Clear registrations and caches, and re-arm autodiscovery.</p>



<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>CitryLifecycleInProgress</code> - If another thread is changing component
lifecycle state.
</li>

<li>
<code>RuntimeError</code> - If called from another lifecycle operation on this
thread.
</li>

</ul>



</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/citry.py" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-citry-2" class="doc-heading">
<span class="doc-symbol doc-symbol-module"></span>
<span class="doc-object-name">
<code>citry</code>
</span>
<span class="doc-kind">module</span>
</h2>


<div class="doc-body">
<p>The Citry global instance - scopes all component state.</p>
<p>A Citry instance owns a component registry, settings, and transient
rendering state. Every Component subclass is assigned to a Citry instance,
either by declaring <code>citry = my_citry</code> in its class body or by using the
default instance.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><p>Using the default instance (most common)::</p>
<pre><code>from citry import Component

class MyTable(Component):
    template = "&lt;table&gt;...&lt;/table&gt;"
</code></pre>
<p>Using a custom instance::</p>
<pre><code>from citry import Citry, Component

my_citry = Citry()

class MyTable(Component):
    citry = my_citry
    template = "&lt;table&gt;...&lt;/table&gt;"
</code></pre>
<p>Isolated instances for testing::</p>
<pre><code>def test_my_component():
    test_citry = Citry()
    # Components registered here don't leak to other tests
    class MyTable(Component):
        citry = test_citry
        template = "..."
</code></pre></blockquote>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_registry.py#L42" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-alreadyregistered" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>AlreadyRegistered</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/library/exceptions.html#Exception">Exception</a></code></p>


<div class="doc-body">
<p>Raised when registering a component under a name that is already taken.</p>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_registry.py#L46" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-notregistered" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>NotRegistered</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/library/exceptions.html#Exception">Exception</a></code></p>


<div class="doc-body">
<p>Raised when looking up a component name that is not registered.</p>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/lifecycle.py#L14" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-citrylifecycleinprogress" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>CitryLifecycleInProgress</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/library/exceptions.html#RuntimeError">RuntimeError</a></code></p>


<div class="doc-body">
<p>Raised when another thread is changing Citry's component lifecycle state.</p>
<p>Component discovery, registration, built-in creation, clearing, and
tag-rule construction publish related state together. A competing thread
receives this error rather than observing an incomplete registry or waiting
in a way that can deadlock with Python's module-import locks.</p>
<p>Finish <a href="/reference/citry/#citry-citry-initialize"><code>Citry.initialize()</code></a> before starting
request threads to avoid this error during normal server operation. An
operation that encounters it may also be retried after the active lifecycle
operation finishes.</p>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/settings.py#L213" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-citrysettings" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>CitrySettings</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Immutable settings for a <code>Citry</code> instance.</p>
<p>Every security mode is enforced during serialization. The defaults
preserve established output; restrictive JavaScript modes inventory,
omit, or reject client behavior without changing render-cache data.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>extensions</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Sequence">Sequence</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/extensions/#citry-extension">Extension</a>] | <a class="doc-type-link" href="/reference/extensions/#citry-extension">Extension</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>]</code>

- The extensions to install on the instance. Each entry is
an <code>Extension</code> subclass, a ready-made instance, or an import
string like <code>"myapp.extensions.MyExtension"</code>. The set is fixed
once the instance is constructed.
</li>

<li>
<code>extensions_defaults</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]]</code>

- Default config values for extensions, keyed by
extension name, e.g. <code>{"events": {"_csrf": True}}</code>. When an
extension reads a config field for a component, the component's
own nested config class wins, a value given here fills in next,
and the extension's built-in default comes last.
</li>

<li>
<code>dirs</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a>, ...]</code>

- Directories searched when resolving a component's asset files
(<code>template_file</code>, <code>js_file</code>, <code>css_file</code>, and <code>Dependencies</code>
entries), after the directory of the component's own <code>.py</code> file.
Entries are converted to <code>Path</code> and must be absolute; this is
validated at construction (a relative entry raises <code>ValueError</code>).
</li>

<li>
<code>cache</code>

<code><a class="doc-type-link" href="/reference/citry/#citry-citrycache">CitryCache</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- Where citry stores what it caches: a
<a href="/reference/citry/#citry-citrycache"><code>CitryCache</code></a> object or an import string
like <code>"myapp.caching.MyCache"</code>. <code>None</code> gives the instance its
own in-memory cache. The live backend built from this setting is
<code>Citry.cache</code>.
</li>

<li>
<code>sandbox_expressions</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code>

- Whether template expressions (<code>{{ ... }}</code> and
dynamic <code>c-*</code> attributes) are evaluated in the security sandbox.
On by default. Turning it off evaluates expressions as plain Python,
which is faster but removes security guardrails.
Only do so when every template comes from a trusted source.
</li>

<li>
<code>autodiscover</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code>

- Whether to import the component modules under <code>dirs</code> the
first time a component is looked up, so their classes register
themselves without being imported by hand. On by default; when no
<code>dirs</code> are set there is nothing to scan, so the default instance
does nothing. The directories must be importable (on
<code>sys.path</code>/<code>PYTHONPATH</code>). See <code>Citry.autodiscover</code> and
<code>citry.autodiscovery</code>.
</li>

<li>
<code>mode</code>

<code>Mode</code>

- The build environment, <code>"production"</code> (the default) or
<code>"development"</code>. It is the single source of truth for whether the
engine includes developer-only output: in <code>"development"</code> the
built-in <code>debug</code> extension is auto-registered (visual component
boundaries) and the client ownership graph carries source
provenance. An unrecognized value raises <code>ValueError</code> at
construction. See <code>docs/design/dev_prod_mode.md</code>.
</li>

<li>
<code>template_globals</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code>

- Variables exposed to every component's template
without being returned from each <code>template_data()</code>. They are
merged into every component's template variables on render, so a
template can reference one directly (<code>{{ site_name }}</code>). A
component's own <code>template_data</code> wins when it returns a key of the
same name, so globals act as defaults. The value given here is the
starting set; the live, editable copy is <code>Citry.template_globals</code>,
which is how you add or change a global after the instance exists
(including the default instance, created at import before your code
runs).
</li>

<li>
<code>lint</code>

<code><a class="doc-type-link" href="/reference/citry/#citry-lintsettings">LintSettings</a></code>

- Template lint severities and analysis-only variables. Runtime
globals are discovered from <code>Citry.template_globals</code> and do not
need to be repeated here.
</li>

<li>
<code>security_csp</code>

<code><a class="doc-type-link" href="/reference/citry/#citry-securitycspmode">SecurityCspMode</a></code>

- CSP compatibility policy for Citry-managed output.
<code>"off"</code> preserves current behavior, <code>"warn"</code> reports
incompatibilities without changing output, and <code>"strict"</code>
enforces Citry's strict-CSP contract.
</li>

<li>
<code>security_javascript</code>

<code><a class="doc-type-link" href="/reference/citry/#citry-securityjavascriptmode">SecurityJavascriptMode</a></code>

- JavaScript delivery policy. <code>"allow"</code> keeps
current behavior, <code>"warn"</code> inventories client requirements,
<code>"omit"</code> leaves Citry-managed JavaScript out, and <code>"forbid"</code>
rejects rendered subtrees that require executable client behavior.
</li>

<li>
<code>security_script_integrity</code>

<code><a class="doc-type-link" href="/reference/citry/#citry-securityscriptintegritymode">SecurityScriptIntegrityMode</a></code>

- Script integrity policy. <code>"off"</code> does
not compute security digests; <code>"citry"</code> collects SHA-384
metadata for structured scripts whose bytes Citry can prove.
</li>

<li>
<code>id_generator</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[], <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>] | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- A function returning the per-render id stamped on each
component instance (<code>component.id</code>, which drives the
<code>data-cid-&lt;id&gt;</code> markers that scope a component's CSS and JS on the
page). Given as a callable or a <code>"path.to.func"</code> import string;
passing a class also works: it is called once, and the resulting
object is used as the generator (handy when the generator keeps
state, like a counter). <code>None</code> uses the built-in generator. Override
it for stable ids in snapshot tests. The generator must return ids
that are unique among the components on one page and contain only
lowercase ASCII letters, digits, hyphens, and underscores. The
lowercase rule is required because the id is embedded in an HTML
attribute name. This does not touch <code>class_id</code>, which stays a
stable hash of the component's import path.
</li>

<li>
<code>secret</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>] | None</code>

- The signing secret for values citry hands to the browser and
must recognize when they come back, such as the state the Events
extension round-trips on each event call. A single string is the
common form. A list means key rotation: the first entry signs new
values, and a value signed by any entry still verifies, so
already-issued values stay valid while a new key rolls out. A bare
string is stored as a one-element list. <code>None</code> (the default)
means no secret is set. Django projects can reuse their existing
key by passing <code>citry.contrib.django.secret()</code>.
</li>

<li>
<code>event_result_resolvers</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Sequence">Sequence</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code>

- Result resolvers for the Events extension.
When an event handler returns a value, citry converts it into the
actions sent back to the browser (the instructions the client
runtime applies: re-render this component, redirect, and so on).
A resolver adds support for your own return types: it is given the
handler's return value and either converts it into those actions
or declines, letting the next resolver try. Resolvers run in
order, after the built-in conversions; the first one to convert
the value wins.
</li>

<li>
<code>event_payload_codecs</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Sequence">Sequence</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code>

- Payload codecs for the Events extension's HTTP
endpoints. A codec reads one request format (identified by its
content type) into the event call the extension expects, so
clients are not limited to the built-in JSON, form, and query
formats. Codecs given here are tried before the built-in ones, in
order.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/settings.py#L325" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrysettings-extensions" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>extensions</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>extensions: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Sequence">Sequence</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/extensions/#citry-extension">Extension</a>] | <a class="doc-type-link" href="/reference/extensions/#citry-extension">Extension</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/settings.py#L326" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrysettings-extensions-defaults" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>extensions_defaults</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>extensions_defaults: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/settings.py#L327" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrysettings-dirs" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>dirs</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>dirs: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/settings.py#L328" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrysettings-cache" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>cache</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>cache: <a class="doc-type-link" href="/reference/citry/#citry-citrycache">CitryCache</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/settings.py#L329" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrysettings-sandbox-expressions" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>sandbox_expressions</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>sandbox_expressions: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/settings.py#L330" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrysettings-autodiscover" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>autodiscover</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>autodiscover: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/settings.py#L331" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrysettings-mode" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>mode</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>mode: Mode</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/settings.py#L332" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrysettings-template-globals" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>template_globals</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>template_globals: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/settings.py#L333" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrysettings-lint" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>lint</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>lint: <a class="doc-type-link" href="/reference/citry/#citry-lintsettings">LintSettings</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/settings.py#L335" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrysettings-id-generator" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>id_generator</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>id_generator: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[], <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>] | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/settings.py#L336" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrysettings-secret" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>secret</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>secret: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>] | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/settings.py#L337" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrysettings-event-result-resolvers" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>event_result_resolvers</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>event_result_resolvers: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Sequence">Sequence</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/settings.py#L338" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrysettings-event-payload-codecs" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>event_payload_codecs</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>event_payload_codecs: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Sequence">Sequence</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/settings.py#L339" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrysettings-security-csp" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>security_csp</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>security_csp: <a class="doc-type-link" href="/reference/citry/#citry-securitycspmode">SecurityCspMode</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/settings.py#L340" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrysettings-security-javascript" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>security_javascript</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>security_javascript: <a class="doc-type-link" href="/reference/citry/#citry-securityjavascriptmode">SecurityJavascriptMode</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/settings.py#L341" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrysettings-security-script-integrity" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>security_script_integrity</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>security_script_integrity: <a class="doc-type-link" href="/reference/citry/#citry-securityscriptintegritymode">SecurityScriptIntegrityMode</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/settings.py#L96" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-lintsettings" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>LintSettings</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Configure Citry's template and browser lint rules and analysis-only variables.</p>



<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>TypeError</code> - If a variable or global collection is not a mapping.
</li>

<li>
<code>ValueError</code> - If a severity or variable name is invalid.
</li>

</ul>


<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>rule_unknown_template_variable</code>

<code><a class="doc-type-link" href="/reference/citry/#citry-lintseverity">LintSeverity</a></code>

- Severity for a free template root that
is absent from the proven component namespace. The default is
<code>"error"</code>. A schema that explicitly allows extra fields caps
this rule at <code>"warning"</code>.
</li>

<li>
<code>template_variables</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>]</code>

- Extra variables known to template analysis but not
injected at runtime. Values are annotations. Use
<code>Annotated[T, "description"]</code> to attach concise documentation.
</li>

<li>
<code>rule_unknown_alpine_variable</code>

<code><a class="doc-type-link" href="/reference/citry/#citry-lintseverity">LintSeverity</a></code>

- Severity for a free Alpine-expression
root absent from the component's proven browser scope. The default
is <code>"error"</code>.
</li>

<li>
<code>alpine_variables</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>]</code>

- Extra variables or custom Alpine magics known only to
browser analysis. Values use the same annotation convention as
<code>template_variables</code>.
</li>

<li>
<code>rule_unknown_component_js_variable</code>

<code><a class="doc-type-link" href="/reference/citry/#citry-lintseverity">LintSeverity</a></code>

- Severity for a free variable used
inside a <code>$component</code> initializer. The default is <code>"error"</code>.
</li>

<li>
<code>component_js_globals</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>]</code>

- Extra globals available to component JavaScript
analysis. Values use the same annotation convention as
<code>template_variables</code>.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/settings.py#L127" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-lintsettings-rule-unknown-template-variable" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>rule_unknown_template_variable</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>rule_unknown_template_variable: <a class="doc-type-link" href="/reference/citry/#citry-lintseverity">LintSeverity</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/settings.py#L128" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-lintsettings-rule-i18n-missing-param-type" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>rule_i18n_missing_param_type</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>rule_i18n_missing_param_type: <a class="doc-type-link" href="/reference/citry/#citry-lintseverity">LintSeverity</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/settings.py#L129" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-lintsettings-template-variables" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>template_variables</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>template_variables: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/settings.py#L130" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-lintsettings-rule-unknown-alpine-variable" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>rule_unknown_alpine_variable</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>rule_unknown_alpine_variable: <a class="doc-type-link" href="/reference/citry/#citry-lintseverity">LintSeverity</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/settings.py#L131" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-lintsettings-alpine-variables" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>alpine_variables</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>alpine_variables: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/settings.py#L132" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-lintsettings-rule-unknown-component-js-variable" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>rule_unknown_component_js_variable</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>rule_unknown_component_js_variable: <a class="doc-type-link" href="/reference/citry/#citry-lintseverity">LintSeverity</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/settings.py#L133" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-lintsettings-component-js-globals" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_js_globals</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component_js_globals: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/settings.py#L31" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-lintseverity" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>LintSeverity</code>
</span>
<span class="doc-kind">attribute</span>
</h2>


<div class="doc-body">






</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/settings.py#L33" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-securitycspmode" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>SecurityCspMode</code>
</span>
<span class="doc-kind">attribute</span>
</h2>


<div class="doc-body">






</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/settings.py#L35" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-securityjavascriptmode" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>SecurityJavascriptMode</code>
</span>
<span class="doc-kind">attribute</span>
</h2>


<div class="doc-body">






</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/settings.py#L37" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-securityscriptintegritymode" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>SecurityScriptIntegrityMode</code>
</span>
<span class="doc-kind">attribute</span>
</h2>


<div class="doc-body">






</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/cache.py#L50" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-citrycache" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>CitryCache</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Protocol">Protocol</a></code></p>


<div class="doc-body">
<p>The cache backend interface.</p>
<p>Implement these four methods to plug in any store (Redis, diskcache,
Django's cache framework, ...). Keys and values are strings.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/cache.py#L59" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrycache-get" class="doc-heading">
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
<p>Return the value for <code>key</code>, or <code>None</code> when absent or expired.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/cache.py#L63" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrycache-set" class="doc-heading">
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
<p>Store <code>value</code> under <code>key</code>. <code>ttl</code> is seconds until expiry; <code>None</code> means keep forever.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/cache.py#L67" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrycache-delete" class="doc-heading">
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
<p>Remove <code>key</code> if present (no error when absent).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/cache.py#L71" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-citrycache-has" class="doc-heading">
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
<p>Whether <code>key</code> is present (and not expired).</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/cache.py#L76" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-inmemorycache" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>InMemoryCache</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>The default cache backend: a thread-safe in-process LRU store.</p>
<p>Unbounded by default. Pass <code>max_entries</code> to cap the size; when full,
the entry that was read or written longest ago is dropped to make room.</p>
<p>Single-process only: each instance is its own store. For multi-worker
deployments use a shared backend instead (see the module docstring).</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/cache.py#L98" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-inmemorycache-get" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/cache.py#L110" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-inmemorycache-set" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/cache.py#L131" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-inmemorycache-delete" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/cache.py#L135" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-inmemorycache-has" class="doc-heading">
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



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/cache.py#L138" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-inmemorycache-clear" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>clear</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>clear() -> None</code></pre>
</div>

<div class="doc-body">
<p>Drop all entries. Called by <code>Citry.clear()</code>.</p>





</div>
</div>


</div>

</div>
</div>



