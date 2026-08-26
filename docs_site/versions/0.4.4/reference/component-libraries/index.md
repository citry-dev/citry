---
title: Component libraries
url: https://citry.dev/v/0.4.4/reference/component-libraries/
description: "Engine-neutral component definitions, explicit manifests, and per-Citry installations."
---
# Component libraries

Engine-neutral component definitions, explicit manifests, and per-Citry installations.




<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/library_component.py#L360" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-componentlibrary" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ComponentLibrary</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Declare one ordered, engine-neutral collection of library components.</p>
<p>Construct the manifest after all class decorators have completed. A valid
manifest seals its definitions against later class-attribute mutation.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>name</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Stable lowercase package identity inside one Citry instance.
</li>

<li>
<code>components</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Sequence">Sequence</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component-libraries/#citry-librarycomponent">LibraryComponent</a>]]</code>

- Definitions in their deterministic registration order.
</li>

<li>
<code>required_extensions</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Sequence">Sequence</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>]</code>

- Exact extension names required before any class
is materialized.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/library_component.py#L376" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentlibrary-name" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>name</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/library_component.py#L377" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentlibrary-components" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>components</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>components: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Sequence">Sequence</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component-libraries/#citry-librarycomponent">LibraryComponent</a>]]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/library_component.py#L378" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentlibrary-required-extensions" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>required_extensions</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>required_extensions: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Sequence">Sequence</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/library_component.py#L253" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-librarycomponent" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>LibraryComponent</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Define a component once for materialization into multiple Citry instances.</p>
<p>A subclass has the same authored surface as <a href="/reference/component/#citry-component"><code>Component</code></a>:
templates, methods, nested schemas, extension declarations, and assets all
live on the class. Defining it has no registry side effects. Calling it
returns a <a href="/reference/component-libraries/#citry-librarycomponentinvocation"><code>LibraryComponentInvocation</code></a>
that resolves through the Citry instance active at render time.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/library_component.py#L265" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-librarycomponent-pure" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>pure</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>pure: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/library_component.py#L266" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-librarycomponent-name" class="doc-heading">
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
<p>Optional explicit registry name, with the same behavior as <code>Component.name</code>.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/library_component.py#L270" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-librarycomponentinvocation" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>LibraryComponentInvocation</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Remember one engine-neutral component call until rendering selects Citry.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>definition</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component-libraries/#citry-librarycomponent">LibraryComponent</a>]</code>

- The exact inert definition object that was called.
</li>

<li>
<code>kwargs</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code>

- A read-only copy of the component keyword arguments.
</li>

<li>
<code>slots</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code>

- A read-only copy of the reserved slot-fill mapping.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/library_component.py#L282" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-librarycomponentinvocation-definition" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>definition</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>definition: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component-libraries/#citry-librarycomponent">LibraryComponent</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/library_component.py#L283" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-librarycomponentinvocation-kwargs" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>kwargs</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>kwargs: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/library_component.py#L284" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-librarycomponentinvocation-slots" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>slots</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>slots: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/library_component.py#L287" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-librarycomponentinvocation-identity" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>identity</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>identity: LibraryComponentIdentity</code></pre>
</div>

<div class="doc-body">
<p>Return the definition's logical source identity for diagnostics.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/library_component.py#L295" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-librarycomponentinvocation-resolve" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>resolve</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>resolve(citry: <a class="doc-type-link" href="/reference/citry/#citry-citry">Citry</a>) -> <a class="doc-type-link" href="/reference/rendering/#citry-citryelement">CitryElement</a></code></pre>
</div>

<div class="doc-body">
<p>Resolve this invocation to a concrete component element.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>citry</code>

<code><a class="doc-type-link" href="/reference/citry/#citry-citry">Citry</a></code>

- The Citry instance whose installed concrete class should be
used.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="/reference/rendering/#citry-citryelement">CitryElement</a>: A normal [`CitryElement`](/v/0.4.4/reference/rendering/#citry-citryelement) associated with the</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>TypeError</code> - If <code>citry</code> is not a Citry instance.
</li>

<li>
<code>LibraryNotInstalled</code> - If no active installation contains this
exact definition generation.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/library_component.py#L322" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-librarycomponentinvocation-render" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>render</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>render(citry: <a class="doc-type-link" href="/reference/citry/#citry-citry">Citry</a> | None = None, template_globals: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None = None, provides: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None = None) -> <a class="doc-type-link" href="/reference/rendering/#citry-citryrender">CitryRender</a></code></pre>
</div>

<div class="doc-body">
<p>Render this invocation through an explicit Citry instance.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>citry</code>

<code><a class="doc-type-link" href="/reference/citry/#citry-citry">Citry</a> | None</code>

- The instance with the component's library installed.
</li>

<li>
<code>template_globals</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None</code>

- Values added to this render's template globals.
</li>

<li>
<code>provides</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None</code>

- Values the root and its rendered descendants may read
with <code>inject()</code>.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="/reference/rendering/#citry-citryrender">CitryRender</a>: The resulting deferred render tree.</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>LibraryComponentContextError</code> - If <code>citry</code> is omitted. Contextual
resolution is supplied automatically only when the invocation
appears inside another component tree.
</li>

</ul>



</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/library_component.py#L476" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-libraryinstallation" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>LibraryInstallation</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>An immutable handle to one committed generation installed into Citry.</p>
<p>Retaining this handle does not make it active after
<a href="/reference/citry/#citry-citry-clear"><code>Citry.clear()</code></a>. Component access validates the exact
active generation before returning a class.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>library</code>

<code><a class="doc-type-link" href="/reference/component-libraries/#citry-componentlibrary">ComponentLibrary</a></code>

- The manifest used for this generation.
</li>

<li>
<code>engine_id</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The receiving Citry instance's stable runtime identity.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/library_component.py#L491" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-libraryinstallation-library" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>library</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>library: <a class="doc-type-link" href="/reference/component-libraries/#citry-componentlibrary">ComponentLibrary</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/library_component.py#L492" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-libraryinstallation-engine-id" class="doc-heading">
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






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/library_component.py#L497" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-libraryinstallation-is-active" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>is_active</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>is_active: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Return whether this is still the Citry instance's exact active record.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/library_component.py#L503" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-libraryinstallation-classes" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>classes</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>classes: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>], ...]</code></pre>
</div>

<div class="doc-body">
<p>Return concrete component classes in manifest order if this record is active.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/library_component.py#L510" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-libraryinstallation-definitions" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>definitions</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>definitions: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component-libraries/#citry-librarycomponent">LibraryComponent</a>], ...]</code></pre>
</div>

<div class="doc-body">
<p>Return the engine-neutral definitions in manifest order.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/library_component.py#L514" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-libraryinstallation-component" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>component</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component(definition: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component-libraries/#citry-librarycomponent">LibraryComponent</a>]) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">
<p>Return the installed concrete class for an exact definition generation.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>definition</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component-libraries/#citry-librarycomponent">LibraryComponent</a>]</code>

- One exact definition object from this manifest.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]: The concrete Component class associated with this installation.</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>LibraryInstallationStale</code> - If the Citry instance was cleared or a
newer installation generation is active.
</li>

<li>
<code>KeyError</code> - If the definition is outside this library.
</li>

</ul>



</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_like.py#L21" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-componentlike" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ComponentLike</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Protocol">Protocol</a></code></p>


<div class="doc-body">
<p>A value that composes a component for the Citry instance rendering it.</p>
<p>Implement this structural protocol when a third-party object should work
in template expressions or slot values without itself being a
<a href="/reference/component/#citry-component"><code>Component</code></a>. Citry resolves the object once at the
render site and verifies that the returned element belongs to the exact
active instance.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><p>::</p>
<pre><code>class NoticeValue:
    def __citry_element__(self, citry, /):
        Notice = citry.get("Notice")
        return Notice(message="Saved")
</code></pre></blockquote>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/library_component.py#L121" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-librarycomponentcontexterror" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>LibraryComponentContextError</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/library/exceptions.html#RuntimeError">RuntimeError</a></code></p>


<div class="doc-body">
<p>Report that a library invocation has no Citry instance to resolve through.</p>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/library_component.py#L129" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-libraryinstallationstale" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>LibraryInstallationStale</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/library/exceptions.html#RuntimeError">RuntimeError</a></code></p>


<div class="doc-body">
<p>Report that a retained installation is not the Citry instance's active generation.</p>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/library_component.py#L133" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-librarymanifestchanged" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>LibraryManifestChanged</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/library/exceptions.html#RuntimeError">RuntimeError</a></code></p>


<div class="doc-body">
<p>Report an incompatible manifest for an already installed library name.</p>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/library_component.py#L125" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-librarynotinstalled" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>LibraryNotInstalled</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/library/exceptions.html#RuntimeError">RuntimeError</a></code></p>


<div class="doc-body">
<p>Report that no active library installation can satisfy an invocation.</p>





</div>
</div>



