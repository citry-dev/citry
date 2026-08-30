---
title: Nodes
url: https://citry.dev/v/0.4.6/reference/nodes/
description: "The runtime node classes the compiled template instantiates."
---
# Nodes

The runtime node classes the compiled template instantiates.




<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L157" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-node" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>Node</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Base class for the runtime nodes the template compiler output instantiates.</p>
<p>A node renders to a body part (a <code>str</code> or a nested <code>CitryRender</code>) against
the render-scoped <code>CitryContext</code>. Concrete nodes override <code>render</code>.</p>
<p>A node sitting in a <em>fill group</em> (a component body that contains
<code>&lt;c-fill&gt;</code> tags) takes part in fill collection through
<code>Node.collect_fills()</code> instead of <code>Node.render()</code>. The default says
the node is not allowed there; nodes that are (<code>FillNode</code>, the control-flow nodes)
override it.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L171" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-node-render" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>render</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>render(context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>) -> RenderPart</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L176" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-node-collect-fills" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>collect_fills</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>collect_fills(context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>, sink: FillSink) -> None</code></pre>
</div>

<div class="doc-body">
<p>Register this node's fills into <code>sink</code>.</p>
<p>Called instead of <code>render</code> when the node sits in a fill group. The
base implementation rejects the node: when a component body contains
<code>&lt;c-fill&gt;</code> tags, all other content must be inside the fills. A node
kind that may sit beside fills (for example one injected by an
extension via <code>on_template_compiled</code>) overrides this to register its
fills with <code>sink.add(...)</code>, recursing into its own bodies with
<code>collect_fills_from_body</code>.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1234" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-componentnode" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ComponentNode</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/nodes/#citry-node">Node</a></code></p>


<div class="doc-body">
<p>A component node (<code>&lt;c-Card&gt;</code>, <code>&lt;c-component&gt;</code>, any <code>&lt;c-*&gt;</code>).</p>
<p>Generated as::</p>
<pre><code>ComponentNode(source, (start, end), (attrs,...), [body], (used_vars,), "name", contains_fills)
</code></pre>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><p>Template <code>&lt;c-Card title="Hi"&gt;body&lt;/c-Card&gt;</code> produces::</p>
<pre><code>ComponentNode(
    source, (0, 21,),
    (StaticHtmlAttr(source, (8, 18,), "title", "Hi", ()),),
    ["body"],
    (), "card", False,
)
</code></pre>
<p>Component names are lowercased (<code>Card</code> -&gt; <code>card</code>); kebab names
are preserved (<code>my-card</code> stays <code>my-card</code>).</p></blockquote>
<p>A tag carrying framework metadata appends one trailing tagged tuple. The
<code>range</code> locus records a logical component-range directive; <code>element</code>
privately carries directives to the dynamic ordinary-element built-in.
Metadata never joins <code>attrs</code> and can therefore never become a kwarg.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1274" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentnode-source" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>source</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1275" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentnode-position" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>position</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1276" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentnode-attrs" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>attrs</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1277" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentnode-body" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>body</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1278" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentnode-used-vars" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>used_vars</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1279" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentnode-name" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1280" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentnode-contains-fills" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>contains_fills</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1281" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentnode-metadata" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>metadata</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1286" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentnode-key" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>key</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>key: <a class="doc-type-link" href="/reference/nodes/#citry-exprhtmlattr">ExprHtmlAttr</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1287" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentnode-morph-mode" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>morph_mode</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>morph_mode: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;ignore&#x27;] | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1322" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-componentnode-render" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>render</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>render(context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>) -> DeferredComponent</code></pre>
</div>

<div class="doc-body">
<p>Work out the child's inputs, but don't render the child yet.</p>
<p>This turns the tag's attributes into the child's kwargs, collects the
body into the child's slots, and returns a <code>DeferredComponent</code>. It
does not render the child here: doing so would make one component
render the next and so on, hitting Python's recursion limit on deeply
nested pages. <code>render_impl</code> renders the child later, with its own
<code>CitryContext</code>, and copies its dependencies into the parent.</p>
<p>The attributes and fill structure are read now, while this component is
still rendering, so a loop variable from an enclosing <code>&lt;c-for&gt;</code> has
the right value. Fill <em>bodies</em> stay lazy: each becomes a <code>Slot</code> that
closes over the current scope and renders only when the child invokes
it.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L898" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-elementattrsnode" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ElementAttrsNode</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/nodes/#citry-node">Node</a></code></p>


<div class="doc-body">
<p>The attribute region of a plain HTML start tag with dynamic attributes.</p>
<p>Generated as: <code>ElementAttrsNode(source, (start, end), (attrs...), ("var1", ...))</code></p>
<p>Emitted when an HTML element (not a component) has at least one dynamic
attribute—a <code>c-*</code> value or a <code>c-bind</code> spread—or a literal extension
binding/output name that must remain structurally visible. The node covers
ALL of the tag's attributes, static ones included, because the set resolves
as one unit:</p>
<ul>
<li>Contributions collect left to right in source order; <code>c-bind</code>
contributes each entry of its mapping (which must be a <code>Mapping</code>).</li>
<li><code>class</code> and <code>style</code> merge across contributions and accept the
structured value forms (string / dict / nested list); every other key
resolves last-one-wins.</li>
<li><code>True</code> renders the bare attribute, <code>False</code> and <code>None</code> omit it,
everything else renders escaped (<code>__html__</code> values pass through).</li>
</ul>
<p>Renders to one string like <code>' class="btn" disabled'</code> (leading space
included) or <code>""</code> when every attribute resolved away.</p>
<p>An <code>on_template_compiled</code> extension may consume parser-proven literal
attributes and collapse an otherwise-static region back to a string before
this node reaches rendering. Events uses that path for <code>@c-*</code> / <code>:c-*</code>.</p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><p>Template <code>&lt;div id="x" c-class="cls"&gt;hi&lt;/div&gt;</code> produces::</p>
<pre><code>ElementAttrsNode(source, (0, 26,), (StaticHtmlAttr(...), ExprHtmlAttr(...),), ("cls",))
</code></pre></blockquote>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L936" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-elementattrsnode-source" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>source</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L937" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-elementattrsnode-position" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>position</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L938" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-elementattrsnode-attrs" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>attrs</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L939" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-elementattrsnode-used-vars" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>used_vars</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L951" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-elementattrsnode-tag-name" class="doc-heading">
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
<p>The element's tag name (e.g. <code>"div"</code>), read from the source slice.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L966" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-elementattrsnode-render" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>render</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>render(context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>) -> RenderPart</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1134" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-elementkeynode" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ElementKeyNode</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/nodes/#citry-node">Node</a></code></p>


<div class="doc-body">
<p>An explicit <code>#c-key</code> on a plain HTML element.</p>
<p>Generated as <code>ElementKeyNode(ExprHtmlAttr(...))</code>. The wrapped attribute
evaluates in the surrounding template scope. <code>None</code> emits nothing, which
makes the element behave exactly as if <code>#c-key</code> were absent. Every other
value, including <code>False</code>, <code>0</code>, and <code>""</code>, emits the escaped composite
key <code>data-citry-key=":&lt;value&gt;"</code>.</p>
<p>The node owns the complete output attribute so omission cannot leave an
empty scope prefix or a dangling quote in the start tag. It stays outside
<code>ElementAttrsNode</code> because framework metadata must not enter ordinary
attribute merging or the <code>on_attrs_resolved</code> extension hook.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>attr</code>

<code><a class="doc-type-link" href="/reference/nodes/#citry-exprhtmlattr">ExprHtmlAttr</a></code>

- The compiled <code>#c-key</code> expression and its source metadata.
</li>

</ul>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1156" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-elementkeynode-attr" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>attr</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1157" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-elementkeynode-source" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>source</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1158" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-elementkeynode-position" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>position</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1159" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-elementkeynode-used-vars" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>used_vars</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1161" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-elementkeynode-render" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>render</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>render(context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>) -> RenderPart</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L601" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-exprnode" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ExprNode</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/nodes/#citry-node">Node</a></code></p>


<div class="doc-body">
<p>A <code>{{ expr }}</code> expression node.</p>
<p>Generated as: <code>ExprNode(source, (start, end), "expr", ("var1", ...))</code></p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><p>Template <code>{{ name }}</code> compiles to::</p>
<pre><code>ExprNode(source, (0, 10,), "name ", ("name",))
</code></pre></blockquote>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L616" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-exprnode-source" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>source</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L617" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-exprnode-position" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>position</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L618" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-exprnode-expr" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>expr</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L619" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-exprnode-used-vars" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>used_vars</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L626" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-exprnode-evaluate" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>evaluate</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>evaluate(variables: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a>], sandboxed: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a> = True) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code></pre>
</div>

<div class="doc-body">
<p>Evaluate the expression against <code>variables</code> and return the raw value.</p>
<p>The compiled evaluator is built on first use and reused (the node is
cached across renders, so the expression compiles once). <code>sandboxed</code>
chooses the security sandbox or plain evaluation; it is read only on the
first call, when the evaluator is compiled, and ignored afterwards (the
instance's setting is fixed, so every call passes the same value).
Called by <code>render</code>, and by the <code>Const</code> optimization
(<code>citry/constness.py</code>), which evaluates an expression ahead of time
when all of its variables are marked constant.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L643" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-exprnode-render" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>render</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>render(context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>) -> RenderPart</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L655" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-exprnode-collect-fills" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>collect_fills</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>collect_fills(context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>, sink: FillSink) -> None</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1767" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-fornode" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ForNode</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/nodes/#citry-node">Node</a></code></p>


<div class="doc-body">
<p>A loop node (<code>&lt;c-for&gt;</code>/<code>&lt;c-empty&gt;</code>).</p>
<p>Generated as: <code>ForNode(source, (for_branch, empty_branch?), (used_vars,))</code></p>
<p>Each branch is a tuple: <code>((start, end), (attrs,), [body], (introduced_vars,))</code></p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><p>Template <code>&lt;c-for each="item in items"&gt;{{ item }}&lt;/c-for&gt;</code> produces
a <code>ForNode</code> with one branch. Adding <code>&lt;c-empty&gt;none&lt;/c-empty&gt;</code>
after it adds a second branch for the empty state.</p></blockquote>
<p>Each branch is <code>((start, end), (attrs,), [body], (introduced_vars,))</code>.
The loop branch carries an <code>each</code> attribute holding a Python comprehension
clause (<code>"item in items"</code>, or the full <code>"x in xs for y in ys if ..."</code>);
<code>introduced_vars</code> are the loop targets it binds.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1789" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-fornode-source" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>source</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1790" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-fornode-branches" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>branches</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1791" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-fornode-used-vars" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>used_vars</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1809" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-fornode-iter-bodies" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>iter_bodies</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>iter_bodies(context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Iterator">Iterator</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[BodyItem], <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>]]</code></pre>
</div>

<div class="doc-body">
<p>Yield <code>(body, context)</code> once per loop iteration.</p>
<p>The <code>each</code> clause is a Python comprehension clause, so the loop is
evaluated by wrapping it in a generator expression that yields the loop
targets as a tuple: <code>each="x in xs if x &gt; 0"</code> becomes
<code>((x,) for x in xs if x &gt; 0)</code>. This reuses Python's own comprehension
semantics, so multi-target unpacking and <code>if</code> filters work for free.</p>
<p>Each iteration's context overlays the loop bindings on the surrounding
<code>variables</code>; it shares the parent's <code>component</code> and <code>extra</code> bag,
so the loop introduces a variable scope without crossing a component
boundary. With no iterations, the optional <code>&lt;c-empty&gt;</code> branch's body
is yielded once, with the surrounding context.</p>
<p>Shared by <code>render</code> and by fill collection (<code>ComponentNode</code> walks
the iterations when gathering <code>&lt;c-fill&gt;</code> tags, so each collected fill
closes over its own iteration's bindings).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1867" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-fornode-render" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>render</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>render(context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>) -> <a class="doc-type-link" href="/reference/rendering/#citry-citryrender">CitryRender</a></code></pre>
</div>

<div class="doc-body">
<p>Render the loop body once per item; the empty branch if there are none.</p>
<p>See <code>iter_bodies</code> for the loop evaluation and scoping rules.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1886" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-fornode-collect-fills" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>collect_fills</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>collect_fills(context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>, sink: FillSink) -> None</code></pre>
</div>

<div class="doc-body">
<p>In a fill group, a <code>&lt;c-for&gt;</code> contributes its fills once per iteration.</p>
<p>Each iteration's fills close over that iteration's loop bindings, so a
fill body using the loop variable keeps the right value no matter when
the child invokes it.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1693" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-ifnode" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>IfNode</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/nodes/#citry-node">Node</a></code></p>


<div class="doc-body">
<p>A conditional node (<code>&lt;c-if&gt;</code>/<code>&lt;c-elif&gt;</code>/<code>&lt;c-else&gt;</code>).</p>
<p>Generated as: <code>IfNode(source, (branch1, branch2, ...), (used_vars,))</code></p>
<p>Each branch is a tuple: <code>((start, end), (attrs,), [body], (introduced_vars,))</code></p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><p>Template <code>&lt;c-if cond="x"&gt;yes&lt;/c-if&gt;&lt;c-else&gt;no&lt;/c-else&gt;</code> produces
an <code>IfNode</code> with two branches - one for the if-body and one for
the else-body.</p></blockquote>
<p>Each branch is <code>((start, end), (attrs,), [body], (introduced_vars,))</code>.
The <code>c-if</code>/<code>c-elif</code> branches carry a <code>cond</code> attribute (an
<code>ExprHtmlAttr</code>); the <code>c-else</code> branch has none and always matches.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1714" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ifnode-source" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>source</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1715" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ifnode-branches" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>branches</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1716" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ifnode-used-vars" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>used_vars</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1718" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ifnode-active-branch-body" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>active_branch_body</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>active_branch_body(context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#list">list</a>[BodyItem] | None</code></pre>
</div>

<div class="doc-body">
<p>Return the body of the first branch that matches, or <code>None</code>.</p>
<p>Branches are tried in source order (<code>c-if</code> then each <code>c-elif</code> then
<code>c-else</code>). A branch's <code>cond</code> attribute is resolved against the
context; the first truthy one wins. A branch with no <code>cond</code> (the
<code>c-else</code>) always matches.</p>
<p>Shared by <code>render</code> and by fill collection (<code>ComponentNode</code> walks
the matching branch when gathering <code>&lt;c-fill&gt;</code> tags).</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1738" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ifnode-render" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>render</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>render(context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>) -> <a class="doc-type-link" href="/reference/rendering/#citry-citryrender">CitryRender</a></code></pre>
</div>

<div class="doc-body">
<p>Render the first branch whose <code>cond</code> is truthy.</p>
<p>If no branch matches, the render is empty. The body renders against the
surrounding <code>context</code> unchanged: an <code>&lt;c-if&gt;</code> introduces no
variables, so there is no new scope.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1756" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-ifnode-collect-fills" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>collect_fills</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>collect_fills(context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>, sink: FillSink) -> None</code></pre>
</div>

<div class="doc-body">
<p>In a fill group, an <code>&lt;c-if&gt;</code> contributes the fills of its matching branch.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1902" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-slotnode" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>SlotNode</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/nodes/#citry-node">Node</a></code></p>


<div class="doc-body">
<p>A slot definition (<code>&lt;c-slot&gt;</code>): the insertion point for slot content.</p>
<p>Generated as::</p>
<pre><code>SlotNode(source, (start, end), (attrs,), [body], (used_vars,), (introduced_vars,))
</code></pre>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><p>Template <code>&lt;c-slot name="header" /&gt;</code> produces::</p>
<pre><code>SlotNode(source, (0, 24,), (StaticHtmlAttr(...),), [], (), ())
</code></pre></blockquote>
<p>Rendering resolves the slot name, looks up the fill the component
received, and invokes it with the slot data; with no fill, the slot's own
body renders as the fallback.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1931" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-slotnode-source" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>source</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1932" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-slotnode-position" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>position</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1933" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-slotnode-attrs" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>attrs</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1934" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-slotnode-body" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>body</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1935" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-slotnode-used-vars" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>used_vars</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1936" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-slotnode-introduced-vars" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>introduced_vars</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L1938" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-slotnode-render" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>render</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>render(context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>) -> RenderPart</code></pre>
</div>

<div class="doc-body">
<p>Render the fill given for this slot, or the slot's own body as fallback.</p>
<p>The slot data (the tag's extra attributes) resolves against the current
context per render of this site, so a slot inside a loop passes
per-iteration data. The fill and the fallback render through the same
path: both are Slots, invoked with <code>(data, fallback)</code>. A fill renders
against the scope where it was written (it closed over it at
collection); the fallback body renders against the current context, as
if the <code>&lt;c-slot&gt;</code> tags were not there.</p>
<p>A required slot with no fill raises, with a "did you mean" hint over
the fills the component received.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L2130" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-fillnode" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>FillNode</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/nodes/#citry-node">Node</a></code></p>


<div class="doc-body">
<p>A slot fill (<code>&lt;c-fill&gt;</code>).</p>
<p>Generated as::</p>
<pre><code>FillNode(source, (start, end), (attrs,), [body], (used_vars,), (introduced_vars,))
</code></pre>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><p>Template <code>&lt;c-fill name="header"&gt;content&lt;/c-fill&gt;</code> produces::</p>
<pre><code>FillNode(source, (0, 40,), (StaticHtmlAttr(...),), ["content"], (), ())
</code></pre></blockquote>
<p>A fill is consumed during fill collection (<code>collect_fills</code> wraps its body
as a <code>Slot</code> and registers it), so it is never rendered as output; it
inherits <code>Node.render</code> raising, and reaching it would mean a
parser/runtime bug.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L2160" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-fillnode-source" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>source</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L2161" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-fillnode-position" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>position</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L2162" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-fillnode-attrs" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>attrs</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L2163" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-fillnode-body" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>body</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L2164" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-fillnode-used-vars" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>used_vars</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L2165" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-fillnode-introduced-vars" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>introduced_vars</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L2167" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-fillnode-collect-fills" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>collect_fills</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>collect_fills(context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>, sink: FillSink) -> None</code></pre>
</div>

<div class="doc-body">
<p>Resolve this fill's attributes and register its body as a <code>Slot</code>.</p>
<p>The Slot closes over <code>context</code>, the scope where the fill was written
(including any loop bindings from an enclosing <code>&lt;c-for&gt;</code>); the body
stays unrendered until the child component invokes the slot.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L668" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-templatenode" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>TemplateNode</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/nodes/#citry-node">Node</a></code></p>


<div class="doc-body">
<p>A nested template value on an HTML tag's dynamic attribute.</p>
<p>Emitted when a <code>c-*</code> attribute value is itself a template (starts with a
tag and ends with a closing tag), as opposed to a plain expression (which
becomes an <code>ExprNode</code>). The <code>expr</code> field holds the nested template
source string.</p>
<p>Generated as: <code>TemplateNode(source, (start, end), "template", ("var1", ...))</code></p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><p>Template <code>&lt;div c-body="&lt;span&gt;{{ x }}&lt;/span&gt;"&gt;</code> compiles the
<code>c-body</code> value to::</p>
<pre><code>TemplateNode(source, (13, 33,), "&lt;span&gt;{{ x }}&lt;/span&gt;", ("x",))
</code></pre></blockquote>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L689" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatenode-source" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>source</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L690" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatenode-position" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>position</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L693" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatenode-expr" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>expr</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L694" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatenode-used-vars" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>used_vars</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L700" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatenode-render" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>render</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>render(context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>) -> <a class="doc-type-link" href="/reference/rendering/#citry-citryrender">CitryRender</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L242" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-htmlattr" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>HtmlAttr</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Base class for HTML attribute nodes (a component's or slot's inputs).</p>
<p>An attribute resolves to a value (which becomes a component kwarg), not to a
rendered body part. Concrete attributes override <code>resolve</code>.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L252" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-htmlattr-key" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>key</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>key: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L253" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-htmlattr-source" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>source</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>source: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L254" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-htmlattr-position" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L256" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-htmlattr-resolve" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>resolve</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>resolve(context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L770" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-exprhtmlattr" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>ExprHtmlAttr</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/nodes/#citry-htmlattr">HtmlAttr</a></code></p>


<div class="doc-body">
<p>A dynamic expression attribute (<code>c-class="expr"</code>).</p>
<p>Generated as: <code>ExprHtmlAttr(source, (start, end), "c-class", "expr", ("var",))</code></p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><p>Template <code>&lt;c-Card c-title="t" /&gt;</code> produces::</p>
<pre><code>ExprHtmlAttr(source, (8, 19,), "c-title", "t", ("t",))
</code></pre></blockquote>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L787" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-exprhtmlattr-source" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>source</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L788" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-exprhtmlattr-position" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>position</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L789" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-exprhtmlattr-key" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>key</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L791" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-exprhtmlattr-expr" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>expr</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L792" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-exprhtmlattr-used-vars" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>used_vars</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L798" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-exprhtmlattr-resolve" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>resolve</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>resolve(context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code></pre>
</div>

<div class="doc-body">
<p>Evaluate the expression and return the raw value.</p>
<p>The value is NOT escaped or stringified: it becomes a component kwarg (a
Python object). Escaping happens later, when the child component renders
the value through an <code>ExprNode</code>. The value is returned without the
<code>Const</code> marker; for an expression that uses no variables (a literal
written in the template), <code>ComponentNode._resolve_inputs</code> adds the
marker where the value becomes a component input.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L729" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-statichtmlattr" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>StaticHtmlAttr</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/nodes/#citry-htmlattr">HtmlAttr</a></code></p>


<div class="doc-body">
<p>A static HTML attribute (<code>key="value"</code>).</p>
<p>Generated as: <code>StaticHtmlAttr(source, (start, end), "key", "value", ())</code></p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><p>Template <code>&lt;c-Card title="Hello" /&gt;</code> produces::</p>
<pre><code>StaticHtmlAttr(source, (8, 21,), "title", "Hello", ())
</code></pre></blockquote>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L746" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-statichtmlattr-source" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>source</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L747" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-statichtmlattr-position" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>position</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L748" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-statichtmlattr-key" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>key</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L749" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-statichtmlattr-value" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>value</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L750" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-statichtmlattr-used-vars" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>used_vars</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L752" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-statichtmlattr-resolve" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>resolve</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>resolve(context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Any">Any</a></code></pre>
</div>

<div class="doc-body">
<p>Return the static value (a string, or <code>True</code> for a boolean attribute).</p>
<p>The value is returned as-is, without the <code>Const</code> marker ("this is
the same on every render"). Attribute values serve double duty: they
can be slot and fill names, provide keys, or component inputs, and
only the component-input use benefits from the marker. So the marking
happens in <code>ComponentNode._resolve_inputs</code>, where the value becomes
a component input, not here.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L824" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-templatehtmlattr" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>TemplateHtmlAttr</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="/reference/nodes/#citry-htmlattr">HtmlAttr</a></code></p>


<div class="doc-body">
<p>A nested template attribute (<code>c-body="&lt;div&gt;...&lt;/div&gt;"</code>).</p>
<p>Generated as: <code>TemplateHtmlAttr(source, (start, end), "c-body", "&lt;div&gt;...&lt;/div&gt;", ("var",))</code></p>
<blockquote class="doc-admonition"><p class="doc-admonition-title">Example</p><p>Template <code>&lt;c-Card c-body="&lt;span&gt;{{ x }}&lt;/span&gt;" /&gt;</code> produces::</p>
<pre><code>TemplateHtmlAttr(source, (8, 37,), "c-body", "&lt;span&gt;{{ x }}&lt;/span&gt;", ("x",))
</code></pre></blockquote>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L848" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatehtmlattr-source" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>source</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L849" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatehtmlattr-position" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>position</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L850" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatehtmlattr-key" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>key</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L851" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatehtmlattr-template" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>template</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L852" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatehtmlattr-used-vars" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>used_vars</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L853" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatehtmlattr-foreign-spans" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>foreign_spans</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L854" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatehtmlattr-source-offset" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>source_offset</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/nodes/__init__.py#L860" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatehtmlattr-resolve" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>resolve</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>resolve(context: <a class="doc-type-link" href="/reference/rendering/#citry-citrycontext">CitryContext</a>) -> <a class="doc-type-link" href="/reference/rendering/#citry-citryrender">CitryRender</a></code></pre>
</div>

<div class="doc-body">
<p>Render the nested template and return it as a <code>CitryRender</code> kwarg value.</p>
<p>The template is defined in the parent's scope, so it renders against the
surrounding component's context (the same rule as <code>TemplateNode</code>).</p>





</div>
</div>


</div>

</div>
</div>



