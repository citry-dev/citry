---
title: HTML attributes
url: https://citry.dev/v/0.4.6/reference/attributes/
description: "Helpers for Vue-like class/style merging on HTML elements."
---
# HTML attributes

Helpers for Vue-like class/style merging on HTML elements.




<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/attrs.py#L348" target="_blank" rel="noopener">
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
<pre><code>format_attrs(attrs: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]) -> <a class="doc-type-link" href="/reference/rendering/#citry-markup">Markup</a></code></pre>
</div>

<div class="doc-body">
<p>Format an attribute dict into an HTML attribute string.</p>
<ul>
<li><code>True</code> renders the bare attribute (<code>disabled</code>); <code>False</code> and
<code>None</code> omit the attribute entirely.</li>
<li><code>class</code> and <code>style</code> values may use the structured forms; they are
normalized here, so <code>merge_attrs</code> output and hand-built dicts render
the same. An empty class or style is omitted.</li>
<li>Everything else renders <code>key="value"</code>, escaped; values with
<code>__html__</code> pass through unescaped.</li>
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/attrs.py#L260" target="_blank" rel="noopener">
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
<pre><code>merge_attrs(*attrs_dicts: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>] = ()) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/attrs.py#L132" target="_blank" rel="noopener">
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
<pre><code>normalize_class(value: ClassValue) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/attrs.py#L183" target="_blank" rel="noopener">
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
<pre><code>normalize_style(value: StyleValue) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
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
<pre><code>normalize_style(["color: red; width: 100px", {"color": "green", "width": False}])
# -&gt; "color: green;"
</code></pre>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/attrs.py#L231" target="_blank" rel="noopener">
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
<pre><code>parse_string_style(css_text: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#dict">dict</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>]</code></pre>
</div>

<div class="doc-body">
<p>Parse an inline CSS string into a property dict.</p>
<p>Strips <code>/* ... */</code> comments. Declarations split on <code>;</code> except inside
parentheses, so <code>url(data:image/png;base64,...)</code> survives. A
declaration without a <code>:</code> is dropped.</p>
<p>Example::</p>
<pre><code>parse_string_style("color: red; width: 100px; /* note */")
# -&gt; {"color": "red", "width": "100px"}
</code></pre>





</div>
</div>



