---
title: HTML attributes
url: https://citry.dev/v/0.6.0/reference/attributes/
description: "Helpers for Vue-like class/style merging on HTML elements, and the error raised when Python data sets an attribute name that Vue reads as code."
---
# HTML attributes

Helpers for Vue-like class/style merging on HTML elements, and the error raised when Python data sets an attribute name that Vue reads as code.




<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/attrs.py#L670" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-format-attrs" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>format_attrs</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>format_attrs(attrs: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]) -> <a class="doc-type-link" href="/reference/rendering/#citry-markup">Markup</a></code></pre>
</div>

<div class="doc-body">
<p>Format an attribute dict into an HTML attribute string.</p>
<ul>
<li><code>True</code> renders the bare attribute (<code>disabled</code>); <code>False</code> and
<code>None</code> omit the attribute entirely.</li>
<li><code>class</code> and <code>style</code> values may use the structured forms; they are
normalized here, so <code>merge_attrs</code> output and hand-built dicts render
the same. An empty class or style is omitted.</li>
<li>Everything else renders <code>key="value"</code>, escaped. A value with
<code>__html__</code> (such as <code>Markup</code>) is escaped too, after decoding its
HTML to the text a browser would read, so a <code>"</code> in it cannot end
the attribute.</li>
</ul>
<p>Example::</p>
<pre><code>format_attrs({
    "class": ["btn", {"active": True}],
    "disabled": True,
    "data-id": 3,
})
# -&gt; 'class="btn active" disabled data-id="3"'
</code></pre>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/attrs.py#L545" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-merge-attrs" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>merge_attrs</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>merge_attrs(*attrs_dicts: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] = ()) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">
<p>Merge attribute dicts left to right into one dict.</p>
<p>Every key resolves last-one-wins, except <code>class</code> and <code>style</code>: their
values from all dicts are collected and combined per <code>normalize_class</code>
/ <code>normalize_style</code>, so several sources can contribute classes and
style properties without overwriting each other.</p>
<p>Key order in the result is the order each key was first seen, so a later
override does not move an attribute.</p>
<p>Example::</p>
<pre><code>merge_attrs(
    {"class": "btn", "id": "first"},
    {"class": {"active": True}, "id": "second"},
)
# -&gt; {"class": "btn active", "id": "second"}
</code></pre>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/attrs.py#L388" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-normalize-class" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>normalize_class</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>normalize_class(value: ClassValue) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Turn a structured <code>class</code> value into a plain class string.</p>
<ul>
<li>A string is used as-is (stripped).</li>
<li>A dict keeps only the keys whose value is truthy.</li>
<li>A list may mix strings, dicts, and nested lists. Each item converts to
a <code>{class_name: bool}</code> dict (strings split on whitespace, all
<code>True</code>) and the dicts merge left to right, so a later falsy entry
removes a class added earlier.</li>
</ul>
<p>Example::</p>
<pre><code>normalize_class(["btn btn-lg", {"active": True, "hidden": False}])
# -&gt; "btn btn-lg active"
</code></pre>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/attrs.py#L461" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-normalize-style" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>normalize_style</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>normalize_style(value: StyleValue) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">
<p>Turn a structured <code>style</code> value into an inline CSS string.</p>
<ul>
<li>A string is used as-is (stripped).</li>
<li>A dict renders each entry as <code>property: value;</code>. Property names are
used as written (kebab-case); numbers render bare (<code>width: 100</code>).</li>
<li>A list may mix strings, dicts, and nested lists. Strings are parsed
into property dicts (see <code>parse_string_style</code>) and the dicts merge
left to right, so the last value of a property wins.</li>
</ul>
<p>Two special values steer a merge: <code>None</code> skips the entry (an earlier
value for the property stands), and a literal <code>False</code> removes the
property entirely, even if set earlier.</p>
<p>Example::</p>
<pre><code>normalize_style([
    "color: red; width: 100px",
    {"color": "green", "width": False},
])
# -&gt; "color: green;"
</code></pre>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/attrs.py#L515" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-parse-string-style" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>parse_string_style</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>parse_string_style(css_text: <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/builtins/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">
<p>Parse an inline CSS string into a property dict.</p>
<p>Strips <code>/* ... */</code> comments. A <code>/*</code> inside a quoted value, or right
after a backslash, is kept as text. Declarations split on <code>;</code> except inside
parentheses, so <code>url(data:image/png;base64,...)</code> survives. A
declaration without a <code>:</code> is dropped.</p>
<p>Example::</p>
<pre><code>parse_string_style("color: red; width: 100px; /* note */")
# -&gt; {"color": "red", "width": "100px"}
</code></pre>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/attrs.py#L77" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-vuecodeerror" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>VueCodeError</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/builtins/exceptions.html#TypeError">TypeError</a></code></p>


<div class="doc-body">
<p>Raised when Python data sets an attribute name that Vue would read as code.</p>
<p>Vue reads an attribute whose name starts with <code>v-</code>, <code>:</code>, <code>.</code>, <code>^</code>, <code>@</code>,
or <code>#</code> (in any letter case) as a directive, a binding, a listener, or a
slot, and evaluates its value as JavaScript. Citry lets only the template
author write such names. When one of them comes from Python data
instead, the render fails with this error. Python data sets attribute
names in three places:</p>
<ul>
<li>a <code>c-bind</code> mapping, such as <code>c-bind="attrs"</code> where <code>attrs</code> holds
<code>{"@click": "save()"}</code>;</li>
<li>a <code>c-*</code> attribute whose name, without the <code>c-</code>, starts with one of
those prefixes, such as <code>c-v-if="is_open"</code>;</li>
<li>an extension's <code>on_attrs_resolved</code> hook that adds such a name, or
changes the value of one written in the template.</li>
</ul>
<p>The check runs on HTML elements and component tags, on every page,
while the template renders. It runs even on a page that does not start
Vue, so the same template never works on one page and fails on another.
Citry's own <code>@c-*</code> event bindings and <code>:c-*</code> State bindings are not
Vue code, so <code>c-bind</code> may still carry them.</p>
<p><code>VueCodeError</code> subclasses <code>TypeError</code>, so code that catches
<code>TypeError</code> around a render keeps working.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><p>Write Vue syntax in the template and pass only its data from
Python:</p>
<pre><code class="language-citry-html">&lt;!-- Fails: the mapping sets &quot;@click&quot; --&gt;
&lt;button c-bind=&quot;{'@click': 'save()'}&quot;&gt;Save&lt;/button&gt;

&lt;!-- Works: the listener is written in the template --&gt;
&lt;button @click=&quot;save()&quot;&gt;Save&lt;/button&gt;
</code></pre></blockquote>





</div>
</div>



