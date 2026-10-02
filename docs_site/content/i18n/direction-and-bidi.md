---
title: Language direction and accessibility
description: Mark language and direction correctly and keep mixed-direction text safe for display and assistive technology.
---

# Language direction and accessibility

A translated page also needs the right markup around its text. Screen
readers pick a voice from the `lang` attribute, so English text marked as
Czech is read with Czech pronunciation. Arabic and Hebrew run right to
left and need `dir="rtl"`. And a Latin name or a number inside an Arabic
sentence can scramble the punctuation around it if nothing keeps it
apart.

Three tools handle this:

- `lang` tells browsers and screen readers which language an element
  contains.
- `dir` tells the browser whether text and layout run left to right or
  right to left.
- Bidirectional isolation keeps an inserted value, such as a name, from
  reordering the words and punctuation around it.

Setting `dir` does not translate anything, and translating text does not
update the `lang` of the elements around it. This page shows how to get
each one right.

## Set lang and dir for part of the page

Give `<c-i18n>` a `tag` so it renders a real element:

```citry-html
<c-i18n locale="ar-EG" tag="section">
  <c-account-summary />
</c-i18n>
```

Citry picks the direction from the locale and renders:

```html
<section lang="ar-EG" dir="rtl">
  ...
</section>
```

## Set lang and dir on the html element

Citry does not change the `<html>` element by itself. When your web
framework renders the document shell, read the locale context there and
set both attributes:

```html
<html lang="ar-EG" dir="rtl">
```

Take the values from `context.locale` and `context.direction`.

## Write CSS that works in both directions

Use logical CSS properties, which follow the text direction, instead of
`left` and `right`:

```css
.account-card {
  padding-inline-start: 1rem;
  border-inline-end: 1px solid var(--border-color);
}
```

Check icons one by one. An arrow that means "next" usually needs to flip
in right-to-left layouts; a play button or a logo usually should not.

## Inserted values keep their own direction

A name, file path, ID, or number inserted into a message may run in a
different direction from the sentence around it. Citry isolates each
inserted value automatically, so it cannot reorder the surrounding text.

This is separate from HTML escaping. Escaping stops a value from adding
markup; isolation stops it from changing the visual order. Citry does
both.

## Translate accessible labels too

Keep a control's visible text and its accessible label in one message,
as Fluent attributes:

```fluent
my-app-account-actions = Actions
    .aria-label = Open account actions
    .title = Show available actions
```

Ask for the attribute by name, as in `tr(..., attr="aria-label")`. Each
attribute falls back on its own, so a missing `.aria-label` translation
is never replaced by the visible label. See
[Write messages](/i18n/messages/#translate-labels-such-as-aria-label).

## Mark fallback text with its language

When a translation is missing, Citry falls back to another language.
`tr()` returns only text, so the text cannot carry its own `lang`, and a
screen reader would read it in the page's language. For this reason
`citry check` reports an error for a `tr()` call that would fall back to
another locale.

Where fallback is acceptable, call `resolve()` and put its locale and
direction on an element you control:

```python
resolved = self.i18n.resolve("my-app-legal-notice")

return {
    "notice": resolved.text,
    "notice_lang": resolved.locale,
    "notice_dir": resolved.direction,
}
```

```citry-html
<p c-lang="notice_lang" c-dir="notice_dir">
  {{ notice }}
</p>
```

`resolved.used_fallback` is `True` when the text came from a different
locale than the one requested.

## Keep server text out of a browser-switched provider

When a [client provider](/i18n/browser/) (a `<c-i18n client>` element)
switches language in the
browser, it updates its `lang` and `dir` together with its Vue-owned
text. Server-rendered text inside it stays in the old language, so the
element would claim a language its text does not use.

Put such text inside its own `<c-i18n tag="...">` without `client`, or
render it again on the server.

## Rules for less common cases

### Choose the direction yourself

`<c-i18n>` accepts `direction="ltr"` or `direction="rtl"` for an unusual
part of the page. Usually, let Citry derive it from the locale.

### Line breaks and direction marks in a value

A value passed into a message may not contain Unicode direction control
characters or line or paragraph breaks. For text on several lines, or
text that needs a fixed direction, use separate elements.

### citry check reports a cross-language fallback

`citry check` reports `citry.i18n.cross-language-fallback` when text
would fall back to another locale and nothing can mark its `lang`. This
covers `tr()` and `self.i18n.tr()` calls, text translated in the browser,
and [rich messages](/i18n/rich-messages/), which have no element around
them. Add a translation for each selectable locale, or use `resolve()`
as shown above for server text.
