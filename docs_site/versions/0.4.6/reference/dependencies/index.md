---
title: Dependencies
url: https://citry.dev/v/0.4.6/reference/dependencies/
description: "The JS/CSS dependency types collected and placed at serialize time, and the built-in citry.ext.dependencies extension that owns them."
---
# Dependencies

The JS/CSS dependency types collected and placed at serialize time, and the built-in `citry.ext.dependencies` extension that owns them.




<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/extension.py#L140" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-dependenciesconfig" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>DependenciesConfig</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/extensions/#citry-extensionconfig">ExtensionConfig</a></code></p>


<div class="doc-body">
<p>Typed runtime view of one component's <code>Dependencies</code> declaration.</p>
<p>Citry creates this value from the component's nested <code>Dependencies</code>
class. Read it through <code>component.dependencies</code> while the component is
rendering. Use <code>Component.get_dependencies()</code> when you need the resolved,
inherited asset list.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>js</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code>

- JavaScript dependency declarations.
</li>

<li>
<code>css</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code>

- CSS dependency declarations.
</li>

<li>
<code>extend</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]]</code>

- Whether to inherit dependencies, or which component classes to
inherit them from.
</li>

<li>
<code>local_files</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Whether local dependency files are inlined or served from
Citry's asset routes.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/extension.py#L159" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-dependenciesconfig-js" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>js</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>js: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/extension.py#L160" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-dependenciesconfig-css" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>css</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>css: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/extension.py#L161" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-dependenciesconfig-extend" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>extend</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>extend: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/extension.py#L162" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-dependenciesconfig-local-files" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>local_files</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>local_files: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/extension.py#L61" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-dependencies-citrydependencies" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>CitryDependencies</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>A component's merged secondary assets (from the nested <code>Dependencies</code>
classes).</p>
<p>Holds resolved entries:</p>
<ul>
<li>a local file (declared with <code>PathLike</code> or a resolvable string) - resolved to <code>Path</code></li>
<li>URLs (plain strings) - unchanged</li>
<li><code>Script</code>/<code>Style</code> objects - unchanged</li>
<li>Pre-rendered tags (<code>__html__</code>) - unchanged</li>
</ul>
<p>The entry's type is what tells the emission step what
to do with it (inline the file content, emit a <code>src</code>/<code>href</code> tag, or
output the tag verbatim; see <code>emission.py</code>).</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>js</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>, ...]</code>

- JS entries, base classes' entries first, then the class's own,
de-duplicated.
</li>

<li>
<code>css</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>, ...]]</code>

- CSS entries per media type (<code>"all"</code>, <code>"print"</code>, ...), same
ordering per list.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/extension.py#L86" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-citrydependencies-js" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>js</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>js: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/extension.py#L87" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-citrydependencies-css" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>css</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>css: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>, ...]]</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/types.py#L117" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-dependencies-dependency" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>Dependency</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Shared base of :class:<code>Script</code> and :class:<code>Style</code>.</p>
<p>Holds either inline <code>content</code> or a <code>url</code>, never both; rendering
raises when neither or both are set.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/types.py#L126" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-dependency-content" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>content</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>content: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Text inside the <code>&lt;script&gt;</code> or <code>&lt;style&gt;</code> tag. <code>None</code> for
url-based dependencies.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/types.py#L129" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-dependency-url" class="doc-heading">
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
<p>If set, renders as <code>&lt;script src="..."&gt;</code> /
<code>&lt;link rel="stylesheet" href="..."&gt;</code> instead of an inline tag.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/types.py#L132" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-dependency-attrs" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>attrs</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>attrs: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a>]</code></pre>
</div>

<div class="doc-body">
<p>Extra HTML attributes (<code>True</code> renders a bare boolean attribute).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/types.py#L134" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-dependency-kind" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>kind</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>kind: DependencyKind</code></pre>
</div>

<div class="doc-body">
<p>What this dependency is for; see :data:<code>DependencyKind</code>.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/types.py#L136" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-dependency-origin-class-id" class="doc-heading">
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
<p><code>class_id</code> of the component class this dependency came from, when
known. Used in error messages and for per-component hooks.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/types.py#L144" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-dependency-render" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>render</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>render() -> <a class="doc-type-link" href="/reference/rendering/#citry-markup">Markup</a></code></pre>
</div>

<div class="doc-body">
<p>Render as an HTML tag string.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/types.py#L157" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-dependency-render-json" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>render_json</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>render_json() -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a>]]</code></pre>
</div>

<div class="doc-body">
<p>Render as a JSON-ready dict with <code>tag</code>, <code>attrs</code>, and <code>content</code>.</p>
<p>This is the shape the client-side manager consumes when it constructs
the element in the browser.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/types.py#L49" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-dependencies-dependencyrecord" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>DependencyRecord</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a></code></p>


<div class="doc-body">
<p>One "this component instance rendered" note, collected during a render.</p>
<p>The dependencies extension appends one of these to the render-scoped
<code>CitryContext.extra</code> per component render, and the notes bubble up to
the root as nested renders are consumed. At serialize time the collected
records are resolved into the actual <code>Script</code>/<code>Style</code> tags. The exact
class is retained until serialization so hot replacement cannot mix a
rendered old body with a new class's assets; heavy content lives in the
cache.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/types.py#L62" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-dependencyrecord-class-id" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>class_id</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>class_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p><code>Component.class_id</code> of the rendered component's class.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/types.py#L64" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-dependencyrecord-component-id" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_id</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>The render id of the component instance (<code>component.id</code>).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/types.py#L66" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-dependencyrecord-js-vars-hash" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>js_vars_hash</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>js_vars_hash: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Hash of the instance's <code>js_data()</code> result, or <code>None</code> when it has none.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/types.py#L68" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-dependencyrecord-css-vars-hash" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>css_vars_hash</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>css_vars_hash: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Hash of the instance's <code>css_data()</code> result, or <code>None</code> when it has none.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/types.py#L70" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-dependencyrecord-component-class" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_class</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>] | None</code></pre>
</div>

<div class="doc-body">
<p>Exact class version that produced the record, retained for delayed serialization.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/types.py#L208" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-dependencies-script" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>Script</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/dependencies/#citry-ext-dependencies-dependency">Dependency</a></code></p>


<div class="doc-body">
<p>One <code>&lt;script&gt;</code> tag.</p>
<p>With <code>url</code> set, renders <code>&lt;script src="..."&gt;</code>; otherwise renders the
<code>content</code> inline as <code>&lt;script&gt;...&lt;/script&gt;</code>.</p>
<p>Example::</p>
<pre><code>Script(content="console.log('hi');", attrs={"type": "module"}, wrap=False)
# &lt;script type="module"&gt;console.log('hi');&lt;/script&gt;
</code></pre>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/types.py#L222" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-script-wrap" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>wrap</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>wrap: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Wrap inline content in a self-executing function, so its top-level
variables do not leak into (or collide with) other scripts on the page::</p>
<pre><code>(function() {
console.log('hi');
})();
</code></pre>
<p>Only applies to classic scripts (no <code>type</code> attribute or a JS MIME
type); <code>module</code>/<code>importmap</code>/other types are never wrapped.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/types.py#L237" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-script-to-json" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>to_json</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>to_json() -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">
<p>Serialize for cache storage; the inverse of :meth:<code>from_json</code>.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/types.py#L248" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-script-from-json" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>from_json</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>from_json(data: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]) -> <a class="doc-type-link" href="/reference/dependencies/#citry-ext-dependencies-script">Script</a></code></pre>
</div>

<div class="doc-body">
<p>Rebuild from :meth:<code>to_json</code> output.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/types.py#L273" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-dependencies-style" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>Style</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/dependencies/#citry-ext-dependencies-dependency">Dependency</a></code></p>


<div class="doc-body">
<p>One stylesheet tag.</p>
<p>With <code>url</code> set, renders <code>&lt;link rel="stylesheet" href="..."/&gt;</code>;
otherwise renders the <code>content</code> inline as <code>&lt;style&gt;...&lt;/style&gt;</code>.</p>
<p>Example::</p>
<pre><code>Style(url="/static/print.css", attrs={"media": "print"})
# &lt;link media="print" rel="stylesheet" href="/static/print.css"/&gt;
</code></pre>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/types.py#L287" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-style-to-json" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>to_json</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>to_json() -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">
<p>Serialize for cache storage; the inverse of :meth:<code>from_json</code>.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/types.py#L297" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-style-from-json" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>from_json</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>from_json(data: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]) -> <a class="doc-type-link" href="/reference/dependencies/#citry-ext-dependencies-style">Style</a></code></pre>
</div>

<div class="doc-body">
<p>Rebuild from :meth:<code>to_json</code> output.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/types.py#L320" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-style-render" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>render</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>render() -> <a class="doc-type-link" href="/reference/rendering/#citry-markup">Markup</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/extension.py#L165" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-dependencies-dependenciesextension" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>DependenciesExtension</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/extensions/#citry-extension">Extension</a></code></p>


<div class="doc-body">
<p>The built-in extension owning the <code>Dependencies</code> secondary-asset class.</p>
<p>The loading half reads each component or reusable definition base's
preserved <code>Dependencies</code> declaration, resolves and merges declarations
lazily in :meth:<code>resolve</code>, and drops a class's derived state when its files
are reset or its final registry alias is removed.</p>
<p>The emission half (docs/design/dependencies.md): records each component
render (<code>on_component_data</code>), bubbles the records up as nested renders
are consumed (<code>on_render_context_merge</code>), and at serialize time turns them into
<code>&lt;script&gt;</code>/<code>&lt;style&gt;</code>/<code>&lt;link&gt;</code> tags placed into the page
(<code>on_serialize</code>, implemented in <code>emission.py</code>).</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/extension.py#L181" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-dependenciesextension-name" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>name</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/extension.py#L182" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-dependenciesextension-render-cache-mode" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>render_cache_mode</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/extension.py#L183" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-dependenciesextension-render-cache-version" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>render_cache_version</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/extension.py#L184" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-dependenciesextension-config" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>Config</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/extension.py#L186" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-dependenciesextension-on-component-unregistered" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_component_unregistered</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_component_unregistered(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-oncomponentunregisteredcontext">OnComponentUnregisteredContext</a>) -> None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/extension.py#L194" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-dependenciesextension-on-files-reset" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_files_reset</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_files_reset(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-onfilesresetcontext">OnFilesResetContext</a>) -> None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/extension.py#L203" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-dependenciesextension-on-component-data" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_component_data</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_component_data(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-oncomponentdatacontext">OnComponentDataContext</a>) -> None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/extension.py#L243" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-dependenciesextension-on-render-context-merge" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_render_context_merge</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_render_context_merge(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-onrendercontextmergecontext">OnRenderContextMergeContext</a>) -> None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/extension.py#L256" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-dependenciesextension-export-render-cache" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>export_render_cache</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>export_render_cache(ctx: OnRenderCacheExportContext) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>]</code></pre>
</div>

<div class="doc-body">
<p>Detach selected dependency records and exact variable-script values.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/extension.py#L273" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-dependenciesextension-stage-render-cache" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>stage_render_cache</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>stage_render_cache(ctx: OnRenderCacheStageContext) -> StagedRenderCacheContribution</code></pre>
</div>

<div class="doc-body">
<p>Validate dependency payloads and prepare exact cache repairs.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/extension.py#L338" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-dependenciesextension-on-serialize" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_serialize</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_serialize(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-onserializecontext">OnSerializeContext</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/extension.py#L365" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-dependenciesextension-urls" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>urls</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>urls: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[<a class="doc-type-link" href="/reference/web/#citry-urlroute">URLRoute</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/extension.py#L374" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-dependenciesextension-resolve" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>resolve</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>resolve(comp_cls: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]) -> <a class="doc-type-link" href="/reference/dependencies/#citry-ext-dependencies-citrydependencies">CitryDependencies</a></code></pre>
</div>

<div class="doc-body">
<p>Resolve and merge <code>comp_cls</code>'s secondary assets, cached per class.</p>
<p>Merge order is <strong>bases first, own entries last</strong>: list order becomes
document order at emission and CSS breaks equal-specificity ties by
document order, so the more specialized class's styles must come later
to win (docs/design/asset_loading.md section 7.3).</p>
<p><code>Component.Dependencies.extend</code> picks the bases:</p>
<ul>
<li><code>True</code> - inherit JS/CSS from <code>Component.Dependencies</code> of Component's base classes</li>
<li><code>False</code> - no inheritance; only the class's own entries (if any)</li>
<li>a list - exactly those classes + their bases, in the order given</li>
</ul>
<p>An explicit <code>Dependencies = None</code> declaration means no own entries and no inheritance.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/emission.py#L73" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-dependencies-ondependenciescontext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>OnDependenciesContext</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Context for the <code>on_dependencies</code> hook, owned by the dependencies
extension (not a "core" hook: any extension that defines an
<code>on_dependencies</code> method receives it, via the manager's <code>emit</code>).</p>
<p>Fires at serialize time with the final, deduplicated tag lists (possibly
empty), just before they are rendered into the page. Mutate the lists in
place to add, remove, or reorder entries.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/emission.py#L85" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-ondependenciescontext-citry" class="doc-heading">
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
<p>The <code>Citry</code> instance the render belongs to.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/emission.py#L87" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-ondependenciescontext-scripts" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>scripts</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>scripts: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[<a class="doc-type-link" href="/reference/dependencies/#citry-ext-dependencies-dependency">Dependency</a>]</code></pre>
</div>

<div class="doc-body">
<p>The <code>&lt;script&gt;</code> entries about to be emitted, in document order (mutable).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/emission.py#L89" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-ondependenciescontext-styles" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>styles</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>styles: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[<a class="doc-type-link" href="/reference/dependencies/#citry-ext-dependencies-dependency">Dependency</a>]</code></pre>
</div>

<div class="doc-body">
<p>The stylesheet entries about to be emitted, in document order (mutable).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/emission.py#L91" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-ondependenciescontext-context" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>context</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a></code></pre>
</div>

<div class="doc-body">
<p>The root render's <code>CitryContext</code>. Its <code>extra</code> carries everything
that bubbled up during the render, so an extension can read back what its
render-time hooks collected.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/emission.py#L95" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-ondependenciescontext-strategy" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>strategy</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>strategy: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>The <code>serialize(deps_strategy=...)</code> value this emission runs under
(<code>"document"</code>, <code>"simple"</code>, or <code>"fragment"</code>).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/emission.py#L98" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-dependencies-ondependenciescontext-before-manifest" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>before_manifest</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>before_manifest: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[<a class="doc-type-link" href="/reference/dependencies/#citry-ext-dependencies-dependency">Dependency</a>]</code></pre>
</div>

<div class="doc-body">
<p>Entries rendered as tags immediately before the <code>data-citry</code> page
manifest tag (mutable). For anything that must already be in the DOM when
the client-side manager processes the manifest, e.g. the events
extension's own manifest tag. Only the strategies that emit the page
manifest render these (<code>"document"</code> and <code>"fragment"</code>); under
<code>"simple"</code> they are not emitted.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/dependencies/extension.py#L126" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-dependencies-get-dependencies" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>get_dependencies</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>get_dependencies(comp_cls: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]) -> <a class="doc-type-link" href="/reference/dependencies/#citry-ext-dependencies-citrydependencies">CitryDependencies</a></code></pre>
</div>

<div class="doc-body">
<p>The merged secondary assets of a component class.</p>
<p>Routes through the class's Citry instance to its built-in <code>dependencies</code>
extension. Users reach this through <code>Card.get_dependencies()</code>.</p>





</div>
</div>



