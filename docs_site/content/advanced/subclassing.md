---
title: Subclass components
description: Reuse a component contract while changing its template, browser code, styles, dependencies, or Python behavior.
---

# Subclass components

Sometimes you need several versions of one component: a card and a linked
card, a dialog and a confirm dialog. They take the same inputs and behave
the same way, and differ only in one part, such as the template or the
styles.

Subclass the component for this. Put the shared parts on a base class, and
let each child change only what makes it different.

A subclass inherits every future change to its parent. When the two
should change independently, render one inside the other's template
instead.

## Inherit behavior

A child inherits its parent's inputs, methods, template, JavaScript, and
CSS. Override only the method that differs:

```citry
from citry import Component


class Message(Component):
    class Kwargs:
        text: str

    def template_data(
        self,
        kwargs: Kwargs,
        slots,
    ) -> dict[str, str]:
        return {"message": self.format_message(kwargs.text)}

    def format_message(self, text: str) -> str:
        return text

    template = """
      <p>{{ message }}</p>
    """


class LoudMessage(Message):
    def format_message(self, text: str) -> str:
        return text.upper()
```

`LoudMessage(text="Saved")` renders `<p>SAVED</p>`. The inherited
`template_data()` calls the child's `format_message()`, and the child
uses its parent's `Kwargs` because it declares none of its own.

## `Kwargs` in a child

To give a child one more input, the natural first attempt is a nested
`Kwargs` with only the new field. That class replaces the parent's, the
same as any nested Python class, so the child loses `text`:

```citry
class SignedMessage(Message):
    # Wrong: this Kwargs has only `author`.
    class Kwargs:
        author: str
```

Citry warns with
[`NestedSchemaReplacedWarning`][citry.NestedSchemaReplacedWarning] when
the class is defined, and rendering
`SignedMessage(text="Saved", author="Ada")` fails with
`unexpected keyword argument 'text'`.

Name the parent's class as a base to keep its fields and defaults, and
add the new ones:

```citry
class SignedMessage(Message):
    # Right: keeps `text` and adds `author`.
    class Kwargs(Message.Kwargs):
        author: str

    def template_data(
        self,
        kwargs: Kwargs,
        slots,
    ) -> dict[str, str]:
        data = super().template_data(kwargs, slots)
        data["message"] += f" ({kwargs.author})"
        return data
```

`SignedMessage` now takes both `text` and `author`. The child calls
`super().template_data()` and adjusts the result.

The same rule applies to every nested class that describes data:

- [`Kwargs`][citry.Component.Kwargs] and [`Slots`][citry.Component.Slots],
  which describe the inputs;
- [`TemplateData`][citry.Component.TemplateData],
  [`JsData`][citry.Component.JsData], and
  [`CssData`][citry.Component.CssData], which describe what
  `template_data()`, `js_data()`, and `css_data()` return;
- [`State`][citry.Component.State], the values
  [server events](/events/) keep between calls.

Nested classes that hold settings, such as `Dependencies` and `Events`,
work differently: a child's class adds to its parent's. See
[Extend settings](#extend-settings).

## Replace or drop inputs

What a child writes for `Kwargs` or another data class decides what it
gets:

| On the child | The child uses |
|---|---|
| Nothing | The parent's class, unchanged. |
| `Kwargs = Message.Kwargs` | The parent's class, unchanged. |
| `class Kwargs(Message.Kwargs):` | The parent's fields, plus its own. |
| `class Kwargs:` | Only its own fields. |
| `Kwargs = None` | No `Kwargs`, so it accepts any input. |

A child can drop the parent's inputs on purpose. A plain class that does
so still warns; see [Silence the warning](#silence-the-warning). Set the
class to `None` to stop checking inputs at all:

```citry
class FreeformMessage(Message):
    Kwargs = None

    def template_data(self, kwargs, slots):
        return {"message": kwargs.get("text", "")}
```

`FreeformMessage` declares no `Kwargs`, so it accepts any inputs. It also
overrides `template_data()`. Without a `Kwargs` class, `kwargs` is a plain
mapping, so the inherited `kwargs.text` fails; read it with
`kwargs.get("text")` instead.

When the child's new class leaves out a field, also override any
inherited method that uses it. A method that reads a dropped input fails
at render with `AttributeError`. A `template_data()` that returns a key
the new `TemplateData` left out fails at render with
`TypeError: unexpected keyword argument`.

Setting a class to anything other than a class or `None`, such as
`Kwargs = 5`, raises `ValueError` when the component is defined.

## Replace inherited code

A component's template, JavaScript, and CSS can each be written inline or
loaded from a file:

- [`template`][citry.Component.template] or `template_file`;
- [`js`][citry.Component.js] or `js_file`;
- [`css`][citry.Component.css] or `css_file`.

Each line above is one pair. A child that sets neither member of a pair inherits
the parent's. A child that sets either member replaces the whole pair, and
still inherits the other two pairs:

```citry
from citry import Component


class BaseCard(Component):
    class Kwargs:
        title: str

    template = """
      <article class="card" ref="root">
        <h2>{{ title }}</h2>
      </article>
    """
    js = """
      $component(({ component }) => {
        const root = component.$refs.root;
        if (root instanceof HTMLElement) {
          root.dataset.ready = "true";
        }
      });
    """
    css = """
      .card {
        border: 1px solid currentColor;
      }
    """


class LinkedCard(BaseCard):
    template_file = "linked_card.html"
```

`LinkedCard` uses its own template file in place of `BaseCard`'s inline
`template`, and keeps `BaseCard`'s JavaScript and CSS.

To drop one of them in a child, set it to `None`:

```citry
class StaticCard(BaseCard):
    js = None
```

`StaticCard` has no JavaScript. Leaving `js` out would inherit it.

## Subclass State

A child's `State` follows the same rule. It also carries settings:
where the values are kept and what browser code can do with them. For
example, `_public` lists the fields browser code can read. Name the
parent's class to keep both its fields and its settings:

```citry
class ProjectPanel(Component):
    class State:
        project_id: int

        _public = ("project_id",)


class SortedProjectPanel(ProjectPanel):
    # Keeps `project_id` and `_public`, and adds `sort`.
    class State(ProjectPanel.State):
        sort: str = "name"
```

Because the child keeps `_public`, browser code cannot read `sort` until
the child lists it: `_public = ("project_id", "sort")`.

A plain `class State:` starts from the default settings, not the
parent's: values are stored, signed, in the page, browser code can read
and change every field, the values never expire, and the size limit
(`_max_bytes`) is the default. Citry warns when the parent set `_public`,
`_model`, or `_max_age` and the new `State` does not. It does not warn
about `_max_bytes`.

If the parent keeps its values on the server with `_storage = "server"`,
a plain `class State:` that does not set `_storage` raises `ValueError`
when the component is defined, because its values would be stored in
the page, where anyone who opens the page can read them. Name the parent's class, or set
`_storage` in the new `State`.

[Event state](/events/state/) explains the State settings.

## Extend settings

A child's settings class keeps every parent setting and adds its own,
and a child setting with the same name wins (`Dependencies` joins its
file lists instead; see below). This covers
[`Events`][citry.Component.Events], `Dependencies`, `Lint`, `Cache`,
`I18n`, `Debug`, `Preview`, and the classes that
[extensions](/advanced/extensions/) add. A child's `Events`, for example,
keeps its parent's handlers, and a handler with the same name replaces the
parent's.

### Extend dependencies

The nested `Dependencies` class lists extra script and stylesheet files a
component needs. A child's `Dependencies` adds to its parents' lists rather
than replacing them. Parent entries come first, so a child's stylesheet
loads later and wins when two CSS rules are equally specific:

```citry
from citry import Component, SlotInput


class BaseDialog(Component):
    class Slots:
        default: SlotInput

    class Dependencies:
        js = ["/static/dialog.js"]
        css = ["/static/dialog.css"]

    template = """
      <dialog>
        <c-slot />
      </dialog>
    """


class ConfirmDialog(BaseDialog):
    class Dependencies:
        css = ["/static/confirm-dialog.css"]
```

`ConfirmDialog` loads `dialog.js`, `dialog.css`, and then
`confirm-dialog.css`.

Set `extend` on `Dependencies` to choose which parents contribute:

- `extend = True`, the default, includes the parent classes;
- `extend = False` includes only this class's own entries;
- `extend = [CompactTheme, BrandTheme]` includes exactly those classes and
  their own parents, in the order written.

`Dependencies = None` gives the child no extra files, not even its
parents'.

[Dependency files](/advanced/dependency-files/) covers the forms an entry
can take, local files, URLs, and how the files are served.

## Less common cases

### Combine two parents

When a child has two parent components that declare different `Kwargs`,
or one of them sets `Kwargs = None`, Citry does not guess which to use.
The same applies to `Slots`, `State`, `TemplateData`, `JsData`, and
`CssData`. A parent that only inherits its `Kwargs` does not count as
declaring one, and two parents that use the same module-level class do
not conflict.

For `class IconButton(Button, Tooltip):`, defining the child raises
`ValueError`:

```text
Component IconButton: its bases declare Kwargs differently
(Button.Kwargs and Tooltip.Kwargs), and Citry does not combine them.
Declare Kwargs on IconButton: write `Kwargs = Button.Kwargs` to use
one of them, or define the fields in module-level classes and write
`class Kwargs(FirstFields, SecondFields):`.
```

To use one parent's inputs, write `Kwargs = Button.Kwargs` on the child.
To take fields from both, keep them in plain classes at module level and
list those as bases:

```citry
class LabelFields:
    label: str


class IconFields:
    icon: str = "star"


class IconButton(Button, Tooltip):
    class Kwargs(LabelFields, IconFields):
        pass
```

`class Kwargs(Button.Kwargs, Tooltip.Kwargs):` does not work: Python
raises `TypeError: multiple bases have instance lay-out conflict`.

When one parent inherits from the other, the nearer declaration applies
and there is no error.

### Fix a child's previews

A child inherits its parent's `Preview.variants()`, which pass the
parent's inputs. When the child's `Kwargs` drops a parent input or adds
a required one, those inputs no longer fit, and its preview fails when
it renders. Give the child its own `Preview` with a `variants()` method that
passes its inputs, or set `Preview = None` to leave it out of the
gallery. See [Component previews](/advanced/previews/).

### Required after defaults

A required field can follow one with a default. Citry then makes fields
keyword-only: in one class, all of its fields; in a child, only the
child's own fields. Components always receive inputs by name, so this
changes nothing for callers. When you build the class yourself, such as
`self.TemplateData(...)`, pass them by name.

### Mixing schema styles

Citry builds one dataclass from a plain class and its plain or
dataclass bases, keeping every field and default. A child of a frozen
dataclass is frozen too. A few kinds of base keep their own behavior:

- A Pydantic model extends a Pydantic parent the usual Pydantic way.
- A class you decorate with `@dataclass` yourself is kept as written.
- When a plain base defines `__init__`, `__new__`, or `__slots__`, the
  class keeps that construction, and Citry does not turn it into a
  dataclass.

Some combinations raise `ValueError` when the component is defined:

- Mixing frozen and non-frozen dataclass bases.
- A `NamedTuple` cannot gain fields in a subclass. Declare a new
  `NamedTuple` that lists every field, or use a plain class.

See [Inputs and validation](/concepts/inputs-and-validation/) for each
schema style.

### Silence the warning

When a child's own class leaves out fields that its parent's class
declared, Citry emits
[`NestedSchemaReplacedWarning`][citry.NestedSchemaReplacedWarning] once
per class, naming the fields and the fix:

```text
Component SignedMessage: Kwargs replaces Message.Kwargs and leaves out
field 'text'. To keep it, write `class Kwargs(Message.Kwargs):`.
```

The warning appears when the component is defined. For a component from
a [component library](/advanced/component-libraries/), it appears when the
library is registered. There is no warning for `Kwargs = None`, for a
class that names the parent's class as a base, or for a new class that
keeps every field name. Choosing another parent's class, such as
`Kwargs = Tooltip.Kwargs` on `IconButton`, does not warn either. A
`State` also warns about dropped settings; see
[Subclass State](#subclass-state).

When you drop the fields on purpose, silence it with a standard warnings
filter. Install it before the module that defines the component is
imported, for example at the top of your entry point, because the warning
fires when the class is defined:

```python
import warnings

import citry

warnings.filterwarnings(
    "ignore",
    category=citry.NestedSchemaReplacedWarning,
)
```

### Conflicting pairs

Setting both `template` and `template_file` to non-empty values on the
same class raises `ValueError` when the class is defined. The same applies
to `js` and `js_file`, and `css` and `css_file`.

### Duplicate entries

A dependency listed more than once is loaded once, at its first position.
For a script, the first entry's tag attributes are used, and a later
duplicate cannot add more. The same holds for a stylesheet listed again
under the same `media` key. Listing one stylesheet under two different
`media` keys raises `ValueError` when the page is rendered to HTML.
