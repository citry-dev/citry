---
title: Security and CSP
description: Run interactive Citry pages under a Content Security Policy, send output with no JavaScript, and see why Citry refuses Vue code from c-bind.
---

# Security and CSP

Your site sends a Content Security Policy, and the browser blocks every
script and style that the policy does not allow. Or the output must carry
no JavaScript at all, such as an HTML email. Or Citry refused to render a
template because a Vue directive came from `c-bind`, and you want to know
why. This page covers all three.

For the rest of Citry's security model, such as State, CSRF, and the
template sandbox, see [Security](/security/).

## Add a CSP nonce { #use-content-security-policy }

A nonce is a random value, new for each response, that the policy lists
and that every trusted `<script>` and `<style>` tag carries. Pass the
request's nonce when you serialize the page:

```python
page = Page()
html = page.render().serialize(csp_nonce=request_nonce)
```

Citry adds the nonce to the scripts and styles it places, including those
that dependency hooks add. Your application still generates the nonce and
sends the matching response header. A `<script>` or `<style>` tag written
directly in a template does not get the nonce. See
[Use a CSP nonce](/security/#apply-a-request-csp-nonce-centrally).

An interactive [HTML fragment](/advanced/html-fragments/) uses the Citry
runtime the page already loaded. Before starting a fragment, Citry checks
that its runtime, CSP nonce, components, and assets match the page. If they
do not, the fragment does not start, and Citry reports an error in the
browser console.

A page with a Content Security Policy is sent with HTML that Vue replaces
rather than adopts, so focus and text typed before Vue starts are lost.
That applies when you pass `csp_nonce`, or set `security_csp` to `"warn"`
or `"strict"`. See
[Replaced pages](/vue/server-rendering/#pages-vue-replaces-instead-of-adopting).

### Inline style attributes { #inline-style-attributes }

When the policy's `style-src` does not allow inline styles, the browser
blocks each `style` attribute in the served HTML and reports it. Vue then
applies the same styles through the DOM, which the policy allows. To avoid
the reports, allow `'unsafe-hashes'` with the style hashes, or move the
styles to component CSS.

## Send no JavaScript { #send-no-javascript }

Set `security_javascript="omit"` for output that should stay static, such
as an email. Citry keeps the server-rendered HTML and CSS, and sends no
Vue runtime, component JavaScript, Events client, or app data. Vue
attributes stay in the HTML, where the browser ignores them.

Set `security_javascript="forbid"` to make serialization fail when the
output needs browser behavior. See
[Limit page JavaScript](/security/#choose-how-much-javascript-citry-may-deliver).

## No Vue code in `c-bind` { #c-bind-never-carries-vue-code }

You build a dict of attributes in Python and spread it with `c-bind`. A
plain HTML attribute such as `title` works. A Vue directive, `:` binding,
or `@` listener in that dict makes the page fail to render:

```python
# Wrong: Python puts Vue code into the attributes
def template_data(self, kwargs, slots):
    return {"attrs": {"@click": "save", ":title": "hint"}}
```

```citry-html
<button c-bind="attrs">Save</button>
```

The error names the attribute, such as `'@click'`. A value that Python
works out at render time may contain user input, so Citry never lets it
become code the browser runs. Write the directive directly in the
template:

```citry-html
<!-- Right: Vue code written in the template -->
<button
  :title="hint"
  @click="save"
>
  Save
</button>
```

Citry rejects every key that Vue would read as a directive: names that
start with `v-`, `:`, `@`, `#`, or `.`. The same applies to a directive
written with a `c-` prefix, such as `c-v-if`, `c-@click`, or `c-:title`,
because its value is also a Python expression.

The check runs on pages that start Vue. On a page with no Vue component,
the attribute is written into the HTML as plain text and nothing runs it.

## See also

- [Security](/security/) for State, CSRF, the template sandbox, and the
  CSP checks.
- [Server-rendered HTML](/vue/server-rendering/) for what the page shows
  before Vue starts.
- [Vue in templates](/syntax/vue/#use-vue-directives) for the directives
  you write in templates.
