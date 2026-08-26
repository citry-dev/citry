---
title: Language direction and accessibility
url: https://citry.dev/v/0.4.4/i18n/direction-and-bidi/
description: "Mark language and direction correctly and keep mixed-direction text safe for display and assistive technology."
---
# Language direction and accessibility

Language, writing direction, and bidirectional text are related but different.

- `lang` tells browsers and assistive technology which language an element
  contains.
- `dir` tells layout and text processing whether the surrounding direction is
  left-to-right or right-to-left.
- Bidirectional isolation prevents an inserted run of text from changing the
  order of surrounding punctuation and words.

Changing `dir` alone does not translate text, and translating text does not
automatically make every surrounding element use the right language.

## Let a real provider own lang and dir

Give `<c-i18n>` a real tag when a subtree needs semantic language markup:


```citry-html
<c-i18n locale="ar-EG" tag="section">
  <c-account-summary />
</c-i18n>
```


Citry derives the normal direction for `ar-EG` and renders:


```html
<section lang="ar-EG" dir="rtl">
  ...
</section>
```


You may set `direction="ltr"` or `direction="rtl"` explicitly for an unusual
subtree. In normal application code, let Citry derive it from the locale.

When another framework owns `<html>`, that framework's document shell should
read `context.locale` and `context.direction` and apply them to its root
element. Citry does not search for and mutate an unrelated document element.

## Use logical CSS properties

Components that support both directions should prefer logical properties:


```css
.account-card {
  padding-inline-start: 1rem;
  border-inline-end: 1px solid var(--border-color);
}
```


Review icons separately. An arrow that means "next" may need to mirror, while
a media-play icon or a brand mark usually should not.

## Citry isolates interpolated scalar text

An inserted name, path, identifier, or number may use another direction from
the surrounding translation. Citry keeps typed scalar boundaries through
message formatting and isolates those runs so they do not reorder surrounding
text.

Application strings may not contain Unicode bidi controls or paragraph
boundaries inside one inline parameter. Use separate structural markup for
multiline or deliberately directed content.

HTML escaping and bidi isolation solve different problems. Escaping prevents
markup injection. Isolation protects visual ordering. Citry applies both where
each is needed.

## Preserve fallback language metadata

`tr()` returns only text. If fallback selects another language, the plain
string cannot attach a different `lang` to itself.

Server code that permits this fallback should use `resolve()` and apply the
returned metadata to an application-owned element:


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


`resolved.used_fallback` tells application code whether the selected locale
differs from the requested locale.

Directional isolation still protects a plain fallback string, but it cannot
tell a screen reader which language to pronounce. Keep the `lang` markup when
the language may differ.

## Translate accessible outputs too

Keep visible and assistive text under one message when they describe the same
control:


```fluent
my-app-account-actions = Actions
    .aria-label = Open account actions
    .title = Show available actions
```


Call the attribute explicitly for `aria-label` or `title`. Catalog fallback is
computed for each attribute, so a missing assistive translation cannot be
mistaken for the visible label.

Browser-owned text and accessibility outputs need equivalent-language coverage
for every selectable locale. Their call sites cannot safely attach a hidden
fallback language after `$i18n.switchLocale()`.

Wrapperless rich messages have the same requirement. See
[Rich messages](/v/0.4.4/i18n/rich-messages/) for why `<c-trans>` rejects a
cross-language fallback.

## Browser providers update their semantic host

A successful browser switch updates the client provider's `lang` and `dir`
attributes together with its readonly context. It does not change ordinary
server-owned text below that element.

Do not put fixed server text directly below a provider whose browser locale can
change, because the wrapper could then claim a new language while the text
stays in the old one. Place fixed text behind its own server-only
`<c-i18n tag="...">` boundary or rerender it from the server.