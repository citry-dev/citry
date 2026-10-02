---
title: Custom component values
description: Let Python objects resolve themselves into Citry components during rendering.
---

# Custom component values

Sometimes one of your own Python objects already knows how it should look
on the page. A payment status, for example, always shows as a green or red
badge. Instead of choosing the badge component in every template, you can
teach the object to turn itself into that component. Then a template only
writes `{{ status }}`.

When the page already knows which component it wants, call that component
directly. It is clearer.

## Turn an object into a component

Add a `__citry_element__(citry)` method to the class. Citry calls it with
the [`Citry`][citry.Citry] instance that is rendering the page. Use that
instance to look up the component, and return the component called with
its inputs:

```python
from dataclasses import dataclass

from citry import Citry, CitryElement


@dataclass(frozen=True)
class PaymentStatus:
    label: str
    successful: bool

    def __citry_element__(
        self,
        citry: Citry,
        /,
    ) -> CitryElement:
        badge = citry.get("acme-badge")
        tone = "success" if self.successful else "danger"
        return badge(label=self.label, tone=tone)
```

The class does not need to inherit from anything. Having this method is
enough for Citry to treat it as a [`ComponentLike`][citry.ComponentLike]
value.

Look the component up on the `citry` argument, as above. Do not use a
component class from another `Citry` instance, such as one imported from
another application.

## Insert the object in a template

Pass the object to the template like any other value:

```citry
from citry import Component


class Receipt(Component):
    citry = app

    class Kwargs:
        status: PaymentStatus

    template = """
      <p>Payment: {{ status }}</p>
    """
```

Each time the template inserts `status`, Citry calls `__citry_element__()`
once and renders the returned component in that place. The same works when
you pass the object as slot content.

## Render the object outside a template

The object knows which component to build only while a page is rendering,
because that is when Citry supplies the `citry` argument. It has no
`.render()` method of its own. To render it on its own, choose the `Citry`
instance yourself and build the component directly.

Library components are the exception: their calls also have
`render(citry=app)`. See [Component libraries](/advanced/component-libraries/).

## Errors from `__citry_element__()`

Citry checks what the method returns:

- a value that is not a [`CitryElement`][citry.CitryElement] raises
  `TypeError`;
- a component from a different `Citry` instance than the one rendering the
  page raises `ValueError`.

## Related reference

- [`ComponentLike`][citry.ComponentLike]
- [`CitryElement`][citry.CitryElement]
- [`Citry.get()`][citry.Citry.get]
