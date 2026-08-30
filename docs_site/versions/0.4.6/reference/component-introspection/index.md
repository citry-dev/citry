---
title: Component introspection
url: https://citry.dev/v/0.4.6/reference/component-introspection/
description: "Frozen metadata records for component catalogs, schemas, assets, and extensions."
---
# Component introspection

Frozen metadata records for component catalogs, schemas, assets, and extensions.




<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L857" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-componentcatalog" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ComponentCatalog</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Hold one immutable, versioned snapshot of registered component metadata.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>schema_version</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code>

- The core component-catalog schema version.
</li>

<li>
<code>citry_version</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Installed Citry package version used for the snapshot.
</li>

<li>
<code>engine_id</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Runtime identity of the inspected Citry instance.
</li>

<li>
<code>extension_versions</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/component-introspection/#citry-extensionversion">ExtensionVersion</a>, ...]</code>

- Requested extension metadata versions, sorted by name.
</li>

<li>
<code>components</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/component-introspection/#citry-componentinfo">ComponentInfo</a>, ...]</code>

- Component records in canonical catalog order.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L871" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentcatalog-schema-version" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>schema_version</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>schema_version: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L872" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentcatalog-citry-version" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>citry_version</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>citry_version: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L873" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentcatalog-engine-id" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L874" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentcatalog-extension-versions" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>extension_versions</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>extension_versions: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/component-introspection/#citry-extensionversion">ExtensionVersion</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L875" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentcatalog-components" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>components</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>components: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/component-introspection/#citry-componentinfo">ComponentInfo</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L927" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentcatalog-to-dict" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>to_dict</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>to_dict() -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>]</code></pre>
</div>

<div class="doc-body">
<p>Return a fresh JSON-ready dictionary for this catalog.</p>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>]: A new nested tree of ordinary dictionaries, lists, and JSON scalar</p>




</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L944" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentcatalog-to-json" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>to_json</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>to_json(indent: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | None = None) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Serialize this catalog to deterministic UTF-8 JSON text.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>indent</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | None</code>

- Optional non-negative indentation width. <code>None</code> emits
compact JSON.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>: Deterministic JSON with recursively sorted object keys and Unicode</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>TypeError</code> - If <code>indent</code> is not an integer or <code>None</code>.
</li>

<li>
<code>ValueError</code> - If <code>indent</code> is negative.
</li>

</ul>



</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L779" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-componentinfo" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ComponentInfo</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Describe one exact registered component class generation.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>class_id</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Stable import-derived component route identity.
</li>

<li>
<code>engine_id</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Runtime identity of the owning Citry instance.
</li>

<li>
<code>definition_id</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Runtime identity of this exact class generation.
</li>

<li>
<code>name</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Deterministically selected primary registration name.
</li>

<li>
<code>aliases</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, ...]</code>

- Other registration names for the same class.
</li>

<li>
<code>class_name</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- Python class name, when available.
</li>

<li>
<code>module</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- Python module name, when available.
</li>

<li>
<code>qualname</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- Python qualified class name, when available.
</li>

<li>
<code>import_path</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- Full Python import path, when available.
</li>

<li>
<code>python_file</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a> | None</code>

- Absolute already-loaded module file, when available.
</li>

<li>
<code>description</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- The component class's own cleaned docstring.
</li>

<li>
<code>transparent</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code>

- Whether the component joins its parent's serialization frame.
</li>

<li>
<code>builtin</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code>

- Whether Citry created this as a framework component.
</li>

<li>
<code>schemas</code>

<code><a class="doc-type-link" href="/reference/component-introspection/#citry-componentschemas">ComponentSchemas</a></code>

- The component's five effective typed schemas.
</li>

<li>
<code>assets</code>

<code><a class="doc-type-link" href="/reference/component-introspection/#citry-componentassets">ComponentAssets</a></code>

- The component's four primary asset declarations.
</li>

<li>
<code>extensions</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/component-introspection/#citry-componentextensioninfo">ComponentExtensionInfo</a>, ...]</code>

- Explicitly requested extension-owned metadata.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L804" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentinfo-class-id" class="doc-heading">
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






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L805" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentinfo-engine-id" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L806" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentinfo-definition-id" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>definition_id</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>definition_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L807" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentinfo-name" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L808" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentinfo-aliases" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>aliases</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>aliases: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L809" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentinfo-class-name" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L810" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentinfo-module" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>module</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>module: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L811" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentinfo-qualname" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>qualname</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>qualname: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L812" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentinfo-import-path" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>import_path</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>import_path: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L813" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentinfo-python-file" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>python_file</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>python_file: <a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L814" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentinfo-description" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>description</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>description: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L815" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentinfo-transparent" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>transparent</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>transparent: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L816" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentinfo-builtin" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>builtin</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>builtin: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L817" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentinfo-schemas" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>schemas</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>schemas: <a class="doc-type-link" href="/reference/component-introspection/#citry-componentschemas">ComponentSchemas</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L818" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentinfo-assets" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>assets</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>assets: <a class="doc-type-link" href="/reference/component-introspection/#citry-componentassets">ComponentAssets</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L819" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentinfo-extensions" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>extensions</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>extensions: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/component-introspection/#citry-componentextensioninfo">ComponentExtensionInfo</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L94" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-componentintrospectioncontext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ComponentIntrospectionContext</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Give one extension the inputs for an explicitly requested metadata query.</p>
<p>The component class is temporary live runtime state. Inspectors publish
copied JSON metadata and must not retain this context or the class.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>citry</code>

<code><a class="doc-type-link" href="/reference/citry/#citry-citry">Citry</a></code>

- The owning Citry instance.
</li>

<li>
<code>component_class</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code>

- The live class from the query's copied registry
snapshot.
</li>

<li>
<code>info</code>

<code><a class="doc-type-link" href="/reference/component-introspection/#citry-componentinfo">ComponentInfo</a></code>

- The complete core metadata record, with no extension entries.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L110" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentintrospectioncontext-citry" class="doc-heading">
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
<p>The <code>Citry</code> instance being inspected.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L112" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentintrospectioncontext-component-class" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_class</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">
<p>The temporary live component class from the copied registry snapshot.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L114" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentintrospectioncontext-info" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>info</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>info: <a class="doc-type-link" href="/reference/component-introspection/#citry-componentinfo">ComponentInfo</a></code></pre>
</div>

<div class="doc-body">
<p>The already-built core metadata record, with no extension entries.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L39" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-componentintrospectionerror" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ComponentIntrospectionError</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/library/exceptions.html#RuntimeError">RuntimeError</a></code></p>


<div class="doc-body">
<p>Report that a requested extension could not publish component metadata.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>extension_name</code>

- The installed or requested extension name.
</li>

<li>
<code>component_name</code>

- The component's primary registered name, when the
failure happened while inspecting one component.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L56" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentintrospectionerror-extension-name" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>extension_name</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L57" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentintrospectionerror-component-name" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_name</code>
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L534" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-componentschemas" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ComponentSchemas</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Group the five typed schema roles exposed by a component.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>kwargs</code>

<code><a class="doc-type-link" href="/reference/component-introspection/#citry-schemainfo">SchemaInfo</a></code>

- Inputs accepted as component keyword arguments.
</li>

<li>
<code>slots</code>

<code><a class="doc-type-link" href="/reference/component-introspection/#citry-schemainfo">SchemaInfo</a></code>

- Slot fills accepted by the component.
</li>

<li>
<code>template_data</code>

<code><a class="doc-type-link" href="/reference/component-introspection/#citry-schemainfo">SchemaInfo</a></code>

- Values returned for template rendering.
</li>

<li>
<code>js_data</code>

<code><a class="doc-type-link" href="/reference/component-introspection/#citry-schemainfo">SchemaInfo</a></code>

- Values made available to component JavaScript.
</li>

<li>
<code>css_data</code>

<code><a class="doc-type-link" href="/reference/component-introspection/#citry-schemainfo">SchemaInfo</a></code>

- Values made available to component CSS.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L548" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentschemas-kwargs" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>kwargs</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>kwargs: <a class="doc-type-link" href="/reference/component-introspection/#citry-schemainfo">SchemaInfo</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L549" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentschemas-slots" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>slots</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>slots: <a class="doc-type-link" href="/reference/component-introspection/#citry-schemainfo">SchemaInfo</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L550" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentschemas-template-data" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>template_data</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>template_data: <a class="doc-type-link" href="/reference/component-introspection/#citry-schemainfo">SchemaInfo</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L551" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentschemas-js-data" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>js_data</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>js_data: <a class="doc-type-link" href="/reference/component-introspection/#citry-schemainfo">SchemaInfo</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L552" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentschemas-css-data" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>css_data</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>css_data: <a class="doc-type-link" href="/reference/component-introspection/#citry-schemainfo">SchemaInfo</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L466" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-schemainfo" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>SchemaInfo</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Describe one effective component schema binding.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>kind</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;absent&#x27;, &#x27;fields&#x27;, &#x27;opaque&#x27;]</code>

- Whether the schema is absent, recognized as fields, or opaque.
</li>

<li>
<code>declared_on</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- Import path of the MRO class that supplied the binding.
</li>

<li>
<code>import_path</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- Import path of the effective schema class.
</li>

<li>
<code>fields</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/component-introspection/#citry-fieldinfo">FieldInfo</a>, ...]</code>

- Recognized fields in runtime declaration order.
</li>

<li>
<code>namespace_policy</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;closed&#x27;, &#x27;allow-extra&#x27;, &#x27;unknown&#x27;]</code>

- Whether declared fields exhaust the normalized
runtime mapping, explicitly permit extras, or leave that unknown.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L481" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-schemainfo-kind" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>kind</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>kind: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;absent&#x27;, &#x27;fields&#x27;, &#x27;opaque&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L482" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-schemainfo-declared-on" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>declared_on</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>declared_on: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L483" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-schemainfo-import-path" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>import_path</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>import_path: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L484" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-schemainfo-fields" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>fields</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>fields: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/component-introspection/#citry-fieldinfo">FieldInfo</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L485" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-schemainfo-namespace-policy" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>namespace_policy</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>namespace_policy: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;closed&#x27;, &#x27;allow-extra&#x27;, &#x27;unknown&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L289" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-fieldinfo" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>FieldInfo</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Describe one field in a recognized component schema.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>name</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The schema adapter's canonical field name.
</li>

<li>
<code>required</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code>

- Whether callers must provide the field.
</li>

<li>
<code>type_display</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- A safe normalized type string, when available.
</li>

<li>
<code>type_fidelity</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;normalized&#x27;, &#x27;unavailable&#x27;]</code>

- Whether <code>type_display</code> contains a normalized type.
</li>

<li>
<code>default_kind</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;missing&#x27;, &#x27;value&#x27;, &#x27;factory&#x27;]</code>

- Whether the field has no default, a value, or a factory.
</li>

<li>
<code>default_value_state</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;not-applicable&#x27;, &#x27;omitted&#x27;, &#x27;available&#x27;, &#x27;unsupported&#x27;]</code>

- Whether a real default value was requested and copied.
</li>

<li>
<code>default_value</code>

<code><a class="doc-type-link" href="/reference/component-introspection/#citry-frozenjsonvalue">FrozenJsonValue</a> | None</code>

- A recursively frozen portable default, when available.
</li>

<li>
<code>description</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- Runtime field documentation from a supported schema source.
</li>

<li>
<code>source_module</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- Module that owns the authored field, when provable.
</li>

<li>
<code>source_qualname</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- Qualified class name that owns the field, when provable.
</li>

<li>
<code>source_file</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a> | None</code>

- Absolute already-loaded module file for that class, when available.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L309" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-fieldinfo-name" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L310" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-fieldinfo-required" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>required</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>required: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L311" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-fieldinfo-type-display" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>type_display</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>type_display: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L312" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-fieldinfo-type-fidelity" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>type_fidelity</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>type_fidelity: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;normalized&#x27;, &#x27;unavailable&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L313" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-fieldinfo-default-kind" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>default_kind</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>default_kind: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;missing&#x27;, &#x27;value&#x27;, &#x27;factory&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L314" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-fieldinfo-default-value-state" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>default_value_state</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>default_value_state: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;not-applicable&#x27;, &#x27;omitted&#x27;, &#x27;available&#x27;, &#x27;unsupported&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L315" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-fieldinfo-default-value" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>default_value</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>default_value: <a class="doc-type-link" href="/reference/component-introspection/#citry-frozenjsonvalue">FrozenJsonValue</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L316" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-fieldinfo-description" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>description</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>description: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L317" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-fieldinfo-source-module" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>source_module</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>source_module: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L318" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-fieldinfo-source-qualname" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>source_qualname</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>source_qualname: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L319" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-fieldinfo-source-file" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>source_file</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>source_file: <a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L77" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-frozenjsonobject" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>FrozenJsonObject</code>
</span>
<span class="doc-kind">attribute</span>
</h2>


<div class="doc-signature highlight">
<pre><code>FrozenJsonObject: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.TypeAlias">TypeAlias</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L78" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-frozenjsonvalue" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>FrozenJsonValue</code>
</span>
<span class="doc-kind">attribute</span>
</h2>


<div class="doc-signature highlight">
<pre><code>FrozenJsonValue: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.TypeAlias">TypeAlias</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L677" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-componentassets" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ComponentAssets</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Group a component's primary template, messages, JavaScript, and CSS declarations.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>template</code>

<code><a class="doc-type-link" href="/reference/component-introspection/#citry-assetinfo">AssetInfo</a></code>

- The primary template declaration.
</li>

<li>
<code>messages</code>

<code><a class="doc-type-link" href="/reference/component-introspection/#citry-assetinfo">AssetInfo</a></code>

- The source-locale Fluent declaration.
</li>

<li>
<code>js</code>

<code><a class="doc-type-link" href="/reference/component-introspection/#citry-assetinfo">AssetInfo</a></code>

- The primary JavaScript declaration.
</li>

<li>
<code>css</code>

<code><a class="doc-type-link" href="/reference/component-introspection/#citry-assetinfo">AssetInfo</a></code>

- The primary CSS declaration.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L690" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentassets-template" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>template</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>template: <a class="doc-type-link" href="/reference/component-introspection/#citry-assetinfo">AssetInfo</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L691" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentassets-messages" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>messages</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>messages: <a class="doc-type-link" href="/reference/component-introspection/#citry-assetinfo">AssetInfo</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L692" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentassets-js" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>js</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>js: <a class="doc-type-link" href="/reference/component-introspection/#citry-assetinfo">AssetInfo</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L693" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentassets-css" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>css</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>css: <a class="doc-type-link" href="/reference/component-introspection/#citry-assetinfo">AssetInfo</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L561" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-assetinfo" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>AssetInfo</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Describe one primary template, JavaScript, or CSS declaration.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>kind</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;none&#x27;, &#x27;inline&#x27;, &#x27;file&#x27;]</code>

- Whether the asset is absent, inline, or file-backed.
</li>

<li>
<code>declared_on</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- Import path of the class that supplied the declaration.
</li>

<li>
<code>owner_file</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a> | None</code>

- Absolute Python file containing the declaring class.
</li>

<li>
<code>declared_path</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- The file path exactly as declared by the component.
</li>

<li>
<code>resolution</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;not-applicable&#x27;, &#x27;not-requested&#x27;, &#x27;resolved&#x27;, &#x27;missing&#x27;, &#x27;unavailable&#x27;]</code>

- Whether path resolution was requested and what it found.
</li>

<li>
<code>resolved_path</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a> | None</code>

- Absolute existing asset path when resolution succeeded.
</li>

<li>
<code>searched_paths</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a>, ...]</code>

- Absolute candidate paths checked during resolution.
</li>

<li>
<code>owner_module</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- Module of the class that supplied the declaration.
</li>

<li>
<code>owner_qualname</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- Qualified name of that declaring class.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L579" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-assetinfo-kind" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>kind</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>kind: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;none&#x27;, &#x27;inline&#x27;, &#x27;file&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L580" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-assetinfo-declared-on" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>declared_on</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>declared_on: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L581" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-assetinfo-owner-file" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>owner_file</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>owner_file: <a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L582" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-assetinfo-declared-path" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>declared_path</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>declared_path: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L583" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-assetinfo-resolution" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>resolution</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>resolution: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;not-applicable&#x27;, &#x27;not-requested&#x27;, &#x27;resolved&#x27;, &#x27;missing&#x27;, &#x27;unavailable&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L584" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-assetinfo-resolved-path" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>resolved_path</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>resolved_path: <a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L585" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-assetinfo-searched-paths" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>searched_paths</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>searched_paths: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L586" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-assetinfo-owner-module" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>owner_module</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>owner_module: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L587" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-assetinfo-owner-qualname" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>owner_qualname</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>owner_qualname: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L702" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-extensionversion" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ExtensionVersion</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Record one requested extension's introspection schema version.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>name</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The extension's unique registered name.
</li>

<li>
<code>introspection_version</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code>

- The extension-owned positive schema version.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L713" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionversion-name" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L714" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionversion-introspection-version" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>introspection_version</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>introspection_version: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L723" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-componentextensioninfo" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ComponentExtensionInfo</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Store one extension's explicitly published component metadata.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>name</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The extension's unique registered name.
</li>

<li>
<code>introspection_version</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code>

- The extension-owned positive schema version.
</li>

<li>
<code>data</code>

<code><a class="doc-type-link" href="/reference/component-introspection/#citry-frozenjsonobject">FrozenJsonObject</a></code>

- A defensively copied and recursively frozen JSON object.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L735" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentextensioninfo-name" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L736" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentextensioninfo-introspection-version" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>introspection_version</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>introspection_version: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/introspection.py#L737" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentextensioninfo-data" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>data</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>data: <a class="doc-type-link" href="/reference/component-introspection/#citry-frozenjsonobject">FrozenJsonObject</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/_nested_declarations.py#L27" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-nestedclassdeclaration" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>NestedClassDeclaration</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>One nested class binding written on a component or definition base.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>declaring_class</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a></code>

- The class whose body contains the binding.
</li>

<li>
<code>name</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The nested declaration name, such as <code>"Events"</code>.
</li>

<li>
<code>value</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a></code>

- The exact authored value. Supported declarations use a class,
while <code>None</code> explicitly resets inherited declarations.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/_nested_declarations.py#L40" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-nestedclassdeclaration-declaring-class" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>declaring_class</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>declaring_class: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/_nested_declarations.py#L41" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-nestedclassdeclaration-name" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/_nested_declarations.py#L42" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-nestedclassdeclaration-value" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>value</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>value: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>



