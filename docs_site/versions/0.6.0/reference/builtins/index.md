---
title: Built-in tags
url: https://citry.dev/v/0.6.0/reference/builtins/
description: "The c-* tags Citry provides in every component template."
---
# Built-in tags

Look up a built-in `<c-*>` tag here: what it does, its attributes, and a
short example. Every component template can use these tags without
registering or importing anything.

- **Control flow:** [`<c-if>`](#c-if), [`<c-elif>`](#c-elif),
  [`<c-else>`](#c-else), [`<c-for>`](#c-for), and
  [`<c-empty>`](#c-empty)
- **Slots:** [`<c-slot>`](#c-slot) and [`<c-fill>`](#c-fill)
- **Dynamic output:** [`<c-component>`](#c-component) and
  [`<c-element>`](#c-element)
- **Data and resilience:** [`<c-provide>`](#c-provide),
  [`<c-cache>`](#c-cache), and
  [`<c-error-fallback>`](#c-error-fallback)
- **Targeted updates:** [`<c-mark>`](#c-mark)
- **Internationalization:** [`<c-i18n>`](#c-i18n) and
  [`<c-trans>`](#c-trans)
- **Page assets:** [`<c-css>`](#c-css) and [`<c-js>`](#c-js)
- **Literal template text:** [`<c-raw>`](#c-raw)

## Control flow

<h3 id="c-if"><code>&lt;c-if&gt;</code></h3>

Render a block only when its `cond` expression is truthy. Any number of
`<c-elif>` branches and one `<c-else>` may follow it.


```citry-html
<c-if cond="is_admin">
  <p>Administrator tools</p>
</c-if>
```


[Conditions and loops](/v/0.6.0/syntax/control-flow/) covers the inline `c-if`
attribute, truthiness, and branch order.

<h3 id="c-elif"><code>&lt;c-elif&gt;</code></h3>

Add another condition to a `<c-if>` chain. The branch renders when every
earlier condition was false and its own `cond` is truthy.


```citry-html
<c-if cond="is_admin">Admin</c-if>
<c-elif cond="is_editor">Editor</c-elif>
```


<h3 id="c-else"><code>&lt;c-else&gt;</code></h3>

Add the final fallback to a `<c-if>` chain. It takes no `cond`.


```citry-html
<c-if cond="is_signed_in">Account</c-if>
<c-else>Sign in</c-else>
```


<h3 id="c-for"><code>&lt;c-for&gt;</code></h3>

Repeat a block for every item in an iterable. The `each` attribute is
written like a Python `for`: a target, `in`, and an expression.


```citry-html
<c-for each="book in books">
  <p>{{ book.title }}</p>
</c-for>
```


[Conditions and loops](/v/0.6.0/syntax/control-flow/#unpack-and-filter-values)
covers unpacking, filtering, and variable scope.

<h3 id="c-empty"><code>&lt;c-empty&gt;</code></h3>

Show an empty state when the `<c-for>` right before it has no items.


```citry-html
<c-for each="book in books">
  <p>{{ book.title }}</p>
</c-for>
<c-empty>No books yet.</c-empty>
```


## Slots

<h3 id="c-slot"><code>&lt;c-slot&gt;</code></h3>

Mark a place in a component where the template that uses it can add
content. Leave out `name` for the default slot, and name each extra slot.
Content inside the tag is shown when no content is passed.


```citry-html
<article>
  <c-slot />
  <footer>
    <c-slot name="footer">No footer supplied.</c-slot>
  </footer>
</article>
```


[Slots](/v/0.6.0/concepts/slots/) covers required slots, slot data, dynamic
names, and fallback content.

<h3 id="c-fill"><code>&lt;c-fill&gt;</code></h3>

Send a block of content to a named slot of the component you are using.
For the default slot alone, put the content directly in the component's
body instead.


```citry-html
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




```citry-html
<c-component is="card" />
<c-component c-is="chosen_component" />
```





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




```citry-html
<c-element c-is="tag" class="heading">
  {{ text }}
</c-element>
```


[Dynamic components](/v/0.6.0/advanced/dynamic-components/) has complete
examples and explains how component names differ from HTML tag names.

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




```citry-html
<c-provide key="theme" name="dark">
  <c-theme-label />
</c-provide>
```


[Provide and inject](/v/0.6.0/concepts/provide-and-inject/) shows how a component
reads the value.




<div class="doc-object">

<h3 id="c-cache" class="doc-heading">
<span class="doc-symbol doc-symbol-built-in component"></span>
<span class="doc-object-name">
<code>&lt;c-cache&gt;</code>
</span>
<span class="doc-kind">built-in component</span>
</h3>


<div class="doc-body">
<p>Save the HTML of the wrapped part of a template and reuse it on later renders.</p>
<p><code>key</code> (required) names the cached part. Templates that use the same
<code>key</code> share saved HTML, so list in <code>vary</code> every value that can
change the output, such as the user id or the locale: each
combination gets its own saved copy. <code>ttl</code> is how many seconds a
copy stays saved (by default, the app's cache setting); with
<code>None</code> it never expires, and
<code>0</code> turns caching off. Change <code>version</code> to stop reusing the
copies saved under the old value, for example after you change what
the wrapped part shows. <code>enabled=False</code> also turns caching off.
Citry does not look at the wrapped content when it builds the key,
and the tag adds no HTML of its own.</p>





</div>
</div>




```citry-html
<c-cache
  key="account-menu"
  c-vary="[current_user.id, locale]"
  c-ttl="300"
>
  <c-account-menu
    c-user="current_user"
    c-locale="locale"
  />
</c-cache>
```


[Caching](/v/0.6.0/performance/caching/) covers keys, expiry, and clearing
entries.




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
which receives the error as slot data (<code>data.error</code>). Ordinary
fallback strings are escaped; use the fill when the fallback needs
markup.</p>





</div>
</div>




```citry-html
<c-error-fallback fallback="Recent activity is unavailable">
  <c-recent-activity />
</c-error-fallback>
```


[Error boundaries](/v/0.6.0/concepts/error-boundaries/) shows a fallback with
markup and nested boundaries.

## Targeted updates




<div class="doc-object">

<h3 id="c-mark" class="doc-heading">
<span class="doc-symbol doc-symbol-built-in component"></span>
<span class="doc-object-name">
<code>&lt;c-mark&gt;</code>
</span>
<span class="doc-kind">built-in component</span>
</h3>


<div class="doc-body">
<p>Name part of a component's template so an event handler can update only that part.</p>
<p><code>name</code> (required) is case-sensitive, starts with a letter, and
contains only letters, digits, hyphens, and underscores. The tag
accepts no other attribute and only its default slot.</p>
<p>Each name may render only once per component: a <code>&lt;c-mark&gt;</code> inside a
<code>&lt;c-for&gt;</code> that loops over more than one item, or two tags with the same name
that both render, raise <code>ValueError</code> when the component renders.
Tags in different <code>&lt;c-if&gt;</code>/<code>&lt;c-else&gt;</code> branches may share a name,
because only one of them renders. A <code>&lt;c-mark&gt;</code> written inside a
<code>&lt;c-fill&gt;</code> belongs to the component whose template holds the fill,
and one in a <code>simple=True</code> component's template belongs to the
component that calls it.</p>





</div>
</div>



To update the marked part, return
`actions.Render(..., target="mark:<name>")` from an event handler:


```citry-html
<c-mark name="summary">
  <c-CartSummary c-cart="cart" />
</c-mark>
```


Write `name` as a plain attribute. A computed `c-name`, or a name that
breaks the rules above, raises `ValueError` when the component renders.
`<c-mark>` takes no `<c-fill>`; put the content directly inside it.

See [`<c-mark>` partial update](/v/0.6.0/events/actions/#update-one-part-of-the-page).

!!! note "You cannot name a component `mark`"

    A component class named `Mark`, or one registered as `mark`, fails when
    it is defined:


    ```text
    AlreadyRegistered: Cannot register 'Mark' as 'mark': the name is
    reserved for the built-in <c-mark> component.
    ```


    Rename the class, for example to `Highlight`, and write
    `<c-highlight>` in your templates.

## Internationalization




<div class="doc-object">

<h3 id="c-i18n" class="doc-heading">
<span class="doc-symbol doc-symbol-built-in component"></span>
<span class="doc-object-name">
<code>&lt;c-i18n&gt;</code>
</span>
<span class="doc-kind">built-in component</span>
</h3>


<div class="doc-body">
<p>Set the locale for the content inside this tag.</p>
<p><code>locale</code>, <code>direction</code> (<code>"ltr"</code> or <code>"rtl"</code>), <code>time_zone</code>, and
<code>context</code> (a whole locale context) override the inherited values.
Add <code>tag</code> to wrap the content in that HTML element with <code>lang</code> and
<code>dir</code> set from the locale. The <code>client</code> attribute, which sends the
locale to browser code, requires <code>tag</code>, and so does a <code>&lt;c-i18n&gt;</code>
placed inside a <code>client</code> one; without it the tag raises
<code>ValueError</code>.</p>





</div>
</div>



Use it to set the locale for one part of the page. Add `tag` when that
part needs `lang` and `dir` attributes. To let browser code in that part
translate and format text, add the bare `client` attribute as well:


```citry-html
<c-i18n locale="ar-EG" tag="aside">
  <c-account-card />
</c-i18n>
```


See [Locales and context](/v/0.6.0/i18n/locale-context/) and
[Browser i18n](/v/0.6.0/i18n/browser/).




<div class="doc-object">

<h3 id="c-trans" class="doc-heading">
<span class="doc-symbol doc-symbol-built-in component"></span>
<span class="doc-object-name">
<code>&lt;c-trans&gt;</code>
</span>
<span class="doc-kind">built-in component</span>
</h3>


<div class="doc-body">
<p>Render a translated message that contains HTML, such as a link or a component.</p>
<p><code>message</code> (required) is the message id. <code>values</code> maps the
message's variables to values, and each <code>&lt;c-fill&gt;</code>
supplies the HTML for the placeholder with the same name, so the
translator decides where the link goes. <code>attr</code> picks one
attribute of the message instead of its main text. Citry escapes
the translated text itself. Using one name both in <code>values</code> and as
a fill, or passing any other attribute, raises <code>ValueError</code>.</p>





</div>
</div>



Use it when a translated sentence contains a link or a component, and the
translator decides where it goes:


```citry-html
<c-trans
  message="my-app-terms-acceptance"
  c-values="{'account_name': account.name}"
>
  <c-fill name="terms_link">
    <a href="/terms">{{ tr("my-app-terms-name") }}</a>
  </c-fill>
</c-trans>
```


See [Rich messages](/v/0.6.0/i18n/rich-messages/).

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
<p>Mark where Citry puts the stylesheet tags for the page's components.</p>
<p>Without it, the stylesheets go at the end of <code>&lt;head&gt;</code>. Passing an
attribute or a body raises <code>ValueError</code>. When a page has several,
the first one gets the stylesheets and the others render nothing.</p>





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
<p>Mark where Citry puts the <code>&lt;script&gt;</code> tags for the page's components.</p>
<p>Without it, the scripts go at the end of <code>&lt;body&gt;</code>. Passing an
attribute or a body raises <code>ValueError</code>. When a page has several,
the first one gets the scripts and the others render nothing.</p>





</div>
</div>



Without them, Citry puts the CSS at the end of `<head>` and the
JavaScript at the end of `<body>`. Use the tags to place them somewhere
else, such as before your own stylesheet:


```citry-html
<head>
  <c-css />
  <link rel="stylesheet" href="/static/overrides.css">
</head>
<body>
  <c-Chart c-points="[1, 2, 3]" />
  <c-js />
</body>
```


[Asset placement][dependencies-guide] explains where Citry puts the
collected files and component assets.

## Literal template text

<h3 id="c-raw"><code>&lt;c-raw&gt;</code></h3>

Keep text that looks like template syntax exactly as written. Citry does
not evaluate expressions or component tags inside `<c-raw>`.


```citry-html
<c-raw>
  {{ this_stays_as_text }}
  <c-Card>This tag stays as text too.</c-Card>
</c-raw>

```


[Literal text](/v/0.6.0/syntax/raw/)
covers what is trusted and the exact rules.

[dependencies-guide]: /advanced/asset-placement/