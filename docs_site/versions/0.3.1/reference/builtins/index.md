---
title: Built-in tags
url: https://citry.dev/v/0.3.1/reference/builtins/
description: "The c-* tags Citry provides in every component template."
---
# Built-in tags

Citry provides these tags in every component template. You do not need to
register or import them.

- **Control flow:** [`<c-if>`](#c-if), [`<c-elif>`](#c-elif),
  [`<c-else>`](#c-else), [`<c-for>`](#c-for), and
  [`<c-empty>`](#c-empty)
- **Slots:** [`<c-slot>`](#c-slot) and [`<c-fill>`](#c-fill)
- **Dynamic output:** [`<c-component>`](#c-component) and
  [`<c-element>`](#c-element)
- **Data and resilience:** [`<c-provide>`](#c-provide),
  [`<c-cache>`](#c-cache), and
  [`<c-error-fallback>`](#c-error-fallback)
- **Page assets:** [`<c-css>`](#c-css) and [`<c-js>`](#c-js)
- **Literal template text:** [`<c-raw>`](#c-raw)

## Control flow

<h3 id="c-if"><code>&lt;c-if&gt;</code></h3>

Render a block when its `cond` expression is truthy. An `<c-if>` may be
followed by any number of `<c-elif>` branches and one `<c-else>` branch.


```citry
<c-if cond="is_admin">
  <p>Administrator tools</p>
</c-if>
```


The [control-flow guide](/v/0.3.1/syntax/control-flow/) covers inline `c-if`
attributes, truthiness, and branch ordering.

<h3 id="c-elif"><code>&lt;c-elif&gt;</code></h3>

Add another condition to an `<c-if>` chain. Citry renders this branch only
when every earlier condition was false and this branch's `cond` is truthy.


```citry
<c-if cond="is_admin">Admin</c-if>
<c-elif cond="is_editor">Editor</c-elif>
```


<h3 id="c-else"><code>&lt;c-else&gt;</code></h3>

Add the final fallback to an `<c-if>` chain. `<c-else>` has no `cond`
attribute.


```citry
<c-if cond="is_signed_in">Account</c-if>
<c-else>Sign in</c-else>
```


<h3 id="c-for"><code>&lt;c-for&gt;</code></h3>

Repeat a block for every value in an iterable. Its `each` attribute uses a
Python-style target and expression.


```citry
<c-for each="book in books">
  <p>{{ book.title }}</p>
</c-for>
```


Read [Control flow](/v/0.3.1/syntax/control-flow/#loops) for unpacking, filtering,
and the `loop` helper.

<h3 id="c-empty"><code>&lt;c-empty&gt;</code></h3>

Show an empty state when the `<c-for>` immediately before it produces no
items.


```citry
<c-for each="book in books">
  <p>{{ book.title }}</p>
</c-for>
<c-empty>No books yet.</c-empty>
```


## Slots

<h3 id="c-slot"><code>&lt;c-slot&gt;</code></h3>

Mark a place where another template can add content. Leave out `name` for the
default slot, or name the slot when a component has more than one. Content
inside the tag is its fallback.


```citry
<article>
  <c-slot />
  <footer>
    <c-slot name="footer">No footer supplied.</c-slot>
  </footer>
</article>
```


See [Slots](/v/0.3.1/concepts/slots/) for required slots, slot data, dynamic names,
and fallback details.

<h3 id="c-fill"><code>&lt;c-fill&gt;</code></h3>

Choose which named slot receives a block of content when you use a component.
You can pass plain body content when you only need the default slot.


```citry
<c-Panel>
  <c-fill name="footer">
    <a href="/help/">Get help</a>
  </c-fill>
</c-Panel>
```


## Dynamic output




<div class="doc-object">

<h3 id="c-component" class="doc-heading">
<span class="doc-symbol doc-symbol-built-in component"></span>
<span class="doc-object-name">
<code>&lt;c-component&gt;</code>
</span>
<span class="doc-kind">built-in component</span>
</h3>


<div class="doc-body">
<p>Render the component named by <code>is</code> in this tag's place.</p>
<p><code>is</code> (required) is a registered component name or a <code>Component</code>
class; every other attribute is passed to it as a kwarg, and the
body (fills included) as its slots.</p>





</div>
</div>







<div class="doc-object">

<h3 id="c-element" class="doc-heading">
<span class="doc-symbol doc-symbol-built-in component"></span>
<span class="doc-object-name">
<code>&lt;c-element&gt;</code>
</span>
<span class="doc-kind">built-in component</span>
</h3>


<div class="doc-body">
<p>Render a plain HTML element whose tag name is the <code>is</code> value.</p>
<p><code>is</code> (required) is the tag name; every other attribute becomes an
HTML attribute of the element, and the body its children. Void
elements (<code>br</code>, <code>img</code>, ...) reject a body.</p>





</div>
</div>




Read [Dynamic components](/v/0.3.1/advanced/dynamic-components/) for complete examples
and the difference between component names and HTML tag names.

## Data and resilience




<div class="doc-object">

<h3 id="c-provide" class="doc-heading">
<span class="doc-symbol doc-symbol-built-in component"></span>
<span class="doc-object-name">
<code>&lt;c-provide&gt;</code>
</span>
<span class="doc-kind">built-in component</span>
</h3>


<div class="doc-body">
<p>Provide data to the components rendered inside this tag.</p>
<p><code>key</code> (required) names the data; all other attributes become the
provided fields, injectable below as
<code>self.inject(key).&lt;field&gt;</code>.</p>





</div>
</div>







<div class="doc-object">

<h3 id="c-cache" class="doc-heading">
<span class="doc-symbol doc-symbol-built-in component"></span>
<span class="doc-object-name">
<code>&lt;c-cache&gt;</code>
</span>
<span class="doc-kind">built-in component</span>
</h3>


<div class="doc-body">
<p>Cache and replay one named transparent template region.</p>
<p><code>key</code> is a required stable fragment name. <code>vary</code> contains every
caller-dependent value that can change the body, <code>ttl</code> controls expiry,
<code>version</code> selects an author-controlled invalidation family, and
<code>enabled=False</code> bypasses caching. The body is not inspected or included
in the key, and a hit emits no wrapper element.</p>





</div>
</div>







<div class="doc-object">

<h3 id="c-error-fallback" class="doc-heading">
<span class="doc-symbol doc-symbol-built-in component"></span>
<span class="doc-object-name">
<code>&lt;c-error-fallback&gt;</code>
</span>
<span class="doc-kind">built-in component</span>
</h3>


<div class="doc-body">
<p>Catch render errors in the wrapped content and show fallback content instead.</p>
<p>The guarded content is the tag body (the default slot). The fallback
is the <code>fallback</code> attribute (a string), or the <code>fallback</code> fill,
which receives the error as slot data (<code>data.error</code>).</p>





</div>
</div>




## Page assets




<div class="doc-object">

<h3 id="c-css" class="doc-heading">
<span class="doc-symbol doc-symbol-built-in component"></span>
<span class="doc-object-name">
<code>&lt;c-css&gt;</code>
</span>
<span class="doc-kind">built-in component</span>
</h3>


<div class="doc-body">
<p>Marks where the collected stylesheet dependency tags are placed.</p>





</div>
</div>







<div class="doc-object">

<h3 id="c-js" class="doc-heading">
<span class="doc-symbol doc-symbol-built-in component"></span>
<span class="doc-object-name">
<code>&lt;c-js&gt;</code>
</span>
<span class="doc-kind">built-in component</span>
</h3>


<div class="doc-body">
<p>Marks where the collected <code>&lt;script&gt;</code> dependency tags are placed.</p>





</div>
</div>




The [JS and CSS dependencies guide][dependencies-guide] explains collection,
placement, and serialization strategies.

## Literal template text

<h3 id="c-raw"><code>&lt;c-raw&gt;</code></h3>

Keep template-looking text unchanged. Citry does not evaluate expressions or
component tags inside `<c-raw>`.


```citry
<c-raw>
  {{ this_stays_as_text }}
  <c-Card>This tag stays as text too.</c-Card>
</c-raw>

```


[dependencies-guide]: /advanced/js-and-css-dependencies/