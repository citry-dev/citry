---
title: Component
url: https://citry.dev/v/0.4.4/reference/component/
description: "The base class every component subclasses."
---
# Component

The base class every component subclasses.




<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L538" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-component" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>Component</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Base class for all Citry components.</p>
<p>A component is a reusable unit of UI defined by:</p>
<ul>
<li>A <strong>template</strong> (Citry template syntax)</li>
<li>Optional <strong>typed inputs</strong> (via inner <code>Kwargs</code>, <code>Slots</code> classes)</li>
<li>A <strong>data method</strong> that maps inputs to template variables</li>
</ul>
<p>Subclass this to define your own components. At minimum, set
<code>template</code> (inline string) or <code>template_file</code> (path to file).</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L555" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-class-id" class="doc-heading">
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
<p>Stable import-derived identity shared by reloads of this component path.</p>
<p>The read-only value is suitable for routes and cross-process logical
identity. Combine it with <a href="/reference/citry/#citry-citry-engine-id"><code>Citry.engine_id</code></a> and
<code>definition_id</code> when retained metadata must match one exact live class
generation in the current process.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L564" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-definition-id" class="doc-heading">
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
<p>Opaque process-lifetime identity of this exact component class object.</p>
<p>The read-only value exists before class-created extension hooks run. An
alias or re-registration preserves it, while defining a replacement class
creates a different value even when <code>class_id</code> remains the same.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L572" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-citry" class="doc-heading">
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
<p>The Citry instance that owns this component class.</p>
<p>Defaults to the module-level default instance. Set this inside the class
body to assign a component to a specific instance. The binding cannot be
changed or deleted after the class is defined. A subclass of a concrete
component uses the same owner; define a fresh component tree when another
engine needs its own copy.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L582" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-transparent" class="doc-heading">
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
<p>Whether this component's output joins the surrounding component's
serialization frame.</p>
<p>A transparent component is structural rather than visual: its rendered
output gets no <code>data-cid-&lt;id&gt;</code> marker and is not framed as a child
component at serialize time. Used by built-ins like <code>&lt;c-provide&gt;</code> that
only wrap content. Hooks, the render id, and dependency merging behave
the same as for any component.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L593" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-pure" class="doc-heading">
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
<p>Whether repeated equal template data may reuse settled body strings.</p>
<p>Set <code>pure = True</code> only when rendering the template is a deterministic,
side-effect-free function of its template variables. The memo lives for
one root render. It can reuse safe strings around a child or Slot, but the
child, Slot, component instances, IDs, ownership, and i18n work still run
for every occurrence. A subclass must declare purity again rather than
inheriting the promise.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L604" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-name" class="doc-heading">
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
<p>Override the name under which this component is registered.</p>
<p>By default, the class name is used (lowercased + kebab-case).
Set this to register under a specific name instead::</p>
<pre><code>class MyWidget(Component):
    name = "fancy-widget"
    # registered as "fancy-widget", not "mywidget" / "my-widget"
</code></pre>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L615" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-template" class="doc-heading">
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
<p>Inline template string (Citry template syntax).</p>
<p>Mutually exclusive with <code>template_file</code>. Read the loaded template with
<code>get_template()</code>.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L622" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-template-file" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>template_file</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>template_file: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Path to a template file. Mutually exclusive with <code>template</code>.</p>
<p>Resolved relative to the directory of the class that declares the value
first, then relative to the owning component's <code>Citry(dirs=...)</code> entries;
absolute paths are used as-is. A subclass that inherits this declaration
therefore keeps the declaring class's file location. A plain mixin can
declare the path while the component still supplies the owning engine.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L632" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-messages" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>messages</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>messages: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Inline source-locale Fluent messages for this component.</p>
<p>Mutually exclusive with <code>messages_file</code>. Declare the source language with
<code>I18n.messages_locale</code>. A registered message asset activates server
source-mode translation for the complete engine catalog, even without
engine i18n settings. Read the loaded source with <code>get_messages()</code>.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L641" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-messages-file" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>messages_file</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>messages_file: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Path to source-locale Fluent messages, resolved like <code>template_file</code>.</p>
<p>This has the same source-mode and <code>I18n.messages_locale</code> contract as
<code>messages</code>.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L648" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-js" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>js</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>js: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Inline primary JS for this component. Mutually exclusive with
<code>js_file</code>. Read the loaded content with <code>get_js()</code>.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L652" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-js-file" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>js_file</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>js_file: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Path to the component's primary JS file. Mutually exclusive with
<code>js</code>. Resolved like <code>template_file</code>.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L656" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-css" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>css</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>css: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Inline primary CSS for this component.</p>
<p>Mutually exclusive with <code>css_file</code>. Citry adds these selectors to the
page exactly as written, so they can style any matching element. Use class
names specific to the component to avoid styling something else by
accident. Values returned by <code>css_data()</code> become custom properties for
one rendered use of the component. Read the loaded content with
<code>get_css()</code>.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L667" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-css-file" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>css_file</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>css_file: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Path to the component's primary CSS file. Mutually exclusive with
<code>css</code>. Resolved like <code>template_file</code>.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L671" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-cache" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>Cache</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>Cache: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Optional output-cache settings owned by the Cache extension.</p>
<p>Define a nested <code>Cache</code> class to enable caching, set its TTL and version,
or return additional variation values. Citry rebuilds the declaration on
<a href="/reference/cache-keys/#citry-cacheconfig"><code>CacheConfig</code></a> when it creates the component class.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L679" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-dependencies" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>Dependencies</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>Dependencies: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Optional secondary JavaScript and CSS assets.</p>
<p>Define a nested <code>Dependencies</code> class with <code>js</code>, <code>css</code>, <code>extend</code>,
or <code>local_files</code>. Read the normalized merged result with
<a href="/reference/component/#citry-component-get-dependencies"><code>get_dependencies()</code></a>. Citry rebuilds
the declaration on <a href="/reference/dependencies/#citry-dependenciesconfig"><code>DependenciesConfig</code></a>.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L688" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-i18n" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>I18n</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>I18n: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Optional per-component settings for the built-in i18n extension.</p>
<p>Define <code>client_messages</code> here when browser code uses a finite dynamic
message name that static analysis cannot discover. The instance-level
<a href="/reference/component/#citry-component-i18n-2"><code>i18n</code></a> value provides translation, formatting,
parsing, and the explicit locale context during a render.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L697" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-kwargs" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>Kwargs</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>Kwargs: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Optional typed keyword arguments.</p>
<p>Define as a plain class with type annotations. The metaclass
combines it with parent component declarations and converts the result to
a dataclass (with slots) automatically::</p>
<pre><code>class Card(Component):
    class Kwargs:
        title: str
        body: str = ""
</code></pre>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L710" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-slots" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>Slots</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>Slots: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Optional typed slot definitions, inherited like <a href="/reference/component/#citry-component-kwargs"><code>Kwargs</code></a>.</p>
<p>Use <a href="/reference/slots/#citry-slotinput"><code>SlotInput</code></a> for places where people can add content.
A field without a default must be filled whenever the component is used.
The <code>required</code> attribute on <code>&lt;c-slot&gt;</code> checks something different: it
raises an error only if Citry renders that tag without content.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L719" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-state" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>State</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>State: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Optional typed values that survive between server event calls.</p>
<p>Define <code>State</code> as a plain nested class with type annotations. The Events
extension combines inherited declarations and converts the result to a
mutable, slotted dataclass automatically::</p>
<pre><code>class Search(Component):
    class State:
        query: str = ""
        page: int = 1
</code></pre>
<p>State must contain only JSON-serializable values. By default, every field
is readable and writable in the browser. Use <code>_public</code> to choose which
fields the browser may read and <code>_model</code> to choose which public fields
it may change. <code>_storage</code> is <code>"signed"</code> by default and may be set to
<code>"server"</code>. <code>_max_bytes</code> defaults to 8192 bytes, and <code>_max_age</code>
accepts a <code>datetime.timedelta</code> or <code>None</code> for no expiry.</p>
<p>Citry starts State from same-named keyword arguments and field defaults.
Define <code>state_data(self, kwargs, slots)</code> when the values need to be
derived instead. Assign <code>State = None</code> on a subclass to stop inheriting
its parent's State declaration.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L744" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-events" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>Events</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>Events: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Optional server event handlers for this component.</p>
<p>Define <code>Events</code> as a nested class. Every public method is an event
handler; underscore-prefixed methods and attributes are private helpers or
configuration::</p>
<pre><code>class Counter(Component):
    class State:
        count: int = 0

    class Events:
        def increment(self, state):
            state.count += 1
</code></pre>
<p>Citry combines inherited <code>Events</code> declarations in component C3 order.
A child method overrides a same-named parent method, while <code>Events = None</code>
stops inherited declarations. The built-in Events extension rebuilds the
effective nested class on its runtime config base.</p>
<p>A plain nested class works without imports. To type handler attributes such
as <code>self.state</code> and <code>self.request</code>, subclass the generic
<a href="/reference/events/#citry-events"><code>Events</code></a> base and parameterize it with the component's State
class. See <a href="/reference/events/#citry-ext-events-event"><code>event</code></a> for per-handler options.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L770" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-lint" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>Lint</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>Lint: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Optional per-component template-lint settings.</p>
<p>Define a nested <code>Lint</code> class with
<code>rule_unknown_template_variable</code> and/or <code>template_variables</code>. Nested
declarations compose through the component C3 order. Assign <code>None</code> to
return to the Citry instance's application lint policy.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L779" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-templatedata" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>TemplateData</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>TemplateData: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Optional typed template data output, inherited like <a href="/reference/component/#citry-component-kwargs"><code>Kwargs</code></a>.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L782" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-jsdata" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>JsData</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>JsData: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Optional typed schema for the <code>js_data()</code> output. Like
<code>TemplateData</code>, it inherits through component C3 and a plain annotated
class converts to a dataclass.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L787" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-cssdata" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>CssData</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>CssData: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Optional typed schema for the <code>css_data()</code> output. Like
<code>TemplateData</code>, it inherits through component C3 and a plain annotated
class converts to a dataclass.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L926" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-id" class="doc-heading">
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
<p>Unique render ID for this component instance.</p>
<p>A fresh ID is minted every time a CitryElement is rendered, so the
same CitryElement rendered twice produces two distinct IDs.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L813" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-kwargs-2" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>kwargs</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>kwargs: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code></pre>
</div>

<div class="doc-body">
<p>The resolved keyword arguments.</p>
<p>If the component defines a <code>Kwargs</code> dataclass, this is an instance
of that class. Otherwise, a plain dict.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L943" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-raw-kwargs" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>raw_kwargs</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>raw_kwargs: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">
<p>The keyword arguments as a plain dict, even if a <code>Kwargs</code>
dataclass is defined. Useful when you need dict access regardless
of typing.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L826" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-slots-2" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>slots</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>slots: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code></pre>
</div>

<div class="doc-body">
<p>The resolved slot fills, with every value normalized to a <code>Slot</code>.</p>
<p>If the component defines a <code>Slots</code> dataclass, this is an instance
of that class. Otherwise, a plain dict.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L944" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-raw-slots" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>raw_slots</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>raw_slots: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="/reference/slots/#citry-slot">Slot</a>]</code></pre>
</div>

<div class="doc-body">
<p>The slot fills as a plain dict of <code>Slot</code> values, even if a <code>Slots</code>
dataclass is defined. Useful when you need dict access regardless
of typing.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L839" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-cache-2" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>cache</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>cache: <a class="doc-type-link" href="/reference/cache-keys/#citry-cacheconfig">CacheConfig</a></code></pre>
</div>

<div class="doc-body">
<p>The Cache extension settings bound to this rendered component.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L842" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-dependencies-2" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>dependencies</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>dependencies: <a class="doc-type-link" href="/reference/dependencies/#citry-dependenciesconfig">DependenciesConfig</a></code></pre>
</div>

<div class="doc-body">
<p>The Dependencies extension settings bound to this rendered component.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L845" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-events-2" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>events</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>events: EventsConfig[<a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">
<p>The Events extension settings and event URL helper for this component.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L848" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-i18n-2" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>i18n</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>i18n: I18nConfig</code></pre>
</div>

<div class="doc-body">
<p>Translation, formatting, parsing, and locale access for this component.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L957" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-parent" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>parent</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>parent: <a class="doc-type-link" href="/reference/component/#citry-component">Component</a> | None</code></pre>
</div>

<div class="doc-body">
<p>The component that wrote this one into its template. None for a root
component, and for one rendered standalone (e.g. an element handed into
an expression as <code>{{ element }}</code>).</p>
<p>The link follows authorship, not slot placement: a component written
inside a <code>&lt;c-fill&gt;</code> keeps the fill's author as its parent, no matter
whose slot the content lands in. (This differs from Vue, whose
<code>$parent</code> points at the slot host.) To ask "what am I rendered
inside, slots included", use <code>provide</code>/<code>inject</code>, which travels the
render path and crosses slot boundaries.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L868" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-root" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>root</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>root: <a class="doc-type-link" href="/reference/component/#citry-component">Component</a></code></pre>
</div>

<div class="doc-body">
<p>Return the component at the top of the authorship <code>parent</code> chain.</p>
<p>For root components, <code>self.root is self</code>. The root case is computed
instead of stored, so preserving that public identity does not create
a root-to-itself reference cycle.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L982" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-template-data" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>template_data</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>template_data(kwargs: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>, slots: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None</code></pre>
</div>

<div class="doc-body">
<p>Return the template variables.</p>
<p>By default this returns <code>kwargs</code>, so a component's inputs are usable
in its template without an override: a <code>Kwargs</code> field named <code>title</code>
is available to the template as <code>{{ title }}</code>. Override this to map
the inputs to a different set of variables. The returned value may be a
dict, a <code>NamedTuple</code>, or the typed <code>TemplateData</code> instance, and a
declared <code>TemplateData</code> validates and normalizes it either way.
Schema defaults and coercions are materialized in the mapping that the
template's expressions see.</p>
<p>A returned variable wins over a <code>template_globals</code> entry of the same
name, so an input shadows a same-named global (globals act as
defaults). Unlike <code>js_data</code> and <code>css_data</code>, which stay opt-in and
return <code>None</code> by default, template variables never cross into the
browser: they only make names resolvable to the template's own
expressions.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>kwargs</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code>

- The keyword arguments passed to the component.
</li>

<li>
<code>slots</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code>

- The slot fills passed to the component.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None: A mapping of template variables. Defaults to the component&#x27;s</p>




</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L1018" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-js-data" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>js_data</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>js_data(kwargs: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>, slots: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None</code></pre>
</div>

<div class="doc-body">
<p>Return the JS variables for this render.</p>
<p>Override this to expose per-render data to the component's browser
behavior. The dict is serialized to strict JSON, seeded into the
component's Alpine scope, and delivered to its <code>$component</code> callback
as <code>data</code> when one exists. Identical JSON is transported only once,
while every rendered instance receives a fresh mutable value graph.
Consumed by the built-in <code>dependencies</code> extension.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>kwargs</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code>

- The keyword arguments passed to the component.
</li>

<li>
<code>slots</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code>

- The slot fills passed to the component.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None: A dict of JS variables, or None for no variables.</p>




</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L1043" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-css-data" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>css_data</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>css_data(kwargs: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>, slots: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None</code></pre>
</div>

<div class="doc-body">
<p>Return the CSS variables for this render.</p>
<p>Override this to expose per-render values to the component's CSS
(<code>Component.css</code>) as CSS custom properties: a returned
<code>{"row-color": "red"}</code> is usable in the CSS as
<code>var(--row-color)</code>, scoped to this component's elements. Identical
data across renders shares one generated stylesheet. Consumed by the
built-in <code>dependencies</code> extension.</p>
<p>Keys are custom-property name suffixes, without the leading <code>--</code>.
Values must be strings, finite numbers, or <code>None</code>. Citry escapes
quoted strings and rejects names or raw values that could escape the
generated declaration. It checks structural containment, while the
browser remains responsible for full CSS value grammar and whether a
value is valid for the property that consumes it.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>kwargs</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code>

- The keyword arguments passed to the component.
</li>

<li>
<code>slots</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code>

- The slot fills passed to the component.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None: A dict of CSS variables, or None for no variables.</p>




</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L1077" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-on-dependencies" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_dependencies</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_dependencies(scripts: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[<a class="doc-type-link" href="/reference/dependencies/#citry-ext-dependencies-dependency">Dependency</a>], styles: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[<a class="doc-type-link" href="/reference/dependencies/#citry-ext-dependencies-dependency">Dependency</a>]) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[<a class="doc-type-link" href="/reference/dependencies/#citry-ext-dependencies-dependency">Dependency</a>], <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[<a class="doc-type-link" href="/reference/dependencies/#citry-ext-dependencies-dependency">Dependency</a>]] | None</code></pre>
</div>

<div class="doc-body">
<p>Hook to adjust this component's JS/CSS tags before they enter the page.</p>
<p>Called at serialize time, once per rendered instance of this
component, with the <code>Script</code>/<code>Style</code> entries this component
contributes (its <code>Dependencies</code> entries and its own
<code>Component.js</code>/<code>css</code>). Return a <code>(scripts, styles)</code> pair to
replace the lists, mutate them in place, or return <code>None</code> (the
default) to keep them. Removing the component's own script entries
can break the component's behavior in the browser; this hook is for
adding attributes, reordering, or dropping entries you know are
provided elsewhere.</p>
<p>To adjust the <em>page-wide</em> lists instead (every component's tags,
after de-duplication), implement an extension with an
<code>on_dependencies</code> method (see
<code>citry.ext.dependencies.OnDependenciesContext</code>).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L1103" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-on-render" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>on_render</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>on_render() -> <a class="doc-type-link" href="/reference/rendering/#citry-renderreplacement">RenderReplacement</a> | <a class="doc-type-link" href="/reference/rendering/#citry-onrendergenerator">OnRenderGenerator</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Hook to replace or post-process this component's rendered output.</p>
<p>Called when this component is rendered without a successful component
cache hit, after <code>template_data</code> and just before the template
renders. A cache hit reuses the completed output and skips data
methods, slots, the template, and this hook. Return <code>None</code> (the
default) to render the template as usual. Return content to use it as
the component's whole output instead; the template is then not
rendered at all. Accepted content:</p>
<ul>
<li>a <code>str</code>, used as-is (NOT autoescaped: it is this component's own
output, the same trust as its template; never concatenate untrusted
input into it)</li>
<li>a composed element (<code>OtherComponent(title="hi")</code>), rendered in
this component's place</li>
<li>an already-rendered <code>CitryRender</code>, inlined</li>
<li>a <code>Slot</code>, invoked with no data</li>
<li>a <code>ComponentLike</code>, resolved against this component's Citry instance</li>
</ul>
<p>Because <code>None</code> means "no replacement", return <code>""</code> to output
literally nothing.</p>
<p>Everything the hook needs is on <code>self</code>: <code>kwargs</code>, <code>slots</code>,
<code>parent</code>, <code>inject()</code>. To pass data to the template, use
<code>template_data</code>; this hook is for replacing output. If the hook
depends on ambient data while component caching is enabled, include
that data in the cache variation inputs.</p>
<p>For example, render a placeholder instead of the template when there
is no data::</p>
<pre><code>class MyTable(Component):
    template = "&lt;table&gt;...&lt;/table&gt;"

    def on_render(self):
        if not self.raw_kwargs.get("rows"):
            return "&lt;p&gt;No data&lt;/p&gt;"
        return None
</code></pre>
<p><strong>Generator form.</strong> Include a <code>yield</code> to also see the component's
finished output, children included, and react to it - for example to
catch a failing child (this is how error boundaries work)::</p>
<pre><code>class Guarded(Component):
    template = "..."

    def on_render(self):
        # BEFORE: runs just before the template renders.
        result, error = yield

        # AFTER: result is the completed CitryRender, or None
        # if rendering failed (then error is the exception).
        if error is not None:
            return "&lt;p&gt;Something went wrong&lt;/p&gt;"
        return None
</code></pre>
<p>The protocol:</p>
<ul>
<li>A bare <code>yield</code> (or <code>yield None</code>) on the first yield means
"render my template as usual"; yielding content means "use this as
my output instead" (same accepted values as above).</li>
<li>The yield receives <code>(result, error)</code> once that output has fully
settled: <code>result</code> is the live <code>CitryRender</code> (not a string; do
not serialize it here unless you are replacing the output with the
serialized form), or <code>None</code> when rendering failed, with <code>error</code>
set. Exactly one of the two is set.</li>
<li>You can yield any number of times; each <code>yield &lt;content&gt;</code>
replaces the output, renders it, and receives the new
<code>(result, error)</code>. A bare <code>yield</code> after the first answers
immediately with the current result unchanged.</li>
<li>End with <code>return &lt;content&gt;</code> to set the final output, <code>raise</code> to
make that the component's error, or plain <code>return</code> to keep the
current result (an unhandled error keeps bubbling).</li>
</ul>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L1181" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-provide" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>provide</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>provide(key: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, value: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a> = MISSING, **data: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a> = {}) -> None</code></pre>
</div>

<div class="doc-body">
<p>Make one value available to this component's descendants.</p>
<p>Any component rendered below this one (including components inside
slot content rendered below it) can read the data with
<code>self.inject(key)</code>. The data does NOT enter the template variables;
descendants opt in explicitly.</p>
<p>Pass a direct positional value when the caller already owns the value
object. Or pass keyword fields and Citry will freeze them into an
immutable payload whose fields are read as attributes::</p>
<pre><code>class Page(Component):
    template = '&lt;c-user-card /&gt;'

    def template_data(self, kwargs, slots):
        self.provide("user_data", user=kwargs["user"])
        return {}

class UserCard(Component):
    template = '&lt;div&gt;{{ name }}&lt;/div&gt;'

    def template_data(self, kwargs, slots):
        return {"name": self.inject("user_data").user}

class LocaleRoot(Component):
    def template_data(self, kwargs, slots):
        self.provide("citry_i18n", kwargs.locale_context)
        return {}
</code></pre>
<p>In templates, the same thing is written with the <code>&lt;c-provide&gt;</code>
built-in component: <code>&lt;c-provide key="user_data" c-user="user"&gt;</code>.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>key</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Name the data is provided under (a non-empty identifier).
Positional-only, so a data field named <code>key</code> is allowed.
</li>

<li>
<code>value</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code>

- One direct value. It is passed through unchanged.
</li>

<li>
<code>**data</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code>

- Fields Citry freezes into one immutable payload. A call
cannot pass both a direct value and keyword fields.
</li>

</ul>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L1230" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-inject" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>inject</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>inject(key: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, default: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a> = MISSING) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code></pre>
</div>

<div class="doc-body">
<p>Read data a component above this one provided under <code>key</code>.</p>
<p>The data must have been provided by a component on the render path
above this one (via <code>Component.provide</code> or the <code>&lt;c-provide&gt;</code>
built-in); the nearest provider wins when the same key is provided
twice. A component's own <code>provide</code> calls are visible to its
descendants only, never to its own <code>inject</code>.</p>
<p>A direct value is returned unchanged. Keyword fields passed to
<code>provide()</code> return an immutable payload with those fields as
attributes: <code>self.inject("user_data").user</code>. Injection works during
<code>template_data</code> and keeps working after the render for as long as the
component instance is kept.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>key</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The name the data was provided under.
</li>

<li>
<code>default</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code>

- Returned when nothing was provided under <code>key</code>. An
explicit <code>None</code> works. Without a default, a missing key
raises <code>KeyError</code>.
</li>

</ul>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L1255" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-unprovide" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>unprovide</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>unprovide(key: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> None</code></pre>
</div>

<div class="doc-body">
<p>Hide an inherited provide from this component's descendants.</p>
<p>The component may still inject the inherited value itself. Components
rendered below it observe the key as missing unless a nearer component
provides a new value under the same key. Call this from
<code>template_data</code> when content below a component boundary must establish
a fresh context before using a compound child.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>key</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The provide key to hide below this component.
</li>

</ul>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L1275" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-ancestors" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>ancestors</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>ancestors: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Iterator">Iterator</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code></pre>
</div>

<div class="doc-body">
<p>All ancestor components, nearest first: the parent, then the parent's
parent, up to and including the root. Empty for a root component.</p>
<p>Useful to check where a component sits, e.g.::</p>
<pre><code>is_themed = any(isinstance(c, Theme) for c in self.ancestors)
</code></pre>
<p>The chain follows who <em>wrote</em> the component, the same as <code>parent</code>:
a component written inside a <code>&lt;c-fill&gt;</code> has the fill's author as
its parent, not the component whose slot rendered it. So the check
above holds when <code>Theme</code>'s own template renders this component;
for "am I rendered inside a Theme, slots included", have <code>Theme</code>
<code>provide</code> a value and <code>inject</code> it here, which travels the render
path and crosses slot boundaries.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L1305" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-get-template" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>get_template</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>get_template() -> <a class="doc-type-link" href="/reference/rendering/#citry-citrytemplate">CitryTemplate</a> | None</code></pre>
</div>

<div class="doc-body">
<p>The loaded template (a <code>CitryTemplate</code>), or <code>None</code> for a
template-less component. Resolved from <code>template</code> /
<code>template_file</code> once per class; <code>on_template_loaded</code> applied.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L1314" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-get-js" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>get_js</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>get_js() -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>The loaded primary JS content, or <code>None</code>. Resolved from <code>js</code> /
<code>js_file</code> once per class; <code>on_js_loaded</code> applied.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L1322" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-get-messages" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>get_messages</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>get_messages() -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Return the loaded <code>messages</code> / <code>messages_file</code> source, or <code>None</code>.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L1327" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-get-css" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>get_css</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>get_css() -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">
<p>The loaded primary CSS content, or <code>None</code>. Resolved from <code>css</code> /
<code>css_file</code> once per class; <code>on_css_loaded</code> applied.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L1335" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-get-dependencies" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>get_dependencies</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>get_dependencies() -> <a class="doc-type-link" href="/reference/dependencies/#citry-ext-dependencies-citrydependencies">CitryDependencies</a></code></pre>
</div>

<div class="doc-body">
<p>The merged secondary assets from this component's (and, per
<code>Dependencies.extend</code>, its bases') nested <code>Dependencies</code> class.
Owned by the built-in <code>dependencies</code> extension.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L1344" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-reset-template" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>reset_template</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>reset_template() -> None</code></pre>
</div>

<div class="doc-body">
<p>Clear this class's loaded template (and its compiled form and cached
<code>Const</code> optimization results), so the next render re-reads it.
Subclasses that inherit this template cache their own copies; reset
them too (<code>Citry.get_components_for_file</code> lists every class using
a given file).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component.py#L1355" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-component-reset-files" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>reset_files</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>reset_files() -> None</code></pre>
</div>

<div class="doc-body">
<p>Clear this class's loaded messages/JS/CSS (and, via the <code>on_files_reset</code>
hook, extension state such as the merged <code>Dependencies</code>), so the
next access re-reads them.</p>





</div>
</div>


</div>

</div>
</div>



