---
title: Rating
description: Select or display an exact localized score with native radio Form behavior.
---

# Rating

Use `CRating` for a short qualitative score such as a product review or
conversation rating. Its public value is an exact canonical decimal string;
`None` means unrated.

## Select a rating

Supply a standalone accessible `label`, or compose Rating in `CField` for a
visible label, description, error, and shared state.

```citry-html
<c-CField required>
  <c-fill name="label">Product rating</c-fill>
  <c-fill name="default"><c-CRating name="rating" /></c-fill>
</c-CField>
```

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/crating/snippets/basic.py" title="Select a rating" />

Without JavaScript, the component remains a same-name native radio group. It
submits and validates `required` normally. The visual stars are decorative;
each radio has a localized “value out of maximum” name.

## Choose fractional precision

`precision` is an exact decimal that divides one. Half, quarter, fifth, and
tenth ratings are supported as long as `max / precision` produces at most 200
choices. Floats and exponent notation are rejected.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/crating/snippets/precision.py" title="Use half and tenth ratings" />

`max` is an integer from 1 through 20. Use `CRadioGroup` if individual values
need different text labels or meanings.

## Clear or control the value

Set `allow_clear=True` to let a person click the committed value again and
return to the unrated state. A required Rating then becomes natively invalid.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/crating/snippets/controlled.py" title="Control and clear a rating" />

Client `value` is a canonical string or `null`. A controlled interaction is a
request: stars, checked radio, and FormData remain unchanged until the owner
returns the requested value. `onHoverChange` reports preview only and never
changes the submitted value.

## Preserve Form and reset behavior

Editable Rating submits the checked native radio. Readonly Rating blocks
mutation but submits its exact value through an owned hidden transport.
Disabled Rating neither focuses nor submits.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/crating/snippets/forms.py" title="Submit and reset ratings" />

An uncanceled reset restores the server value. Controlled state receives a
reset request and waits for its owner. `form` supports an external native Form;
inside `CForm`, Rating cannot redirect ownership.

## Localize accessible value names

`citry-ui-rating-value` names each exact choice and updates in place beneath a
client-enabled `<c-i18n>` provider. The number profile is
`citry-ui-rating`. Zero-configuration source mode uses canonical digits and the
component's English source message.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/crating/snippets/locales.py" title="Localize Rating choice names" />

Set `value_label="Score {value} / {max}"` for an application-owned fixed
pattern. An explicit override creates no catalog binding.

## Choose states and public styles

Solid and subtle variants combine with sm, md, and lg sizes. Public
`--cui-rating-*` variables and `[data-citry-ui-part="..."]` selectors
customize the documented anatomy.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/crating/snippets/states.py" title="Compare Rating states and styling" />

RTL uses logical geometry. Coarse pointers retain large hit targets and forced
colors preserve fill and focus. Custom symbol markup is intentionally not part
of this contract; use Radio for differently named choices.

<!-- UI_LIBRARY_API_REFERENCE -->
