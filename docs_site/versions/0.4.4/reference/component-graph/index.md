---
title: Component graph
url: https://citry.dev/v/0.4.4/reference/component-graph/
description: "Authored component dependencies, reverse references, source locations, and partial-analysis problems."
---
# Component graph

Authored component dependencies, reverse references, source locations, and partial-analysis problems.




<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L355" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-componentgraph" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ComponentGraph</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Hold a versioned snapshot of authored dependencies between registered components.</p>
<p>Build a graph with
<a href="/reference/citry/#citry-citry-inspect-component-graph"><code>Citry.inspect_component_graph()</code></a>.
Query direct dependencies or reverse references by primary name, alias, or
a node returned from the same graph.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><pre><code class="language-python">graph = app.inspect_component_graph()

for dependency in graph.dependencies(&quot;page&quot;):
    print(dependency.name)

for dependent in graph.dependents(&quot;button&quot;):
    print(dependent.name)
</code></pre></blockquote>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>schema_version</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code>

- Graph JSON schema version.
</li>

<li>
<code>citry_version</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Installed Citry package version used to build the graph.
</li>

<li>
<code>engine_id</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Runtime identity of the inspected Citry instance.
</li>

<li>
<code>nodes</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/component-graph/#citry-componentgraphnode">ComponentGraphNode</a>, ...]</code>

- Registered component definitions in canonical order.
</li>

<li>
<code>references</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/component-graph/#citry-componentgraphreference">ComponentGraphReference</a>, ...]</code>

- Resolved authored occurrences in canonical source order.
</li>

<li>
<code>unresolved</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/component-graph/#citry-unresolvedcomponentreference">UnresolvedComponentReference</a>, ...]</code>

- Unknown and dynamic authored occurrences.
</li>

<li>
<code>problems</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/component-graph/#citry-componentgraphproblem">ComponentGraphProblem</a>, ...]</code>

- Sources that could not be inspected completely.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L387" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraph-schema-version" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L388" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraph-citry-version" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L389" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraph-engine-id" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L390" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraph-nodes" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>nodes</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>nodes: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/component-graph/#citry-componentgraphnode">ComponentGraphNode</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L391" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraph-references" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>references</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>references: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/component-graph/#citry-componentgraphreference">ComponentGraphReference</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L392" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraph-unresolved" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>unresolved</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>unresolved: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/component-graph/#citry-unresolvedcomponentreference">UnresolvedComponentReference</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L393" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraph-problems" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>problems</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>problems: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/component-graph/#citry-componentgraphproblem">ComponentGraphProblem</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L469" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraph-coverage-complete" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>coverage_complete</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>coverage_complete: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Whether every selected primary template was available and parseable.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L474" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraph-fully-resolved" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>fully_resolved</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>fully_resolved: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Whether source coverage is complete and every reference has a static target.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L478" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraph-component" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>component</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component(selector: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="/reference/component-graph/#citry-componentgraphnode">ComponentGraphNode</a>) -> <a class="doc-type-link" href="/reference/component-graph/#citry-componentgraphnode">ComponentGraphNode</a></code></pre>
</div>

<div class="doc-body">
<p>Return one graph node selected by registered name, alias, or retained node.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>selector</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="/reference/component-graph/#citry-componentgraphnode">ComponentGraphNode</a></code>

- Case-insensitive registered name or a node from this graph.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="/reference/component-graph/#citry-componentgraphnode">ComponentGraphNode</a>: The canonical node stored in this graph.</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>TypeError</code> - If <code>selector</code> is not a string or graph node.
</li>

<li>
<code>NotRegistered</code> - If the selector does not identify this graph's exact
component generation.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L508" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraph-dependencies" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>dependencies</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>dependencies(component: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="/reference/component-graph/#citry-componentgraphnode">ComponentGraphNode</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/component-graph/#citry-componentgraphnode">ComponentGraphNode</a>, ...]</code></pre>
</div>

<div class="doc-body">
<p>Return unique registered components directly referenced by <code>component</code>.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L518" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraph-dependents" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>dependents</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>dependents(component: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="/reference/component-graph/#citry-componentgraphnode">ComponentGraphNode</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/component-graph/#citry-componentgraphnode">ComponentGraphNode</a>, ...]</code></pre>
</div>

<div class="doc-body">
<p>Return unique registered components that directly reference <code>component</code>.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L528" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraph-references-from" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>references_from</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>references_from(component: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="/reference/component-graph/#citry-componentgraphnode">ComponentGraphNode</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/component-graph/#citry-componentgraphreference">ComponentGraphReference</a>, ...]</code></pre>
</div>

<div class="doc-body">
<p>Return every resolved authored reference owned by <code>component</code>.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L535" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraph-references-to" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>references_to</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>references_to(component: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="/reference/component-graph/#citry-componentgraphnode">ComponentGraphNode</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/component-graph/#citry-componentgraphreference">ComponentGraphReference</a>, ...]</code></pre>
</div>

<div class="doc-body">
<p>Return every resolved authored reference targeting <code>component</code>.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L542" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraph-unresolved-from" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>unresolved_from</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>unresolved_from(component: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | <a class="doc-type-link" href="/reference/component-graph/#citry-componentgraphnode">ComponentGraphNode</a> | None = None) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/component-graph/#citry-unresolvedcomponentreference">UnresolvedComponentReference</a>, ...]</code></pre>
</div>

<div class="doc-body">
<p>Return unresolved references from one component, or all of them when omitted.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L554" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraph-to-dict" class="doc-heading">
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
<p>Return a fresh JSON-ready dictionary for this graph.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L568" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraph-to-json" class="doc-heading">
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
<p>Serialize this graph to deterministic UTF-8 JSON text.</p>

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
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>: Deterministic JSON with recursively sorted object keys.</p>


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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L104" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-componentgraphnode" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ComponentGraphNode</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Identify one registered component definition in an authored dependency graph.</p>
<p>Use <code>name</code> in templates and graph queries. <code>aliases</code> contains the other
registered spellings that resolve to the same component.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><pre><code class="language-python">graph = app.inspect_component_graph()
card = graph.component(&quot;card&quot;)
print(card.name)
</code></pre></blockquote>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>class_id</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Stable identity for the component's Python route.
</li>

<li>
<code>engine_id</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Runtime identity of the Citry instance that built the graph.
</li>

<li>
<code>definition_id</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Runtime identity of this exact class generation.
</li>

<li>
<code>name</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Canonical registered component name.
</li>

<li>
<code>aliases</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, ...]</code>

- Other registered names for the same component.
</li>

<li>
<code>builtin</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code>

- Whether Citry created this framework component.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L129" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraphnode-class-id" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L130" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraphnode-engine-id" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L131" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraphnode-definition-id" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L132" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraphnode-name" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L133" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraphnode-aliases" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L134" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraphnode-builtin" class="doc-heading">
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


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L221" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-componentgraphreference" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ComponentGraphReference</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Describe one authored component reference that resolves to a registered target.</p>
<p>Repeated invocations remain separate records. Use
<a href="/reference/component-graph/#citry-componentgraph-dependencies"><code>ComponentGraph.dependencies</code></a> when
you need unique target components.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>source_definition_id</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Exact component definition that owns the source.
</li>

<li>
<code>target_definition_id</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Exact registered target definition.
</li>

<li>
<code>registered_name</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Normalized registry name that matched the reference.
</li>

<li>
<code>authored_name</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Target name exactly as written by the author.
</li>

<li>
<code>syntax</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;tag&#x27;, &#x27;static-selector&#x27;]</code>

- Whether the target came from a tag or static selector.
</li>

<li>
<code>location</code>

<code><a class="doc-type-link" href="/reference/component-graph/#citry-componentgraphlocation">ComponentGraphLocation</a></code>

- Authored source occurrence.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L240" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraphreference-source-definition-id" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>source_definition_id</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>source_definition_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L241" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraphreference-target-definition-id" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>target_definition_id</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>target_definition_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L242" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraphreference-registered-name" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>registered_name</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>registered_name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L243" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraphreference-authored-name" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>authored_name</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>authored_name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L244" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraphreference-syntax" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>syntax</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>syntax: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;tag&#x27;, &#x27;static-selector&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L245" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraphreference-location" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>location</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>location: <a class="doc-type-link" href="/reference/component-graph/#citry-componentgraphlocation">ComponentGraphLocation</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L261" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-unresolvedcomponentreference" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>UnresolvedComponentReference</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Describe an authored component reference whose target is not statically known.</p>
<p><code>unknown-component</code> retains the written name. <code>dynamic-target</code> uses
<code>authored_name=None</code> because the runtime expression or spread chooses it.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>source_definition_id</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Exact component definition that owns the source.
</li>

<li>
<code>authored_name</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- Written target name, or <code>None</code> for a dynamic target.
</li>

<li>
<code>reason</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;unknown-component&#x27;, &#x27;dynamic-target&#x27;]</code>

- Whether the name is unknown or the target is dynamic.
</li>

<li>
<code>syntax</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;tag&#x27;, &#x27;static-selector&#x27;, &#x27;dynamic-selector&#x27;]</code>

- Authored tag or selector form.
</li>

<li>
<code>location</code>

<code><a class="doc-type-link" href="/reference/component-graph/#citry-componentgraphlocation">ComponentGraphLocation</a></code>

- Authored source occurrence.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L278" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-unresolvedcomponentreference-source-definition-id" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>source_definition_id</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>source_definition_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L279" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-unresolvedcomponentreference-authored-name" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>authored_name</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>authored_name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L280" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-unresolvedcomponentreference-reason" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>reason</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>reason: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;unknown-component&#x27;, &#x27;dynamic-target&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L281" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-unresolvedcomponentreference-syntax" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>syntax</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>syntax: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;tag&#x27;, &#x27;static-selector&#x27;, &#x27;dynamic-selector&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L282" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-unresolvedcomponentreference-location" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>location</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>location: <a class="doc-type-link" href="/reference/component-graph/#citry-componentgraphlocation">ComponentGraphLocation</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L156" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-componentgraphlocation" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ComponentGraphLocation</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Point to one component reference in an authored primary template.</p>
<p><code>start_index</code> and <code>end_index</code> are half-open UTF-8 byte offsets in the
normalized root template. <code>source_range</code> carries the same span as
zero-based UTF-16 positions for editors.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>origin</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Human-readable template origin.
</li>

<li>
<code>source_kind</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;inline&#x27;, &#x27;file&#x27;]</code>

- Whether the template is inline or file-backed.
</li>

<li>
<code>declared_on</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code>

- Import path of the class that declared the template.
</li>

<li>
<code>declaration_file</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a> | None</code>

- Python file containing that declaration, when known.
</li>

<li>
<code>template_file</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a> | None</code>

- Resolved file-backed template path, when applicable.
</li>

<li>
<code>start_index</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code>

- Inclusive UTF-8 byte offset in the root template.
</li>

<li>
<code>end_index</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code>

- Exclusive UTF-8 byte offset in the root template.
</li>

<li>
<code>source_range</code>

<code><a class="doc-type-link" href="/reference/template-analysis/#citry-lsprange">LspRange</a></code>

- Equivalent zero-based UTF-16 editor range.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L177" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraphlocation-origin" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L178" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraphlocation-source-kind" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>source_kind</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>source_kind: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;inline&#x27;, &#x27;file&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L179" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraphlocation-declared-on" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L180" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraphlocation-declaration-file" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>declaration_file</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>declaration_file: <a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L181" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraphlocation-template-file" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>template_file</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>template_file: <a class="doc-type-link" href="https://docs.python.org/3.13/library/pathlib.html#pathlib.Path">Path</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L182" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraphlocation-start-index" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>start_index</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>start_index: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L183" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraphlocation-end-index" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>end_index</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>end_index: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L184" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraphlocation-source-range" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>source_range</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>source_range: <a class="doc-type-link" href="/reference/template-analysis/#citry-lsprange">LspRange</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L311" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-componentgraphproblem" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ComponentGraphProblem</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Report why Citry could not inspect part of an authored template source.</p>
<p>Graph construction continues after a problem, so callers can use references
from unaffected components. <code>component_definition_ids</code> identifies every
selected component that consumes the affected physical source.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>component_definition_ids</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, ...]</code>

- Sorted exact definitions affected.
</li>

<li>
<code>code</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Stable graph-local problem category.
</li>

<li>
<code>message</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Human-readable explanation.
</li>

<li>
<code>origin</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Source or declaration that failed.
</li>

<li>
<code>location</code>

<code><a class="doc-type-link" href="/reference/component-graph/#citry-componentgraphlocation">ComponentGraphLocation</a> | None</code>

- Authored range when the failure supplied one.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L329" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraphproblem-component-definition-ids" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_definition_ids</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component_definition_ids: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L330" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraphproblem-code" class="doc-heading">
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






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L331" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraphproblem-message" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>message</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>message: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L332" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraphproblem-origin" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/component_graph.py#L333" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentgraphproblem-location" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>location</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>location: <a class="doc-type-link" href="/reference/component-graph/#citry-componentgraphlocation">ComponentGraphLocation</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>



