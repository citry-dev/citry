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

## Set lang and dir

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

## Set `<html>` lang and dir

Citry does not change the `<html>` element by itself. When your web
framework renders the document shell, read the locale context there and
set both attributes:

```html
<html lang="ar-EG" dir="rtl">
```

Take the values from `context.locale` and `context.direction`.

## Use logical CSS

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

## Values keep direction

A name, file path, ID, or number inserted into a message may run in a
different direction from the sentence around it. Citry isolates each
inserted value automatically, so it cannot reorder the surrounding text.

This is separate from HTML escaping. Escaping stops a value from adding
markup; isolation stops it from changing the visual order. Citry does
both.

## Translate labels too

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

## Mark fallback text { #mark-fallback-text-with-its-language }

When a translation is missing, Citry falls back to another language.
If that language runs in the other direction, such as English text on
an Arabic page, Citry isolates the fallback text so it cannot reorder
the sentence around it. The server and the browser isolate it the same
way, so the text does not change when Vue takes over the page.

`tr()` returns only text, so the text cannot carry its own `lang`, and a
screen reader reads it in the page's language. `citry check` warns about
each `tr()` call that would fall back to another locale.

To mark the fallback text with its own language, call `resolve()` and put
its locale and direction on an element you control:

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

## Keep server text apart

When a [client provider](/i18n/browser/) (a `<c-i18n client>` element)
switches language in the
browser, it updates its `lang` and `dir` together with its Vue-owned
text. Server-rendered text inside it stays in the old language, so the
element would claim a language its text does not use.

Put such text inside its own `<c-i18n tag="...">` without `client`, or
render it again on the server.

## Less common cases

### Force a direction

`<c-i18n>` accepts `direction="ltr"` or `direction="rtl"` for an unusual
part of the page. Usually, let Citry derive it from the locale.

### Line breaks in values

A value passed into a message may not contain Unicode direction control
characters or line or paragraph breaks. For text on several lines, or
text that needs a fixed direction, use separate elements.

### Fallback warnings

`citry check` reports a warning, `citry.i18n.cross-language-fallback`,
when a `tr()` call, a `self.i18n.tr()` call, or a message in
`I18n.client_messages` would fall back to another locale. The page still
renders; the warning only points out text whose `lang` is wrong. A
region or script change, such as `en-GB` falling back to `en-US`, also
counts. Add the missing translations, or use `resolve()` as shown above
for server text.

To require complete translations, make the warning an error with
`LintSettings(rule_i18n_cross_language_fallback="error")`. To hide it, set
`"ignore"`. A component's own `Lint` class can override either setting;
see [Translation workflow](/i18n/workflow/#change-fallback-warnings).

[Rich messages](/i18n/rich-messages/#translate-all-locales) are
different: `<c-trans>` has no element around its text, so rendering one
in a locale without its translation fails. `citry check` reports that as
an error, `citry.i18n.rich-message-fallback`, whatever the setting.
