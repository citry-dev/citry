---
title: Extensions
url: https://citry.dev/v/0.6.0/reference/extensions/
description: "The plugin system: the extension base, its commands, and the hook context objects."
---
# Extensions

The plugin system: the extension base, its commands, and the hook context objects.




<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L662" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-extension" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>Extension</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Base class for all extensions.</p>
<p>Subclass this, set <code>name</code> (a lowercase Python identifier), and implement the
<code>on_*</code> hooks you care about. Every hook has an empty default, so an
extension only overrides what it needs (the manager calls only the hooks an
extension actually overrides). The <code>on_*</code> methods below are the full hook
catalog.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L673" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-name" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>name</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>name: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Name of the extension. Lowercase, a valid Python identifier. Determines
the attribute the per-component config is reachable under
(<code>component.&lt;name&gt;</code>) and, through
<a href="/reference/extensions/#citry-extension-class-name"><code>class_name</code></a>, the nested class name.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L679" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-class-name" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>class_name</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>class_name: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>PascalCase name of the per-component nested config class, derived from
<a href="/reference/extensions/#citry-extension-name"><code>name</code></a> at subclass creation (<code>my_extension</code> -&gt;
<code>MyExtension</code>).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L684" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-config" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>Config</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>Config: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/extensions/#citry-extensionconfig">ExtensionConfig</a>]</code></pre>
</div>

<div class="doc-body">
<p>Base class the per-component nested config inherits from.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L687" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-commands" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>commands</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>commands: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#list">list</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/extensions/#citry-extensioncommand">ExtensionCommand</a>]]</code></pre>
</div>

<div class="doc-body">
<p>CLI commands this extension provides (see <a href="/reference/extensions/#citry-extensioncommand"><code>ExtensionCommand</code></a>).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L690" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-introspection-version" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>introspection_version</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>introspection_version: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#int">int</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Positive schema version when this extension publishes component metadata.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L693" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-render-cache-mode" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>render_cache_mode</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>render_cache_mode: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;deny&#x27;, &#x27;stateless&#x27;, &#x27;payload&#x27;]</code></pre>
</div>

<div class="doc-body">
<p>Whether settled render state from this extension can be replayed.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L696" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-render-cache-version" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>render_cache_version</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>render_cache_version: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#int">int</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Positive compatibility version for stateless or payload replay.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L705" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-citry" class="doc-heading">
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
<p>The <code>Citry</code> instance this extension instance belongs to. Set by the
manager when the extension is attached (extensions are per-instance, so
the back-reference is unambiguous).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L711" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-urls" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>urls</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>urls: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#list">list</a>[<a class="doc-type-link" href="/reference/web/#citry-urlroute">URLRoute</a>]</code></pre>
</div>

<div class="doc-body">
<p>HTTP routes this extension provides, as <a href="/reference/web/#citry-urlroute"><code>URLRoute</code></a> values.</p>
<p>Mounted by the web-integration adapters as part of <code>Citry.urls</code>: a
user extension's routes live under <code>ext/&lt;extension name&gt;/</code>;
built-in extensions own their paths directly. Override as an
attribute or property; handlers can reach engine state through
<code>self.citry</code>.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L742" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-validate-config-fields" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>validate_config_fields</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>validate_config_fields(fields: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>], component: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>] | None = None) -> None</code></pre>
</div>

<div class="doc-body">
<p>Check the config fields declared for this extension, at declaration time.</p>
<p>Users configure an extension in two places: a component's nested config
class (<code>class View:</code> for an extension named <code>"view"</code>), and the
engine-wide
<a href="/reference/citry/#citry-citrysettings-extensions-defaults"><code>extensions_defaults</code></a>
setting. Citry calls this method once per declaration:</p>
<ul>
<li>At engine construction, with the extension's entry in the
<code>extensions_defaults</code> setting (<code>component</code> is <code>None</code>).</li>
<li>At component class definition, with the fields declared on the
component's nested config class, including fields from its
user-written base classes (<code>component</code> is the component class).</li>
</ul>
<p>The base implementation accepts everything: by default an extension's
config may hold any fields, even methods. Override it to reject bad
fields early, so a typo in a field name fails at startup or at class
definition instead of surfacing later as a confusing downstream error.
Because both declaration sites are checked, the fields are known-valid
by the time the config class is instantiated.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><p>An extension whose config accepts exactly one field:</p>
<pre><code class="language-python">from citry import Extension

class TimeoutExtension(Extension):
    name = &quot;timeout&quot;

    def validate_config_fields(
        self, fields, *, component=None
    ):
        for name in fields:
            if name != &quot;seconds&quot;:
                msg = (
                    f&quot;unknown field {name!r}; &quot;
                    &quot;the only field is 'seconds'&quot;
                )
                raise ValueError(msg)
</code></pre></blockquote>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>fields</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code>

- The declared fields, mapping field name to declared value.
For a nested config class, dunder names, the <code>Config</code> base's
members, and citry's own bookkeeping attributes are already
filtered out.
</li>

<li>
<code>component</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>] | None</code>

- The component class the fields were declared on, or
<code>None</code> when the fields come from the <code>extensions_defaults</code>
setting.
</li>

</ul>



<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>ValueError</code> - When a field is not valid for this extension. Raise it
with a message naming the offending field and what is valid;
citry prefixes the declaration site (the component and its
nested class, or the setting).
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L807" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-inspect-component" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>inspect_component</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>inspect_component(ctx: <a class="doc-type-link" href="/reference/component-introspection/#citry-componentintrospectioncontext">ComponentIntrospectionContext</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#object">object</a>] | None</code></pre>
</div>

<div class="doc-body">
<p>Publish this extension's allowlisted metadata for one component.</p>
<p>Citry calls this direct query method only when a caller explicitly
requests the extension by name. Override it together with a positive
<a href="/reference/extensions/#citry-extension-introspection-version"><code>introspection_version</code></a>.
Return an exact built-in <code>dict</code> made only from strict JSON values,
or <code>None</code> when this component has no entry. The method must be
observational, deterministic, reentrant, and thread-safe; it must not
render, load assets, mutate registration, or depend on request state.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>ctx</code>

<code><a class="doc-type-link" href="/reference/component-introspection/#citry-componentintrospectioncontext">ComponentIntrospectionContext</a></code>

- The owning engine, temporary live component class, and its
already-built core metadata record. <code>ctx.info.extensions</code> is
always empty.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#object">object</a>] | None: An extension-owned JSON object, or ``None``.</p>




</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L829" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-inspect-template-namespace" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>inspect_template_namespace</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>inspect_template_namespace(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-templatenamespacecontext">TemplateNamespaceContext</a>) -> <a class="doc-type-link" href="/reference/extensions/#citry-templatenamespacecontribution">TemplateNamespaceContribution</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Describe template variables supplied by this extension.</p>
<p>Citry calls this observational hook while it captures tooling analysis.
Return detached annotations only. Do not render, mutate the component,
or depend on request state. The contribution can add known names or
report that the extension preserves unenumerated extras, but it cannot
change lint severity.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>ctx</code>

<code><a class="doc-type-link" href="/reference/extensions/#citry-templatenamespacecontext">TemplateNamespaceContext</a></code>

- The owning engine and temporary component class.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="/reference/extensions/#citry-templatenamespacecontribution">TemplateNamespaceContribution</a> | None: Portable namespace metadata, or ``None`` for no contribution.</p>




</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L852" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-on-extension-created" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_extension_created</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_extension_created(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-onextensioncreatedcontext">OnExtensionCreatedContext</a>) -> None</code></pre>
</div>

<div class="doc-body">
<p>Called once when this extension instance is created.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L857" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-on-component-class-created" class="doc-heading">
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
<p>Called after a Component class is defined, before it is registered.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L860" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-on-component-registered" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_component_registered</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_component_registered(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-oncomponentregisteredcontext">OnComponentRegisteredContext</a>) -> None</code></pre>
</div>

<div class="doc-body">
<p>Called after a Component class is registered.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L863" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-on-component-unregistered" class="doc-heading">
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
<p>Called after a Component class is unregistered.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L866" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-on-citry-cleared" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_citry_cleared</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_citry_cleared(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-oncitryclearedcontext">OnCitryClearedContext</a>) -> None</code></pre>
</div>

<div class="doc-body">
<p>Called during <code>Citry.clear()</code> after its registry is empty.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L871" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-on-component-input" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_component_input</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_component_input(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-oncomponentinputcontext">OnComponentInputContext</a>) -> None</code></pre>
</div>

<div class="doc-body">
<p>Called when a component starts rendering, before <code>template_data</code>.</p>
<p>Inspect or mutate <code>ctx.kwargs</code> / <code>ctx.slots</code> in place. These are
the authoritative raw mappings. Citry normalizes Slots and constructs
the component's final typed <code>kwargs</code> and <code>slots</code> once all input
hooks finish.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L881" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-on-component-data" class="doc-heading">
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
<p>Called after <code>template_data</code>; mutate <code>ctx.template_data</code> to add or
change template variables.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L887" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-on-component-rendered" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_component_rendered</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_component_rendered(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-oncomponentrenderedcontext">OnComponentRenderedContext</a>) -> <a class="doc-type-link" href="/reference/rendering/#citry-citryrender">CitryRender</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Called after a component (and its children) rendered. Return new
content to replace the output, raise to replace the error, or return
<code>None</code> to keep the original.</p>
<p>The content follows the rule of a <code>{{ ... }}</code> value, on static and
interactive pages alike: a <code>CitryRender</code> replaces the output, a
plain <code>str</code> is shown as text (Citry escapes it), and
<a href="/reference/rendering/#citry-markup"><code>Markup</code></a> is inserted as HTML. Never pass user input
to the <code>Markup()</code> constructor.</p>
<p>HTML you serialize inside the hook, such as <code>str(ctx.render)</code>, is a
plain <code>str</code>, so wrap it in <code>Markup</code> before you return it. It does
not carry the component's own <code>data-cid-*</code> attribute; Citry adds it
to the HTML you return.</p>



<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>TypeError</code> - Citry raises it when the hook returns a value of any
other type. It is raised as soon as the hook returns, before
any later extension runs, and the message names the
extension and the component.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L912" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-on-slot-rendered" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_slot_rendered</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_slot_rendered(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-onslotrenderedcontext">OnSlotRenderedContext</a>) -> RenderPart | None</code></pre>
</div>

<div class="doc-body">
<p>Called after a <code>&lt;c-slot&gt;</code> site rendered (a fill, or the fallback).</p>
<p>Return new content to replace the output, or <code>None</code> to keep the
original. Raising propagates. As with <code>on_component_rendered</code>, a
<code>CitryRender</code> replaces the output, a plain <code>str</code> is shown as text
(Citry escapes it), and <a href="/reference/rendering/#citry-markup"><code>Markup</code></a> is inserted as HTML,
on static and interactive pages alike.</p>



<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>TypeError</code> - Citry raises it when the hook returns a value of any
other type, such as a bare <code>Placeholder</code> or component.
It is raised before any later extension runs, and the
message names the extension and the slot. Return <code>None</code>
or the unchanged <code>ctx.result</code> to keep the output.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L931" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-on-attrs-resolved" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_attrs_resolved</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_attrs_resolved(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-onattrsresolvedcontext">OnAttrsResolvedContext</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None</code></pre>
</div>

<div class="doc-body">
<p>Called after an HTML element's dynamic attributes resolved to their
final dict, before it is formatted into the output. Return a new dict
to replace the attributes, or <code>None</code> to keep them.</p>
<p>Fires per element per render, only for elements with at least one
dynamic attribute (a <code>c-*</code> value or a <code>c-bind</code> spread).</p>



<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>TypeError</code> - Citry raises it when the hook returns a value that
is not a mapping, such as a <code>dict</code>, or <code>None</code>, before
any later extension runs. The message names the extension.
</li>

<li>
<code>VueCodeError</code> - Citry raises <a href="/reference/attributes/#citry-vuecodeerror"><code>VueCodeError</code></a>
when the hook adds an attribute name that Vue would read as
code (one starting with <code>v-</code>, <code>:</code>, <code>.</code>, <code>^</code>, <code>@</code>,
or <code>#</code>), or changes the value of such an attribute written
in the template. Removing one, or keeping it unchanged, is
allowed.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L953" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-on-render-context-merge" class="doc-heading">
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
<p>Called when a nested render's output is consumed by an enclosing
render (a child component settling into its parent, or an
already-rendered value embedded via an expression or slot).</p>
<p>Merge your extension's slice of <code>ctx.child_context.extra</code> into
<code>ctx.parent_context.extra</code>, with your own policy (the dependencies
extension, for example, appends records preserving order). The core
does not merge anything itself.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L965" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-export-render-cache" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>export_render_cache</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>export_render_cache(ctx: OnRenderCacheExportContext) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#object">object</a>]</code></pre>
</div>

<div class="doc-body">
<p>Export this payload extension's selected strict-JSON contribution.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L970" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-stage-render-cache" class="doc-heading">
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
<p>Validate a detached payload and return a mutation-free replay contribution.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L995" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-render-cache-bypass-reason" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>render_cache_bypass_reason</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>render_cache_bypass_reason() -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Return a stable reason when this extension requires live rendering.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L999" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-on-serialize" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_serialize</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_serialize(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-onserializecontext">OnSerializeContext</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Called at the end of <code>CitryRender.serialize()</code> with the joined HTML.</p>
<p>Return a new string to replace the output (threaded across
extensions), or <code>None</code> to keep it. This is where serialize-time
work that needs the whole page happens; the dependencies extension
places the collected JS/CSS here, using <code>ctx.placeholders</code> for the
<code>&lt;c-js&gt;</code>/<code>&lt;c-css&gt;</code> positions.</p>



<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>TypeError</code> - Citry raises it when the hook returns a value that
is not a <code>str</code> or <code>None</code>, before any later extension
runs. The message names the extension.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L1016" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-browser-plugin" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>browser_plugin</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>browser_plugin() -> BrowserPluginDescriptor | None</code></pre>
</div>

<div class="doc-body">
<p>Describe the fixed Vue plugin installed before an interactive app mounts.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L1020" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-prepare-browser-render" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>prepare_browser_render</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>prepare_browser_render(ctx: OnBrowserRenderPrepareContext) -> BrowserRenderContribution | None</code></pre>
</div>

<div class="doc-body">
<p>Project this extension's selected render records into prepared browser data.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L1040" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-on-template-loaded" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_template_loaded</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_template_loaded(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-ontemplateloadedcontext">OnTemplateLoadedContext</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Called once per class with the template string before it is parsed.
Return a new string to modify it.</p>



<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>TypeError</code> - Citry raises it when the hook returns a value that
is not a <code>str</code> or <code>None</code>, before any later extension
runs. The message names the extension and the component.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L1052" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-on-template-foreign-spans" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_template_foreign_spans</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_template_foreign_spans(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-ontemplateforeignspanscontext">OnTemplateForeignSpansContext</a>) -> <a class="doc-type-link" href="/reference/extensions/#citry-foreignspanset">ForeignSpanSet</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Declare UTF-8 source ranges owned by this extension's host engine.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L1058" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-on-messages-loaded" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_messages_loaded</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_messages_loaded(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-onmessagesloadedcontext">OnMessagesLoadedContext</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Called once per source declaration with source-locale Fluent text
before compilation. A parent and children that inherit the same
messages share this one call.</p>
<p>Return a new string to replace the source. User extensions run in
installation order. The built-in i18n extension always runs after
those transformations, so it compiles the same final string the asset
loader caches.</p>



<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>TypeError</code> - Citry raises it when the hook returns a value that
is not a <code>str</code> or <code>None</code>, before any later extension
runs. The message names the extension and the component.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L1076" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-on-template-compiled" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_template_compiled</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_template_compiled(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-ontemplatecompiledcontext">OnTemplateCompiledContext</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#list">list</a>[BodyItem] | None</code></pre>
</div>

<div class="doc-body">
<p>Called once per compiled body, with the generated node list. Mutate it
in place or return a new list.</p>



<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>TypeError</code> - Citry raises it when the hook returns a value that
is not a sequence, such as a <code>list</code>, or <code>None</code>, before
any later extension runs. A <code>str</code> is not accepted. The
message names the extension and the component.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L1089" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-on-template-foreign-compiled" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_template_foreign_compiled</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_template_foreign_compiled(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-ontemplateforeigncompiledcontext">OnTemplateForeignCompiledContext</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#list">list</a>[BodyItem] | None</code></pre>
</div>

<div class="doc-body">
<p>Replace this provider's claims in one independent body list.</p>
<p>The provider must call <code>ctx.mark_resolved</code> exactly once for every
claim it handles. Core verifies the ledger before general compiled
hooks run.</p>



<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>TypeError</code> - Citry raises it when the hook returns a value that
is not a sequence, such as a <code>list</code>, or <code>None</code>, before
any later extension runs. A <code>str</code> is not accepted. The
message names the extension and the component.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L1108" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-on-template-reset" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_template_reset</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_template_reset(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-ontemplateresetcontext">OnTemplateResetContext</a>) -> None</code></pre>
</div>

<div class="doc-body">
<p>Called after a component class's loaded template is reset.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L1113" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-on-js-loaded" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_js_loaded</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_js_loaded(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-onjsloadedcontext">OnJsLoadedContext</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Called once per class with the component's primary JS content (inline
or read from <code>js_file</code>). Return a new string to modify it.</p>



<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>TypeError</code> - Citry raises it when the hook returns a value that
is not a <code>str</code> or <code>None</code>, before any later extension
runs. The message names the extension and the component.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L1125" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extension-on-css-loaded" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_css_loaded</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_css_loaded(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-oncssloadedcontext">OnCssLoadedContext</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Called once per class with the component's primary CSS content (inline
or read from <code>css_file</code>). Return a new string to modify it.</p>



<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>TypeError</code> - Citry raises it when the hook returns a value that
is not a <code>str</code> or <code>None</code>, before any later extension
runs. The message names the extension and the component.
</li>

</ul>



</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L615" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-extensionconfig" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ExtensionConfig</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Base for the per-component nested config class (reached as <code>Extension.Config</code>).</p>
<p>An extension named <code>"view"</code> (<code>class_name == "View"</code>) lets a user define a
nested <code>class View:</code> on a component. The manager rebuilds that nested class
as a subclass of this base (binding <code>component_class</code>), then instantiates it
per render and attaches it as <code>component.view</code>.</p>
<p>The config holds only a weak reference to its component, and the
component may be <code>None</code> when an extension creates the config outside a
component render.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L629" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionconfig-component-class" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_class</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">
<p>The Component class this config is defined on (bound by the manager).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L638" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionconfig-component" class="doc-heading">
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
<p>The owning Component instance.</p>



<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>RuntimeError</code> - If this config was created without a component, or
the component has been garbage-collected.
</li>

</ul>



</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L1327" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-extensionmanager" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ExtensionManager</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Fans each lifecycle hook out across a <code>Citry</code> instance's extensions.</p>
<p>Each <a href="/reference/citry/#citry-citry"><code>Citry</code></a> instance builds one manager when it is
created. A component class is bound to its <code>Citry</code> instance (and so to
these extensions) when the class is defined, so the extensions are
always present when a hook fires.</p>
<p>For each hook name, the manager calls only the extensions that override
that hook, so an extension that does not implement a hook costs nothing.
<a href="/reference/extensions/#citry-extensionmanager-emit"><code>emit()</code></a> uses the same lookup by name,
which lets extensions fire their own custom hooks (e.g.
<code>on_dependencies</code>).</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L1348" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionmanager-citry" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>citry</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L1514" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionmanager-get-extension" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>get_extension</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>get_extension(name: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="/reference/extensions/#citry-extension">Extension</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L1729" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionmanager-get-extension-command" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>get_extension_command</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>get_extension_command(name: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, command_name: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/extensions/#citry-extensioncommand">ExtensionCommand</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L1737" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionmanager-commands" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>commands</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>commands: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/extensions/#citry-extensioncommand">ExtensionCommand</a>], ...]]</code></pre>
</div>

<div class="doc-body">
<p>Every extension's CLI commands, keyed by extension name (read as <code>Citry.commands</code>).</p>
<p>Built-in extensions come first (they are prepended at construction), then
the user's extensions in spec order; only extensions that declare commands
appear. Extension names are unique (enforced at construction), so the keys
never collide. The CLI reaches a command as
<code>citry ext run &lt;extension name&gt; &lt;command name&gt;</code>.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L1750" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionmanager-urls" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>urls</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>urls: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/web/#citry-urlroute">URLRoute</a>, ...]</code></pre>
</div>

<div class="doc-body">
<p>The combined route table of every extension (read as <code>Citry.urls</code>).</p>
<p>Built-in extensions own their paths directly (e.g. the dependencies
extension's <code>cache/...</code> and <code>citry.js</code>); a user extension's
routes are namespaced under <code>ext/&lt;extension name&gt;/</code> so they cannot
collide with citry's own or each other's.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L1808" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionmanager-emit" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>emit</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>emit(name: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, ctx: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>, result: _Result = &#x27;none&#x27;, field: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None = None) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code></pre>
</div>

<div class="doc-body">
<p>Dispatch hook <code>name</code> to the extensions that define it, combining the
hooks' returned values per <code>result</code>:</p>
<ul>
<li><code>"none"</code>: call every extension, ignore returns; return <code>None</code>.</li>
<li><code>"first"</code>: return the first non-<code>None</code> return (short-circuit).</li>
<li><code>"map"</code>: thread <code>ctx.&lt;field&gt;</code> - each non-<code>None</code> return replaces it
(via <code>dataclasses.replace</code>) and is passed to the next extension; the
final field value is returned.</li>
</ul>
<p>An extension takes part by defining a method called <code>name</code>.
<code>name</code> need not be a hook declared on
<a href="/reference/extensions/#citry-extension"><code>Extension</code></a>, so an extension can fire its own
custom hook for others to implement.</p>
<div class="doc-examples"><p class="doc-section-title">Example</p><p><code>on_render_context_merge</code> notifies every extension that
defines it (<code>"none"</code>)::</p>
<pre><code>manager.emit("on_render_context_merge", ctx)
</code></pre>
<p>A custom hook can thread <code>ctx.value</code> through the extensions
(<code>"map"</code>) and return the final value. <code>emit</code> does not check
the type of each return, so the code that reads the result
should check it::</p>
<pre><code>manager.emit(
    "on_my_value",
    ctx,
    result="map",
    field="value",
)
</code></pre>
<p>A custom hook can let an extension short-circuit (<code>"first"</code> returns
the first non-<code>None</code> value)::</p>
<pre><code>manager.emit("on_my_event", ctx, result="first")
</code></pre></div>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L2021" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionmanager-on-extension-created" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_extension_created</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_extension_created() -> None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L2027" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionmanager-on-component-class-created" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_component_class_created</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_component_class_created(component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]) -> None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L2037" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionmanager-on-component-registered" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_component_registered</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_component_registered(name: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]) -> None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L2043" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionmanager-on-component-unregistered" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_component_unregistered</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_component_unregistered(name: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]) -> None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L2049" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionmanager-on-citry-cleared" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_citry_cleared</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_citry_cleared() -> None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L2054" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionmanager-on-component-input" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_component_input</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_component_input(component: <a class="doc-type-link" href="/reference/component/#citry-component">Component</a>) -> None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L2083" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionmanager-on-component-data" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_component_data</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_component_data(component: <a class="doc-type-link" href="/reference/component/#citry-component">Component</a>, context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>, template_data: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>], js_data: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>], css_data: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]) -> None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L2114" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionmanager-on-render-context-merge" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_render_context_merge</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_render_context_merge(parent_context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>, child_context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>) -> None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L2120" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionmanager-on-serialize" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_serialize</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_serialize(context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>, selected_render: <a class="doc-type-link" href="/reference/rendering/#citry-citryrender">CitryRender</a>, html: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, placeholders: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>], deps_strategy: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, deps_position: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, _script_security: _ScriptSecurityMaterializer | None = None, _security_csp: <a class="doc-type-link" href="/reference/citry/#citry-securitycspmode">SecurityCspMode</a> = &#x27;off&#x27;, _javascript_policy: _JavascriptPolicy | None = None, _security_javascript: <a class="doc-type-link" href="/reference/citry/#citry-securityjavascriptmode">SecurityJavascriptMode</a> = &#x27;allow&#x27;) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L2161" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionmanager-on-component-rendered" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_component_rendered</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_component_rendered(component: <a class="doc-type-link" href="/reference/component/#citry-component">Component</a>, render: <a class="doc-type-link" href="/reference/rendering/#citry-citryrender">CitryRender</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None, error: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/exceptions.html#Exception">Exception</a> | None, context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a> | None = None) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/rendering/#citry-citryrender">CitryRender</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None, <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/exceptions.html#Exception">Exception</a> | None, <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a>]</code></pre>
</div>

<div class="doc-body">
<p>Thread the rendered output through the extensions; a return replaces the
render, a raise replaces the error.</p>
<p>With <code>context</code> (the component's render context), a returned <code>str</code>
or <code>Markup</code> becomes a render in that context before the next
extension sees it, so a plain <code>str</code> stays text along the chain.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L2221" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionmanager-on-slot-rendered" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_slot_rendered</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_slot_rendered(component: <a class="doc-type-link" href="/reference/component/#citry-component">Component</a>, slot: <a class="doc-type-link" href="/reference/slots/#citry-slot">Slot</a>, slot_name: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, slot_node: <a class="doc-type-link" href="/reference/nodes/#citry-slotnode">SlotNode</a>, slot_is_required: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a>, result: RenderPart, context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a> | None = None) -> RenderPart</code></pre>
</div>

<div class="doc-body">
<p>Thread a slot's rendered output through the extensions; a return
replaces the result, a raise propagates.</p>
<p>With <code>context</code> (the context of the <code>&lt;c-slot&gt;</code> site), a returned
<code>str</code> or <code>Markup</code> becomes a render in that context before the
next extension sees it, so a plain <code>str</code> stays text along the chain.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L2276" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionmanager-has-hook" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>has_hook</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>has_hook(name: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Whether any installed extension implements the hook <code>name</code>.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L2287" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionmanager-has-attrs-resolved-hook" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>has_attrs_resolved_hook</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>has_attrs_resolved_hook(runtime_candidate: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a> = True) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Whether this element has an applicable resolved-attributes hook.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L2291" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionmanager-on-attrs-resolved" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_attrs_resolved</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_attrs_resolved(component: <a class="doc-type-link" href="/reference/component/#citry-component">Component</a>, tag_name: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, attrs: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>], runtime_candidate: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a> = True) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">
<p>Thread an element's resolved attribute dict through the extensions; a
return replaces the dict, a raise propagates.</p>
<p>This sits on a per-element per-render hot path, so when no extension
implements the hook the dict is returned without building a context.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L2342" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionmanager-on-template-loaded" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_template_loaded</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_template_loaded(component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>], content: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, template_id: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> = &#x27;&#x27;, origin: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> = &#x27;&#x27;, template_kind: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;primary&#x27;, &#x27;standalone&#x27;, &#x27;nested&#x27;] = &#x27;primary&#x27;) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L2367" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionmanager-on-template-foreign-spans" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_template_foreign_spans</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_template_foreign_spans(component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>], content: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, template_id: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, origin: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, template_kind: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;primary&#x27;, &#x27;standalone&#x27;, &#x27;nested&#x27;], foreign_compile_contexts: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#object">object</a>] | None = None) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#object">object</a>, ...], <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#object">object</a> | None]]</code></pre>
</div>

<div class="doc-body">
<p>Collect provider spans against one final post-load source string.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L2421" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionmanager-on-template-foreign-compiled" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_template_foreign_compiled</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_template_foreign_compiled(component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>], nodes: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#list">list</a>[BodyItem], provider_metadata: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#object">object</a> | None], template_id: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, origin: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, template_kind: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;primary&#x27;, &#x27;standalone&#x27;, &#x27;nested&#x27;]) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#list">list</a>[BodyItem]</code></pre>
</div>

<div class="doc-body">
<p>Resolve every provider claim, one independently compiled body at a time.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L2544" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionmanager-on-messages-loaded" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_messages_loaded</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_messages_loaded(component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>], declaration_owner: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>, content: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, origin: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L2579" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionmanager-on-template-compiled" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_template_compiled</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_template_compiled(component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>], nodes: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#list">list</a>[BodyItem], template_id: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> = &#x27;&#x27;, origin: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> = &#x27;&#x27;, template_kind: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;primary&#x27;, &#x27;standalone&#x27;, &#x27;nested&#x27;] = &#x27;primary&#x27;) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#list">list</a>[BodyItem]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L2604" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionmanager-on-template-reset" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_template_reset</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_template_reset(component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]) -> None</code></pre>
</div>

<div class="doc-body">
<p>Notify extensions after a component class's template is reset.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L2613" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionmanager-on-js-loaded" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_js_loaded</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_js_loaded(component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>], content: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L2623" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionmanager-on-css-loaded" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_css_loaded</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_css_loaded(component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>], content: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L2633" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensionmanager-on-files-reset" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_files_reset</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_files_reset(component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]) -> None</code></pre>
</div>

<div class="doc-body">
<p>Notify extensions that a component class's loaded asset files were
reset, so each drops its own per-class state (the <code>dependencies</code>
built-in drops its merged result here).</p>
<p>This hook is not declared on the <a href="/reference/extensions/#citry-extension"><code>Extension</code></a>
base. An extension receives it by defining a method named
<code>on_files_reset</code>.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L569" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-extensioncommand" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ExtensionCommand</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Base class for an extension's CLI command.</p>
<p>Subclass this, set <code>name</code> (and usually <code>help</code>), declare any
<code>arguments</code>, and define <code>handle</code> to do the work. A command that only
groups <code>subcommands</code> leaves <code>handle</code> unset, and the runner prints its
help instead of running anything. Citry turns the declarations into an
<code>argparse</code> parser and runs the matching command; an extension lists its
command classes in <code>Extension.commands</code> and a user reaches one as
<code>citry ext run &lt;extension&gt; &lt;command&gt;</code>. An extension declares HTTP
routes separately, in <code>Extension.urls</code>.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L583" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensioncommand-name" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>name</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>name: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>The command name (<code>citry ext run &lt;extension&gt; &lt;name&gt;</code>).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L586" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensioncommand-help" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>help</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>help: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>One-line description of the command, shown in <code>--help</code> output.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L589" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensioncommand-arguments" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>arguments</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>arguments: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Sequence">Sequence</a>[<a class="doc-type-link" href="/reference/extensions/#citry-commandarg">CommandArg</a> | <a class="doc-type-link" href="/reference/extensions/#citry-commandarggroup">CommandArgGroup</a>]</code></pre>
</div>

<div class="doc-body">
<p>Positional arguments and options, declared with <a href="/reference/extensions/#citry-commandarg"><code>CommandArg</code></a>.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L592" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensioncommand-subcommands" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>subcommands</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>subcommands: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Sequence">Sequence</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/extensions/#citry-extensioncommand">ExtensionCommand</a>]]</code></pre>
</div>

<div class="doc-body">
<p>Nested commands. A command with subcommands usually has no <code>handle</code> of its own.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L595" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensioncommand-subparser-input" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>subparser_input</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>subparser_input: <a class="doc-type-link" href="/reference/extensions/#citry-commandsubcommand">CommandSubcommand</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Optional customization of how this command appears when nested under a parent.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L598" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensioncommand-handle" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>handle</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>handle: CommandHandler | None</code></pre>
</div>

<div class="doc-body">
<p>Runs the command, called with the parsed options as keyword arguments.
<code>None</code> (the default) marks a command that only groups subcommands; a real
command overrides this with <code>def handle(self, **kwargs)</code>.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L603" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-extensioncommand-citry" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>citry</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>citry: <a class="doc-type-link" href="/reference/citry/#citry-citry">Citry</a> | None</code></pre>
</div>

<div class="doc-body">
<p>The engine the command runs against, bound by the runner before
<code>handle</code> is called (like <a href="/reference/extensions/#citry-extension-citry"><code>Extension.citry</code></a>).
A command's <code>handle</code> reads it to reach the component registry and the
installed extensions.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/ext/debug.py#L97" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-debug-debug" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>Debug</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/extensions/#citry-extension">Extension</a></code></p>


<div class="doc-body">
<p>Draw development-only boundaries around component and slot output.</p>
<p>Install this extension explicitly with <code>Citry(extensions=[Debug])</code>.
Its per-component config has two exact boolean fields,
<code>highlight_components</code> and <code>highlight_slots</code>. Set them globally in
<code>extensions_defaults["debug"]</code> or override them in a component's nested
<code>class Debug</code>.</p>
<p>The visual boundaries are real <code>div</code> elements. They are useful for
inspecting ordinary page structure, but can affect layout, direct-child
selectors, and restricted table or select content models. Do not enable
them in production or use them for layout-sensitive verification.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><p>Enable both boundary types for one engine:</p>
<pre><code class="language-python">from citry import Citry
from citry.ext.debug import Debug

app = Citry(
    extensions=[Debug],
    extensions_defaults={
        &quot;debug&quot;: {
            &quot;highlight_components&quot;: True,
            &quot;highlight_slots&quot;: True,
        },
    },
)
</code></pre></blockquote>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/ext/debug.py#L132" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-debug-debug-name" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/ext/debug.py#L152" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-debug-debug-validate-config-fields" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>validate_config_fields</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>validate_config_fields(fields: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#object">object</a>], component: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>] | None = None) -> None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/ext/debug.py#L167" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-debug-debug-on-component-registered" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_component_registered</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_component_registered(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-oncomponentregisteredcontext">OnComponentRegisteredContext</a>) -> None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/ext/debug.py#L171" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-debug-debug-on-component-unregistered" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/ext/debug.py#L176" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-debug-debug-render-cache-bypass-reason" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>render_cache_bypass_reason</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>render_cache_bypass_reason() -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Require live rendering while debug highlighting is enabled.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/ext/debug.py#L187" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-debug-debug-on-component-rendered" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_component_rendered</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_component_rendered(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-oncomponentrenderedcontext">OnComponentRenderedContext</a>) -> <a class="doc-type-link" href="/reference/rendering/#citry-citryrender">CitryRender</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/ext/debug.py#L206" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-debug-debug-on-slot-rendered" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_slot_rendered</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_slot_rendered(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-onslotrenderedcontext">OnSlotRenderedContext</a>) -> <a class="doc-type-link" href="/reference/rendering/#citry-citryrender">CitryRender</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/ext/debug.py#L221" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-debug-debug-on-render-context-merge" class="doc-heading">
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


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/command.py#L68" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-commandarg" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>CommandArg</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>One positional argument or option, mirroring <code>ArgumentParser.add_argument</code>.</p>
<p>Every field maps to the <code>add_argument</code> keyword of the same name, and
Citry passes the fields to argparse unchanged. A field left as <code>None</code>
is not passed, so argparse applies its own default.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/command.py#L78" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-commandarg-name-or-flags" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>name_or_flags</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>name_or_flags: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Sequence">Sequence</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>]</code></pre>
</div>

<div class="doc-body">
<p>A positional name (<code>"path"</code>) or a list of option flags (<code>["--shout", "-s"]</code>).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/command.py#L80" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-commandarg-action" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>action</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>action: CommandAction | <a class="doc-type-link" href="/reference/events/#citry-ext-events-actions-action">Action</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/command.py#L81" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-commandarg-nargs" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>nargs</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>nargs: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#int">int</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;*&#x27;, &#x27;+&#x27;, &#x27;?&#x27;] | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/command.py#L82" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-commandarg-const" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>const</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>const: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/command.py#L83" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-commandarg-default" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>default</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>default: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/command.py#L84" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-commandarg-type" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>type</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>type: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>], <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/command.py#L85" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-commandarg-choices" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>choices</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>choices: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Sequence">Sequence</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/command.py#L86" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-commandarg-required" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>required</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>required: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/command.py#L87" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-commandarg-help" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>help</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>help: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/command.py#L88" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-commandarg-metavar" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>metavar</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>metavar: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/command.py#L89" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-commandarg-dest" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>dest</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>dest: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/command.py#L90" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-commandarg-version" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>version</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>version: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/command.py#L92" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-commandarg-to-add-argument-kwargs" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>to_add_argument_kwargs</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>to_add_argument_kwargs() -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">
<p>The <code>add_argument</code> keywords for this argument, minus <code>name_or_flags</code>.</p>
<p>Citry passes <code>name_or_flags</code> to <code>add_argument</code> positionally, so it
is not included here; unset (<code>None</code>) fields are dropped.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/command.py#L116" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-commandarggroup" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>CommandArgGroup</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>A titled group of arguments, mirroring <code>ArgumentParser.add_argument_group</code>.</p>
<p>Place one in a command's <code>arguments</code> list to group related options together
in the <code>--help</code> output.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/command.py#L125" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-commandarggroup-title" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>title</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>title: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/command.py#L126" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-commandarggroup-description" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>description</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>description: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/command.py#L127" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-commandarggroup-arguments" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>arguments</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>arguments: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Sequence">Sequence</a>[<a class="doc-type-link" href="/reference/extensions/#citry-commandarg">CommandArg</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/command.py#L130" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-commandsubcommand" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>CommandSubcommand</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>How a command appears when nested under a parent, mirroring <code>add_subparsers().add_parser</code>.</p>
<p>A command sets this as its <code>subparser_input</code> to customize its entry in the
parent's subcommand list (for example a different help line or program name).</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/command.py#L139" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-commandsubcommand-prog" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>prog</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>prog: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/command.py#L140" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-commandsubcommand-help" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>help</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>help: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/command.py#L141" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-commandsubcommand-description" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>description</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>description: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/command.py#L142" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-commandsubcommand-metavar" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>metavar</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>metavar: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/command.py#L144" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-commandsubcommand-to-add-parser-kwargs" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>to_add_parser_kwargs</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>to_add_parser_kwargs() -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">
<p>The <code>add_parser</code> keywords for this subcommand entry (unset fields dropped).</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L278" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-onattrsresolvedcontext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>OnAttrsResolvedContext</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">






<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L280" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onattrsresolvedcontext-citry" class="doc-heading">
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
<p>The <code>Citry</code> instance the component belongs to.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L282" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onattrsresolvedcontext-component" class="doc-heading">
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
<p>The component whose template holds the element. For <code>&lt;c-element&gt;</code>,
this is the lexical owner, not the transparent built-in renderer.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L285" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onattrsresolvedcontext-tag-name" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>tag_name</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>tag_name: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>The HTML tag the attributes belong to (e.g. <code>"div"</code>).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L287" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onattrsresolvedcontext-attrs" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>attrs</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>attrs: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">
<p>The resolved attribute dict: <code>class</code>/<code>style</code> already normalized to
strings, booleans still <code>True</code>, omitted attributes already absent.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L415" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-oncitryclearedcontext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>OnCitryClearedContext</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">






<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L417" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-oncitryclearedcontext-citry" class="doc-heading">
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
<p>The <code>Citry</code> instance whose registry and engine caches were cleared.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L166" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-oncomponentclasscreatedcontext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>OnComponentClassCreatedContext</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">






<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L168" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-oncomponentclasscreatedcontext-citry" class="doc-heading">
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
<p>The <code>Citry</code> instance the component class belongs to.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L170" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-oncomponentclasscreatedcontext-component-class" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_class</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">
<p>The created Component class.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L173" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-oncomponentclasscreatedcontext-nested-declarations" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>nested_declarations</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>nested_declarations(name: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/component-introspection/#citry-nestedclassdeclaration">NestedClassDeclaration</a>, ...]</code></pre>
</div>

<div class="doc-body">
<p>Return the exact authored bindings for <code>name</code> in component C3 order.</p>
<p>A record whose value is <code>None</code> is an explicit reset, distinct from
the name being absent. The classes are the original source objects,
even after Citry replaces the component attribute with an effective
runtime config class.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>name</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code>

- The nested declaration name, usually the extension's
<a href="/reference/extensions/#citry-extension-class-name"><code>class_name</code></a>.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/component-introspection/#citry-nestedclassdeclaration">NestedClassDeclaration</a>, ...]: The declarations from the component through its bases in C3 order.</p>




</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L225" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-oncomponentdatacontext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>OnComponentDataContext</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">






<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L227" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-oncomponentdatacontext-citry" class="doc-heading">
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
<p>The <code>Citry</code> instance the component belongs to.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L229" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-oncomponentdatacontext-component" class="doc-heading">
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
<p>The Component instance being rendered.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L231" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-oncomponentdatacontext-context" class="doc-heading">
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
<p>The render-scoped <code>CitryContext</code> for this component's render.
Extensions stash tree-wide state in <code>context.extra</code> (for example the
dependencies extension's render records); it bubbles up through
<code>on_render_context_merge</code> as nested renders are consumed. <code>context.provides</code>
is not yet populated when this hook fires.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L237" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-oncomponentdatacontext-template-data" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>template_data</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>template_data: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">
<p>The template variables from <code>Component.template_data()</code> (mutable).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L239" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-oncomponentdatacontext-js-data" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>js_data</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>js_data: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">
<p>The JS variables from <code>Component.js_data()</code> (mutable). Citry sends
them to the browser as fields on the component's Vue instance, and checks
the keys after this hook runs.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L243" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-oncomponentdatacontext-css-data" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>css_data</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>css_data: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">
<p>The CSS variables from <code>Component.css_data()</code> (mutable). Consumed by
the built-in <code>dependencies</code> extension.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L213" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-oncomponentinputcontext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>OnComponentInputContext</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">






<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L215" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-oncomponentinputcontext-citry" class="doc-heading">
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
<p>The <code>Citry</code> instance the component belongs to.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L217" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-oncomponentinputcontext-component" class="doc-heading">
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
<p>The Component instance being rendered.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L219" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-oncomponentinputcontext-kwargs" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>kwargs</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>kwargs: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">
<p>The keyword arguments passed to the component (mutable plain dict).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L221" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-oncomponentinputcontext-slots" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>slots</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>slots: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">
<p>The slot fills passed to the component (mutable plain dict).</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L193" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-oncomponentregisteredcontext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>OnComponentRegisteredContext</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">






<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L195" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-oncomponentregisteredcontext-citry" class="doc-heading">
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
<p>The <code>Citry</code> instance the component was registered with.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L197" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-oncomponentregisteredcontext-name" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>name</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>name: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>The name the component was registered under.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L199" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-oncomponentregisteredcontext-component-class" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_class</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">
<p>The registered Component class.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L248" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-oncomponentrenderedcontext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>OnComponentRenderedContext</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">






<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L250" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-oncomponentrenderedcontext-citry" class="doc-heading">
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
<p>The <code>Citry</code> instance the component belongs to.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L252" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-oncomponentrenderedcontext-component" class="doc-heading">
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
<p>The Component instance that was rendered.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L254" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-oncomponentrenderedcontext-render" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>render</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>render: <a class="doc-type-link" href="/reference/rendering/#citry-citryrender">CitryRender</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>The rendered output, or <code>None</code> if rendering failed.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L256" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-oncomponentrenderedcontext-error" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>error</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>error: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/exceptions.html#Exception">Exception</a> | None</code></pre>
</div>

<div class="doc-body">
<p>The error raised during rendering, or <code>None</code> if it succeeded.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L203" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-oncomponentunregisteredcontext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>OnComponentUnregisteredContext</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">






<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L205" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-oncomponentunregisteredcontext-citry" class="doc-heading">
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
<p>The <code>Citry</code> instance the component was unregistered from.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L207" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-oncomponentunregisteredcontext-name" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>name</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>name: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>The name the component was registered under.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L209" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-oncomponentunregisteredcontext-component-class" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_class</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">
<p>The unregistered Component class.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L506" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-oncssloadedcontext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>OnCssLoadedContext</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">






<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L508" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-oncssloadedcontext-citry" class="doc-heading">
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
<p>The <code>Citry</code> instance the component class belongs to.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L510" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-oncssloadedcontext-component-class" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_class</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">
<p>The Component class whose CSS was loaded.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L512" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-oncssloadedcontext-content" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>content</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>content: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>The CSS content (inline or read from <code>css_file</code>).</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L99" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-onextensioncreatedcontext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>OnExtensionCreatedContext</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">






<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L101" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onextensioncreatedcontext-citry" class="doc-heading">
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
<p>The <code>Citry</code> instance the extension belongs to.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L103" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onextensioncreatedcontext-extension" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>extension</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>extension: <a class="doc-type-link" href="/reference/extensions/#citry-extension">Extension</a></code></pre>
</div>

<div class="doc-body">
<p>The created extension instance.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L516" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-onfilesresetcontext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>OnFilesResetContext</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">






<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L518" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onfilesresetcontext-citry" class="doc-heading">
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
<p>The <code>Citry</code> instance the component class belongs to.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L520" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onfilesresetcontext-component-class" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_class</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">
<p>The Component class whose loaded asset files were reset.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L496" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-onjsloadedcontext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>OnJsLoadedContext</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">






<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L498" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onjsloadedcontext-citry" class="doc-heading">
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
<p>The <code>Citry</code> instance the component class belongs to.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L500" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onjsloadedcontext-component-class" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_class</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">
<p>The Component class whose JS was loaded.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L502" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onjsloadedcontext-content" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>content</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>content: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>The JS content (inline or read from <code>js_file</code>).</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L401" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-onmessagesloadedcontext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>OnMessagesLoadedContext</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">






<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L403" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onmessagesloadedcontext-citry" class="doc-heading">
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
<p>The <code>Citry</code> instance the component class belongs to.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L405" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onmessagesloadedcontext-component-class" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_class</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">
<p>The Component class whose source messages were loaded.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L407" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onmessagesloadedcontext-declaration-owner" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>declaration_owner</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>declaration_owner: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a></code></pre>
</div>

<div class="doc-body">
<p>The class that authored the inherited messages/messages_file pair.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L409" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onmessagesloadedcontext-content" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>content</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>content: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>The source-locale Fluent text before compilation.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L411" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onmessagesloadedcontext-origin" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>origin</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>origin: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>A file path or inline <code>module::Class.messages</code> label for diagnostics.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L532" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-onrendercontextmergecontext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>OnRenderContextMergeContext</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">






<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L534" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onrendercontextmergecontext-citry" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L536" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onrendercontextmergecontext-parent-context" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>parent_context</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>parent_context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a></code></pre>
</div>

<div class="doc-body">
<p>The context of the render that consumed the nested one.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L538" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onrendercontextmergecontext-child-context" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>child_context</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>child_context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a></code></pre>
</div>

<div class="doc-body">
<p>The context of the consumed nested render.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L542" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-onserializecontext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>OnSerializeContext</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">






<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L544" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onserializecontext-citry" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L546" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onserializecontext-context" class="doc-heading">
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
<p>The root render's <code>CitryContext</code> (its <code>extra</code> carries everything
that bubbled up during the render).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L549" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onserializecontext-selected-render" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>selected_render</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>selected_render: <a class="doc-type-link" href="/reference/rendering/#citry-citryrender">CitryRender</a></code></pre>
</div>

<div class="doc-body">
<p>The final hook-selected render tree being serialized.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L551" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onserializecontext-html" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>html</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>html: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>The joined HTML (threaded: return a new string to replace it).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L553" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onserializecontext-placeholders" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>placeholders</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>placeholders: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>]</code></pre>
</div>

<div class="doc-body">
<p>The placeholder parts found during serialization: unique placeholder id
(the <code>Placeholder.key</code> plus a counter and a private serialization
identity) to the exact text standing in for it in <code>html</code>. Match the key
prefix rather than relying on the private suffix.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L558" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onserializecontext-deps-strategy" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>deps_strategy</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>deps_strategy: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>The <code>serialize(deps_strategy=...)</code> argument.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L560" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onserializecontext-deps-position" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>deps_position</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>deps_position: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>The <code>serialize(deps_position=...)</code> argument.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L260" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-onslotrenderedcontext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>OnSlotRenderedContext</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">






<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L262" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onslotrenderedcontext-citry" class="doc-heading">
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
<p>The <code>Citry</code> instance the component belongs to.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L264" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onslotrenderedcontext-component" class="doc-heading">
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
<p>The component whose template holds the <code>&lt;c-slot&gt;</code> that was rendered.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L266" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onslotrenderedcontext-slot" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>slot</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>slot: <a class="doc-type-link" href="/reference/slots/#citry-slot">Slot</a></code></pre>
</div>

<div class="doc-body">
<p>The Slot that was rendered: the fill, or the fallback when no fill was given.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L268" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onslotrenderedcontext-slot-name" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>slot_name</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>slot_name: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>The resolved slot name (<code>"default"</code> for an unnamed slot).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L270" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onslotrenderedcontext-slot-node" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>slot_node</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>slot_node: <a class="doc-type-link" href="/reference/nodes/#citry-slotnode">SlotNode</a></code></pre>
</div>

<div class="doc-body">
<p>The runtime <code>SlotNode</code> at whose site the slot rendered.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L272" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onslotrenderedcontext-slot-is-required" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>slot_is_required</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>slot_is_required: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Whether the slot resolved as required.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L274" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-onslotrenderedcontext-result" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>result</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>result: RenderPart</code></pre>
</div>

<div class="doc-body">
<p>The rendered output (a <code>str</code> or a <code>CitryRender</code>).</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L359" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-foreignspan" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ForeignSpan</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>One half-open UTF-8 byte range declared by a host provider.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L363" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-foreignspan-start-byte" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>start_byte</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>start_byte: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#int">int</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L364" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-foreignspan-end-byte" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>end_byte</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>end_byte: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#int">int</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L365" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-foreignspan-may-control-body" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>may_control_body</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>may_control_body: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L368" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-foreignspanset" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ForeignSpanSet</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>The spans and private compile metadata returned by one provider.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L372" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-foreignspanset-spans" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>spans</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>spans: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/extensions/#citry-foreignspan">ForeignSpan</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L373" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-foreignspanset-provider-metadata" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>provider_metadata</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>provider_metadata: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#object">object</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L376" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-foreigncompilecontext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ForeignCompileContext</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Protocol">Protocol</a></code></p>


<div class="doc-body">
<p>Typed adapter state participating in standalone-template cache identity.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L380" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-foreigncompilecontext-provider" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>provider</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>provider: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Name of the extension allowed to receive this context.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L385" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-foreigncompilecontext-cache-fingerprint" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>cache_fingerprint</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>cache_fingerprint: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#bytes">bytes</a></code></pre>
</div>

<div class="doc-body">
<p>Deterministic identity for compile-time host state.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L390" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ontemplateforeignspanscontext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>OnTemplateForeignSpansContext</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">






<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L392" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplateforeignspanscontext-citry" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L393" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplateforeignspanscontext-component-class" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_class</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L394" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplateforeignspanscontext-content" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>content</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>content: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L395" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplateforeignspanscontext-template-id" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>template_id</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>template_id: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L396" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplateforeignspanscontext-origin" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>origin</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>origin: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L397" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplateforeignspanscontext-template-kind" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>template_kind</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>template_kind: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;primary&#x27;, &#x27;standalone&#x27;, &#x27;nested&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L398" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplateforeignspanscontext-compile-context" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>compile_context</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>compile_context: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#object">object</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L421" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ontemplatecompiledcontext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>OnTemplateCompiledContext</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">






<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L423" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplatecompiledcontext-citry" class="doc-heading">
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
<p>The <code>Citry</code> instance the component class belongs to.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L425" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplatecompiledcontext-component-class" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_class</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">
<p>The Component class whose template was compiled.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L427" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplatecompiledcontext-nodes" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>nodes</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>nodes: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#list">list</a>[BodyItem]</code></pre>
</div>

<div class="doc-body">
<p>The generated body node list.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L429" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplatecompiledcontext-template-id" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>template_id</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>template_id: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Immutable identity of the exact template record being compiled.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L431" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplatecompiledcontext-origin" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>origin</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>origin: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Authored source origin used for diagnostics.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L433" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplatecompiledcontext-template-kind" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>template_kind</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>template_kind: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;primary&#x27;, &#x27;standalone&#x27;, &#x27;nested&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L436" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-foreignclaim" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ForeignClaim</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>One provider-owned runtime claim in an independently compiled body.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L440" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-foreignclaim-provider" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>provider</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>provider: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L441" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-foreignclaim-ordinal" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>ordinal</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>ordinal: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#int">int</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L442" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-foreignclaim-source" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>source</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>source: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L443" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-foreignclaim-position" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>position</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>position: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#int">int</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#int">int</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L444" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-foreignclaim-may-control-body" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>may_control_body</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>may_control_body: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L445" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-foreignclaim-locus" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>locus</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>locus: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;body&#x27;, &#x27;component_input&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L448" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-foreignclaim-claim-id" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>claim_id</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>claim_id: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#int">int</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L452" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ontemplateforeigncompiledcontext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>OnTemplateForeignCompiledContext</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Owner-dispatched compilation context for one independent body list.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L456" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplateforeigncompiledcontext-citry" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L457" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplateforeigncompiledcontext-component-class" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_class</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L458" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplateforeigncompiledcontext-nodes" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>nodes</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>nodes: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#list">list</a>[BodyItem]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L459" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplateforeigncompiledcontext-claims" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>claims</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>claims: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/extensions/#citry-foreignclaim">ForeignClaim</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L460" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplateforeigncompiledcontext-provider-metadata" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>provider_metadata</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>provider_metadata: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#object">object</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L461" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplateforeigncompiledcontext-template-id" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>template_id</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>template_id: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L462" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplateforeigncompiledcontext-origin" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>origin</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>origin: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L463" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplateforeigncompiledcontext-template-kind" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>template_kind</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>template_kind: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;primary&#x27;, &#x27;standalone&#x27;, &#x27;nested&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L466" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplateforeigncompiledcontext-mark-resolved" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>mark_resolved</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>mark_resolved(*claims: <a class="doc-type-link" href="/reference/extensions/#citry-foreignclaim">ForeignClaim</a> = ()) -> None</code></pre>
</div>

<div class="doc-body">
<p>Record explicit outcomes for claims replaced by the provider.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L478" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplateforeigncompiledcontext-compiled-body" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>compiled_body</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>compiled_body(nodes: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#list">list</a>[BodyItem]) -> <a class="doc-type-link" href="/reference/rendering/#citry-compiledbody">CompiledBody</a></code></pre>
</div>

<div class="doc-body">
<p>Compile and protect one Citry run for later host-selected rendering.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L344" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ontemplateloadedcontext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>OnTemplateLoadedContext</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">






<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L346" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplateloadedcontext-citry" class="doc-heading">
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
<p>The <code>Citry</code> instance the component class belongs to.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L348" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplateloadedcontext-component-class" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_class</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">
<p>The Component class whose template was loaded.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L350" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplateloadedcontext-content" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>content</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>content: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>The template string (before parsing).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L352" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplateloadedcontext-template-id" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>template_id</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>template_id: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Immutable identity of this loaded template record.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L354" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplateloadedcontext-origin" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>origin</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>origin: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Source origin used for diagnostics.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L356" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplateloadedcontext-template-kind" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>template_kind</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>template_kind: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;primary&#x27;, &#x27;standalone&#x27;, &#x27;nested&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L524" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ontemplateresetcontext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>OnTemplateResetContext</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">






<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L526" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplateresetcontext-citry" class="doc-heading">
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
<p>The <code>Citry</code> instance the component class belongs to.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L528" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ontemplateresetcontext-component-class" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_class</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">
<p>The Component class whose loaded template was reset.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L131" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-templatenamespacecontext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>TemplateNamespaceContext</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Give an extension one component whose template namespace it can describe.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L135" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatenamespacecontext-citry" class="doc-heading">
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
<p>The owning Citry instance.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L137" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatenamespacecontext-component-class" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_class</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">
<p>The temporary live component class from the registry snapshot.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L141" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-templatenamespacecontribution" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>TemplateNamespaceContribution</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Publish analysis-only variables added by one installed extension.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>template_variables</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#object">object</a>]</code>

- Variable names mapped to annotations, using the
same format as <a href="/reference/citry/#citry-lintsettings-template-variables"><code>LintSettings.template_variables</code></a>.
</li>

<li>
<code>allows_extra_variables</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a></code>

- Whether this extension intentionally preserves
additional names that it cannot enumerate. Such unknown names are
linted as warnings, never silently accepted.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L155" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatenamespacecontribution-template-variables" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>template_variables</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>template_variables: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#object">object</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/citry@0.6.0/packages/py/citry/citry/extension.py#L156" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatenamespacecontribution-allows-extra-variables" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>allows_extra_variables</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>allows_extra_variables: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>



