---
title: Events
url: https://citry.dev/v/0.4.6/reference/events/
description: "Event handlers declared on components: the class Events: contract, the typed base for it, and the built-in citry.ext.events extension that owns it."
---
# Events

Event handlers declared on components: the `class Events:` contract, the typed base for it, and the built-in `citry.ext.events` extension that owns it.




<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/config.py#L34" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-events" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>Events</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/extensions/#citry-extensionconfig">ExtensionConfig</a></code>, <code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Generic">Generic</a></code></p>


<div class="doc-body">
<p>Optional typed base for a component's <code>Events</code> class.</p>
<p>A component's <code>class Events:</code> needs no base class: the built-in
<code>events</code> extension rebuilds it on this class either way, so subclassing
is purely a typing aid and changes nothing at runtime. Subscript the base
with the component's State class to type <code>self.state</code> for editors and
type checkers (mypy and pyright):</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><pre><code class="language-python">import citry
from citry import Component

class TodoState:
    project_id: int
    query: str = &quot;&quot;

class TodoList(Component):
    State = TodoState

    class Events(citry.Events[TodoState]):
        def refresh(self) -&gt; None:
            self.state.query  # typed as str
</code></pre>
<p>On a component with no State class, subclass the bare base:
<code>self.state</code> is then typed (and is) <code>None</code>.</p></blockquote>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>state</code>

<code>StateT</code>

- The component's State instance for the call being handled;
<code>None</code> when the component declares no State class.
</li>

<li>
<code>context</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code>

- Whatever the <code>_context</code> hook returned for the call being
handled; <code>None</code> when no hook is configured.
</li>

<li>
<code>request</code>

<code><a class="doc-type-link" href="/reference/web/#citry-routerequest">RouteRequest</a></code>

- A framework-neutral view of the request that carried the
call (<a href="/reference/web/#citry-routerequest"><code>RouteRequest</code></a>).
</li>

<li>
<code>event</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code>

- Metadata about the call being handled.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/config.py#L75" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-events-state" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>state</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>state: StateT</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/config.py#L76" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-events-context" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>context</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>context: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/config.py#L77" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-events-request" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>request</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>request: <a class="doc-type-link" href="/reference/web/#citry-routerequest">RouteRequest</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/config.py#L78" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-events-event" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>event</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>event: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/csrf.py#L54" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-events-x-citry-events-header" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>X_CITRY_EVENTS_HEADER</code>
</span>
<span class="doc-kind">attribute</span>
</h2>


<div class="doc-body">
<p>Header required on JSON Events calls as part of the same-origin CSRF check.</p>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/dispatcher.py#L208" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-events-callevent" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>CallEvent</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>The <code>event</code> value injected into event handlers: metadata about one call.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>name</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The handler's wire name the call addressed.
</li>

<li>
<code>instance_id</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- The calling instance's render id, or <code>None</code> for an
instance-less call (an API client, a hand-written form).
</li>

<li>
<code>transport</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The transport that carried the call (<code>"http"</code>, ...).
</li>

<li>
<code>args</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code>

- The raw, unvalidated wire args payload. Guards read this when
they need payload values, because one guard covers handlers with
different schemas (design 3.5).
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/dispatcher.py#L224" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-callevent-name" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/dispatcher.py#L225" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-callevent-instance-id" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>instance_id</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>instance_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/dispatcher.py#L226" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-callevent-transport" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>transport</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>transport: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/dispatcher.py#L227" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-callevent-args" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>args</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>args: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/errors.py#L46" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-events-eventerror" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>EventError</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/library/exceptions.html#Exception">Exception</a></code></p>


<div class="doc-body">
<p>A structured error an event handler or guard raises to answer a call.</p>
<p>The client receives the <code>status</code>, a stable string <code>code</code> derived from
it, the <code>message</code> as the human summary (a toast or banner), and
<code>fieldErrors</code> as the per-field error map surfaced next to inputs
(for example, <code>$error('submit')?.fieldErrors</code>). Raising it anywhere in a
handler, a guard, or the
<code>_context</code> hook turns the call into that error response; it never
becomes a host 500.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><pre><code class="language-python">from citry.ext.events import EventError

class DocumentEditor(Component):
    class State:
        document_id: int

    class Events:
        def _guard(self):
            user = user_from_request(self.request)
            if can_edit(user, self.state.document_id):
                return
            raise EventError(
                &quot;You cannot edit this document.&quot;,
                status=403,
            )

        def subscribe(self, data: SubscribeIn):
            if is_taken(data.email):
                raise EventError(
                    &quot;Please fix the errors below.&quot;,
                    fields={&quot;email&quot;: &quot;This address is already subscribed.&quot;},
                )
</code></pre></blockquote>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>message</code>

- The human summary of the error.
</li>

<li>
<code>fields</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>]</code>

- Per-field error messages, keyed by data-schema field name
(e.g. <code>{"email": "Enter a valid email address."}</code>). Empty when
the error is not about specific fields.
</li>

<li>
<code>status</code>

- The HTTP status of the error (400 to 599). <code>422</code> (the
default) is a validation failure; <code>403</code>, <code>404</code>, and <code>409</code>
cover forbidden, not found, and conflict.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/errors.py#L112" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventerror-message" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>message</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/errors.py#L113" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventerror-fields" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>fields</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>fields: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/errors.py#L114" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventerror-status" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>status</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/errors.py#L117" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventerror-code" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>code</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>code: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>The stable wire code for the error's status (e.g. <code>"forbidden"</code> for 403).</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/dispatcher.py#L170" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-events-eventrequest" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>EventRequest</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>The <code>request</code> value injected into event handlers.</p>
<p>The framework-neutral request fields (design 3.3), always populated: the
HTTP routes fill everything; other transports fill what they carry. The
untouched host object stays reachable as <code>native</code>, and
<code>event.transport</code> says which transport built it.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>method</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The HTTP method, uppercase.
</li>

<li>
<code>path</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The full URL path of the request.
</li>

<li>
<code>query</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, ...]]</code>

- The query-string parameters; each key maps to every value it
was sent with, in order.
</li>

<li>
<code>headers</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>]</code>

- The request headers; lookups ignore case.
</li>

<li>
<code>body</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#bytes">bytes</a></code>

- The raw request body.
</li>

<li>
<code>content_type</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The <code>Content-Type</code> header value, or <code>""</code>.
</li>

<li>
<code>form</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code>

- The parsed form fields of a form post (urlencoded today),
mapping field name to its string value (or list of values for a
repeated field); empty for non-form requests.
</li>

<li>
<code>files</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code>

- Uploaded files by field name when the selected payload codec or
transport supplies them; otherwise empty.
</li>

<li>
<code>native</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code>

- The untouched host request object.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/dispatcher.py#L197" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventrequest-method" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>method</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>method: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/dispatcher.py#L198" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventrequest-path" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>path</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>path: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/dispatcher.py#L199" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventrequest-query" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>query</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>query: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, ...]]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/dispatcher.py#L200" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventrequest-headers" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>headers</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>headers: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/dispatcher.py#L201" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventrequest-body" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>body</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>body: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#bytes">bytes</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/dispatcher.py#L202" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventrequest-content-type" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>content_type</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>content_type: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/dispatcher.py#L203" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventrequest-form" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>form</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>form: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/dispatcher.py#L204" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventrequest-files" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>files</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>files: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/dispatcher.py#L205" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventrequest-native" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>native</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>native: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/dispatcher.py#L369" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-events-eventsdispatcher" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>EventsDispatcher</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Runs call envelopes through the events pipeline and answers result envelopes.</p>
<p>Stateless: everything a dispatch needs rides in the envelope and the
<a href="/reference/events/#citry-ext-events-transportcontext"><code>TransportContext</code></a>, so
one instance (or a fresh one per call) serves every transport. The HTTP
routes own the built-in usage; a custom transport (a GraphQL mutation
resolver, say) decodes its request into the call envelope of design 4.2
and calls <a href="/reference/events/#citry-ext-events-eventsdispatcher-dispatch"><code>dispatch</code></a>
(or its async twin) directly.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/dispatcher.py#L382" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventsdispatcher-dispatch" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>dispatch</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>dispatch(envelope: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>], ctx: <a class="doc-type-link" href="/reference/events/#citry-ext-events-transportcontext">TransportContext</a>, request: <a class="doc-type-link" href="/reference/events/#citry-ext-events-eventrequest">EventRequest</a> | None = None, url_component: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None = None, url_event: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None = None, csrf_check: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[EventHandler], None] | None = None) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | <a class="doc-type-link" href="/reference/web/#citry-routeresponse">RouteResponse</a></code></pre>
</div>

<div class="doc-body">
<p>Dispatch a call envelope synchronously and return the result envelope.</p>
<p>This is the plain-<code>def</code> pipeline WSGI and sync Django hosts run.
An <code>async def</code> event handler is answered with the 500 error naming
the fix (dispatch through
<a href="/reference/events/#citry-ext-events-eventsdispatcher-dispatch-async"><code>dispatch_async</code></a>,
which an async transport calls); it is never silently run on a
private event loop.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>envelope</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code>

- The decoded call envelope (design 4.2).
</li>

<li>
<code>ctx</code>

<code><a class="doc-type-link" href="/reference/events/#citry-ext-events-transportcontext">TransportContext</a></code>

- What the transport knows about the request.
</li>

<li>
<code>request</code>

<code><a class="doc-type-link" href="/reference/events/#citry-ext-events-eventrequest">EventRequest</a> | None</code>

- The neutral request injected into handlers as
<code>request</code>; <code>None</code> builds an empty one carrying
<code>ctx.host_request</code> as <code>native</code>.
</li>

<li>
<code>url_component</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- The class id the per-event URL names; when given,
the URL is authoritative and a differing body field is
rejected. <code>None</code> on the batch endpoint.
</li>

<li>
<code>url_event</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- The event wire name the per-event URL names. A raw
response additionally requires HTTP and
<code>@event(bundle=False)</code>.
</li>

<li>
<code>csrf_check</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[EventHandler], None] | None</code>

- The transport's per-call CSRF check, called with the
resolved handler; raise to reject the call as
<code>csrf_failed</code>. <code>None</code> skips the check (a transport with
its own protection, or a direct caller).
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | <a class="doc-type-link" href="/reference/web/#citry-routeresponse">RouteResponse</a>: The result envelope (design 4.3), or the handler&#x27;s</p>




</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/dispatcher.py#L444" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventsdispatcher-dispatch-async" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>dispatch_async</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>dispatch_async(envelope: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>], ctx: <a class="doc-type-link" href="/reference/events/#citry-ext-events-transportcontext">TransportContext</a>, request: <a class="doc-type-link" href="/reference/events/#citry-ext-events-eventrequest">EventRequest</a> | None = None, url_component: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None = None, url_event: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None = None, csrf_check: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[EventHandler], None] | None = None) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | <a class="doc-type-link" href="/reference/web/#citry-routeresponse">RouteResponse</a></code></pre>
</div>

<div class="doc-body">
<p>Dispatch a call envelope from async code.</p>
<p>The one behavioral difference from
<a href="/reference/events/#citry-ext-events-eventsdispatcher-dispatch"><code>dispatch</code></a>:
<code>async def</code> event handlers are awaited on the running loop, and
sync handlers are offloaded to a worker thread
(<code>citry.util.routing.call_maybe_sync</code>) so they cannot block it.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>envelope</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code>

- The decoded call envelope.
</li>

<li>
<code>ctx</code>

<code><a class="doc-type-link" href="/reference/events/#citry-ext-events-transportcontext">TransportContext</a></code>

- What the transport knows about the request.
</li>

<li>
<code>request</code>

<code><a class="doc-type-link" href="/reference/events/#citry-ext-events-eventrequest">EventRequest</a> | None</code>

- The neutral request injected into handlers, or <code>None</code>
to build one from <code>ctx.host_request</code>.
</li>

<li>
<code>url_component</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- The class id named by a per-event URL, or <code>None</code>
for a batch or custom transport.
</li>

<li>
<code>url_event</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- The event name named by a per-event URL. A raw response
additionally requires HTTP and <code>@event(bundle=False)</code>.
</li>

<li>
<code>csrf_check</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[EventHandler], None] | None</code>

- A callable that raises to reject a resolved handler,
or <code>None</code> when the transport provides its own protection.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | <a class="doc-type-link" href="/reference/web/#citry-routeresponse">RouteResponse</a>: The result envelope, or the handler&#x27;s ``RouteResponse`` when the</p>




</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/extension.py#L191" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-events-eventsextension" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>EventsExtension</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/extensions/#citry-extension">Extension</a></code></p>


<div class="doc-body">
<p>Built-in extension that validates, serves, and renders component Events.</p>
<p>Every <a href="/reference/citry/#citry-citry"><code>Citry</code></a> instance installs this extension. It validates
a component's <code>Events</code> and <code>State</code> declarations when the component
class is created, contributes the Events HTTP routes, prepares declarative
bindings, and emits the browser runtime data needed by rendered instances.</p>
<p>Most applications use the nested <code>class Events</code> API described in
<a href="/events/">Server events</a> and never instantiate this class
directly. Extension and tooling authors can retrieve it from the instance's
<a href="/reference/extensions/#citry-extensionmanager"><code>ExtensionManager</code></a> to inspect resolved handler or
State metadata.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/extension.py#L207" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventsextension-name" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/extension.py#L210" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventsextension-introspection-version" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>introspection_version</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/extension.py#L211" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventsextension-render-cache-mode" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/extension.py#L213" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventsextension-render-cache-version" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/extension.py#L215" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventsextension-config" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/extension.py#L218" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventsextension-commands" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>commands</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/extension.py#L221" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventsextension-urls" class="doc-heading">
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
<p>Return the Events routes bound to this extension's Citry instance.</p>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[<a class="doc-type-link" href="/reference/web/#citry-urlroute">URLRoute</a>]: Routes for the client runtime, batched calls, named handlers, and</p>




</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/extension.py#L242" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventsextension-validate-config-fields" class="doc-heading">
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
<p>Check declared Events config fields against the two-tier rule.</p>
<p>Underscore names are configuration and must be one of the recognized
config attributes (<code>_guard</code>, <code>_context</code>, <code>_csrf</code>, <code>_methods</code>,
<code>_debounce</code>, <code>_throttle</code>, <code>_topics</code>, plus the engine-wide
<code>_max_envelope_bytes</code>, which only <code>extensions_defaults</code> may set);
on a component's <code>Events</code> class an underscore <code>def</code> is a private
helper and is exempt.
Unprefixed names are event handlers: they belong on a component's
nested <code>Events</code> class, so they are rejected in
<code>extensions_defaults</code> (an event handler cannot be defaulted
globally), and on the component they must be plain methods defined
with <code>def</code>, which is exactly what handler enumeration collects
(design <code>events.md</code> 3.1). A <code>staticmethod</code> or <code>classmethod</code>
passes here so enumeration can reject it with its own pointed error;
anything else (a <code>property</code>, a <code>functools.partial</code>, a plain
value) fails here rather than sit on Events as silently neither
handler nor config. Citry calls this at engine construction (for the
setting) and at component class definition; see
<a href="/reference/extensions/#citry-extension-validate-config-fields"><code>Extension.validate_config_fields</code></a>.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>fields</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code>

- The declared fields, mapping field name to declared value.
</li>

<li>
<code>component</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>] | None</code>

- The component class the fields were declared on, or
<code>None</code> when they come from the <code>extensions_defaults</code>
setting.
</li>

</ul>



<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>ValueError</code> - For an unrecognized underscore name (with a "did you
mean" hint), an event handler in <code>extensions_defaults</code>, or a
handler value that is not a plain function.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/extension.py#L329" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventsextension-on-component-class-created" class="doc-heading">
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
<p>Validate and record one component's Events and State declarations.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/extension.py#L342" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventsextension-inspect-component" class="doc-heading">
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
<p>Return public, JSON-safe Events metadata for component introspection.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>ctx</code>

<code><a class="doc-type-link" href="/reference/component-introspection/#citry-componentintrospectioncontext">ComponentIntrospectionContext</a></code>

- The component-introspection request.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>] | None: Versioned handler metadata, or ``None`` when the component has no</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>RuntimeError</code> - When the component was not recorded at class
creation.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/extension.py#L364" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventsextension-on-template-compiled" class="doc-heading">
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
<p>Validate and compile literal <code>@c-*</code> and <code>:c-*</code> bindings.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>ctx</code>

<code><a class="doc-type-link" href="/reference/extensions/#citry-ontemplatecompiledcontext">OnTemplateCompiledContext</a></code>

- The compiled template body and its owning component.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]: The body with parser-proven element bindings compiled.</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>ValueError</code> - When a binding names an unknown handler or State field,
or uses an invalid modifier combination.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/extension.py#L391" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventsextension-on-template-reset" class="doc-heading">
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
<p>Discard binding diagnostics derived from the previous compiled body.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/extension.py#L395" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventsextension-on-attrs-resolved" class="doc-heading">
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
<p>Validate and compile <code>@c-*</code> and <code>:c-*</code> bindings from dynamic attrs.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>ctx</code>

<code><a class="doc-type-link" href="/reference/extensions/#citry-onattrsresolvedcontext">OnAttrsResolvedContext</a></code>

- The resolved-attribute context for one HTML element.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None: Updated attributes, or ``None`` when the element has no Events</p>




</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/extension.py#L416" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventsextension-on-component-data" class="doc-heading">
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
<p>Prepare one rendered Events instance for browser activation.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>ctx</code>

<code><a class="doc-type-link" href="/reference/extensions/#citry-oncomponentdatacontext">OnComponentDataContext</a></code>

- The component-data context for the instance being rendered.
</li>

</ul>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/extension.py#L426" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventsextension-on-render-context-merge" class="doc-heading">
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
<p>Merge child Events records into their parent render context.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/extension.py#L432" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventsextension-export-render-cache" class="doc-heading">
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






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/extension.py#L435" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventsextension-stage-render-cache" class="doc-heading">
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






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/extension.py#L438" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventsextension-on-dependencies" class="doc-heading">
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
<p>Add the Events runtime and instance data to serialized dependencies.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>ctx</code>

<code><a class="doc-type-link" href="/reference/dependencies/#citry-ext-dependencies-ondependenciescontext">OnDependenciesContext</a></code>

- The dependencies context for the render being serialized.
</li>

</ul>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/extension.py#L448" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventsextension-two-way-binding-targets" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>two_way_binding_targets</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>two_way_binding_targets(comp_cls: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#frozenset">frozenset</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>]</code></pre>
</div>

<div class="doc-body">
<p>The State fields bound two-way in a component's template.</p>
<p>Populated when the template first compiles, so it is empty for a
component whose template has not been compiled yet or that has no
two-way bindings. Each individual target was already validated against
<code>_model</code> during compilation; this aggregate is exposed for
diagnostics and introspection.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>comp_cls</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code>

- The component class to look up.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#frozenset">frozenset</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>]: The two-way bound State field names (empty when none).</p>




</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/extension.py#L467" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventsextension-resolve" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>resolve</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>resolve(comp_cls: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]) -> EventsInfo</code></pre>
</div>

<div class="doc-body">
<p>The events info of a component class: handlers, State, resolved config.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>comp_cls</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code>

- The component class to look up.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns">EventsInfo: The resolved handler, State, and configuration record computed</p>




</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/extension.py#L487" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-eventsextension-build-state" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>build_state</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>build_state(component: <a class="doc-type-link" href="/reference/component/#citry-component">Component</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code></pre>
</div>

<div class="doc-body">
<p>Build the State instance for the component instance being rendered.</p>
<p>Uses the component's own <code>state_data(kwargs, slots)</code> when it
defines one (returning the State instance or a dict for it);
otherwise derives the State from same-named kwargs, with State-field
defaults filling the gaps.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>component</code>

<code><a class="doc-type-link" href="/reference/component/#citry-component">Component</a></code>

- The component instance being rendered.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>: The State instance, or ``None`` when the component declares no</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>ValueError</code> - When a State field has neither a matching kwarg nor
a default, or when <code>state_data()</code> returns something other
than the State or a dict.
</li>

</ul>



</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/dispatcher.py#L139" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-events-transportcontext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>TransportContext</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>What a transport tells the dispatcher about the request it decoded.</p>
<p>One is built per request by the transport (the HTTP routes build it in
<code>citry.ext.events.routes</code>; a custom transport builds its own) and
passed to <a href="/reference/events/#citry-ext-events-eventsdispatcher-dispatch"><code>EventsDispatcher.dispatch</code></a>.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>transport</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The transport's name (<code>"http"</code>, later <code>"ws"</code>); handlers
see it as <code>event.transport</code>.
</li>

<li>
<code>citry</code>

<code><a class="doc-type-link" href="/reference/citry/#citry-citry">Citry</a></code>

- The engine the call dispatches against.
</li>

<li>
<code>host_request</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code>

- The untouched host request object (Django's
<code>HttpRequest</code>, the ASGI scope, a WS connection); <code>None</code> when
the transport has none.
</li>

<li>
<code>headers</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>]</code>

- A case-insensitive view of the request headers; empty when
the transport carries none.
</li>

<li>
<code>response_mode</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;wire&#x27;, &#x27;compat&#x27;]</code>

- <code>"wire"</code> for an ordinary result envelope, or
<code>"compat"</code> when the HTTP transport will turn one call into a
browser-native HTML, redirect, JSON, or empty response.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/dispatcher.py#L163" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-transportcontext-transport" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>transport</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>transport: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/dispatcher.py#L164" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-transportcontext-citry" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/dispatcher.py#L165" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-transportcontext-host-request" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>host_request</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>host_request: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/dispatcher.py#L166" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-transportcontext-headers" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>headers</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>headers: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/dispatcher.py#L167" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-transportcontext-response-mode" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>response_mode</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>response_mode: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;wire&#x27;, &#x27;compat&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/files.py#L19" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-events-uploadedfile" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>UploadedFile</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>One file received by an event handler, independent of the web framework.</p>
<p>Payload codecs and custom transports can construct this neutral wrapper so
handler code does not depend on a host framework's file type. Reading is
synchronous: plain handlers run in a worker thread under ASGI, so a plain
<code>read()</code> cannot stall the event loop.</p>
<p>Citry's built-in payload codecs do not parse multipart request bodies. Use
this type with a custom codec or transport that supplies the file values.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><pre><code class="language-python">class AvatarIn:
    avatar: UploadedFile

class Profile(Component):
    class Events:
        def upload_avatar(self, data: AvatarIn):
            data.avatar.save(MEDIA_DIR / f&quot;{uuid4()}.png&quot;)
</code></pre></blockquote>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>filename</code>

- The file name the client sent (never a trusted path).
</li>

<li>
<code>size</code>

- The file size in bytes.
</li>

<li>
<code>content_type</code>

- The content type the client sent, or <code>None</code> when the
request did not carry one.
</li>

<li>
<code>native</code>

- The host framework's own file object (e.g. Django's
<code>UploadedFile</code> or Starlette's <code>UploadFile</code>), for the rare
case a handler needs a host-specific capability; <code>None</code> when
there is no host object.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/files.py#L76" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-uploadedfile-file" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>file</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/files.py#L77" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-uploadedfile-filename" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>filename</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/files.py#L78" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-uploadedfile-content-type" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>content_type</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/files.py#L79" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-uploadedfile-native" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>native</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/files.py#L84" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-uploadedfile-size" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>size</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/files.py#L86" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-uploadedfile-read" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>read</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>read(size: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> = -1) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#bytes">bytes</a></code></pre>
</div>

<div class="doc-body">
<p>Read the file's content, synchronously.</p>
<p>A full read (no <code>size</code>) always returns the whole content: a
seekable file is rewound first, so calling <code>read()</code> twice returns
the content twice. A partial <code>read(n)</code> reads the next <code>n</code> bytes
from the current position, like any Python file.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>size</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code>

- How many bytes to read; the whole content when negative.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#bytes">bytes</a>: The bytes read.</p>




</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/files.py#L106" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-uploadedfile-save" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>save</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>save(path: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a></code></pre>
</div>

<div class="doc-body">
<p>Write the file's whole content to <code>path</code>.</p>
<p>A seekable file is rewound first, so <code>save()</code> writes the full
content regardless of earlier reads. The parent directory must
already exist.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>path</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a></code>

- Where to write the file.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a>: The destination as a ``Path``.</p>




</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/view_events.py#L61" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-events-viewevents" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ViewEvents</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/events/#citry-events">Events</a></code></p>


<div class="doc-body">
<p>Base class for verb-shaped <code>Events</code> classes, for ports from view code.</p>
<p>Subclass it as a component's <code>class Events(ViewEvents):</code> and the seven
HTTP verb names (<code>get</code>, <code>post</code>, <code>put</code>, <code>patch</code>, <code>delete</code>,
<code>head</code>, <code>options</code>) become reserved handler names: each one accepts
exactly its own HTTP method, and the extra route
<code>ext/events/e/{class_id}</code> dispatches to it from the request method
alone, so a form can post to the component URL with no event name in it.
Existing handler bodies still need to replace host-specific request
parsing and responses with typed <code>data</code>, the neutral <code>request</code>, and
Events return values.</p>
<p>The verb compatibility route does not require a State token, and verb
handlers cannot inject <code>state</code>. A named runtime call to a verb on a
State-declaring component may still carry the component token. Stateful
work belongs in named event handlers, which can live on the same class.</p>
<p>Prefer naming events after actions: once a component has more than one
mutation, one <code>post</code> that inspects the payload is the multiplexing
this extension exists to remove. Keep the verbs for the initial port,
then split them into named handlers (<code>save</code>, <code>archive</code>, ...) as the
component grows.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><pre><code class="language-python">from citry import Component
from citry.ext.events import ViewEvents

class ContactIn:
    email: str = &quot;&quot;
    message: str = &quot;&quot;

class ContactForm(Component):
    class Events(ViewEvents):
        def post(self, data: ContactIn, request):
            send_message(data.email, data.message)
            return ContactForm()

# &lt;form method=&quot;post&quot;&gt; posting to ext/events/e/{class_id}
# reaches ContactForm.Events.post.
</code></pre></blockquote>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/actions.py" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-events-actions" class="doc-heading">
<span class="doc-symbol doc-symbol-module"></span>
<span class="doc-object-name">
<code>actions</code>
</span>
<span class="doc-kind">module</span>
</h2>


<div class="doc-body">
<p>The action constructors of the <code>events</code> extension: what a handler returns.</p>
<p>An event handler's return value is its whole response, and what flows back to
the browser is <strong>actions</strong>: self-addressed instructions the client runtime
applies in order (design <code>docs/design/events.md</code> 3.4). The capitalized
constructors here build those action values; calling one performs nothing.
Import the namespace once and return what you build::</p>
<pre><code>from citry.ext.events import actions

class Events:
    def save(self, state):
        order = create_order(state.draft_id)
        return [
            actions.Dispatch("order-saved", {"id": order.id}),
            actions.Redirect(f"/orders/{order.id}"),
        ]
</code></pre>
<p>Every envelope action accepts <code>delay</code> (seconds before the client applies the
action). Most also accept <code>wait</code> (whether later actions hold for it). A
<code>Data</code> action always waits because applying it resolves the caller's
promise. <code>Download</code> is not an envelope action; it constructs a raw HTTP
response result.</p>
<p>Turning return values into these actions (dicts, elements, resolver-claimed
values) and encoding them for the wire lives in the sibling <code>results</code>
module; this module is only the vocabulary.</p>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/actions.py#L71" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-events-actions-action" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>Action</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Base class of the action values an event handler returns.</p>
<p>The concrete constructors are <a href="/reference/events/#citry-ext-events-actions-render"><code>Render</code></a>,
<a href="/reference/events/#citry-ext-events-actions-data"><code>Data</code></a>,
<a href="/reference/events/#citry-ext-events-actions-dispatch"><code>Dispatch</code></a>, and
<a href="/reference/events/#citry-ext-events-actions-redirect"><code>Redirect</code></a>, plus the history actions
<a href="/reference/events/#citry-ext-events-actions-pushurl"><code>PushUrl</code></a> and
<a href="/reference/events/#citry-ext-events-actions-replaceurl"><code>ReplaceUrl</code></a>. An action is a plain
value: constructing one performs nothing, and it only takes effect when
the handler returns it (alone or in a list).</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>delay</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#float">float</a></code>

- Seconds the client waits before applying the action. <code>0</code>
(the default) applies it immediately.
</li>

<li>
<code>wait</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code>

- Whether later actions in the same result hold until this one
(and its <code>delay</code>) has applied. <code>True</code> (the default) keeps the
list strictly sequential; <code>False</code> schedules this action and
lets the rest proceed immediately. Concrete actions may require
<code>True</code> when their effect cannot run independently.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/actions.py#L96" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-actions-action-delay" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>delay</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>delay: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#float">float</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/actions.py#L97" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-actions-action-wait" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>wait</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>wait: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/actions.py#L118" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-events-actions-render" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>Render</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/events/#citry-ext-events-actions-action">Action</a></code></p>


<div class="doc-body">
<p>Render a component element server-side and morph it into the page.</p>
<p>The element renders as a citry fragment (markup plus its dependency and
events manifests), and the client swaps it into <code>target</code>. A handler
builds a fresh tree to render; nothing of the instance's original render
is replayed (design <code>events.md</code> 7.5).</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><pre><code class="language-python">def add_to_cart(self, data: CartIn, context):
    cart = add_item(context.user, data.product_id)
    return actions.Render(
        CartBadge(count=cart.count),
        target=&quot;#cart-badge&quot;,
    )
</code></pre></blockquote>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>element</code>

<code><a class="doc-type-link" href="/reference/rendering/#citry-citryelement">CitryElement</a> | <a class="doc-type-link" href="/reference/rendering/#citry-citryrender">CitryRender</a></code>

- What to render: a component element (<code>MyComponent(...)</code>)
or an already-rendered
<a href="/reference/rendering/#citry-citryrender"><code>CitryRender</code></a>.
</li>

<li>
<code>target</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- Where the rendered HTML goes: a CSS selector string (applied
to every match), or <code>None</code> (the default) for the component
instance whose event was called.
</li>

<li>
<code>swap</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- How the HTML is applied: <code>"morph"</code> (the default, a minimal
in-place diff), <code>"replace"</code>, <code>"inner"</code>, <code>"append"</code>,
<code>"prepend"</code>, <code>"remove"</code>, or <code>"none"</code>.
</li>

<li>
<code>delay</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#float">float</a></code>

- Seconds the client waits before applying the action.
</li>

<li>
<code>wait</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code>

- Whether later actions hold until this one has applied.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/actions.py#L153" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-actions-render-element" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>element</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>element: <a class="doc-type-link" href="/reference/rendering/#citry-citryelement">CitryElement</a> | <a class="doc-type-link" href="/reference/rendering/#citry-citryrender">CitryRender</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/actions.py#L154" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-actions-render-target" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>target</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>target: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/actions.py#L155" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-actions-render-swap" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>swap</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>swap: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/actions.py#L194" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-events-actions-data" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>Data</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/events/#citry-ext-events-actions-action">Action</a></code></p>


<div class="doc-body">
<p>Resolve the client caller's promise with a JSON value.</p>
<p>The value becomes the resolution of the <code>$sendEvent</code>,
<code>$component</code> <code>sendEvent</code>, or <code>Citry.events.send</code> promise on the
client. Declarative <code>@c-*</code> bindings discard that promise, so they do
not expose the Data value; return <code>Dispatch</code> when browser code must
observe their result. At most one <code>Data</code> may appear in one handler
result (two would contradict: which value resolves the promise?);
returning a bare <code>dict</code> from a handler builds this action implicitly.</p>



<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>ValueError</code> - If <code>wait</code> is <code>False</code>, or another timing value is
invalid.
</li>

</ul>


<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>value</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code>

- The JSON-serializable value the caller receives.
</li>

<li>
<code>delay</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#float">float</a></code>

- Seconds the client waits before applying the action.
</li>

<li>
<code>wait</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code>

- Always <code>True</code> because applying this action resolves the
caller's promise.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/actions.py#L219" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-actions-data-value" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>value</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>value: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/actions.py#L228" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-events-actions-dispatch" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>Dispatch</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/events/#citry-ext-events-actions-action">Action</a></code></p>


<div class="doc-body">
<p>Dispatch a named browser event (a DOM <code>CustomEvent</code>).</p>
<p>The event fires under the exact given name on the calling instance's first
live root (or on <code>document</code> when the call carries no instance), bubbles,
and reaches <code>onEvent</code> listeners and plain <code>addEventListener</code> alike. A
multi-root or mirrored instance deliberately uses one canonical root so a
logical dispatch reaches document-level listeners only once.
Names starting with <code>citry:</code> are reserved for the runtime's own events;
the documented convention is prefixing with the component name
(<code>"MyCard:submit"</code>).</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>name</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The event name, dispatched verbatim.
</li>

<li>
<code>detail</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code>

- The <code>CustomEvent</code> <code>detail</code> payload, a JSON-serializable
value; <code>None</code> (the default) sends no detail.
</li>

<li>
<code>delay</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#float">float</a></code>

- Seconds the client waits before applying the action.
</li>

<li>
<code>wait</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code>

- Whether later actions hold until this one has applied.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/actions.py#L251" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-actions-dispatch-name" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/actions.py#L252" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-actions-dispatch-detail" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>detail</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>detail: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/actions.py#L268" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-events-actions-redirect" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>Redirect</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/events/#citry-ext-events-actions-action">Action</a></code></p>


<div class="doc-body">
<p>Navigate the page to a URL.</p>
<p>A redirect is an ordinary action, not an HTTP 30x: it applies in list
order like everything else. Actions listed after it race the navigation,
so put it last, or give it <code>delay</code> / <code>wait</code> timing when something
(say a farewell toast) must be seen first:
<code>actions.Redirect(url, delay=5, wait=False)</code>.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>url</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The URL to navigate to.
</li>

<li>
<code>delay</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#float">float</a></code>

- Seconds the client waits before applying the action.
</li>

<li>
<code>wait</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code>

- Whether later actions hold until this one has applied.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/actions.py#L286" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-actions-redirect-url" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/actions.py#L295" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-events-actions-pushurl" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>PushUrl</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/events/#citry-ext-events-actions-action">Action</a></code></p>


<div class="doc-body">
<p>Push a URL onto the browser's history stack without navigating.</p>
<p>The browser changes the address and adds one history entry, but Citry does
not fetch the URL or replace the page. Back and Forward therefore change
the address without restoring component HTML or State; use a client router
when that restoration is required.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>url</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The same-origin URL to place in browser history. Relative URLs,
query strings, and fragments are accepted; the browser resolves
them against the current document.
</li>

<li>
<code>delay</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#float">float</a></code>

- Seconds the client waits before applying the action.
</li>

<li>
<code>wait</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code>

- Whether later actions hold until this one has applied.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/actions.py#L314" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-actions-pushurl-url" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/actions.py#L323" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-events-actions-replaceurl" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ReplaceUrl</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/events/#citry-ext-events-actions-action">Action</a></code></p>


<div class="doc-body">
<p>Replace the browser's current history URL without navigating.</p>
<p>The browser changes the address in place, but Citry does not fetch the URL
or replace the page. Back and Forward therefore change the address without
restoring component HTML or State; use a client router when that
restoration is required.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>url</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The same-origin URL to place in browser history. Relative URLs,
query strings, and fragments are accepted; the browser resolves
them against the current document.
</li>

<li>
<code>delay</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#float">float</a></code>

- Seconds the client waits before applying the action.
</li>

<li>
<code>wait</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code>

- Whether later actions hold until this one has applied.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/actions.py#L342" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-actions-replaceurl-url" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/actions.py#L374" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-events-actions-download" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>Download</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Return a file download from a per-event HTTP handler.</p>
<p>A download is an HTTP response result, not an envelope action. Its handler
must use <code>@event(bundle=False)</code> and be called through its per-event HTTP
route. It may be returned bare or as the only item in a list or tuple.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><pre><code class="language-python">from citry.ext.events import actions, event

@event(bundle=False)
def export(self):
    return actions.Download(
        make_csv(),
        &quot;orders.csv&quot;,
        content_type=&quot;text/csv; charset=utf-8&quot;,
    )
</code></pre></blockquote>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>content</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#bytes">bytes</a></code>

- The response body, as text or raw bytes.
</li>

<li>
<code>filename</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The filename offered to the browser. It may contain Unicode,
but cannot be a path or contain control characters.
</li>

<li>
<code>content_type</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The response's media type. The default is
<code>"application/octet-stream"</code>.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/actions.py#L405" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-actions-download-content" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>content</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>content: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#bytes">bytes</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/actions.py#L406" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-actions-download-filename" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>filename</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>filename: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/actions.py#L407" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ext-events-actions-download-content-type" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>content_type</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>content_type: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/handlers.py#L240" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-events-event" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>event</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>event(func: _F | None = None, name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None = None, methods: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, ...] | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>] | None = None, guard: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[..., <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None = None, csrf: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[..., <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None = None, debounce: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | None = None, throttle: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | None = None, latest_wins: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a> = False, bundle: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a> = True) -> _F | <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[_F], _F]</code></pre>
</div>

<div class="doc-body">
<p>Per-handler configuration for one event handler.</p>
<p>Bare handlers need no decorator; use <code>@event(...)</code> only to override the
component-level defaults for one handler. Every key not given falls back
to the component's underscore config
(<code>_methods</code>, <code>_guard</code>, <code>_csrf</code>, <code>_debounce</code>, <code>_throttle</code>),
which itself falls back to <code>extensions_defaults["events"]</code> and then the
built-in defaults. The queue knobs <code>latest_wins</code> and <code>bundle</code> are the
exception: they exist per handler only, so a call site that needs
different queue semantics names a different handler.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><pre><code class="language-python">from citry.ext.events import event

class Document(Component):
    class Events:
        @event(debounce=400)
        def autosave(self, state: DocState):
            save_draft(state.doc_id, state.title)

        @event(methods=(&quot;GET&quot;,))
        def word_count(self, data: WordCountIn) -&gt; dict:
            return {&quot;words&quot;: count_words(data.doc_id)}
</code></pre></blockquote>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>func</code>

<code>_F | None</code>

- The handler, when used as a bare <code>@event</code> (no arguments).
</li>

<li>
<code>name</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- Wire name override: rename the Python method without touching
templates.
</li>

<li>
<code>methods</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, ...] | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>] | None</code>

- The allowed HTTP methods for this handler, e.g. <code>("GET",)</code>.
</li>

<li>
<code>guard</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[..., <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None</code>

- Per-handler authorization callable; replaces (does not stack
on) the component's <code>_guard</code>.
</li>

<li>
<code>csrf</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[..., <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None</code>

- Per-handler CSRF policy: <code>"auto"</code>, <code>False</code>, or a callable.
</li>

<li>
<code>debounce</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | None</code>

- Client-side debounce, in milliseconds.
</li>

<li>
<code>throttle</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | None</code>

- Client-side throttle, in milliseconds.
</li>

<li>
<code>latest_wins</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code>

- Opt this handler into newest-wins queueing on the
client. When a newer call to the handler is queued for the same
component instance, calls still waiting to be sent are dropped,
and an in-flight one is abandoned (its response is ignored when
it arrives). The server still executes every call it received,
so opt in only when overlapping runs are safe, e.g. an
idempotent autosave. Off by default, because dropping a call is
data loss unless the handler is written for it.
</li>

<li>
<code>bundle</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code>

- Whether the client may send this handler's calls in a shared
batch request alongside other calls that become ready at the
same moment. Pass <code>False</code> for a handler that should always
travel alone, e.g. a slow export that fast toggles should not
wait on.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns">_F | <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[_F], _F]: The handler itself (the decorator only attaches the configuration).</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>ValueError</code> - When a value has the wrong shape (e.g. a <code>methods</code>
string instead of a tuple), at decoration time.
</li>

</ul>



</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/ext/events/routes.py#L115" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ext-events-get-event-url" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>get_event_url</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>get_event_url(comp_cls: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>], name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, query: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None = None, fragment: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None = None) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>The URL one event handler is dispatchable at (the per-event route).</p>
<p>Checks the event exists on the component, so a typo fails at build time
instead of 404-ing at call time. Requires a mounted web integration
(the URL must point somewhere); <code>Citry.build_url</code> raises the standard
pointed error otherwise.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><pre><code class="language-python">from citry.ext.events import get_event_url

get_event_url(TodoList, &quot;search&quot;, query={&quot;q&quot;: &quot;milk&quot;})
</code></pre></blockquote>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>comp_cls</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#type">type</a>[<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>]</code>

- The component class declaring the handler.
</li>

<li>
<code>name</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- The handler's wire name.
</li>

<li>
<code>query</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None</code>

- Optional query parameters to append.
</li>

<li>
<code>fragment</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- Optional <code>#fragment</code> to append.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>: The absolute URL path, e.g. ``&quot;/citry/ext/events/e/Doc_a1b2c3/save&quot;``.</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>ValueError</code> - When the component declares no event of that name.
</li>

<li>
<code>RuntimeError</code> - When no web integration is mounted.
</li>

</ul>



</div>
</div>



