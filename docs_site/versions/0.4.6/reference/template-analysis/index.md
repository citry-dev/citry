---
title: Template analysis
url: https://citry.dev/v/0.4.6/reference/template-analysis/
description: "Discovery, analysis, source mapping, and formatting for Python-embedded templates."
---
# Template analysis

Discovery, analysis, source mapping, and formatting for Python-embedded templates.




<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L767" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-lspposition" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>LspPosition</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>A zero-based line and UTF-16 character position used by LSP clients.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>line</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code>

- Zero-based source line.
</li>

<li>
<code>character</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code>

- Zero-based UTF-16 code-unit offset on that line.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L778" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-lspposition-line" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>line</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>line: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L779" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-lspposition-character" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>character</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>character: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L782" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-lsprange" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>LspRange</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>A half-open LSP range in a source document.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>start</code>

<code><a class="doc-type-link" href="/reference/template-analysis/#citry-lspposition">LspPosition</a></code>

- Inclusive start position.
</li>

<li>
<code>end</code>

<code><a class="doc-type-link" href="/reference/template-analysis/#citry-lspposition">LspPosition</a></code>

- Exclusive end position.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L793" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-lsprange-start" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>start</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>start: <a class="doc-type-link" href="/reference/template-analysis/#citry-lspposition">LspPosition</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L794" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-lsprange-end" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>end</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>end: <a class="doc-type-link" href="/reference/template-analysis/#citry-lspposition">LspPosition</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1866" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-pythoncomponentassetdiscovery" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>PythonComponentAssetDiscovery</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Conservative direct literal and static file component assets.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1870" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetdiscovery-regions" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>regions</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>regions: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetregion">PythonComponentAssetRegion</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1871" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetdiscovery-files" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>files</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>files: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetfile">PythonComponentAssetFile</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1872" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetdiscovery-notices" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>notices</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>notices: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetnotice">PythonComponentAssetNotice</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1873" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetdiscovery-valid-python" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>valid_python</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>valid_python: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1846" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-pythoncomponentassetfile" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>PythonComponentAssetFile</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>One statically proven direct component asset-file declaration.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1850" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetfile-component-name" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_name</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component_name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1851" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetfile-kind" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>kind</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>kind: <a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetkind">PythonComponentAssetKind</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1852" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetfile-path" class="doc-heading">
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


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1940" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-pythoncomponentassetformatresult" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>PythonComponentAssetFormatResult</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>One validated, atomic Python component-asset formatting result.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>source</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Complete formatted Python source.
</li>

<li>
<code>changed_component_assets</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetkind">PythonComponentAssetKind</a>], ...]</code>

- Changed <code>(component_name, kind)</code> pairs.
</li>

<li>
<code>notices</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetnotice">PythonComponentAssetNotice</a>, ...]</code>

- Assets left unchanged with an explicit reason.
</li>

<li>
<code>providers</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, ...]</code>

- Sorted provider identities reported by accepted results.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1953" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetformatresult-source" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1954" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetformatresult-changed-component-assets" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>changed_component_assets</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>changed_component_assets: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetkind">PythonComponentAssetKind</a>], ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1955" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetformatresult-notices" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>notices</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>notices: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetnotice">PythonComponentAssetNotice</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1956" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetformatresult-providers" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>providers</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>providers: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1821" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-pythoncomponentassetkind" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>PythonComponentAssetKind</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>, <code><a class="doc-type-link" href="https://docs.python.org/3.13/library/enum.html#enum.Enum">Enum</a></code></p>


<div class="doc-body">
<p>A direct Citry component asset selected for formatting.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1824" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetkind-template" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>TEMPLATE</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1825" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetkind-js" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>JS</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1826" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetkind-css" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>CSS</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1855" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-pythoncomponentassetnotice" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>PythonComponentAssetNotice</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>A component-specific reason why one asset was skipped or unchanged.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1859" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetnotice-component-name" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_name</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component_name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1860" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetnotice-kind" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>kind</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>kind: <a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetkind">PythonComponentAssetKind</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1861" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetnotice-code" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1862" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetnotice-message" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1863" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetnotice-request-id" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>request_id</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>request_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1913" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-pythoncomponentassetplan" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>PythonComponentAssetPlan</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>An immutable Python-source plan awaiting JavaScript and CSS providers.</p>
<p>A plan is bound to the complete source passed to
<a href="/reference/template-analysis/#citry-prepare-python-component-assets"><code>prepare_python_component_assets</code></a>.
Provider work may happen asynchronously before the caller passes every
reply to <a href="/reference/template-analysis/#citry-finish-python-component-assets"><code>finish_python_component_assets</code></a>.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>id</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Stable source and selection identity echoed by provider results.
</li>

<li>
<code>source</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Complete original Python source.
</li>

<li>
<code>requests</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetrequest">PythonComponentAssetRequest</a>, ...]</code>

- Standalone JavaScript and CSS provider requests.
</li>

<li>
<code>notices</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetnotice">PythonComponentAssetNotice</a>, ...]</code>

- Non-fatal embedded regions that could not be delegated.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1931" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetplan-id" class="doc-heading">
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






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1932" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetplan-source" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1933" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetplan-requests" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>requests</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>requests: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetrequest">PythonComponentAssetRequest</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1934" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetplan-notices" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>notices</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>notices: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetnotice">PythonComponentAssetNotice</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1829" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-pythoncomponentassetregion" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>PythonComponentAssetRegion</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>One definite direct literal asset on a Citry component class.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>component_name</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Name of the declaring component class.
</li>

<li>
<code>kind</code>

<code><a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetkind">PythonComponentAssetKind</a></code>

- Component attribute represented by this region.
</li>

<li>
<code>source_map</code>

<code><a class="doc-type-link" href="/reference/template-analysis/#citry-pythontemplatesourcemap">PythonTemplateSourceMap</a></code>

- Mapping between the decoded asset and its Python literal.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1841" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetregion-component-name" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_name</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component_name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1842" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetregion-kind" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>kind</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>kind: <a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetkind">PythonComponentAssetKind</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1843" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetregion-source-map" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>source_map</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>source_map: <a class="doc-type-link" href="/reference/template-analysis/#citry-pythontemplatesourcemap">PythonTemplateSourceMap</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1876" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-pythoncomponentassetrequest" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>PythonComponentAssetRequest</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>One standalone JavaScript or CSS document offered to a provider.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>plan_id</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Identity of the source-bound Python formatting plan.
</li>

<li>
<code>id</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Identity of this request within the plan.
</li>

<li>
<code>component_name</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Name of the declaring component class.
</li>

<li>
<code>asset_kind</code>

<code><a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetkind">PythonComponentAssetKind</a></code>

- Component asset containing this provider region.
</li>

<li>
<code>language</code>

<code>EmbeddedLanguage</code>

- Standalone language expected by the provider.
</li>

<li>
<code>region_kind</code>

<code>EmbeddedRegionKind | None</code>

- Template body kind, or <code>None</code> for a direct <code>js</code> or
<code>css</code> literal.
</li>

<li>
<code>source</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Decoded provider-owned source.
</li>

<li>
<code>virtual_source</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Standalone source to send to the provider.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1894" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetrequest-plan-id" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>plan_id</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>plan_id: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1895" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetrequest-id" class="doc-heading">
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






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1896" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetrequest-component-name" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_name</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component_name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1897" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetrequest-asset-kind" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>asset_kind</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>asset_kind: <a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetkind">PythonComponentAssetKind</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1898" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetrequest-language" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>language</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>language: EmbeddedLanguage</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1899" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetrequest-region-kind" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>region_kind</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>region_kind: EmbeddedRegionKind | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1900" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetrequest-source" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1901" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythoncomponentassetrequest-virtual-source" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>virtual_source</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>virtual_source: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1743" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-pythontemplatediscovery" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>PythonTemplateDiscovery</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Conservative inline template regions and non-parser notices.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1747" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythontemplatediscovery-regions" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>regions</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>regions: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/template-analysis/#citry-pythontemplateregion">PythonTemplateRegion</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1748" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythontemplatediscovery-notices" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>notices</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>notices: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/template-analysis/#citry-pythontemplatenotice">PythonTemplateNotice</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1749" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythontemplatediscovery-valid-python" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>valid_python</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>valid_python: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1787" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-pythontemplateformaterror" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>PythonTemplateFormatError</code>
</span>
<span class="doc-kind">class</span>
</h2>

<p class="doc-class-bases">Bases: <code><a class="doc-type-link" href="https://docs.python.org/3.13/library/exceptions.html#ValueError">ValueError</a></code></p>


<div class="doc-body">
<p>A formatting refusal that never exposes a partial Python candidate.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>code</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Stable formatter failure code.
</li>

<li>
<code>notices</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/template-analysis/#citry-pythontemplatenotice">PythonTemplateNotice</a>, ...]</code>

- Component-specific reasons relevant to the refusal.
</li>

<li>
<code>range</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a>] | None</code>

- Optional absolute half-open Python string-offset range.
</li>

<li>
<code>diagnostic</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a> | None</code>

- Optional nested parser diagnostic. Template parser
diagnostic offsets remain relative to the decoded template.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1815" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythontemplateformaterror-code" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1816" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythontemplateformaterror-notices" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>notices</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>notices: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/template-analysis/#citry-pythontemplatenotice">PythonTemplateNotice</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1817" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythontemplateformaterror-range" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>range</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>range: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a>, <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a>] | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1818" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythontemplateformaterror-diagnostic" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>diagnostic</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>diagnostic: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1778" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-pythontemplateformatresult" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>PythonTemplateFormatResult</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>One validated, atomic Python template-formatting result.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1782" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythontemplateformatresult-source" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1783" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythontemplateformatresult-changed-component-names" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>changed_component_names</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>changed_component_names: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1784" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythontemplateformatresult-notices" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>notices</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>notices: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/template-analysis/#citry-pythontemplatenotice">PythonTemplateNotice</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1735" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-pythontemplatenotice" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>PythonTemplateNotice</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>One definite component template skipped for an explicit reason.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1739" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythontemplatenotice-component-name" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_name</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component_name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1740" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythontemplatenotice-message" class="doc-heading">
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


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1727" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-pythontemplateregion" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>PythonTemplateRegion</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>One definite direct literal template on a Citry component class.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1731" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythontemplateregion-component-name" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_name</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component_name: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1732" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythontemplateregion-source-map" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>source_map</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>source_map: <a class="doc-type-link" href="/reference/template-analysis/#citry-pythontemplatesourcemap">PythonTemplateSourceMap</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L982" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-pythontemplatesourcemap" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>PythonTemplateSourceMap</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Map Citry parser byte ranges back into an authored Python document.</p>
<p>The map decodes plain, raw, and Unicode string literals, including
implicit literal concatenation. Parser indices address the decoded
template as UTF-8 bytes. Returned positions address the Python document
with the zero-based UTF-16 coordinates required by LSP.</p>
<p>Build a map with <a href="/reference/template-analysis/#citry-pythontemplatesourcemap-from-ast"><code>from_ast</code></a> for
valid Python or
<a href="/reference/template-analysis/#citry-pythontemplatesourcemap-from-coordinates"><code>from_coordinates</code></a> for a
literal region found by a conservative lexical scanner.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>template_source</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Decoded, common-indent-normalized Citry template text
passed to the parser.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1009" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythontemplatesourcemap-template-source" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>template_source</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>template_source: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1055" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythontemplatesourcemap-from-ast" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>from_ast</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>from_ast(host_source: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, node: <a class="doc-type-link" href="https://docs.python.org/3.13/library/ast.html#ast.Constant">Constant</a>) -> <a class="doc-type-link" href="/reference/template-analysis/#citry-pythontemplatesourcemap">PythonTemplateSourceMap</a></code></pre>
</div>

<div class="doc-body">
<p>Build a map for a string-valued Python AST constant.</p>
<p>Python AST columns are interpreted as zero-based UTF-8 byte offsets,
matching CPython's contract. Adjacent literals represented by the same
constant are decoded as one template.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>host_source</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Complete Python document text.
</li>

<li>
<code>node</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/ast.html#ast.Constant">Constant</a></code>

- A string-valued <code>ast.Constant</code> from <code>host_source</code>.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="/reference/template-analysis/#citry-pythontemplatesourcemap">PythonTemplateSourceMap</a>: A source map whose ``template_source`` is the normalized inline</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>TypeError</code> - If <code>node</code> is not a string-valued <code>ast.Constant</code>.
</li>

<li>
<code>ValueError</code> - If source positions are missing or the authored text
does not decode to <code>node.value</code>.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1096" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythontemplatesourcemap-from-coordinates" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>from_coordinates</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>from_coordinates(host_source: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, lineno: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a>, col_offset: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a>, end_lineno: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | None = None, end_col_offset: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | None = None, accept_incomplete: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a> = False) -> <a class="doc-type-link" href="/reference/template-analysis/#citry-pythontemplatesourcemap">PythonTemplateSourceMap</a></code></pre>
</div>

<div class="doc-body">
<p>Build a map from Python parser coordinates around a literal expression.</p>
<p>Supply both end coordinates for complete source. A conservative
lexical scanner may omit them and set <code>accept_incomplete=True</code> for
an unfinished final triple-quoted literal, in which case the document
end is the temporary content boundary.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>host_source</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Complete Python document text.
</li>

<li>
<code>lineno</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code>

- 1-based line containing the first literal prefix or quote.
</li>

<li>
<code>col_offset</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code>

- Zero-based UTF-8 byte column of that prefix or quote.
</li>

<li>
<code>end_lineno</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | None</code>

- 1-based line immediately after the expression.
</li>

<li>
<code>end_col_offset</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | None</code>

- Zero-based UTF-8 byte column immediately after the
expression.
</li>

<li>
<code>accept_incomplete</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code>

- Accept an unfinished final triple-quoted
literal and map its content through the end of the document.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="/reference/template-analysis/#citry-pythontemplatesourcemap">PythonTemplateSourceMap</a>: A map for the decoded string expression.</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>ValueError</code> - If coordinates, literal syntax, or escape syntax are
invalid or unsupported.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1275" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythontemplatesourcemap-map-range" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>map_range</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>map_range(start_index: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a>, end_index: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a>) -> <a class="doc-type-link" href="/reference/template-analysis/#citry-lsprange">LspRange</a></code></pre>
</div>

<div class="doc-body">
<p>Convert one half-open parser byte range to Python-document coordinates.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>start_index</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code>

- Inclusive UTF-8 byte offset in <code>template_source</code>.
</li>

<li>
<code>end_index</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code>

- Exclusive UTF-8 byte offset in <code>template_source</code>.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="/reference/template-analysis/#citry-lsprange">LspRange</a>: The corresponding zero-based LSP range in the Python document.</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>ValueError</code> - If the range is reversed, outside the template, or
splits a UTF-8 code point.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1312" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythontemplatesourcemap-range-is-unambiguous" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>range_is_unambiguous</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>range_is_unambiguous(start_index: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a>, end_index: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code></pre>
</div>

<div class="doc-body">
<p>Return whether a parser range stays inside one authored literal body.</p>
<p>Normalized indentation and Python escapes remain mappable inside one
literal. Crossing an implicit-concatenation boundary is ambiguous for
editor edits and semantic result ranges.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>start_index</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code>

- Inclusive UTF-8 byte offset in <code>template_source</code>.
</li>

<li>
<code>end_index</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code>

- Exclusive UTF-8 byte offset in <code>template_source</code>.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a>: ``True`` when both boundaries belong to one literal body.</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>ValueError</code> - If the range is reversed, outside the template, or
splits a UTF-8 code point.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1348" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-pythontemplatesourcemap-parser-index-at" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>parser_index_at</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>parser_index_at(position: <a class="doc-type-link" href="/reference/template-analysis/#citry-lspposition">LspPosition</a>) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | None</code></pre>
</div>

<div class="doc-body">
<p>Return the parser byte boundary at an authored LSP position.</p>
<p>Positions in quotes, prefixes, comments between concatenated literals,
or other Python outside the decoded template return <code>None</code>. A
position inside an authored escape maps to the byte boundary after the
decoded character.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L797" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-templateanalysis" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>TemplateAnalysis</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>A complete, immutable snapshot of one Citry component registry.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>component_names</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#frozenset">frozenset</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>]</code>

- Normalized registered names without the <code>c-</code> tag
prefix. The set includes aliases and built-in component names.
</li>

<li>
<code>lint</code>

<code><a class="doc-type-link" href="/reference/template-analysis/#citry-templatelintinfo">TemplateLintInfo</a></code>

- Application lint settings and known global variables.
</li>

<li>
<code>component_lint</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="/reference/template-analysis/#citry-templatelintinfo">TemplateLintInfo</a>]</code>

- Effective lint settings and known variables keyed by
stable component definition ID.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L811" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templateanalysis-component-names" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_names</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component_names: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#frozenset">frozenset</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L812" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templateanalysis-lint" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>lint</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>lint: <a class="doc-type-link" href="/reference/template-analysis/#citry-templatelintinfo">TemplateLintInfo</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L813" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templateanalysis-component-lint" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_lint</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component_lint: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Mapping">Mapping</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, <a class="doc-type-link" href="/reference/template-analysis/#citry-templatelintinfo">TemplateLintInfo</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L831" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templateanalysis-parse-template" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>parse_template</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>parse_template(source: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> Template</code></pre>
</div>

<div class="doc-body">
<p>Parse authored Citry source with this registry's component contracts.</p>
<p>The parser checks registered component inputs and slots. Extension
transforms are not run because they do not currently provide a mapping
back to the authored source. Names absent from <code>component_names</code> need
a separate unknown-component diagnostic after a successful parse.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>source</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Authored Citry template source.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns">Template: The parsed template AST.</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>SyntaxError</code> - If syntax or a registered component contract is
invalid.
</li>

<li>
<code>ValueError</code> - If parser configuration is invalid.
</li>

</ul>



</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L854" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templateanalysis-to-dict" class="doc-heading">
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
<p>Return a fresh JSON-ready copy of this analysis snapshot.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L875" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templateanalysis-from-dict" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>from_dict</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>from_dict(value: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>) -> <a class="doc-type-link" href="/reference/template-analysis/#citry-templateanalysis">TemplateAnalysis</a></code></pre>
</div>

<div class="doc-body">
<p>Rebuild a snapshot from :meth:<code>to_dict</code> portable data.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L164" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-templatelintconsumer" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>TemplateLintConsumer</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Describe one proven component namespace used by a physical template.</p>




<p class="doc-section">Attributes</p>
<ul class="doc-list">

<li>
<code>known_names</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#frozenset">frozenset</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>]</code>

- Root names available to this component's template.
</li>

<li>
<code>namespace_policy</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;closed&#x27;, &#x27;allow-extra&#x27;, &#x27;unknown&#x27;]</code>

- Whether those names exhaust normalized template data.
</li>

<li>
<code>rule_unknown_template_variable</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;ignore&#x27;, &#x27;warning&#x27;, &#x27;error&#x27;]</code>

- Configured severity for undeclared
free roots.
</li>

</ul>


<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L177" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatelintconsumer-known-names" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>known_names</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>known_names: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#frozenset">frozenset</a>[<a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L178" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatelintconsumer-namespace-policy" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>namespace_policy</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>namespace_policy: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;closed&#x27;, &#x27;allow-extra&#x27;, &#x27;unknown&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L179" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatelintconsumer-rule-unknown-template-variable" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>rule_unknown_template_variable</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>rule_unknown_template_variable: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;ignore&#x27;, &#x27;warning&#x27;, &#x27;error&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L203" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-templatelintfinding" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>TemplateLintFinding</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Report one parser-proven free root missing from a known namespace.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L207" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatelintfinding-name" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L208" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatelintfinding-message" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L209" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatelintfinding-code" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L210" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatelintfinding-severity" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>severity</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>severity: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;warning&#x27;, &#x27;error&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L211" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatelintfinding-start-index" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L212" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatelintfinding-end-index" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L213" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatelintfinding-line" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>line</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>line: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L214" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatelintfinding-column" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>column</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>column: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/_linting.py#L165" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-templatelintinfo" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>TemplateLintInfo</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Carry one component's effective lint rule and known global variables.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/_linting.py#L169" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatelintinfo-rule-unknown-template-variable" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>rule_unknown_template_variable</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>rule_unknown_template_variable: <a class="doc-type-link" href="/reference/citry/#citry-lintseverity">LintSeverity</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/_linting.py#L170" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatelintinfo-template-variables" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>template_variables</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>template_variables: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/template-analysis/#citry-templatevariableinfo">TemplateVariableInfo</a>, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/_linting.py#L171" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatelintinfo-rule-i18n-missing-param-type" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>rule_i18n_missing_param_type</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>rule_i18n_missing_param_type: <a class="doc-type-link" href="/reference/citry/#citry-lintseverity">LintSeverity</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/_linting.py#L172" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatelintinfo-rule-unknown-alpine-variable" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>rule_unknown_alpine_variable</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>rule_unknown_alpine_variable: <a class="doc-type-link" href="/reference/citry/#citry-lintseverity">LintSeverity</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/_linting.py#L173" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatelintinfo-alpine-variables" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>alpine_variables</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>alpine_variables: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[AlpineVariableInfo, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/_linting.py#L174" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatelintinfo-rule-unknown-component-js-variable" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>rule_unknown_component_js_variable</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>rule_unknown_component_js_variable: <a class="doc-type-link" href="/reference/citry/#citry-lintseverity">LintSeverity</a></code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/_linting.py#L175" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatelintinfo-component-js-globals" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>component_js_globals</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>component_js_globals: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[AlpineVariableInfo, ...]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/_linting.py#L176" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatelintinfo-allows-extra-variables" class="doc-heading">
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



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/_linting.py#L234" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatelintinfo-to-dict" class="doc-heading">
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
<p>Return a JSON-ready detached copy.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/_linting.py#L247" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatelintinfo-from-dict" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>from_dict</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>from_dict(value: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>) -> <a class="doc-type-link" href="/reference/template-analysis/#citry-templatelintinfo">TemplateLintInfo</a></code></pre>
</div>

<div class="doc-body">
<p>Validate and restore one detached lint record.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/_linting.py#L29" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-templatevariableinfo" class="doc-heading">
<span class="doc-symbol doc-symbol-class"></span>
<span class="doc-object-name">
<code>TemplateVariableInfo</code>
</span>
<span class="doc-kind">class</span>
</h2>


<div class="doc-body">
<p>Describe one known template variable using detached portable text.</p>





<div class="doc-members">


<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/_linting.py#L33" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatevariableinfo-name" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/_linting.py#L34" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatevariableinfo-type-display" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>type_display</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>type_display: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a> | None</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/_linting.py#L35" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatevariableinfo-type-fidelity" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>type_fidelity</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>type_fidelity: <a class="doc-type-link" href="https://docs.python.org/3.13/library/typing.html#typing.Literal">Literal</a>[&#x27;normalized&#x27;, &#x27;unavailable&#x27;]</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/_linting.py#L36" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatevariableinfo-description" class="doc-heading">
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

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/_linting.py#L37" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatevariableinfo-source" class="doc-heading">
<span class="doc-symbol doc-symbol-attribute"></span>
<span class="doc-object-name">
<code>source</code>
</span>
<span class="doc-kind">attribute</span>
</h3>


<div class="doc-signature highlight">
<pre><code>source: VariableSource</code></pre>
</div>

<div class="doc-body">






</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/_linting.py#L66" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatevariableinfo-to-dict" class="doc-heading">
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
<p>Return a JSON-ready detached copy.</p>





</div>
</div>



<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/_linting.py#L76" target="_blank" rel="noopener">
View source
</a>

<h3 id="citry-templatevariableinfo-from-dict" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>from_dict</code>
</span>
<span class="doc-kind">function</span>
</h3>


<div class="doc-signature highlight">
<pre><code>from_dict(value: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>) -> <a class="doc-type-link" href="/reference/template-analysis/#citry-templatevariableinfo">TemplateVariableInfo</a></code></pre>
</div>

<div class="doc-body">
<p>Validate and restore one detached variable record.</p>





</div>
</div>


</div>

</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1959" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-discover-python-component-assets" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>discover_python_component_assets</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>discover_python_component_assets(source: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>) -> <a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetdiscovery">PythonComponentAssetDiscovery</a></code></pre>
</div>

<div class="doc-body">
<p>Discover direct literal and static file assets on proven components.</p>
<p>Discovery recognizes direct <code>template</code>, <code>js</code>, and <code>css</code> literals,
plus constant <code>template_file</code>, <code>js_file</code>, and <code>css_file</code> paths. It
never imports the module or evaluates a computed declaration.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>source</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Complete Python module source.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetdiscovery">PythonComponentAssetDiscovery</a>: Definite inline regions, file declarations, and explicit notices.</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>SyntaxError</code> - If <code>source</code> is not a complete valid Python module.
</li>

<li>
<code>TypeError</code> - If <code>source</code> is not a string.
</li>

</ul>



</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1752" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-discover-python-templates" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>discover_python_templates</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>discover_python_templates(source: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, recover_incomplete: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a> = False) -> <a class="doc-type-link" href="/reference/template-analysis/#citry-pythontemplatediscovery">PythonTemplateDiscovery</a></code></pre>
</div>

<div class="doc-body">
<p>Discover direct literal templates on provable Citry component classes.</p>
<p>Normal batch tooling leaves <code>recover_incomplete</code> false and receives the
original Python <code>SyntaxError</code>. An interactive editor may opt into the
narrow recovery of one unfinished direct triple-quoted template literal.</p>





</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L2186" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-finish-python-component-assets" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>finish_python_component_assets</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>finish_python_component_assets(plan: <a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetplan">PythonComponentAssetPlan</a>, results: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Sequence">Sequence</a>[EmbeddedFormatResult], require_providers: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a> = False) -> <a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetformatresult">PythonComponentAssetFormatResult</a></code></pre>
</div>

<div class="doc-body">
<p>Validate provider replies and atomically finish one Python source plan.</p>
<p>Every selected literal is rewritten only after every provider reply,
Python parse, asset rediscovery, and decoded-value check succeeds. A
failure raises without exposing a partial source candidate.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>plan</code>

<code><a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetplan">PythonComponentAssetPlan</a></code>

- Exact plan returned by
<a href="/reference/template-analysis/#citry-prepare-python-component-assets"><code>prepare_python_component_assets</code></a>.
</li>

<li>
<code>results</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Sequence">Sequence</a>[EmbeddedFormatResult]</code>

- One source-bound reply for every request in <code>plan</code>.
</li>

<li>
<code>require_providers</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code>

- Reject unavailable providers and embedded regions
that could not be delegated.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetformatresult">PythonComponentAssetFormatResult</a>: The complete formatted Python source and provider metadata.</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>PythonTemplateFormatError</code> - If replies are missing, stale, duplicated,
unavailable when required, invalid, or unsafe to rewrite.
</li>

<li>
<code>TypeError</code> - If <code>plan</code>, <code>results</code>, or <code>require_providers</code> has the
wrong type.
</li>

</ul>



</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L2361" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-format-python-component-assets" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>format_python_component_assets</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>format_python_component_assets(source: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, kinds: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Collection">Collection</a>[<a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetkind">PythonComponentAssetKind</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>] = tuple(PythonComponentAssetKind), host_offset: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | None = None, provider: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[<a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetrequest">PythonComponentAssetRequest</a>], EmbeddedFormatResult] | None = None, require_providers: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a> = False) -> <a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetformatresult">PythonComponentAssetFormatResult</a></code></pre>
</div>

<div class="doc-body">
<p>Format selected direct component assets in one atomic Python-file edit.</p>
<p>This synchronous convenience function prepares a plan, invokes <code>provider</code>
once per JavaScript or CSS request, then validates and finishes the plan.
Call the two-pass prepare and finish functions directly when provider work
must be asynchronous. With no provider, M2 template formatting still runs
while JavaScript and CSS requests remain unchanged with notices.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>source</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Complete Python module source.
</li>

<li>
<code>kinds</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Collection">Collection</a>[<a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetkind">PythonComponentAssetKind</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>]</code>

- Explicit <code>template</code>, <code>js</code>, and <code>css</code> kinds to select.
</li>

<li>
<code>host_offset</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | None</code>

- Optional zero-based Python string offset selecting only
the containing direct asset.
</li>

<li>
<code>provider</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Callable">Callable</a>[[<a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetrequest">PythonComponentAssetRequest</a>], EmbeddedFormatResult] | None</code>

- Optional synchronous JavaScript/CSS formatting callback.
</li>

<li>
<code>require_providers</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#bool">bool</a></code>

- Reject the complete operation when any selected
embedded region has no provider.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetformatresult">PythonComponentAssetFormatResult</a>: The validated complete source, changed asset identities, notices, and</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>PythonTemplateFormatError</code> - If discovery, formatting, a provider, or
final validation fails. No partial candidate is exposed.
</li>

<li>
<code>TypeError</code> - If an argument or provider reply has the wrong type.
</li>

<li>
<code>ValueError</code> - If <code>host_offset</code> or a selected kind is invalid.
</li>

</ul>



</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L2435" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-format-python-templates" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>format_python_templates</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>format_python_templates(source: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, host_offset: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | None = None) -> <a class="doc-type-link" href="/reference/template-analysis/#citry-pythontemplateformatresult">PythonTemplateFormatResult</a></code></pre>
</div>

<div class="doc-body">
<p>Format proven direct Citry template literals in complete Python source.</p>
<p>With no offset, every definite inline template is one atomic operation. A
host offset selects only the literal content containing that Python string
position. The result preserves string prefixes, delimiters, and all host
text outside the exact decoded-template rewrite hunks.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>source</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Complete Python module source.
</li>

<li>
<code>host_offset</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | None</code>

- Optional zero-based Python string offset inside one
template literal body.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="/reference/template-analysis/#citry-pythontemplateformatresult">PythonTemplateFormatResult</a>: The validated source, changed component names, and discovery notices.</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>PythonTemplateFormatError</code> - If Python or Citry syntax is invalid, a
selected literal is not safely rewriteable, or validation fails.
</li>

<li>
<code>TypeError</code> - If <code>source</code> or <code>host_offset</code> has the wrong type.
</li>

<li>
<code>ValueError</code> - If <code>host_offset</code> is outside <code>source</code>.
</li>

</ul>



</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L1991" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-prepare-python-component-assets" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>prepare_python_component_assets</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>prepare_python_component_assets(source: <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>, kinds: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Collection">Collection</a>[<a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetkind">PythonComponentAssetKind</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>] = tuple(PythonComponentAssetKind), host_offset: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | None = None) -> <a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetplan">PythonComponentAssetPlan</a></code></pre>
</div>

<div class="doc-body">
<p>Prepare one atomic Python component-asset formatting operation.</p>
<p>Templates first receive Citry structure and Python-expression formatting.
Safe <code>script</code> and <code>style</code> bodies, plus direct <code>js</code> and <code>css</code>
literals, become standalone provider requests. The returned plan makes no
source edit, so callers may resolve those requests asynchronously.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>source</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a></code>

- Complete Python module source.
</li>

<li>
<code>kinds</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Collection">Collection</a>[<a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetkind">PythonComponentAssetKind</a> | <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#str">str</a>]</code>

- Explicit component asset kinds selected for this operation.
</li>

<li>
<code>host_offset</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#int">int</a> | None</code>

- Optional zero-based Python string offset. When supplied,
only the containing selected direct asset is prepared.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="/reference/template-analysis/#citry-pythoncomponentassetplan">PythonComponentAssetPlan</a>: A source-bound plan and its provider requests.</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>PythonTemplateFormatError</code> - If Python or selected asset syntax is
invalid, or a selected literal cannot be rewritten safely.
</li>

<li>
<code>TypeError</code> - If an argument has the wrong type.
</li>

<li>
<code>ValueError</code> - If <code>host_offset</code> is outside <code>source</code> or a kind is
unknown.
</li>

</ul>



</div>
</div>






<div class="doc-object">

<a class="doc-source-link" href="https://github.com/citry-dev/citry/blob/main/packages/py/citry/citry/analysis.py#L418" target="_blank" rel="noopener">
View source
</a>

<h2 id="citry-lint-unknown-template-variables" class="doc-heading">
<span class="doc-symbol doc-symbol-function"></span>
<span class="doc-object-name">
<code>lint_unknown_template_variables</code>
</span>
<span class="doc-kind">function</span>
</h2>


<div class="doc-signature highlight">
<pre><code>lint_unknown_template_variables(template: <a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a>, consumers: <a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Sequence">Sequence</a>[<a class="doc-type-link" href="/reference/template-analysis/#citry-templatelintconsumer">TemplateLintConsumer</a>]) -> <a class="doc-type-link" href="https://docs.python.org/3.13/library/stdtypes.html#tuple">tuple</a>[<a class="doc-type-link" href="/reference/template-analysis/#citry-templatelintfinding">TemplateLintFinding</a>, ...]</code></pre>
</div>

<div class="doc-body">
<p>Diagnose free roots missing from at least one proven component namespace.</p>

<p class="doc-section">Parameters</p>
<ul class="doc-list">

<li>
<code>template</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/functions.html#object">object</a></code>

- Parsed Citry template AST. Its parser-reported free variables
already exclude lexical and Python-local bindings.
</li>

<li>
<code>consumers</code>

<code><a class="doc-type-link" href="https://docs.python.org/3.13/library/collections.abc.html#collections.abc.Sequence">Sequence</a>[<a class="doc-type-link" href="/reference/template-analysis/#citry-templatelintconsumer">TemplateLintConsumer</a>]</code>

- Every proven component that consumes this physical template.
</li>

</ul>


<p class="doc-section">Returns</p>
<p class="doc-returns"><a class="doc-type-link" href="/reference/template-analysis/#citry-templatelintfinding">TemplateLintFinding</a>: Findings in the parser&#x27;s stable free-variable order. No consumer means</p>


<p class="doc-section">Raises</p>
<ul class="doc-list">

<li>
<code>TypeError</code> - If the parsed object lacks Citry free-variable records.
</li>

</ul>



</div>
</div>



