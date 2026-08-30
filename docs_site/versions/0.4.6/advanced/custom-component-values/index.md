---
title: Custom component values
url: https://citry.dev/v/0.4.6/advanced/custom-component-values/
description: "Let Python objects resolve themselves into Citry components during rendering."
---
# Custom component values

Sometimes a value from your domain already knows how it should appear. A
payment status might choose a status badge, for example. The
[`ComponentLike`](/v/0.4.6/reference/component-libraries/#citry-componentlike) protocol lets that object become a Citry
component when a template inserts it.

This is an advanced composition tool. A direct component call is clearer when
the page already knows which component it wants.

## Define the conversion

Add `__citry_element__(citry)` to the value. Use the supplied engine to find or
create the component element:


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


`ComponentLike` is a structural protocol. You do not need to inherit from it.
Implementing this method with the right shape is enough.

The method must return a [`CitryElement`](/v/0.4.6/reference/rendering/#citry-citryelement) that belongs to
the engine Citry supplied. Do not use the module-level default engine or keep a
component class from another application.

## Insert the value in a template

Return the object as ordinary template data:


```citry
from citry import Component


class Receipt(Component):
    class Kwargs:
        status: PaymentStatus

    citry = app

    template = """
      <p>Payment: {{ status }}</p>
    """
```


When the expression is inserted, Citry calls `__citry_element__()` once for
that occurrence and renders the returned element in the current component
tree. The same conversion works for a value passed into a slot.

There is no ambient engine outside a component render. A general custom value
does not gain a `.render()` method, so application code should choose a Citry
instance and build the concrete component directly when rendering on its own.

[`LibraryComponentInvocation`](/v/0.4.6/reference/component-libraries/#citry-librarycomponentinvocation) implements
the same protocol and adds `render(citry=app)` for that library-specific use
case. See [Component libraries](/v/0.4.6/advanced/component-libraries/).

## Related reference

- [`ComponentLike`](/v/0.4.6/reference/component-libraries/#citry-componentlike)
- [`CitryElement`](/v/0.4.6/reference/rendering/#citry-citryelement)
- [`Citry.get()`](/v/0.4.6/reference/citry/#citry-citry-get)