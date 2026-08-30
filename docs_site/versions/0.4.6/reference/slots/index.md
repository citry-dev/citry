---
title: Slots
url: https://citry.dev/v/0.4.6/reference/slots/
description: "The slot value and fill types."
---
# Slots

The slot value and fill types.




<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/slots.py#L189" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-slot" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>Slot</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Generic">Generic</a></code></p>


<div class="doc-body">
<p>Normalized slot content: a lazy, repeatable, standalone callable.</p>
<p>Construct it from a string, a function, a <code>CitryElement</code>, a
<code>ComponentLike</code>, or a <code>CitryRender</code>. Calling the Slot returns a render
part; <code>str(slot)</code> renders and serializes in one step. A standalone Slot
containing a <code>ComponentLike</code> cannot resolve without an active component
render.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><p>::</p>
<pre><code>Slot("Hello!")                                # static content
Slot(lambda ctx: f"Hi {ctx.data.name}!")   # content function
Slot(Card(title="Hi"))                        # composed element
</code></pre></blockquote>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/slots.py#L235" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-slot-contents" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>contents</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">
<p>The original value the Slot was created from.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/slots.py#L237" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-slot-component-name" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_name</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">
<p>Name of the component this slot content was given to (for debugging).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/slots.py#L239" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-slot-slot-name" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>slot_name</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">
<p>Name of the slot this content fills (for debugging).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/slots.py#L241" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-slot-source-position" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>source_position</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">
<p>The <code>(start, end)</code> span of the <code>&lt;c-fill&gt;</code> in its template, if any.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/slots.py#L243" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-slot-extra" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>extra</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>extra: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">
<p>Scratch space for extensions to attach per-slot metadata.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/slots.py#L251" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-slot-content-func" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>content_func</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>content_func: <a class="doc-type-link" href="/reference/slots/#citry-slotfunc">SlotFunc</a>[TSlotData]</code></pre>
</div>

<div class="doc-body">
<p>The content function. Call the Slot itself instead of calling this directly.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/slots.py#L130" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-slotcontext" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>SlotContext</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Generic">Generic</a></code></p>


<div class="doc-body">
<p>The single argument a slot function receives.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><p>::</p>
<pre><code>def my_slot(ctx: SlotContext) -&gt; str:
    return f"Hello, {ctx.data.name}!"
</code></pre></blockquote>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/slots.py#L143" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-slotcontext-data" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>data</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>data: TSlotData</code></pre>
</div>

<div class="doc-body">
<p>Data passed to the slot by the <code>&lt;c-slot&gt;</code> tag (its extra attributes), or
by the caller when the Slot is invoked directly. At runtime this is an
immutable <a href="/reference/slots/#citry-slotdata"><code>SlotData</code></a>; the type parameter may describe a
more precise component-specific field shape.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/slots.py#L151" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-slotcontext-fallback" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>fallback</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>fallback: <a class="doc-type-link" href="/reference/slots/#citry-slot">Slot</a> | None</code></pre>
</div>

<div class="doc-body">
<p>The slot's fallback content (the body of the <code>&lt;c-slot&gt;</code> tag), as a Slot.</p>
<p><code>None</code> when the Slot is called directly, outside a <code>&lt;c-slot&gt;</code> site.
Coerce it to a string (or render it via <code>{{ fallback }}</code>) to render the
fallback.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/slots.py#L160" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-slotcontext-provides" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>provides</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>provides: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None</code></pre>
</div>

<div class="doc-body">
<p>The provide/inject entries active where the Slot was invoked (the
<code>&lt;c-slot&gt;</code> site or expression site). <code>None</code> when the Slot is called
directly, outside a render. Template-defined fills use this so their
bodies render with the invoking site's provides; a slot function may read
it to inspect provided data.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/slots.py#L52" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-slotdata" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>SlotData</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a></code></p>


<div class="doc-body">
<p>Immutable data passed from a slot outlet to its fill.</p>
<p>Identifier-like keys are available as attributes, while every key remains
available through mapping access. Keys beginning with an underscore and
keys that collide with mapping methods intentionally require bracket
access or fill-data destructuring.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><p>::</p>
<pre><code>data = SlotData({"label": "Save", "aria-label": "Save item"})
data.label
data["aria-label"]
</code></pre></blockquote>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>values</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] | None</code>

- The slot data values. Citry takes a shallow copy so later
changes to the input mapping do not change a retained slot call.
</li>

</ul>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/slots.py#L170" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-slotfunc" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>SlotFunc</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Protocol">Protocol</a></code></p>


<div class="doc-body">
<p>The signature of a slot content function.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><p>::</p>
<pre><code>def header(ctx: SlotContext) -&gt; str:
    if ctx.data.get("name"):
        return f"Hello, {ctx.data.name}!"
    return str(ctx.fallback)
</code></pre></blockquote>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/slots.py#L361" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-slotinput" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>SlotInput</code>
</span>
<span class="doc-kind">attribute</span>
</h2>


<div class="doc-body">
<p>All forms in which slot content can be passed to a component.</p>
<p>Use this to type the fields of a component's <code>Slots</code> class::</p>
<pre><code>class Table(Component):
    class Slots:
        header: SlotInput
        footer: SlotInput[FooterSlotData]
</code></pre>
<p>A field without a default must be filled whenever the component is used. A
field annotated as <code>SlotInput | None</code> with a <code>None</code> default is optional.
The <code>required</code> attribute on <code>&lt;c-slot&gt;</code> checks something different: it
raises an error only if Citry renders that tag without content.</p>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/slots.py#L117" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-slotresult" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>SlotResult</code>
</span>
<span class="doc-kind">attribute</span>
</h2>


<div class="doc-body">
<p>What a slot function may return.</p>
<p>A plain <code>str</code> is escaped when the slot renders; <code>Markup</code> or a
<code>CitryRender</code> is trusted and inlined as-is. A <code>ComponentLike</code> resolves
against the Citry instance rendering the slot.</p>





</div>
</div>



