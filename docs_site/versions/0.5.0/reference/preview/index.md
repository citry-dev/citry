---
title: Preview
url: https://citry.dev/v/0.5.0/reference/preview/
description: "Component examples, layouts, and metadata for command-owned preview pages."
---
# Preview

Component examples, layouts, and metadata for command-owned preview pages.




<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/extension.py#L91" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-preview-previewextension" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>PreviewExtension</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/extensions/#citry-extension">Extension</a></code></p>


<div class="doc-body">
<p>Declare component previews and expose them only through CLI-owned servers.</p>
<p>Install with <code>Citry(extensions=[PreviewExtension])</code>. Components configure
examples through a nested <code>Preview</code> class. Ordinary application adapters
receive no routes from this extension.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/extension.py#L100" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-previewextension-name" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/extension.py#L101" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-previewextension-class-name" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>class_name</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/extension.py#L102" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-previewextension-config" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/extension.py#L104" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-previewextension-render-cache-mode" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/extension.py#L105" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-previewextension-render-cache-version" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/extension.py#L107" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-previewextension-on-extension-created" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_extension_created</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_extension_created(_ctx: <a class="doc-type-link" href="/reference/extensions/#citry-onextensioncreatedcontext">OnExtensionCreatedContext</a>) -> None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/extension.py#L111" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-previewextension-validate-config-fields" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>validate_config_fields</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>validate_config_fields(fields: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>], component: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>] | None = None) -> None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/extension.py#L137" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-previewextension-on-component-class-created" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_component_class_created</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_component_class_created(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-oncomponentclasscreatedcontext">OnComponentClassCreatedContext</a>) -> None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/extension.py#L152" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-previewextension-file-path" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>file_path</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>file_path(component: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>] | None, field: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, path: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a></code></pre>
</div>

<div class="doc-body">
<p>Resolve a file beside its declaration, retaining inherited provenance.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/extension.py#L168" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-previewextension-previews" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>previews</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>previews(selection: Selection | None = None) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[_Preview, ...]</code></pre>
</div>

<div class="doc-body">
<p>Resolve an ordered selection with fresh variant inputs on each call.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L91" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-preview-variant" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>variant</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>variant(slug: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, label: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, description: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> = &#x27;&#x27;, params: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None = None, viewport: <a class="doc-type-link" href="/reference/preview/#citry-ext-preview-viewport">Viewport</a> | None = None) -> <a class="doc-type-link" href="/reference/preview/#citry-ext-preview-variant-2">Variant</a></code></pre>
</div>

<div class="doc-body">
<p>Declare one preview variant with metadata and component or template params.</p>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L54" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-preview-variant-2" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>Variant</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>One named example with display metadata and ordinary Python inputs.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>slug</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Stable lowercase name, using letters, digits, and single hyphens.
</li>

<li>
<code>label</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Human-readable example label.
</li>

<li>
<code>description</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Plain-text explanation of the example.
</li>

<li>
<code>params</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code>

- Inputs for the component or variables for its preview template.
</li>

<li>
<code>viewport</code>

<code><a class="doc-type-link" href="/reference/preview/#citry-ext-preview-viewport">Viewport</a> | None</code>

- Optional browser dimensions overriding component defaults.
</li>

</ul>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L68" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-variant-slug" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>slug</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>slug: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L69" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-variant-label" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>label</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>label: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L70" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-variant-description" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>description</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>description: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L71" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-variant-params" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>params</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>params: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L72" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-variant-viewport" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>viewport</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>viewport: <a class="doc-type-link" href="/reference/preview/#citry-ext-preview-viewport">Viewport</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L28" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-preview-viewport" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>Viewport</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Browser dimensions and pixel scale used to capture one variant.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>width</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code>

- CSS width from 1 through 8192 pixels.
</li>

<li>
<code>height</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code>

- CSS height from 1 through 8192 pixels.
</li>

<li>
<code>device_scale_factor</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#float">float</a></code>

- Finite pixel scale greater than zero, at most four.
</li>

</ul>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L40" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-viewport-width" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>width</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>width: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L41" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-viewport-height" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>height</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>height: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L42" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-viewport-device-scale-factor" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>device_scale_factor</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>device_scale_factor: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#float">float</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L105" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-preview-layout" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>Layout</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Wrap preview content with one template or component class.</p>
<p>Exactly one source is required. The layout receives <code>preview</code> and a
named <code>content</code> slot. Component classes must belong to the rendering app.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>template</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- Trusted inline Citry template source.
</li>

<li>
<code>template_file</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a> | None</code>

- UTF-8 template path relative to the declaring class.
</li>

<li>
<code>component</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>] | None</code>

- Component class accepting preview metadata and content.
</li>

</ul>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L120" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-layout-template" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>template</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>template: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L121" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-layout-template-file" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>template_file</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>template_file: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L122" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-layout-component" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>] | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L19" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-preview-previewerror" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>PreviewError</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/library/exceptions.html#ValueError">ValueError</a></code></p>


<div class="doc-body">
<p>A preview declaration, selection, or rendering request is invalid.</p>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L139" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-preview-previewcomponent" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>PreviewComponent</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Display metadata for one component, without its live class or inputs.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L143" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-previewcomponent-id" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>id</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L144" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-previewcomponent-name" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L145" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-previewcomponent-group" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>group</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>group: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L148" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-preview-previewvariant" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>PreviewVariant</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Display metadata for one variant, without its Python params.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L152" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-previewvariant-slug" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>slug</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>slug: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L153" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-previewvariant-label" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>label</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>label: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L154" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-previewvariant-description" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>description</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>description: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L155" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-previewvariant-viewport" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>viewport</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>viewport: <a class="doc-type-link" href="/reference/preview/#citry-ext-preview-viewport">Viewport</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L156" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-previewvariant-url" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>url</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>url: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L159" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-preview-previewmetadata" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>PreviewMetadata</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Component and variant metadata supplied to an example or variant layout.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L163" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-previewmetadata-component" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component: <a class="doc-type-link" href="/reference/preview/#citry-ext-preview-previewcomponent">PreviewComponent</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L164" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-previewmetadata-variant" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>variant</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>variant: <a class="doc-type-link" href="/reference/preview/#citry-ext-preview-previewvariant">PreviewVariant</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L167" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-preview-previewitem" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>PreviewItem</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Variant metadata paired with lazily rendered content for a page layout.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L171" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-previewitem-variant" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>variant</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>variant: <a class="doc-type-link" href="/reference/preview/#citry-ext-preview-previewvariant">PreviewVariant</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L172" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-previewitem-content" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>content</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>content: <a class="doc-type-link" href="/reference/slots/#citry-slot">Slot</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L175" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-preview-previewgroup" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>PreviewGroup</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>One component's metadata and ordered preview items.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L179" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-previewgroup-component" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component: <a class="doc-type-link" href="/reference/preview/#citry-ext-preview-previewcomponent">PreviewComponent</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L180" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-previewgroup-items" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>items</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>items: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/preview/#citry-ext-preview-previewitem">PreviewItem</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L183" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-preview-previewpage" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>PreviewPage</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Ordered component groups supplied to a single-preview or gallery layout.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L187" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-previewpage-selection" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>selection</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>selection: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;variant&#x27;, &#x27;component&#x27;, &#x27;all&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/preview/types.py#L188" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-preview-previewpage-components" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>components</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>components: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/preview/#citry-ext-preview-previewgroup">PreviewGroup</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>



