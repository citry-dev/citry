---
title: Internationalization
url: https://citry.dev/v/0.4.4/reference/internationalization/
description: "Locale contexts, messages, named formats, and strict localized-input parsers."
---
# Internationalization

Locale contexts, messages, named formats, and strict localized-input parsers.




<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/api.py#L14" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-i18n-make-context" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>make_context</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>make_context(app: <a class="doc-type-link" href="/reference/citry/#citry-citry">Citry</a>, locale: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None = None, time_zone: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None = None) -> <a class="doc-type-link" href="/reference/internationalization/#citry-localecontext">LocaleContext</a></code></pre>
</div>

<div class="doc-body">
<p>Create a locale context for one Citry application.</p>
<p>The application argument keeps the owning engine explicit while hiding
the extension-registry lookup needed to reach its i18n extension. The
returned context does not change application, task, or process state.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><pre><code class="language-python">from citry.ext.i18n import make_context

context = make_context(app, locale=request.locale)
html = Page().render(provides={&quot;citry_i18n&quot;: context})
</code></pre></blockquote>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>app</code>

<code><a class="doc-type-link" href="/reference/citry/#citry-citry">Citry</a></code>

- The Citry application that owns the i18n configuration.
</li>

<li>
<code>locale</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- A configured or inferred source locale, or <code>None</code> to use the
configured or inferred default locale.
</li>

<li>
<code>time_zone</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- An IANA time-zone name, or <code>None</code> for a zone-free context.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="/reference/internationalization/#citry-localecontext">LocaleContext</a>: A validated immutable locale context for that application.</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>I18nNotConfiguredError</code> - The application has neither i18n settings nor
registered component messages.
</li>

<li>
<code>ValueError</code> - A locale or time-zone value is invalid or unavailable.
</li>

</ul>



</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L842" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-i18n-i18nextension" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>I18nExtension</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/extensions/#citry-extension">Extension</a></code></p>


<div class="doc-body">
<p>Own one application's catalog graph, profiles, and locale contexts.</p>
<p>Registered component messages activate the server catalog in source mode.
Explicit engine settings additionally activate selectable locales, catalog
packages, named profiles, parsing, and browser delivery.</p>
<p>Application code normally obtains this built-in extension from
<code>app.extensions.get_extension("i18n")</code>. Create a context with
<a href="/reference/internationalization/#citry-ext-i18n-make-context"><code>make_context()</code></a>, pass it through root
<code>render(provides={"citry_i18n": context})</code>, and use
<code>for_context()</code> outside components.
Components receive the same operations through <code>self.i18n</code>.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L858" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-name" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L859" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-config" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L860" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-commands" class="doc-heading">
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






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L861" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-render-cache-mode" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L862" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-render-cache-version" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L879" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-configured" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>configured</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>configured: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Return whether the engine supplied the required i18n settings.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L884" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-available" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>available</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>available: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Return whether settings or registered component messages provide server i18n.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L891" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-config-2" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>config</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>config: I18nEngineConfig</code></pre>
</div>

<div class="doc-body">
<p>Return the validated immutable engine configuration.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L896" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-catalog-revision" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>catalog_revision</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>catalog_revision: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>The current checked catalog graph revision.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L903" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-urls" class="doc-heading">
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
<p>Serve the browser runtime and exact message-partition endpoint.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L912" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-context" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>context</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>context: <a class="doc-type-link" href="/reference/internationalization/#citry-localecontext">LocaleContext</a></code></pre>
</div>

<div class="doc-body">
<p>Build a fresh context for the configured or inferred source locale.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L918" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-context-for-component" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>context_for_component</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>context_for_component(component: <a class="doc-type-link" href="/reference/component/#citry-component">Component</a>) -> <a class="doc-type-link" href="/reference/internationalization/#citry-localecontext">LocaleContext</a></code></pre>
</div>

<div class="doc-body">
<p>Return the exact context provided to a component, or the default.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L929" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-format-for-component" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>format_for_component</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>format_for_component(component: <a class="doc-type-link" href="/reference/component/#citry-component">Component</a>, usage: I18nUsageCollector | None = None) -> <a class="doc-type-link" href="/reference/internationalization/#citry-i18nformatter">I18nFormatter</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L939" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-parse-for-component" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>parse_for_component</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>parse_for_component(component: <a class="doc-type-link" href="/reference/component/#citry-component">Component</a>, usage: I18nUsageCollector | None = None) -> <a class="doc-type-link" href="/reference/internationalization/#citry-i18nparser">I18nParser</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L949" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-for-context" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>for_context</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>for_context(context: <a class="doc-type-link" href="/reference/internationalization/#citry-localecontext">LocaleContext</a>) -> <a class="doc-type-link" href="/reference/internationalization/#citry-i18nservice">I18nService</a></code></pre>
</div>

<div class="doc-body">
<p>Return the complete i18n service bound to one explicit context.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>context</code>

<code><a class="doc-type-link" href="/reference/internationalization/#citry-localecontext">LocaleContext</a></code>

- The locale, direction, time zone, and catalog revisions
that every operation must use.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="/reference/internationalization/#citry-i18nservice">I18nService</a>: Translation, resolution, formatting, and parsing operations that</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>I18nNotConfiguredError</code> - The engine has no i18n configuration.
</li>

<li>
<code>TypeError</code> - <code>context</code> is not an exact <a href="/reference/internationalization/#citry-localecontext"><code>LocaleContext</code></a>.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L1038" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-validate-config-fields" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L1050" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-on-extension-created" class="doc-heading">
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






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L1080" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-on-messages-loaded" class="doc-heading">
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






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L1089" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-on-files-reset" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_files_reset</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_files_reset(_ctx: <a class="doc-type-link" href="/reference/extensions/#citry-onfilesresetcontext">OnFilesResetContext</a>) -> None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L1095" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-on-component-registered" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L1111" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-on-component-unregistered" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L1116" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-on-citry-cleared" class="doc-heading">
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






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L1128" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-inspect-template-namespace" class="doc-heading">
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






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L1146" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-on-component-data" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L1187" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-on-template-compiled" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_template_compiled</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_template_compiled(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-ontemplatecompiledcontext">OnTemplateCompiledContext</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">
<p>Install render-time wrappers for direct, dynamic, and spread <code>$c-tr</code>.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L1193" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-on-component-rendered" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_component_rendered</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_component_rendered(ctx: <a class="doc-type-link" href="/reference/extensions/#citry-oncomponentrenderedcontext">OnComponentRenderedContext</a>) -> None</code></pre>
</div>

<div class="doc-body">
<p>Seal checked binding metadata after the complete component body rendered.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L1269" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-on-render-context-merge" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L1275" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-on-dependencies" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_dependencies</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_dependencies(ctx: <a class="doc-type-link" href="/reference/dependencies/#citry-ext-dependencies-ondependenciescontext">OnDependenciesContext</a>) -> None</code></pre>
</div>

<div class="doc-body">
<p>Emit browser i18n only for a client-enabled provider subtree.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L1281" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-export-render-cache" class="doc-heading">
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
<p>Detach i18n metadata for the selected cached subtree.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L1305" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-stage-render-cache" class="doc-heading">
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
<p>Validate cached i18n metadata and bind it to fresh render IDs.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L1767" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-make-context" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>make_context</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>make_context(locale: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None = None, time_zone: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None = None) -> <a class="doc-type-link" href="/reference/internationalization/#citry-localecontext">LocaleContext</a></code></pre>
</div>

<div class="doc-body">
<p>Build one validated locale context without changing shared state.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>locale</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- An allowed configured/source locale, or <code>None</code> for the
configured or inferred default locale.
</li>

<li>
<code>time_zone</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- An IANA time-zone name, or <code>None</code> for a zone-free context.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="/reference/internationalization/#citry-localecontext">LocaleContext</a>: A new immutable context carrying the current catalog and profile revisions.</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>I18nNotConfiguredError</code> - The extension has neither settings nor
registered component message sources.
</li>

<li>
<code>ValueError</code> - The locale or time zone is invalid or unavailable.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L1797" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-browser-artifact" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>browser_artifact</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>browser_artifact(locale: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, outputs: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[MessageOutputUse, ...] | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, ...], messages: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, ...]) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>]</code></pre>
</div>

<div class="doc-body">
<p>Compile one exact browser catalog partition from checked roots.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L1827" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-browser-parser-artifact" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>browser_parser_artifact</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>browser_parser_artifact(locale: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>]</code></pre>
</div>

<div class="doc-body">
<p>Build locale-specific records for the checked browser parsers.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L1838" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-tr" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>tr</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>tr(message_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, attr: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None = None, context: <a class="doc-type-link" href="/reference/internationalization/#citry-localecontext">LocaleContext</a> | None = None, **values: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a> = {}) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Resolve one message or attribute to plain text.</p>
<p>Prefer <code>for_context(context).tr(...)</code> outside components so the locale
dependency stays explicit. Omitting <code>context</code> here uses a new default
context and is mainly useful for tooling and simple startup checks.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L1855" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-resolve" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>resolve</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>resolve(message_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, attr: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None = None, context: <a class="doc-type-link" href="/reference/internationalization/#citry-localecontext">LocaleContext</a> | None = None, **values: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a> = {}) -> <a class="doc-type-link" href="/reference/internationalization/#citry-localizedtext">LocalizedText</a></code></pre>
</div>

<div class="doc-body">
<p>Resolve one message and retain its selected locale and fallback data.</p>
<p><code>message_id</code> and <code>attr</code> must name a public checked output. <code>values</code>
must match that output's <code>@param</code> interface exactly. The supplied
context must still carry the current catalog revision.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L1910" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-i18n-i18nextension-resolve-rich" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>resolve_rich</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>resolve_rich(message_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, values: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>], slots: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>], attr: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None = None, context: <a class="doc-type-link" href="/reference/internationalization/#citry-localecontext">LocaleContext</a> | None = None) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>]</code></pre>
</div>

<div class="doc-body">
<p>Resolve one rich message to escaped text records and named Slot parts.</p>
<p>This is the lower-level operation used by <code>&lt;c-trans&gt;</code>. Application code
should normally use that component so fills retain their Citry scope
and ownership.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/config.py#L29" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-i18n" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>I18n</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/extensions/#citry-extensionconfig">ExtensionConfig</a></code></p>


<div class="doc-body">
<p>Per-component i18n settings and access to the provided locale context.</p>
<p>Set <code>Component.I18n.messages_locale</code> to the locale in which that
component's <code>messages</code> / <code>messages_file</code> source is authored. Declaring a
message asset activates server translations even when the engine has no
i18n settings. Declare <code>client_messages</code> only for finite dynamic message
IDs that static browser analysis cannot see. Instances expose the nearest
explicit context, translation, formatting, and parsing through <code>self.i18n</code>.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/config.py#L41" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18n-messages-locale" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>messages_locale</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>messages_locale: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/config.py#L42" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18n-client-messages" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>client_messages</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>client_messages: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/config.py#L73" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18n-configured" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>configured</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>configured: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Return whether this component's engine has explicit i18n settings.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/config.py#L78" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18n-available" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>available</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>available: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Return whether server translation is available from settings or component messages.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/config.py#L83" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18n-context" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>context</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>context: <a class="doc-type-link" href="/reference/internationalization/#citry-localecontext">LocaleContext</a></code></pre>
</div>

<div class="doc-body">
<p>Return the explicit locale context provided to this component tree.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/config.py#L91" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18n-tr" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>tr</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>tr(message_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, attr: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None = None, **values: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a> = {}) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Resolve one message or attribute to plain text.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/config.py#L103" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18n-resolve" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>resolve</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>resolve(message_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, attr: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None = None, **values: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a> = {}) -> <a class="doc-type-link" href="/reference/internationalization/#citry-localizedtext">LocalizedText</a></code></pre>
</div>

<div class="doc-body">
<p>Resolve text and keep the selected locale and fallback metadata.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/config.py#L115" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18n-format" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>format</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>format: <a class="doc-type-link" href="/reference/internationalization/#citry-i18nformatter">I18nFormatter</a></code></pre>
</div>

<div class="doc-body">
<p>Return named formatter operations bound to this component context.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/config.py#L120" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18n-parse" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>parse</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>parse: <a class="doc-type-link" href="/reference/internationalization/#citry-i18nparser">I18nParser</a></code></pre>
</div>

<div class="doc-body">
<p>Return strict parser operations bound to this component context.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L770" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-i18nservice" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>I18nService</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Use messages, formatting, and parsing with one explicit locale context.</p>
<p>Create this service with
<code>I18nExtension.for_context</code>. Components
receive the same operations through <a href="/reference/component/#citry-component-i18n-2"><code>Component.i18n</code></a>.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>context</code>

<code><a class="doc-type-link" href="/reference/internationalization/#citry-localecontext">LocaleContext</a></code>

- The exact locale context used by every operation.
</li>

<li>
<code>format</code>

<code><a class="doc-type-link" href="/reference/internationalization/#citry-i18nformatter">I18nFormatter</a></code>

- Named formatting operations bound to <code>context</code>.
</li>

<li>
<code>parse</code>

<code><a class="doc-type-link" href="/reference/internationalization/#citry-i18nparser">I18nParser</a></code>

- Strict parsing operations bound to <code>context</code>.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L792" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18nservice-configured" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>configured</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>configured: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Return whether the owning engine configured i18n.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L797" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18nservice-available" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>available</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>available: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Return whether settings or component messages provide server i18n.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L802" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18nservice-context" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>context</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>context: <a class="doc-type-link" href="/reference/internationalization/#citry-localecontext">LocaleContext</a></code></pre>
</div>

<div class="doc-body">
<p>Return the exact locale context bound to this service.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L806" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18nservice-tr" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>tr</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>tr(message_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, attr: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None = None, **values: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a> = {}) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Resolve one message to plain text with the bound context.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L810" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18nservice-resolve" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>resolve</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>resolve(message_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, attr: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None = None, **values: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a> = {}) -> <a class="doc-type-link" href="/reference/internationalization/#citry-localizedtext">LocalizedText</a></code></pre>
</div>

<div class="doc-body">
<p>Resolve text and retain its selected locale and fallback metadata.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L815" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18nservice-format" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>format</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>format: <a class="doc-type-link" href="/reference/internationalization/#citry-i18nformatter">I18nFormatter</a></code></pre>
</div>

<div class="doc-body">
<p>Return the named formatter operations bound to this context.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L820" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18nservice-parse" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>parse</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>parse: <a class="doc-type-link" href="/reference/internationalization/#citry-i18nparser">I18nParser</a></code></pre>
</div>

<div class="doc-body">
<p>Return the strict parser operations bound to this context.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L553" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-i18nformatter" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>I18nFormatter</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Format canonical values with one component or locale context.</p>
<p>Citry creates this object for <a href="/reference/internationalization/#citry-i18n-format"><code>I18n.format</code></a> and
<a href="/reference/internationalization/#citry-i18nservice-format"><code>I18nService.format</code></a>. Application code should
use those entry points rather than constructing it directly.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L582" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18nformatter-number" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>number</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>number(value: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/decimal.html#decimal.Decimal">Decimal</a>, format: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Format an exact integer or decimal with a named number profile.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L588" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18nformatter-percent" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>percent</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>percent(value: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/decimal.html#decimal.Decimal">Decimal</a>, format: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Format an exact ratio with a named percent profile.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L594" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18nformatter-currency" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>currency</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>currency(value: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/decimal.html#decimal.Decimal">Decimal</a>, currency: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, format: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Format an exact value and ISO 4217 code with a currency profile.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L605" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18nformatter-date" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>date</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>date(value: date, format: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Format a calendar date with a named date profile.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L611" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18nformatter-time" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>time</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>time(value: <a class="doc-type-link" href="https://docs.python.org/3.13/library/time.html#module-time">time</a>, format: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Format a zone-free wall-clock time with a named profile.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L617" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18nformatter-datetime" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>datetime</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>datetime(value: <a class="doc-type-link" href="https://docs.python.org/3.13/library/datetime.html#module-datetime">datetime</a>, format: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Format an aware instant in the context's explicit time zone.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L623" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18nformatter-relative-time" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>relative_time</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>relative_time(value: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/decimal.html#decimal.Decimal">Decimal</a>, unit: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, format: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Format an exact relative value with a named relative-time profile.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L634" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18nformatter-list" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>list</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>list(values: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>, format: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Format non-empty strings as a localized conjunction or disjunction.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L640" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18nformatter-unit" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>unit</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>unit(value: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/decimal.html#decimal.Decimal">Decimal</a>, unit: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, format: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Format an exact value with an explicit CLDR unit identifier.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L661" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-i18nparser" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>I18nParser</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Parse localized edits with one component or locale context.</p>
<p>Citry creates this object for <a href="/reference/internationalization/#citry-i18n-parse"><code>I18n.parse</code></a> and
<a href="/reference/internationalization/#citry-i18nservice-parse"><code>I18nService.parse</code></a>. Application code should
use those entry points rather than constructing it directly.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L690" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18nparser-number" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>number</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>number(input: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, format: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="/reference/internationalization/#citry-numberparseresult">NumberParseResult</a></code></pre>
</div>

<div class="doc-body">
<p>Parse one strict localized number edit into an exact decimal.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L696" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18nparser-percent" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>percent</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>percent(input: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, format: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="/reference/internationalization/#citry-percentparseresult">PercentParseResult</a></code></pre>
</div>

<div class="doc-body">
<p>Parse one strict localized percent edit into its exact ratio.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L702" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18nparser-date" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>date</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>date(input: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, format: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="/reference/internationalization/#citry-dateparseresult">DateParseResult</a></code></pre>
</div>

<div class="doc-body">
<p>Parse one strict localized date string with a text-input profile.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L708" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18nparser-date-segments" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>date_segments</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>date_segments(input: <a class="doc-type-link" href="/reference/internationalization/#citry-datesegments">DateSegments</a>, format: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="/reference/internationalization/#citry-dateparseresult">DateParseResult</a></code></pre>
</div>

<div class="doc-body">
<p>Parse named date fields with a segmented-input profile.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L714" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18nparser-time" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>time</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>time(input: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, format: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="/reference/internationalization/#citry-timeparseresult">TimeParseResult</a></code></pre>
</div>

<div class="doc-body">
<p>Parse one strict localized wall-clock time string.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L720" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18nparser-time-segments" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>time_segments</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>time_segments(input: <a class="doc-type-link" href="/reference/internationalization/#citry-timesegments">TimeSegments</a>, format: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="/reference/internationalization/#citry-timeparseresult">TimeParseResult</a></code></pre>
</div>

<div class="doc-body">
<p>Parse named wall-clock fields with a segmented-input profile.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L726" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18nparser-datetime" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>datetime</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>datetime(input: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, format: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, fold: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None = None) -> <a class="doc-type-link" href="/reference/internationalization/#citry-datetimeparseresult">DateTimeParseResult</a></code></pre>
</div>

<div class="doc-body">
<p>Parse local datetime text and resolve it through the context time zone.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/extension.py#L743" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-i18nparser-datetime-segments" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>datetime_segments</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>datetime_segments(input: <a class="doc-type-link" href="/reference/internationalization/#citry-datetimesegments">DateTimeSegments</a>, format: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, fold: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None = None) -> <a class="doc-type-link" href="/reference/internationalization/#citry-datetimeparseresult">DateTimeParseResult</a></code></pre>
</div>

<div class="doc-body">
<p>Parse named local datetime fields and resolve an explicit DST fold.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L13" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-localecontext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>LocaleContext</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>All explicit render inputs that can change localized output.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>locale</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The selected canonical locale.
</li>

<li>
<code>fallback_locales</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, ...]</code>

- The ordered configured fallback chain.
</li>

<li>
<code>direction</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;ltr&#x27;, &#x27;rtl&#x27;]</code>

- The writing direction used by the render subtree.
</li>

<li>
<code>time_zone</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- The explicit IANA time zone, or <code>None</code> for zone-free work.
</li>

<li>
<code>tzdb_revision</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The exact time-zone data revision.
</li>

<li>
<code>catalog_revision</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The exact checked message graph revision.
</li>

<li>
<code>formats_revision</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The exact named-profile registry revision.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L29" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-localecontext-locale" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>locale</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>locale: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L30" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-localecontext-fallback-locales" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>fallback_locales</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>fallback_locales: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L31" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-localecontext-direction" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>direction</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>direction: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;ltr&#x27;, &#x27;rtl&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L32" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-localecontext-time-zone" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>time_zone</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>time_zone: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L33" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-localecontext-tzdb-revision" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>tzdb_revision</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>tzdb_revision: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L34" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-localecontext-catalog-revision" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>catalog_revision</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>catalog_revision: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L35" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-localecontext-formats-revision" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>formats_revision</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>formats_revision: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L38" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-localecontext-identity" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>identity</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>identity: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>, ...]</code></pre>
</div>

<div class="doc-body">
<p>Plain immutable data that identifies every input to localized output.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L53" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-localizedtext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>LocalizedText</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Resolved text plus the locale metadata needed by semantic wrappers.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>text</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The formatted message text.
</li>

<li>
<code>locale</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The locale that supplied the selected pattern.
</li>

<li>
<code>direction</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;ltr&#x27;, &#x27;rtl&#x27;]</code>

- The selected pattern's writing direction.
</li>

<li>
<code>used_fallback</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code>

- Whether resolution used a locale other than the request.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L66" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-localizedtext-text" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>text</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>text: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L67" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-localizedtext-locale" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>locale</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>locale: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L68" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-localizedtext-direction" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>direction</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>direction: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;ltr&#x27;, &#x27;rtl&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L69" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-localizedtext-used-fallback" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>used_fallback</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>used_fallback: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L296" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-formatregistry" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>FormatRegistry</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Store the application's named formatter profiles.</p>
<p>The profile names are application-defined. Each value uses one of Citry's
checked profile types so the Rust server and browser can share the same
contract.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><p>Give call sites names that describe why they format a value::</p>
<pre><code>formats = FormatRegistry(
    number={
        "measurement": NumberFormat(),
    },
    date={
        "invoice-date": DateFormat(
            length="long",
        ),
    },
)

# Inside a component:
text = self.i18n.format.number(
    meters,
    format="measurement",
)
</code></pre></blockquote>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>number</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="/reference/internationalization/#citry-numberformat">NumberFormat</a>]</code>

- Exact-decimal number profiles.
</li>

<li>
<code>percent</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="/reference/internationalization/#citry-percentformat">PercentFormat</a>]</code>

- Ratio-based percent profiles and their input rules.
</li>

<li>
<code>currency</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="/reference/internationalization/#citry-currencyformat">CurrencyFormat</a>]</code>

- Currency profiles.
</li>

<li>
<code>date</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="/reference/internationalization/#citry-dateformat">DateFormat</a>]</code>

- Calendar-date profiles.
</li>

<li>
<code>time</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="/reference/internationalization/#citry-timeformat">TimeFormat</a>]</code>

- Wall-clock time profiles.
</li>

<li>
<code>datetime</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="/reference/internationalization/#citry-datetimeformat">DateTimeFormat</a>]</code>

- Instant and time-zone profiles.
</li>

<li>
<code>relative_time</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="/reference/internationalization/#citry-relativetimeformat">RelativeTimeFormat</a>]</code>

- Relative-time profiles.
</li>

<li>
<code>list</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="/reference/internationalization/#citry-listformat">ListFormat</a>]</code>

- Conjunction and disjunction list profiles.
</li>

<li>
<code>unit</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="/reference/internationalization/#citry-unitformat">UnitFormat</a>]</code>

- Standalone measurement-unit profiles.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L338" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-formatregistry-number" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>number</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>number: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="/reference/internationalization/#citry-numberformat">NumberFormat</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L339" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-formatregistry-percent" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>percent</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>percent: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="/reference/internationalization/#citry-percentformat">PercentFormat</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L340" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-formatregistry-currency" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>currency</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>currency: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="/reference/internationalization/#citry-currencyformat">CurrencyFormat</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L341" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-formatregistry-date" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>date</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>date: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="/reference/internationalization/#citry-dateformat">DateFormat</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L342" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-formatregistry-time" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>time</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>time: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="/reference/internationalization/#citry-timeformat">TimeFormat</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L343" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-formatregistry-datetime" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>datetime</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>datetime: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="/reference/internationalization/#citry-datetimeformat">DateTimeFormat</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L344" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-formatregistry-relative-time" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>relative_time</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>relative_time: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="/reference/internationalization/#citry-relativetimeformat">RelativeTimeFormat</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L345" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-formatregistry-list" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>list</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>list: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="/reference/internationalization/#citry-listformat">ListFormat</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L346" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-formatregistry-unit" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>unit</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>unit: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="/reference/internationalization/#citry-unitformat">UnitFormat</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L383" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-formatregistry-to-wire" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>to_wire</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>to_wire() -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>]]]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L437" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-formatregistry-revision" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>revision</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>revision: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L52" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-numberformat" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>NumberFormat</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Use ICU4X's locale-default exact-decimal format and input grammar.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L56" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-numberformat-input" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>input</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>input: <a class="doc-type-link" href="/reference/internationalization/#citry-numberinput">NumberInput</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L39" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-numberinput" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>NumberInput</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Declare the strict notation accepted by a named number profile.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L43" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-numberinput-notation" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>notation</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>notation: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;decimal&#x27;, &#x27;decimal_or_scientific&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L72" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-numberparseresult" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>NumberParseResult</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>One strict localized number edit without losing unfinished text.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>input</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The exact user edit.
</li>

<li>
<code>state</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;valid&#x27;, &#x27;incomplete&#x27;, &#x27;invalid&#x27;]</code>

- <code>valid</code>, <code>incomplete</code>, or <code>invalid</code>.
</li>

<li>
<code>value</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/decimal.html#decimal.Decimal">Decimal</a> | None</code>

- The canonical exact decimal when valid.
</li>

<li>
<code>error</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- A stable explanation for an invalid result, otherwise <code>None</code>.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L85" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-numberparseresult-input" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>input</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>input: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L86" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-numberparseresult-state" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>state</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>state: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;valid&#x27;, &#x27;incomplete&#x27;, &#x27;invalid&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L87" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-numberparseresult-value" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>value</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>value: <a class="doc-type-link" href="https://docs.python.org/3.13/library/decimal.html#decimal.Decimal">Decimal</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L88" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-numberparseresult-error" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>error</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>error: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L91" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-numberparseresult-valid" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>valid</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>valid: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Return whether the edit contains one complete canonical number.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L82" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-percentformat" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>PercentFormat</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Format a canonical ratio and optionally accept localized percent edits.</p>
<p>A value of <code>Decimal("0.125")</code> represents 12.5 percent. Parsing returns
the same ratio domain value.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>input</code>

<code><a class="doc-type-link" href="/reference/internationalization/#citry-percentinput">PercentInput</a></code>

- The strict editing rule used by <code>i18n.parse.percent()</code>.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L95" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-percentformat-input" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>input</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>input: <a class="doc-type-link" href="/reference/internationalization/#citry-percentinput">PercentInput</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L63" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-percentinput" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>PercentInput</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Choose whether a percent edit includes the locale's percent affix.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>affix</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;required&#x27;, &#x27;omit&#x27;]</code>

- <code>"required"</code> accepts the same affix that formatting emits.
<code>"omit"</code> accepts only the localized number, which is useful when
a control renders the affix outside its editable field.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L75" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-percentinput-affix" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>affix</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>affix: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;required&#x27;, &#x27;omit&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L96" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-percentparseresult" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>PercentParseResult</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Keep one localized percent edit and its canonical ratio separate.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>input</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The exact user edit.
</li>

<li>
<code>state</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;valid&#x27;, &#x27;incomplete&#x27;, &#x27;invalid&#x27;]</code>

- <code>valid</code>, <code>incomplete</code>, or <code>invalid</code>.
</li>

<li>
<code>value</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/decimal.html#decimal.Decimal">Decimal</a> | None</code>

- The canonical ratio when valid; <code>0.125</code> means 12.5 percent.
</li>

<li>
<code>error</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- A stable explanation for an invalid result, otherwise <code>None</code>.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L109" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-percentparseresult-input" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>input</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>input: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L110" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-percentparseresult-state" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>state</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>state: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;valid&#x27;, &#x27;incomplete&#x27;, &#x27;invalid&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L111" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-percentparseresult-value" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>value</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>value: <a class="doc-type-link" href="https://docs.python.org/3.13/library/decimal.html#decimal.Decimal">Decimal</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L112" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-percentparseresult-error" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>error</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>error: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L115" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-percentparseresult-valid" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>valid</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>valid: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Return whether the edit contains one complete percent value.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L102" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-currencyformat" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>CurrencyFormat</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Use ICU4X's checked locale-default currency format.</p>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L132" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-dateformat" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>DateFormat</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Format a date and optionally accept input through the same profile.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>fields</code>

<code><a class="doc-type-link" href="/reference/internationalization/#citry-dateformatfields">DateFormatFields</a></code>

- The exact calendar fields included in display output.
</li>

<li>
<code>length</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;short&#x27;, &#x27;medium&#x27;, &#x27;long&#x27;]</code>

- The locale-sensitive display length.
</li>

<li>
<code>input</code>

<code><a class="doc-type-link" href="/reference/internationalization/#citry-dateinput">DateInput</a> | None</code>

- The strict editing rule. <code>None</code> keeps the profile display-only.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L144" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-dateformat-fields" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>fields</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>fields: <a class="doc-type-link" href="/reference/internationalization/#citry-dateformatfields">DateFormatFields</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L145" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-dateformat-length" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>length</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>length: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;short&#x27;, &#x27;medium&#x27;, &#x27;long&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L146" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-dateformat-input" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>input</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>input: <a class="doc-type-link" href="/reference/internationalization/#citry-dateinput">DateInput</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L12" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-dateformatfields" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>DateFormatFields</code>
</span>
<span class="doc-kind">attribute</span>
</h2>


<div class="doc-body">






</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L107" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-dateinput" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>DateInput</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Declare how a named date profile accepts editable input.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>mode</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;strict_text&#x27;, &#x27;segments&#x27;]</code>

- <code>"strict_text"</code> accepts one localized date string.
<code>"segments"</code> accepts named year, month, and day edit segments.
</li>

<li>
<code>two_digit_year_start</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | None</code>

- The first year in the selected calendar's
explicit 100-year window. <code>None</code> requires a full year.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L120" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-dateinput-mode" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>mode</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>mode: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;strict_text&#x27;, &#x27;segments&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L121" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-dateinput-two-digit-year-start" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>two_digit_year_start</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>two_digit_year_start: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L120" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-datesegments" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>DateSegments</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Hold the three editable fields from a segmented date control.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>year</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The localized calendar-year edit.
</li>

<li>
<code>month</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The localized numeric month edit.
</li>

<li>
<code>day</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The localized day-of-month edit.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L132" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-datesegments-year" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>year</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>year: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L133" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-datesegments-month" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>month</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>month: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L134" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-datesegments-day" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>day</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>day: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L143" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-dateparseresult" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>DateParseResult</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Keep one localized date edit and its canonical Python date separate.</p>
<p><code>ambiguous</code> reports an input that needs an explicit calendar decision.
<code>valid</code> is the only state with a canonical <code>value</code>.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L152" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-dateparseresult-input" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>input</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>input: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="/reference/internationalization/#citry-datesegments">DateSegments</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L153" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-dateparseresult-state" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>state</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>state: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;valid&#x27;, &#x27;incomplete&#x27;, &#x27;invalid&#x27;, &#x27;ambiguous&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L154" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-dateparseresult-value" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>value</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>value: <a class="doc-type-link" href="https://docs.python.org/3.13/library/datetime.html#datetime.date">date</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L155" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-dateparseresult-error" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>error</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>error: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L158" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-dateparseresult-valid" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>valid</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>valid: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Return whether the edit contains one complete calendar date.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L175" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-timeformat" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>TimeFormat</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Format a wall-clock time and optionally accept localized edits.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>length</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;short&#x27;, &#x27;medium&#x27;, &#x27;long&#x27;]</code>

- The locale-sensitive display length.
</li>

<li>
<code>input</code>

<code><a class="doc-type-link" href="/reference/internationalization/#citry-timeinput">TimeInput</a> | None</code>

- The strict editing rule. <code>None</code> keeps the profile display-only.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L186" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-timeformat-length" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>length</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>length: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;short&#x27;, &#x27;medium&#x27;, &#x27;long&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L187" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-timeformat-input" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>input</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>input: <a class="doc-type-link" href="/reference/internationalization/#citry-timeinput">TimeInput</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L159" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-timeinput" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>TimeInput</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Declare how a named wall-clock time profile accepts editable input.</p>
<p><code>strict_text</code> accepts one locale-shaped string. <code>segments</code> accepts a
<a href="/reference/internationalization/#citry-timesegments"><code>TimeSegments</code></a> value from a segmented control.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L168" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-timeinput-mode" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>mode</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>mode: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;strict_text&#x27;, &#x27;segments&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L163" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-timesegments" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>TimeSegments</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Hold editable fields from a segmented wall-clock time control.</p>
<p><code>second</code> and <code>day_period</code> are optional because the named profile decides
whether those fields are present.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L172" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-timesegments-hour" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>hour</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>hour: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L173" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-timesegments-minute" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>minute</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>minute: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L174" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-timesegments-second" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>second</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>second: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L175" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-timesegments-day-period" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>day_period</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>day_period: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L188" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-timeparseresult" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>TimeParseResult</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Keep one localized time edit and its canonical wall-clock value separate.</p>
<p>The result is a zone-free <code>datetime.time</code>. Converting it
to an instant requires a date and time zone.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L197" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-timeparseresult-input" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>input</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>input: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="/reference/internationalization/#citry-timesegments">TimeSegments</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L198" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-timeparseresult-state" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>state</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>state: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;valid&#x27;, &#x27;incomplete&#x27;, &#x27;invalid&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L199" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-timeparseresult-value" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>value</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>value: <a class="doc-type-link" href="https://docs.python.org/3.13/library/datetime.html#datetime.time">time</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L200" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-timeparseresult-error" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>error</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>error: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L203" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-timeparseresult-valid" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>valid</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>valid: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Return whether the edit contains one complete wall-clock time.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L222" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-datetimeformat" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>DateTimeFormat</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Format an instant after conversion to the context's explicit IANA zone.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>length</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;short&#x27;, &#x27;medium&#x27;, &#x27;long&#x27;]</code>

- The locale-sensitive date and time display length.
</li>

<li>
<code>time_zone_name</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;none&#x27;, &#x27;short&#x27;, &#x27;long&#x27;]</code>

- Whether and how to display the resolved zone name.
</li>

<li>
<code>input</code>

<code><a class="doc-type-link" href="/reference/internationalization/#citry-datetimeinput">DateTimeInput</a> | None</code>

- The strict local-edit rule. <code>None</code> keeps the profile display-only.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L234" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-datetimeformat-length" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>length</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>length: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;short&#x27;, &#x27;medium&#x27;, &#x27;long&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L235" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-datetimeformat-time-zone-name" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>time_zone_name</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>time_zone_name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;none&#x27;, &#x27;short&#x27;, &#x27;long&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L236" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-datetimeformat-input" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>input</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>input: <a class="doc-type-link" href="/reference/internationalization/#citry-datetimeinput">DateTimeInput</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L196" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-datetimeinput" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>DateTimeInput</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Declare how a named local datetime profile accepts editable input.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>mode</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;strict_text&#x27;, &#x27;segments&#x27;]</code>

- <code>strict_text</code> for one string or <code>segments</code> for named fields.
</li>

<li>
<code>two_digit_year_start</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | None</code>

- First year in an explicit 100-year window, or
<code>None</code> to require a full year.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L208" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-datetimeinput-mode" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>mode</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>mode: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;strict_text&#x27;, &#x27;segments&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L209" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-datetimeinput-two-digit-year-start" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>two_digit_year_start</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>two_digit_year_start: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L208" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-datetimesegments" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>DateTimeSegments</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Combine named date and time fields from one local datetime control.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L212" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-datetimesegments-date" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>date</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>date: <a class="doc-type-link" href="/reference/internationalization/#citry-datesegments">DateSegments</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L213" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-datetimesegments-time" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>time</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>time: <a class="doc-type-link" href="/reference/internationalization/#citry-timesegments">TimeSegments</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L222" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-datetimeparseresult" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>DateTimeParseResult</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Keep a local datetime edit separate from its resolved aware instant.</p>
<p>An <code>ambiguous</code> daylight-saving fold returns both aware instants in
<code>alternatives</code>. Pass <code>fold="earlier"</code> or <code>fold="later"</code> to the parser
to resolve that choice explicitly.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L232" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-datetimeparseresult-input" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>input</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>input: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="/reference/internationalization/#citry-datetimesegments">DateTimeSegments</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L233" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-datetimeparseresult-state" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>state</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>state: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;valid&#x27;, &#x27;incomplete&#x27;, &#x27;invalid&#x27;, &#x27;ambiguous&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L234" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-datetimeparseresult-value" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>value</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>value: <a class="doc-type-link" href="https://docs.python.org/3.13/library/datetime.html#datetime.datetime">datetime</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L235" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-datetimeparseresult-error" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>error</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>error: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L236" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-datetimeparseresult-alternatives" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>alternatives</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>alternatives: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/datetime.html#datetime.datetime">datetime</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/context.py#L239" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-datetimeparseresult-valid" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>valid</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>valid: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Return whether the edit resolved to one complete aware instant.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L249" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-relativetimeformat" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>RelativeTimeFormat</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Format a relative day count; the current checked unit is <code>day</code>.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L253" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-relativetimeformat-unit" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>unit</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>unit: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;day&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L260" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-listformat" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ListFormat</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Format a conjunction or disjunction list.</p>
<p><code>kind</code> chooses “and” or “or”. <code>length</code> chooses the locale's wide, short,
or narrow pattern.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L269" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-listformat-kind" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>kind</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>kind: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;and&#x27;, &#x27;or&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L270" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-listformat-length" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>length</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>length: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;wide&#x27;, &#x27;short&#x27;, &#x27;narrow&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L279" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-unitformat" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>UnitFormat</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Format an exact value with an explicit CLDR unit identifier.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>width</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;long&#x27;, &#x27;short&#x27;, &#x27;narrow&#x27;]</code>

- How fully ICU4X writes the unit name.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/formats.py#L289" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-unitformat-width" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>width</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>width: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;long&#x27;, &#x27;short&#x27;, &#x27;narrow&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/errors.py#L4" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-i18nerror" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>I18nError</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/library/exceptions.html#Exception">Exception</a></code></p>


<div class="doc-body">
<p>Base class for i18n errors.</p>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/errors.py#L8" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-i18nnotconfigurederror" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>I18nNotConfiguredError</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/internationalization/#citry-i18nerror">I18nError</a></code></p>


<div class="doc-body">
<p>Raised when an i18n operation needs settings or messages that are absent.</p>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/i18n/errors.py#L12" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-i18nruntimeunavailableerror" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>I18nRuntimeUnavailableError</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/internationalization/#citry-i18nerror">I18nError</a></code></p>


<div class="doc-body">
<p>Raised when the requested i18n operation cannot run in the current context.</p>





</div>
</div>



