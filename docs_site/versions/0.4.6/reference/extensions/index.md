---
title: Extensions
url: https://citry.dev/v/0.4.6/reference/extensions/
description: "The plugin system: the extension base, its commands, and the hook context objects."
---
# Extensions

The plugin system: the extension base, its commands, and the hook context objects.




<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L641" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L652" target="_blank" rel="noopener">
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
<pre><code>name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Name of the extension. Lowercase, a valid Python identifier. Determines
the attribute the per-component config is reachable under
(<code>component.&lt;name&gt;</code>) and, via :attr:<code>class_name</code>, the nested class name.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L657" target="_blank" rel="noopener">
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
<pre><code>class_name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>PascalCase name of the per-component nested config class, derived from
:attr:<code>name</code> at subclass creation (<code>my_extension</code> -&gt; <code>MyExtension</code>).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L661" target="_blank" rel="noopener">
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
<pre><code>Config: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/extensions/#citry-extensionconfig">ExtensionConfig</a>]</code></pre>
</div>

<div class="doc-body">
<p>Base class the per-component nested config inherits from.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L664" target="_blank" rel="noopener">
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
<pre><code>commands: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/extensions/#citry-extensioncommand">ExtensionCommand</a>]]</code></pre>
</div>

<div class="doc-body">
<p>CLI commands this extension provides (see :class:<code>ExtensionCommand</code>).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L667" target="_blank" rel="noopener">
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
<pre><code>introspection_version: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Positive schema version when this extension publishes component metadata.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L670" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L673" target="_blank" rel="noopener">
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
<pre><code>render_cache_version: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Positive compatibility version for stateless or payload replay.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L682" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L688" target="_blank" rel="noopener">
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
<pre><code>urls: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[<a class="doc-type-link" href="/reference/web/#citry-urlroute">URLRoute</a>]</code></pre>
</div>

<div class="doc-body">
<p>HTTP routes this extension provides (see <code>citry/util/routing.py</code>).</p>
<p>Mounted by the web-integration adapters as part of <code>Citry.urls</code>: a
user extension's routes live under <code>ext/&lt;extension name&gt;/</code>;
built-in extensions own their paths directly. Override as an
attribute or property; handlers can reach engine state through
<code>self.citry</code>.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L719" target="_blank" rel="noopener">
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
<pre><code>validate_config_fields(fields: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>], component: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>] | None = None) -> None</code></pre>
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

class CacheExtension(Extension):
    name = &quot;cache&quot;

    def validate_config_fields(self, fields, *, component=None):
        for name in fields:
            if name != &quot;ttl&quot;:
                msg = f&quot;unknown config field {name!r}; the only field is 'ttl'&quot;
                raise ValueError(msg)
</code></pre></blockquote>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>fields</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code>

- The declared fields, mapping field name to declared value.
For a nested config class, dunder names, the <code>Config</code> base's
members, and citry's own bookkeeping attributes are already
filtered out.
</li>

<li>
<code>component</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>] | None</code>

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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L779" target="_blank" rel="noopener">
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
<pre><code>inspect_component(ctx: <a class="doc-type-link" href="/reference/component-introspection/#citry-componentintrospectioncontext">ComponentIntrospectionContext</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>] | None</code></pre>
</div>

<div class="doc-body">
<p>Publish this extension's allowlisted metadata for one component.</p>
<p>Citry calls this direct query method only when a caller explicitly
requests the extension by name. Override it together with a positive
:attr:<code>introspection_version</code>. Return an exact built-in <code>dict</code> made
only from strict JSON values, or <code>None</code> when this component has no
entry. The method must be observational, deterministic, reentrant, and
thread-safe; it must not render, load assets, mutate registration, or
depend on request state.</p>

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
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>] | None: An extension-owned JSON object, or ``None``.</p>




</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L801" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L824" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L829" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L832" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L835" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L838" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L843" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L853" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L859" target="_blank" rel="noopener">
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
<pre><code>on_component_rendered(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-oncomponentrenderedcontext">OnComponentRenderedContext</a>) -> <a class="doc-type-link" href="/reference/rendering/#citry-citryrender">CitryRender</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Called after a component (and its children) rendered. Return a new
<code>CitryRender</code> / <code>str</code> to replace the output, raise to replace the
error, or return <code>None</code> to keep the original.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L866" target="_blank" rel="noopener">
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
<p>Return a new render part (<code>str</code> or <code>CitryRender</code>) to replace the
output, or <code>None</code> to keep the original. Raising propagates.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L874" target="_blank" rel="noopener">
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
<pre><code>on_attrs_resolved(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-onattrsresolvedcontext">OnAttrsResolvedContext</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None</code></pre>
</div>

<div class="doc-body">
<p>Called after an HTML element's dynamic attributes resolved to their
final dict, before it is formatted into the output. Return a new dict
to replace the attributes, or <code>None</code> to keep them.</p>
<p>Fires per element per render, only for elements with at least one
dynamic attribute (a <code>c-*</code> value or a <code>c-bind</code> spread).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L884" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L896" target="_blank" rel="noopener">
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
<pre><code>export_render_cache(ctx: OnRenderCacheExportContext) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>]</code></pre>
</div>

<div class="doc-body">
<p>Export this payload extension's selected strict-JSON contribution.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L901" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L926" target="_blank" rel="noopener">
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
<pre><code>render_cache_bypass_reason() -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Return a stable reason when this extension requires live rendering.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L930" target="_blank" rel="noopener">
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
<pre><code>on_serialize(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-onserializecontext">OnSerializeContext</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Called at the end of <code>CitryRender.serialize()</code> with the joined HTML.</p>
<p>Return a new string to replace the output (threaded across
extensions), or <code>None</code> to keep it. This is where serialize-time
work that needs the whole page happens; the dependencies extension
places the collected JS/CSS here, using <code>ctx.placeholders</code> for the
<code>&lt;c-js&gt;</code>/<code>&lt;c-css&gt;</code> positions.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L955" target="_blank" rel="noopener">
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
<pre><code>on_template_loaded(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-ontemplateloadedcontext">OnTemplateLoadedContext</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Called once per class with the template string before it is parsed.
Return a new string to modify it.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L961" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L967" target="_blank" rel="noopener">
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
<pre><code>on_messages_loaded(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-onmessagesloadedcontext">OnMessagesLoadedContext</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Called once per source declaration with source-locale Fluent text
before compilation. A parent and children that inherit the same
messages share this one call.</p>
<p>Return a new string to replace the source. User extensions run in
installation order. The built-in i18n extension always runs after
those transformations, so it compiles the same final string the asset
loader caches.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L979" target="_blank" rel="noopener">
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
<pre><code>on_template_compiled(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-ontemplatecompiledcontext">OnTemplateCompiledContext</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[BodyItem] | None</code></pre>
</div>

<div class="doc-body">
<p>Called once per compiled body, with the generated node list. Mutate it
in place or return a new list.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L985" target="_blank" rel="noopener">
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
<pre><code>on_template_foreign_compiled(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-ontemplateforeigncompiledcontext">OnTemplateForeignCompiledContext</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[BodyItem] | None</code></pre>
</div>

<div class="doc-body">
<p>Replace this provider's claims in one independent body list.</p>
<p>The provider must call <code>ctx.mark_resolved</code> exactly once for every
claim it handles. Core verifies the ledger before general compiled
hooks run.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L997" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L1002" target="_blank" rel="noopener">
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
<pre><code>on_js_loaded(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-onjsloadedcontext">OnJsLoadedContext</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Called once per class with the component's primary JS content (inline
or read from <code>js_file</code>). Return a new string to modify it.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L1008" target="_blank" rel="noopener">
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
<pre><code>on_css_loaded(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-oncssloadedcontext">OnCssLoadedContext</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Called once per class with the component's primary CSS content (inline
or read from <code>css_file</code>). Return a new string to modify it.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L596" target="_blank" rel="noopener">
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
<p>The component back-reference is a weakref, and the component may be <code>None</code>
for extensions that run outside a component lifecycle (for example a future
Storybook extension).</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L610" target="_blank" rel="noopener">
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
<pre><code>component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">
<p>The Component class this config is defined on (bound by the manager).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L619" target="_blank" rel="noopener">
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
<p>Raises <code>RuntimeError</code> if this config runs outside a component lifecycle
(no component), or if the component has been garbage-collected.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L1094" target="_blank" rel="noopener">
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
<p>Owned by :class:<code>~citry.citry.Citry</code> and built once in its <code>__init__</code>.
Unlike DJC's module-level singleton, there is no deferred-event machinery: a
component class is bound to its <code>Citry</code> (and thus these extensions) at
definition time, so the extensions are always present when a hook fires.</p>
<p>Dispatch is <em>smart</em>: for each hook name, only the extensions that actually
override that hook are called (an extension that does not implement a hook
costs nothing). The same name-keyed dispatch underlies :meth:<code>emit</code>, which
extensions use for their own custom hooks (e.g. <code>on_dependencies</code>).</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L1114" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L1280" target="_blank" rel="noopener">
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
<pre><code>get_extension(name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="/reference/extensions/#citry-extension">Extension</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L1491" target="_blank" rel="noopener">
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
<pre><code>get_extension_command(name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, command_name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/extensions/#citry-extensioncommand">ExtensionCommand</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L1499" target="_blank" rel="noopener">
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
<pre><code>commands: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/extensions/#citry-extensioncommand">ExtensionCommand</a>], ...]]</code></pre>
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L1512" target="_blank" rel="noopener">
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
<pre><code>urls: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/web/#citry-urlroute">URLRoute</a>, ...]</code></pre>
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L1570" target="_blank" rel="noopener">
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
<pre><code>emit(name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, ctx: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>, result: _Result = &#x27;none&#x27;, field: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None = None) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code></pre>
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
<p>An extension defines <code>name</code> by overriding it (see
<code>_extensions_with_hook</code>). <code>name</code> need not be a hook declared on
:class:<code>Extension</code>, so an extension can fire its own custom hook for
others to implement.</p>
<div class="doc-examples"><p class="doc-section-title">Example</p><p>Most named hooks delegate here. <code>on_component_data</code> notifies every
extension that defines it (<code>"none"</code>)::</p>
<pre><code>manager.emit("on_component_data", ctx)
</code></pre>
<p><code>on_template_loaded</code> threads <code>ctx.content</code> through the extensions
(<code>"map"</code>) and returns the final string::</p>
<pre><code>manager.emit("on_template_loaded", ctx, result="map", field="content")
</code></pre>
<p>A custom hook can let an extension short-circuit (<code>"first"</code> returns
the first non-<code>None</code> value)::</p>
<pre><code>manager.emit("on_my_event", ctx, result="first")
</code></pre></div>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L1747" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L1753" target="_blank" rel="noopener">
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
<pre><code>on_component_class_created(component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]) -> None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L1763" target="_blank" rel="noopener">
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
<pre><code>on_component_registered(name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]) -> None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L1769" target="_blank" rel="noopener">
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
<pre><code>on_component_unregistered(name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]) -> None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L1775" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L1780" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L1796" target="_blank" rel="noopener">
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
<pre><code>on_component_data(component: <a class="doc-type-link" href="/reference/component/#citry-component">Component</a>, context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>, template_data: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>], js_data: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>], css_data: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]) -> None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L1824" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L1830" target="_blank" rel="noopener">
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
<pre><code>on_serialize(context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>, html: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, placeholders: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>], deps_strategy: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, deps_position: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, _script_security: _ScriptSecurityMaterializer | None = None, _security_csp: <a class="doc-type-link" href="/reference/citry/#citry-securitycspmode">SecurityCspMode</a> = &#x27;off&#x27;, _javascript_policy: _JavascriptPolicy | None = None, _security_javascript: <a class="doc-type-link" href="/reference/citry/#citry-securityjavascriptmode">SecurityJavascriptMode</a> = &#x27;allow&#x27;, _ownership_artifact: OwnershipManifestArtifact | None = None) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L1865" target="_blank" rel="noopener">
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
<pre><code>on_component_rendered(component: <a class="doc-type-link" href="/reference/component/#citry-component">Component</a>, render: <a class="doc-type-link" href="/reference/rendering/#citry-citryrender">CitryRender</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None, error: <a class="doc-type-link" href="https://docs.python.org/3.13/library/exceptions.html#Exception">Exception</a> | None) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/rendering/#citry-citryrender">CitryRender</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None, <a class="doc-type-link" href="https://docs.python.org/3.13/library/exceptions.html#Exception">Exception</a> | None, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a>]</code></pre>
</div>

<div class="doc-body">
<p>Thread the rendered output through the extensions; a return replaces the
render, a raise replaces the error.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L1897" target="_blank" rel="noopener">
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
<pre><code>on_slot_rendered(component: <a class="doc-type-link" href="/reference/component/#citry-component">Component</a>, slot: <a class="doc-type-link" href="/reference/slots/#citry-slot">Slot</a>, slot_name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, slot_node: <a class="doc-type-link" href="/reference/nodes/#citry-slotnode">SlotNode</a>, slot_is_required: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a>, result: RenderPart) -> RenderPart</code></pre>
</div>

<div class="doc-body">
<p>Thread a slot's rendered output through the extensions; a return
replaces the result, a raise propagates.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L1930" target="_blank" rel="noopener">
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
<pre><code>has_hook(name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Whether any installed extension implements the hook <code>name</code>.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L1941" target="_blank" rel="noopener">
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
<pre><code>has_attrs_resolved_hook(runtime_candidate: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a> = True) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Whether this element has an applicable resolved-attributes hook.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L1945" target="_blank" rel="noopener">
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
<pre><code>on_attrs_resolved(component: <a class="doc-type-link" href="/reference/component/#citry-component">Component</a>, tag_name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, attrs: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>], runtime_candidate: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a> = True) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">
<p>Thread an element's resolved attribute dict through the extensions; a
return replaces the dict, a raise propagates.</p>
<p>This sits on a per-element per-render hot path, so when no extension
implements the hook the dict is returned without building a context.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L1977" target="_blank" rel="noopener">
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
<pre><code>on_template_loaded(component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>], content: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, template_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> = &#x27;&#x27;, origin: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> = &#x27;&#x27;, template_kind: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;primary&#x27;, &#x27;standalone&#x27;, &#x27;nested&#x27;] = &#x27;primary&#x27;) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L2000" target="_blank" rel="noopener">
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
<pre><code>on_template_foreign_spans(component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>], content: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, template_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, origin: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, template_kind: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;primary&#x27;, &#x27;standalone&#x27;, &#x27;nested&#x27;], foreign_compile_contexts: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>] | None = None) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>, ...], <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a> | None]]</code></pre>
</div>

<div class="doc-body">
<p>Collect provider spans against one final post-load source string.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L2054" target="_blank" rel="noopener">
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
<pre><code>on_template_foreign_compiled(component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>], nodes: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[BodyItem], provider_metadata: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a> | None], template_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, origin: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, template_kind: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;primary&#x27;, &#x27;standalone&#x27;, &#x27;nested&#x27;]) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[BodyItem]</code></pre>
</div>

<div class="doc-body">
<p>Resolve every provider claim, one independently compiled body at a time.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L2170" target="_blank" rel="noopener">
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
<pre><code>on_messages_loaded(component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>], declaration_owner: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>, content: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, origin: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L2199" target="_blank" rel="noopener">
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
<pre><code>on_template_compiled(component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>], nodes: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[BodyItem], template_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> = &#x27;&#x27;, origin: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> = &#x27;&#x27;, template_kind: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;primary&#x27;, &#x27;standalone&#x27;, &#x27;nested&#x27;] = &#x27;primary&#x27;) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[BodyItem]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L2222" target="_blank" rel="noopener">
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
<pre><code>on_template_reset(component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]) -> None</code></pre>
</div>

<div class="doc-body">
<p>Notify extensions after a component class's template is reset.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L2231" target="_blank" rel="noopener">
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
<pre><code>on_js_loaded(component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>], content: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L2239" target="_blank" rel="noopener">
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
<pre><code>on_css_loaded(component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>], content: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L2247" target="_blank" rel="noopener">
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
<pre><code>on_files_reset(component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]) -> None</code></pre>
</div>

<div class="doc-body">
<p>Notify extensions that a component class's loaded asset files were
reset, so each drops its own per-class state (the <code>dependencies</code>
built-in drops its merged result here).</p>
<p>Deliberately not declared on the :class:<code>Extension</code> base: this is the
first consumer of the duck-typed custom-hook dispatch (an extension
subscribes by defining a method named <code>on_files_reset</code>).</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L551" target="_blank" rel="noopener">
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
<p>Subclass this, set <code>name</code> (and usually <code>help</code>), declare any <code>arguments</code>,
and define <code>handle</code> to do the work. A command that only groups
<code>subcommands</code> leaves <code>handle</code> unset, and the runner prints its help
instead of running anything. The declarations are turned into an <code>argparse</code>
parser and dispatched by :mod:<code>citry.command</code>; an extension lists its command
classes in <code>Extension.commands</code> and a user reaches one as
<code>citry ext run &lt;extension&gt; &lt;command&gt;</code>. (Extension HTTP routes are a
separate surface, <code>Extension.urls</code>.)</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L565" target="_blank" rel="noopener">
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
<pre><code>name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>The command name (<code>citry ext run &lt;extension&gt; &lt;name&gt;</code>).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L568" target="_blank" rel="noopener">
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
<pre><code>help: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>One-line description of the command, shown in <code>--help</code> output.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L571" target="_blank" rel="noopener">
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
<p>Positional arguments and options, declared with :class:<code>~citry.command.CommandArg</code>.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L574" target="_blank" rel="noopener">
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
<pre><code>subcommands: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Sequence">Sequence</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/extensions/#citry-extensioncommand">ExtensionCommand</a>]]</code></pre>
</div>

<div class="doc-body">
<p>Nested commands. A command with subcommands usually has no <code>handle</code> of its own.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L577" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L580" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L585" target="_blank" rel="noopener">
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
<p>The engine the command runs against, bound by the runner before <code>handle</code>
is called (mirrors :attr:<code>Extension.citry</code>). A command's <code>handle</code> reads it
to reach the component registry and the installed extensions.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/debug.py#L136" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/debug.py#L171" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/debug.py#L191" target="_blank" rel="noopener">
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
<pre><code>validate_config_fields(fields: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>], component: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>] | None = None) -> None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/debug.py#L206" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/debug.py#L210" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/debug.py#L215" target="_blank" rel="noopener">
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
<pre><code>render_cache_bypass_reason() -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Require live rendering while debug highlighting is enabled.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/debug.py#L226" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/debug.py#L250" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/debug.py#L261" target="_blank" rel="noopener">
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



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/debug.py#L268" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-debug-debug-on-serialize" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_serialize</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_serialize(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-onserializecontext">OnSerializeContext</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/command.py#L68" target="_blank" rel="noopener">
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
<p>Every field maps to the matching <code>add_argument</code> keyword, and
:func:<code>build_parser</code> passes them through unchanged, so the field names must
stay aligned with argparse.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/command.py#L78" target="_blank" rel="noopener">
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
<pre><code>name_or_flags: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Sequence">Sequence</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>]</code></pre>
</div>

<div class="doc-body">
<p>A positional name (<code>"path"</code>) or a list of option flags (<code>["--shout", "-s"]</code>).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/command.py#L80" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/command.py#L81" target="_blank" rel="noopener">
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
<pre><code>nargs: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;*&#x27;, &#x27;+&#x27;, &#x27;?&#x27;] | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/command.py#L82" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/command.py#L83" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/command.py#L84" target="_blank" rel="noopener">
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
<pre><code>type: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>], <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/command.py#L85" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/command.py#L86" target="_blank" rel="noopener">
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
<pre><code>required: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/command.py#L87" target="_blank" rel="noopener">
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
<pre><code>help: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/command.py#L88" target="_blank" rel="noopener">
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
<pre><code>metavar: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/command.py#L89" target="_blank" rel="noopener">
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
<pre><code>dest: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/command.py#L90" target="_blank" rel="noopener">
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
<pre><code>version: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/command.py#L92" target="_blank" rel="noopener">
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
<pre><code>to_add_argument_kwargs() -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">
<p>The <code>add_argument</code> keywords for this argument, minus <code>name_or_flags</code>.</p>
<p><code>name_or_flags</code> is passed positionally by :func:<code>build_parser</code>, so it is
not included here; unset (<code>None</code>) fields are dropped.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/command.py#L116" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/command.py#L125" target="_blank" rel="noopener">
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
<pre><code>title: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/command.py#L126" target="_blank" rel="noopener">
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
<pre><code>description: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/command.py#L127" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/command.py#L130" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/command.py#L139" target="_blank" rel="noopener">
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
<pre><code>prog: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/command.py#L140" target="_blank" rel="noopener">
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
<pre><code>help: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/command.py#L141" target="_blank" rel="noopener">
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
<pre><code>description: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/command.py#L142" target="_blank" rel="noopener">
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
<pre><code>metavar: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/command.py#L144" target="_blank" rel="noopener">
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
<pre><code>to_add_parser_kwargs() -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">
<p>The <code>add_parser</code> keywords for this subcommand entry (unset fields dropped).</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L264" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L266" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L268" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L271" target="_blank" rel="noopener">
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
<pre><code>tag_name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>The HTML tag the attributes belong to (e.g. <code>"div"</code>).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L273" target="_blank" rel="noopener">
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
<pre><code>attrs: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L399" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L401" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L153" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L155" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L157" target="_blank" rel="noopener">
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
<pre><code>component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">
<p>The created Component class.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L160" target="_blank" rel="noopener">
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
<pre><code>nested_declarations(name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/component-introspection/#citry-nestedclassdeclaration">NestedClassDeclaration</a>, ...]</code></pre>
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

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The nested declaration name, usually the extension's
<a href="/reference/extensions/#citry-extension-class-name"><code>class_name</code></a>.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/component-introspection/#citry-nestedclassdeclaration">NestedClassDeclaration</a>, ...]: The declarations from the component through its bases in C3 order.</p>




</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L212" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L214" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L216" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L218" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L224" target="_blank" rel="noopener">
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
<pre><code>template_data: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">
<p>The template variables from <code>Component.template_data()</code> (mutable).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L226" target="_blank" rel="noopener">
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
<pre><code>js_data: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">
<p>The JS variables from <code>Component.js_data()</code> (mutable). Consumed by
the built-in <code>dependencies</code> extension.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L229" target="_blank" rel="noopener">
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
<pre><code>css_data: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L200" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L202" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L204" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L206" target="_blank" rel="noopener">
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
<pre><code>kwargs: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">
<p>The keyword arguments passed to the component (mutable plain dict).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L208" target="_blank" rel="noopener">
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
<pre><code>slots: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">
<p>The slot fills passed to the component (mutable plain dict).</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L180" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L182" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L184" target="_blank" rel="noopener">
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
<pre><code>name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>The name the component was registered under.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L186" target="_blank" rel="noopener">
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
<pre><code>component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">
<p>The registered Component class.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L234" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L236" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L238" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L240" target="_blank" rel="noopener">
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
<pre><code>render: <a class="doc-type-link" href="/reference/rendering/#citry-citryrender">CitryRender</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>The rendered output, or <code>None</code> if rendering failed.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L242" target="_blank" rel="noopener">
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
<pre><code>error: <a class="doc-type-link" href="https://docs.python.org/3.13/library/exceptions.html#Exception">Exception</a> | None</code></pre>
</div>

<div class="doc-body">
<p>The error raised during rendering, or <code>None</code> if it succeeded.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L190" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L192" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L194" target="_blank" rel="noopener">
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
<pre><code>name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>The name the component was registered under.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L196" target="_blank" rel="noopener">
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
<pre><code>component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">
<p>The unregistered Component class.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L490" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L492" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L494" target="_blank" rel="noopener">
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
<pre><code>component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">
<p>The Component class whose CSS was loaded.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L496" target="_blank" rel="noopener">
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
<pre><code>content: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>The CSS content (inline or read from <code>css_file</code>).</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L86" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L88" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L90" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L500" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L502" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L504" target="_blank" rel="noopener">
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
<pre><code>component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">
<p>The Component class whose loaded asset files were reset.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L480" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L482" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L484" target="_blank" rel="noopener">
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
<pre><code>component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">
<p>The Component class whose JS was loaded.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L486" target="_blank" rel="noopener">
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
<pre><code>content: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>The JS content (inline or read from <code>js_file</code>).</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L385" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L387" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L389" target="_blank" rel="noopener">
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
<pre><code>component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">
<p>The Component class whose source messages were loaded.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L391" target="_blank" rel="noopener">
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
<pre><code>declaration_owner: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a></code></pre>
</div>

<div class="doc-body">
<p>The class that authored the inherited messages/messages_file pair.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L393" target="_blank" rel="noopener">
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
<pre><code>content: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>The source-locale Fluent text before compilation.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L395" target="_blank" rel="noopener">
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
<pre><code>origin: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>A file path or inline <code>module::Class.messages</code> label for diagnostics.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L516" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L518" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L520" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L522" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L526" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L528" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L530" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L533" target="_blank" rel="noopener">
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
<pre><code>html: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>The joined HTML (threaded: return a new string to replace it).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L535" target="_blank" rel="noopener">
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
<pre><code>placeholders: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>]</code></pre>
</div>

<div class="doc-body">
<p>The placeholder parts found during serialization: unique placeholder id
(the <code>Placeholder.key</code> plus a counter and a private serialization
identity) to the exact text standing in for it in <code>html</code>. Match the key
prefix rather than relying on the private suffix.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L540" target="_blank" rel="noopener">
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
<pre><code>deps_strategy: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>The <code>serialize(deps_strategy=...)</code> argument.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L542" target="_blank" rel="noopener">
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
<pre><code>deps_position: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>The <code>serialize(deps_position=...)</code> argument.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L246" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L248" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L250" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L252" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L254" target="_blank" rel="noopener">
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
<pre><code>slot_name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>The resolved slot name (<code>"default"</code> for an unnamed slot).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L256" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L258" target="_blank" rel="noopener">
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
<pre><code>slot_is_required: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Whether the slot resolved as required.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L260" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L343" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L347" target="_blank" rel="noopener">
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
<pre><code>start_byte: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L348" target="_blank" rel="noopener">
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
<pre><code>end_byte: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L349" target="_blank" rel="noopener">
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
<pre><code>may_control_body: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L352" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L356" target="_blank" rel="noopener">
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
<pre><code>spans: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/extensions/#citry-foreignspan">ForeignSpan</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L357" target="_blank" rel="noopener">
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
<pre><code>provider_metadata: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L360" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L364" target="_blank" rel="noopener">
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
<pre><code>provider: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Name of the extension allowed to receive this context.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L369" target="_blank" rel="noopener">
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
<pre><code>cache_fingerprint: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#bytes">bytes</a></code></pre>
</div>

<div class="doc-body">
<p>Deterministic identity for compile-time host state.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L374" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L376" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L377" target="_blank" rel="noopener">
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
<pre><code>component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L378" target="_blank" rel="noopener">
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
<pre><code>content: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L379" target="_blank" rel="noopener">
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
<pre><code>template_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L380" target="_blank" rel="noopener">
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
<pre><code>origin: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L381" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L382" target="_blank" rel="noopener">
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
<pre><code>compile_context: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L405" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L407" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L409" target="_blank" rel="noopener">
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
<pre><code>component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">
<p>The Component class whose template was compiled.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L411" target="_blank" rel="noopener">
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
<pre><code>nodes: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[BodyItem]</code></pre>
</div>

<div class="doc-body">
<p>The generated body node list.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L413" target="_blank" rel="noopener">
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
<pre><code>template_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Immutable identity of the exact template record being compiled.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L415" target="_blank" rel="noopener">
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
<pre><code>origin: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Authored source origin used for diagnostics.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L417" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L420" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L424" target="_blank" rel="noopener">
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
<pre><code>provider: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L425" target="_blank" rel="noopener">
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
<pre><code>ordinal: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L426" target="_blank" rel="noopener">
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
<pre><code>source: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L427" target="_blank" rel="noopener">
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
<pre><code>position: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L428" target="_blank" rel="noopener">
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
<pre><code>may_control_body: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L429" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L432" target="_blank" rel="noopener">
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
<pre><code>claim_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L436" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L440" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L441" target="_blank" rel="noopener">
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
<pre><code>component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L442" target="_blank" rel="noopener">
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
<pre><code>nodes: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[BodyItem]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L443" target="_blank" rel="noopener">
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
<pre><code>claims: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/extensions/#citry-foreignclaim">ForeignClaim</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L444" target="_blank" rel="noopener">
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
<pre><code>provider_metadata: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L445" target="_blank" rel="noopener">
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
<pre><code>template_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L446" target="_blank" rel="noopener">
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
<pre><code>origin: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L447" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L450" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L462" target="_blank" rel="noopener">
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
<pre><code>compiled_body(nodes: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[BodyItem]) -> <a class="doc-type-link" href="/reference/rendering/#citry-compiledbody">CompiledBody</a></code></pre>
</div>

<div class="doc-body">
<p>Compile and protect one Citry run for later host-selected rendering.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L328" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L330" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L332" target="_blank" rel="noopener">
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
<pre><code>component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">
<p>The Component class whose template was loaded.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L334" target="_blank" rel="noopener">
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
<pre><code>content: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>The template string (before parsing).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L336" target="_blank" rel="noopener">
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
<pre><code>template_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Immutable identity of this loaded template record.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L338" target="_blank" rel="noopener">
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
<pre><code>origin: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Source origin used for diagnostics.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L340" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L508" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L510" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L512" target="_blank" rel="noopener">
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
<pre><code>component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">
<p>The Component class whose loaded template was reset.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L118" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L122" target="_blank" rel="noopener">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L124" target="_blank" rel="noopener">
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
<pre><code>component_class: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">
<p>The temporary live component class from the registry snapshot.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L128" target="_blank" rel="noopener">
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

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>]</code>

- Variable names mapped to annotations, using the
same format as <a href="/reference/citry/#citry-lintsettings-template-variables"><code>LintSettings.template_variables</code></a>.
</li>

<li>
<code>allows_extra_variables</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code>

- Whether this extension intentionally preserves
additional names that it cannot enumerate. Such unknown names are
linted as warnings, never silently accepted.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L142" target="_blank" rel="noopener">
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
<pre><code>template_variables: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/extension.py#L143" target="_blank" rel="noopener">
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
<pre><code>allows_extra_variables: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>



