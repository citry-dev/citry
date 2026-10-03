---
title: Migrate from django-components
description: Move a django-components project to Citry with a complete, agent-friendly checklist of template, Python, asset, extension, and testing changes.
---

# Migrate from django-components

This guide helps you move a django-components project to Citry, one
component at a time, without breaking the pages that still use the old
components.

Citry comes from the maintainer of django-components and keeps its
component model, so much of your project carries over. A component is still a Python class with a
template, JavaScript, and CSS. It still declares typed inputs and slots,
and fills, provide and inject, render caching, extensions, error
fallbacks, and the dynamic component all have Citry counterparts.

These changes cause most of the migration work:

- **Attribute values are literal unless the name starts with `c-`.**
  `class="{{ kind }}"` renders the text `{{ kind }}`, with no error. Write
  `c-class="kind"` ([DJC-033](#djc-033)).
- **Citry templates are not Django templates.** They have no `{% %}`
  tags, filters, `{% extends %}`, or `{% include %}`. Use `<c-if>`,
  `<c-for>`, components, and Python expressions.
- **A component sees only what it is given.** There is no Django context,
  request, or context processor. Pass values as inputs, or share them
  with provide and inject.
- **The data methods are renamed.** `get_template_data()` becomes
  `template_data(self, kwargs, slots)`. A method with the old name is
  never called, and nothing tells you ([DJC-067](#djc-067)).
- **Settings and the registry belong to a `Citry` object.** Django
  settings and global registries move onto one `Citry` instance
  ([DJC-026](#djc-026), [DJC-027](#djc-027)).
- **Browser code runs as Vue.** Citry mounts interactive components as
  Vue apps, and `Component.View` handlers become Citry Events: component
  methods that the browser calls over HTTP.

This guide compares Citry with the django-components source at commit
[`5d4d4f5`](https://github.com/django-components/django-components/commit/5d4d4f5d13dd06c80ba389f30fc63fdbb71cda75){: target="_blank" rel="noopener"}
from June 20, 2026. If your project uses another django-components
version, check its release notes for further differences. Read the
version of these docs that matches the Citry version you installed.

## Port one component

Here is a small django-components component and its caller:

```citry
from django_components import Component, register


@register("todo_list")
class TodoList(Component):
    template = """
      <ul class="{{ kind }}">
        {% for item in items %}
          <li>{{ item|upper }}</li>
        {% empty %}
          <li>Nothing to do</li>
        {% endfor %}
      </ul>
    """

    def get_template_data(self, args, kwargs, slots, context):
        return {
            "items": kwargs["items"],
            "kind": kwargs.get("kind", "plain"),
        }
```

```htmldjango
{% component "todo_list" items=todos kind="compact" / %}
```

The same component in Citry:

```citry
from citry import Component


class TodoList(Component):
    citry = app  # your Citry instance

    class Kwargs:
        items: list[str]
        kind: str = "plain"

    def template_data(self, kwargs, slots):
        return {"items": kwargs.items, "kind": kwargs.kind}

    template = """
      <ul c-class="kind">
        <c-for each="item in items">
          <li>{{ item.upper() }}</li>
        </c-for>
        <c-empty>
          <li>Nothing to do</li>
        </c-empty>
      </ul>
    """
```

```citry-html
<c-todo-list c-items="todos" kind="compact" />
```

What changed:

- The class registers itself on `app` when Python defines it, under
  `todo-list` and `todolist`, so `@register` goes away.
- Inputs and their defaults are fields on `Kwargs`.
- `get_template_data()` became `template_data()`, without `args` and
  `context`.
- `class="{{ kind }}"` became `c-class="kind"`, and the filter became a
  Python method call.
- `c-items="todos"` evaluates `todos`. `kind="compact"` passes the plain
  string.

## Choose how to migrate

For a gradual migration inside Django, use
[`citry-django`](https://github.com/joeyjurjens/citry-django){: target="_blank" rel="noopener"}.
It lets you put Citry components in Django templates and use Django
template tags in Citry components, so both kinds of component can live
on one page while you migrate. It is a community project, so follow its
README for the versions and setup it supports.

For a direct port, render Citry through its
[Django integration](/advanced/web-frameworks/#django), which mounts Citry's
rendering, asset routes, and event routes in your Django project. Replace
a whole component subtree at a time.

Either way, work in this order:

1. Create a branch and run the existing Python, browser, and snapshot
   tests.
2. List what you have: component directories, settings, custom template
   tags, extensions, JavaScript hooks, caches, and `Component.View`
   subclasses.
3. Install Citry, create one `Citry` instance, connect it to Django, and
   register one leaf component (a component that renders no other
   components).
4. Port that component and its tests, and check it in the browser before
   you move to the next connected group.
5. Remove django-components only after searches and tests show that
   nothing still depends on it.

Citry has no django-components compatibility aliases or shims. Migrate
each leftover pattern explicitly.

## Read the checklist { #how-to-read-the-checklist }

The checklist covers every known difference you can observe. Each row has
a stable `DJC-###` ID; use it when you track work or ask for help.

- **🔴 Breaks:** the project fails until you change the pattern.
- **🟡 Check behavior:** output or runtime behavior may differ.
- **🟢 Update tests:** the browser shows the same page, but an exact
  output or error assertion may need updating.

The django-components column names the code to search for. Not every row
applies to every project, so mark rows that do not match as not
applicable rather than changing code just in case. Rows marked "Details
below" have more notes in the list under their table.

The sections run from the changes almost every project needs to the
ones only some projects hit. In the Citry column, `app` means your
`Citry` instance.

## Rewrite templates

Start here. These patterns appear in almost every template, and the
first one fails silently.

| ID | django-components | Citry: what to do | Impact |
|---|---|---|---|
| <span id="djc-033">DJC-033</span> | Attribute values are evaluated; `{{ }}` works inside a quoted value | Plain values are literal. Add `c-` to evaluate: `class="{{ x }}"` becomes `c-class="x"`. Details below. | 🔴 |
| <span id="djc-037">DJC-037</span> | `{% %}` tags such as `{% lorem %}` or custom tags, also inside arguments | `{% %}` is not executed; it renders as typed. Use `<c-if>` / `<c-for>`, or compute the value in `template_data` and pass it as `c-flag="is_active"`. | 🔴 |
| <span id="djc-014">DJC-014</span> | `{% extends %}`, `{% block %}`, `{% include %}` | Turn the base template into a component with slots. Replace `{% include 'p.html' %}` with a `<c-p />` component. | 🔴 |
| <span id="djc-018">DJC-018</span> | Django template filters, filter registries, chaining | No filters. Rewrite each one as a Python expression. Details below. | 🔴 |
| <span id="djc-020">DJC-020</span> | Positional inputs and `...list` spreads | Inputs are keyword-only. Name every input. Replace a list spread with a mapping in `c-bind`, or pass the list as one named input. | 🔴 |
| <span id="djc-030">DJC-030</span> | A missing variable renders as `""` | Raises `KeyError` that points at the line and column. Pass the name, guard the branch, or set a default in `template_data`. | 🟡 |
| <span id="djc-080">DJC-080</span> | A dot reads dict keys: `{{ data.error }}` | A dot is Python attribute access. Slot data still allows `d.error`; an ordinary dict needs `d['error']`. Details below. | 🟡 |
| <span id="djc-019">DJC-019</span> | `_('text')` in arguments, lists, and dicts | Citry rejects template names that start with `_`. Use Citry's [i18n](/i18n/) `tr()` messages, or translate in `template_data`. Details below. | 🔴 |
| <span id="djc-039">DJC-039</span> | `bool_var=" {% noop is_active %} "` gives the string `" True "` | A `c-` value is one expression and keeps its type. Build a string yourself where you want one: `c-label="f' {is_active} '"`. For markup values, see [DJC-042](#djc-042). | 🟡 |
| <span id="djc-042">DJC-042</span> | A `{% component %}` inside an argument renders to HTML for that input | Write the markup in the value: `c-body="<span>Hello {{ name }}</span>"`. Details below. | 🟡 |
| <span id="djc-040">DJC-040</span> | `{# #}` anywhere, including inside an argument | Comments go between tags or between attributes, not inside a value. Move each one before the attribute or above the tag. Details below. | 🟡 |
| <span id="djc-051">DJC-051</span> | `@lol=2` passes a data input | On a component tag, `@lol` is a Vue event listener. Rename data inputs, for example to `at_lol`. Details below. | 🔴 |
| <span id="djc-017">DJC-017</span> | An unclosed `{{` or `{#` renders as text | `SyntaxError` on the first render, before any output. Close the delimiter. | 🟡 |
| <span id="djc-007">DJC-007</span> | Unclosed tags in a component template are tolerated | Every tag must be closed and matched, or the first render raises `SyntaxError: Unclosed tag <thead>` (or "Mismatched tags"). Details below. | 🟡 |

Details:

- **DJC-033:** `key="hi"` passes the string `"hi"`; `c-key="hi"`
  evaluates the name `hi`. `class="{{ kind }}"` outputs
  `class="{{ kind }}"` with no error, so search your templates for `{{`
  inside attribute values.
- **DJC-018:** In Citry, `|` inside an expression is Python's bitwise or.
  `{{ value|upper }}` becomes `{{ value.upper() }}`, and
  `{{ value|yesno:"yes,no" }}` becomes `{{ 'yes' if value else 'no' }}`.
  For anything longer, pass a helper function as an input or register it
  once with `Citry(template_globals={...})`.
- **DJC-080:** Fill data is an immutable `SlotData` mapping, so keys that
  are valid Python names work with a dot. A key such as `aria-label`, a
  key starting with `_`, or a key with the same name as a mapping method
  needs brackets: `d['aria-label']`. Dot access to real object
  attributes works as before.
- **DJC-019:** Citry evaluates template expressions in a restricted
  mode, and a name that starts with `_` raises `SecurityError` at render.
  Write the text as a message in the component's `messages`
  block and call it with `tr()`, also in attributes:
  `c-label="tr('my-app-hello')"`. The component also declares the
  language its messages are written in (`class I18n: messages_locale`);
  [Internationalization](/i18n/) shows the setup. Citry messages use
  Fluent, not gettext. To keep your `.po` files, translate in
  `template_data`, or register a helper under another name, such as
  `translate`, with `Citry(template_globals=...)`.
- **DJC-042:** A `c-` value that starts with an HTML tag and ends with its
  closing tag is a nested template, not a Python expression. It renders
  with the same data, so `{{ }}` works inside it. Several roots
  (`<em>a</em><em>b</em>`), a self-closing tag (`<br/>`), and a component
  (`<c-badge c-label='name' />`) all work. Any other value is an
  expression, so plain text needs quotes: `c-body="'hello'"`. A half-open
  tag is an error. The nested template renders after the outer component,
  so the outer component's `template_data` cannot read its HTML.
- **DJC-040:** `<a {# note #} class="x">` works. Inside a plain attribute
  value the comment renders as visible text, so `title="{# note #}Hi"`
  sends the comment to the browser. Inside a `c-` value it is an error.
- **DJC-051:** `@lol="2"` listens for a `lol` event and never reaches the
  component's inputs. A bare `@lol` raises `TypeError` naming the
  attribute. An `@lol` key in a `c-bind` mapping raises an error that asks
  you to write it in the template. Check every `@` attribute that was
  meant as data.
- **DJC-007:** In django-components a component template is any text.
  Citry parses it as markup. A partial that was a bare `<thead>` fragment
  must become a complete unit, for example by including its `<table>` and
  receiving the rows through a slot.

## Set up Citry

Create one `Citry` instance and move Django settings and registries onto
it. A `Citry` instance holds your settings, the names of your components,
and the caches.

| ID | django-components | Citry: what to do | Impact |
|---|---|---|---|
| <span id="djc-026">DJC-026</span> | Standalone registries, `@register(..., registry=...)`, `all_registries()` | Each `Citry` instance owns its registry. Set `citry = app` on the class or call `app.register(...)`. Keep your own references instead of calling `all_registries()`. | 🔴 |
| <span id="djc-027">DJC-027</span> | `COMPONENTS` setting; `dirs` defaults to `BASE_DIR/components` | Pass the settings to `Citry(...)` or `CitrySettings(...)`. List every component directory as an absolute path; Citry does not read `BASE_DIR`. | 🔴 |
| <span id="djc-064">DJC-064</span> | `COMPONENTS["libraries"]` and `import_libraries()` | Remove them. Put those modules under a scanned directory (`Citry(dirs=...)`), or import them where your app starts. | 🔴 |
| <span id="djc-065">DJC-065</span> | `autodiscover(map_module=...)` | Call `app.autodiscover()`, or rely on the scan Citry runs at the first lookup. There is no `map_module`; module names are worked out from the `sys.path` entry that contains each file. | 🟡 |
| <span id="djc-028">DJC-028</span> | Reserved names follow registered Django tags and the tag formatter | `if`, `elif`, `else`, `for`, `empty`, `raw`, `fill`, and `slot` are Citry's own tags. Rename a colliding component, for example `Empty` to `EmptyState`. | 🔴 |
| <span id="djc-077">DJC-077</span> | `dynamic` and `error_fallback` are reserved | Built-in names are reserved too: `component`, `element`, `provide`, `cache`, `error-fallback`, `js`, `css`, `i18n`, `trans`, `mark`. Details below. | 🔴 |
| <span id="djc-024">DJC-024</span> | Names with `/`, such as `te-s/t` | A name starts with a letter, followed by letters, digits, `-`, `_`, or `.`. Rename (`te-s-t`) and update the `<c-*>` tags. | 🔴 |
| <span id="djc-015">DJC-015</span> | `tag_formatter`, `TagFormatter`, `ShorthandComponentFormatter` | The tag form is always `<c-name />`. Remove the setting and formatter classes. | 🔴 |
| <span id="djc-021">DJC-021</span> | `TagSpec` flags that the parser removes from the inputs | No parser flags. A bare attribute is an input with the value `True`. Turn each flag into a boolean input. | 🔴 |
| <span id="djc-016">DJC-016</span> | django-template-partials: `template.html#partial_name` | No equivalent. Make the partial a Citry component and render it directly. | 🔴 |
| <span id="djc-070">DJC-070</span> | A dotted name such as `card.old.py` or `assets.v2/` crashes the scan | Files and directories with an extra dot are silently skipped. Details below. | 🟡 |
| <span id="djc-060">DJC-060</span> | `reload_on_file_change` setting | Delete it. Call `enable_hot_reload(app, mode="hot")` (or `"restart"`) from `citry.contrib.django`, once, in your `AppConfig.ready()`. Details below. | 🟡 |

Details:

- **DJC-077:** A component class registers under its lowercased class
  name, so a class named `Element` fails at class definition with
  `AlreadyRegistered`, naming the built-in it collides with. Rename it
  (for example to `ElementView`) or give it a `name` attribute that is not
  reserved, then update its `<c-*>` tags. [DJC-028](#djc-028) lists the
  reserved tag names.
- **DJC-070:** Citry skips any file or directory with a dot in its name
  beyond the `.py` suffix: editor and system files (`.#card.py`,
  `._card.py`, `.cache/`), backups like `card.old.py`, dotted directories
  with everything inside them, and symlinks that resolve to such paths.
  Every regular file django-components found is still found. The one
  exception is a symlink with a plain name that points into a
  dot-prefixed directory: point it at a path without dots, or replace it
  with the real file. To have a skipped file discovered, rename it.
- **DJC-060:** Nothing is watched until you call `enable_hot_reload`.
  There is no `"off"` mode, and an invalid mode fails at the call.

## Merge HTML attributes

`{% html_attrs %}` becomes ordinary attributes on the element. These
changes are easy to find and can silently change output.

| ID | django-components | Citry: what to do | Impact |
|---|---|---|---|
| <span id="djc-001">DJC-001</span> | `{% html_attrs attrs defaults class=... %}`, `attrs:` and `defaults:` keys | Write `<div c-bind="defaults" c-bind="attrs" c-class="...">`. Fallbacks go first. Details below. | 🔴 |
| <span id="djc-002">DJC-002</span> | The same key twice is joined: `foo="bar baz"` | The same attribute twice on one tag is an error ("Duplicate attribute 'foo' found"). Combine the values into one attribute. Only `c-bind` may repeat. | 🟡 |
| <span id="djc-043">DJC-043</span> | No equivalent: one argument syntax | `title="x"` and `c-title="y"` on one tag is a parse error. Pick one form per input (`c-bind` may still repeat). Details below. | 🟡 |

Details:

- **DJC-001:** `c-bind="mapping"` spreads a dict of attributes onto the
  element; `c-class` and `c-style` add classes and styles. Attributes
  apply left to right and the later one wins, so put the fallback
  mapping first and the caller's mapping after it. `class` and `style`
  merge instead of overwriting. A leftover `attrs:foo=` is not rejected:
  it arrives as an input literally named `attrs:foo`, so search attribute
  names for `:`.
- **DJC-002:** When a `c-bind` mapping and an explicit attribute set the
  same key, the later one wins (`foo="baz"`). `class` and `style` still
  merge.
- **DJC-043:** On plain elements, `class` with `c-class` and `style` with
  `c-style` may appear together and add up. A `c-bind` spread may sit
  beside one explicit form, because its key may be missing at render
  time. Put conditional overrides in `c-bind`. Writing the same
  form twice is always an error.

## Pass data explicitly

A Citry component reads only its inputs, its slots, and values provided
by an ancestor. Port the data methods and the class-level declarations
here.

| ID | django-components | Citry: what to do | Impact |
|---|---|---|---|
| <span id="djc-067">DJC-067</span> | `get_template_data(self, args, kwargs, slots, context)`, `get_js_data`, `get_css_data` | Rename to `template_data(self, kwargs, slots)`, `js_data`, `css_data`, and drop `args` and `context`. Details below. | 🔴 |
| <span id="djc-008">DJC-008</span> | Reading variables from the surrounding `Context`; `self.outer_context` | No ambient context. Pass each value as an input. For values deep descendants need, use provide and inject. | 🔴 |
| <span id="djc-010">DJC-010</span> | `self.request`, context processors, `csrf_token` | Not injected. Read the request in your view and pass what components need as inputs. Details below. | 🔴 |
| <span id="djc-009">DJC-009</span> | `context_behavior` setting; `only` | Remove both. Citry always behaves like `isolated`. Details below. | 🟡 |
| <span id="djc-011">DJC-011</span> | `{% if component_vars.is_filled.title %}` | No `component_vars`. In `template_data`, return `{'has_title': slots.get('title') is not None}` and branch with `<c-if>`. | 🟡 |
| <span id="djc-050">DJC-050</span> | `on_render_before`, `on_render`, `on_render_after` | Merge them into one `on_render(self)`, written as a generator when it runs before and after the template. Details below. | 🔴 |
| <span id="djc-071">DJC-071</span> | Inner `Defaults` class; `Default(...)`; `get_component_defaults()` | Make defaults annotated fields on `Kwargs`: `size: int = 10`. Delete `Defaults`, which Citry silently ignores. Details below. | 🔴 |
| <span id="djc-072">DJC-072</span> | Passing `None` gets the declared default | `None` is a value; the default applies only when the input is left out. Details below. | 🟡 |
| <span id="djc-073">DJC-073</span> | `self.raw_kwargs` includes defaults | `self.raw_kwargs` holds only what the caller passed, so an omitted input raises `KeyError`. Read defaults from the typed kwargs: `kwargs.size`. | 🟡 |
| <span id="djc-068">DJC-068</span> | A bare inner `Kwargs`, `Slots`, or `TemplateData` class becomes a NamedTuple | It becomes a dataclass. Use attribute access instead of tuple access. Details below. | 🟡 |
| <span id="djc-069">DJC-069</span> | `Kwargs = Empty` | There is no `Empty`; the import fails. Write `class Kwargs: pass`, and delete `Args = Empty`. Details below. | 🟡 |

Details:

- **DJC-067:** A ported component that still defines `get_template_data`
  renders without error, but the method is never called, so the template
  sees only the raw inputs. After porting, search for
  `def get_template_data`, `def get_js_data`, and `def get_css_data`; each
  hit is dead code. Values from `args` become named inputs
  ([DJC-020](#djc-020)). Values from `context` become inputs, provided
  values, or template globals ([DJC-008](#djc-008)).
- **DJC-010:** For a value many components need, such as the CSRF token,
  the current user, or the locale, provide it once near the top of the
  page with `<c-provide>` and read it with `inject()`. See
  [CSRF protection](/security/#protect-event-posts-from-csrf) for Django
  and Citry Events.
- **DJC-009:** A project that ran in `"django"` mode must also rewrite
  fills that read the child component's variables, such as loop items.
  Pass those values as slot data: `<c-slot name="row" c-item="item" />` in
  the child and `data="row"` on the `<c-fill>`.
- **DJC-050:** `on_render` may return content, or `None` to keep the
  template output. As a generator, code before `yield` runs before the
  template renders. Write `result, error = yield`: `result` is the
  finished render (a `CitryRender`, not a string), or `None` when
  rendering failed, and then `error` holds the exception. To add content
  after the output, put it in the template. Each `yield content` replaces
  the output and receives a new `(result, error)` pair. Code that added
  template variables in `on_render_before` moves into `template_data`.
  A plain `str` that `on_render` returns shows as text; wrap HTML in
  `Markup`.
- **DJC-071:** Move each `Defaults` attribute onto `Kwargs` with an
  annotation: `variable = "test"` becomes `variable: str = "test"`. An
  unannotated `name = value` declares nothing.
    - `Default(fn)` becomes `dataclasses.field(default_factory=fn)`, and a
      mutable default like `items = []` becomes
      `field(default_factory=list)`. Writing `items: list = []` fails at
      class definition with "mutable default ... use default_factory".
    - A leftover `Defaults` class raises no error; the defaults just stop
      applying. A template that reads the value fails with a missing-name
      error. If `Kwargs` is declared, passing the input is rejected as
      unexpected; without `Kwargs` it is accepted untyped.
    - `get_component_defaults()` has no direct replacement. To inspect
      declarations, iterate `dataclasses.fields(MyComp.Kwargs)` and
      handle `dataclasses.MISSING` while reading each field's `default` or
      `default_factory`. For resolved values, read the typed kwargs while
      rendering, or write a helper that calls the factories.
- **DJC-072:** A template that showed the default now shows `None`, with
  no error. Leave the input out where you meant "use the default". If a
  caller may really hold `None`, resolve it in `template_data`:
  `value if value is not None else fallback`. Audit call sites that pass
  `None` on purpose.
- **DJC-068:** Indexing, unpacking, `_asdict()`, and `_replace()` raise,
  and so does setting an attribute the class does not declare. Use
  attribute access, or `self.raw_kwargs` for a plain dict. A class with an
  explicit base (NamedTuple, `@dataclass`, or a pydantic model) is left as
  it is by both libraries and needs no change.
- **DJC-069:** With an empty `Kwargs`, a template attribute fails when the
  template is parsed ("can only have the following attributes ..."), and
  a keyword argument in a Python call raises `TypeError` at render. Delete
  `Args = Empty` because components take no positional inputs
  ([DJC-020](#djc-020)).

## Port slots and provide

Port these together, so slot data and the values shared with descendants
stay explicit.

| ID | django-components | Citry: what to do | Impact |
|---|---|---|---|
| <span id="djc-029">DJC-029</span> | `{% slot "main" default %}` marks the slot for body content | Body content always fills the slot named `default` (`<c-slot />` or `<c-slot name="default" />`). Rename the slot to `default`, or wrap caller content in `<c-fill name="main">`. | 🔴 |
| <span id="djc-032">DJC-032</span> | `{% fill "x" default="fallback_var" %}` | Rename `default=` to `fallback=`. | 🔴 |
| <span id="djc-031">DJC-031</span> | `SlotContext.context`, `SlotFallback`, `{% fill body=my_slot %}` | `SlotContext` has `data`, `fallback` (an optional `Slot`), and `provides`. Stop reading `ctx.context`. Forward a slot with `<c-fill name="x">{{ my_slot }}</c-fill>`. | 🔴 |
| <span id="djc-034">DJC-034</span> | `{% provide "x" key=val var:field=... %}` | Write `<c-provide key="x" ...>` (`c-key` for a computed name). Turn each group into one dict: `var1:key="hi"` becomes `c-var1="{'key': 'hi'}"`. | 🟡 |
| <span id="djc-035">DJC-035</span> | `inject()` returns a `DepInject` NamedTuple | It returns a `Provided` NamedTuple. Field access and tuple behavior are the same; update assertions or logs that match the type name or repr. | 🟡 |
| <span id="djc-036">DJC-036</span> | A bad provide name raises `TypeError` / `TemplateSyntaxError` | It raises `ValueError`. A missing inject key still raises `KeyError`, now suggesting the closest provided key. Update `except` clauses and assertions. | 🟡 |

## Move assets and JS

Replace Django static-file handling, then check how each migrated page
starts its browser behavior.

| ID | django-components | Citry: what to do | Impact |
|---|---|---|---|
| <span id="djc-095">DJC-095</span> | `class Media` on a component | Citry ignores `Media` silently: no error and no assets. Rename it to `class Dependencies`. Details below. | 🔴 |
| <span id="djc-025">DJC-025</span> | The page loads its own runtime script and component scripts | Remove that runtime and the attributes only it understood. Citry sends one Vue runtime that mounts every Citry Vue app. Details below. | 🔴 |
| <span id="djc-022">DJC-022</span> | `$component` callback receives the JS data object and a context argument | The callback receives one object; read `js_data()` values from its `component`. Prefer Vue Options (a Vue component options object). Details below. | 🔴 |
| <span id="djc-085">DJC-085</span> | `DjangoComponents`, `Components`, `createComponentsManager()`, `registerComponentData(...)` | Delete that code and return browser data from `js_data()`. Browser code uses `Citry.events` for server calls and `Citry.vue` for Vue helpers. | 🔴 |
| <span id="djc-012">DJC-012</span> | `ComponentsFileSystemFinder`, `collectstatic`, `static_files_allowed` / `static_files_forbidden` | Remove the finder from `STATICFILES_FINDERS`, skip `collectstatic` for components, drop the settings, and mount Citry's routes. Details below. | 🔴 |
| <span id="djc-004">DJC-004</span> | `render_dependencies(html, strategy=...)`, `DJC_DEPS_STRATEGY` | Call `render().serialize(deps_strategy=..., deps_position=...)`. Details below. | 🟡 |
| <span id="djc-023">DJC-023</span> | `{% component_css_dependencies %}` and `{% component_js_dependencies %}` emit assets | `<c-css />` and `<c-js />` only choose where assets go. Leaving one out does not keep assets off the page. Details below. | 🟡 |
| <span id="djc-074">DJC-074</span> | `get_js_data()` values ship whenever the component has any JS | `js_data()` values reach the browser on every render and become reactive members of the component's Vue instance. A plain script that runs once on load cannot read them. Details below. | 🟡 |
| <span id="djc-086">DJC-086</span> | `callComponent()` returns a Promise; callback errors reject it | Citry calls each `$component` callback itself; you cannot call or await it. Return nothing or a cleanup function. Details below. | 🔴 |
| <span id="djc-087">DJC-087</span> | The call rejects when no element carries the instance marker | For a component that renders only text or nothing, the callback still runs, but `component.$el` is not an element and `els` is empty. Check before using them. | 🟡 |
| <span id="djc-045">DJC-045</span> | A subclass's `Media` entries come before its parent's | The parent's come first, so the subclass's CSS wins ties. Usually nothing to do; if you relied on the parent winning, restate its rule in the subclass. | 🟡 |
| <span id="djc-046">DJC-046</span> | Classes in `extend` merge in reverse order | They merge in the order written: `extend = [A, B]` puts A's assets first. Reverse your list only if you relied on the old order. | 🟡 |
| <span id="djc-047">DJC-047</span> | `bytes` asset paths are accepted | `TypeError` naming the component and the value. Use `str` or `pathlib.Path`. | 🟡 |

Details:

- **DJC-095:** A nested `Dependencies` class takes `js`, `css` (a list, or
  a dict keyed by media type such as `"print"`), and `extend`, like
  `Media`. [Dependency files](/advanced/dependency-files/) shows the
  options. Search for `class Media` after porting; a leftover one fails
  silently.
- **DJC-025:** Let Citry deliver its Vue runtime, which matches the
  installed Citry version, and the compiled components. In templates, use
  Vue's own `v-*` attributes, Citry's `@c-*` attributes to call the
  server, and `:c-*` attributes to bind State (values Citry keeps between
  server calls).
- **DJC-022:** `$component` accepts Vue Options or a callback. The
  callback runs after mount and after each server render the page applies
  to the component. Its argument has `component` (the Vue instance),
  `revision`, `onEvent`, `state`, `sendEvent`, `loading`, `error`, `i18n`,
  `els` (the root elements), and `id` (the render ID). Rewrite the
  callback to take `({ component, revision, onEvent })` and read
  `js_data()` values from `component`, such as `component.message`. Or
  use `onServerRender({ component, revision, onEvent })` in the
  Options object.
- **DJC-012:** Citry serves only the scripts and styles it generates,
  from routes you mount in your app, and never serves component source
  (`.py` or `.html`). A custom `media_class` that overrode
  `render_js` / `render_css` has no direct counterpart: control the tags
  with `Script` and `Style` entries and the `on_dependencies` extension
  hooks, which can change the list of scripts and styles before Citry
  writes the tags.
- **DJC-004:** `deps_strategy` is `document`, `simple`, `fragment`, or
  `ignore`, and `deps_position` is `smart`, `prepend`, or `append`. The
  defaults are `document` and `smart`. Map `prepend` and `append` to
  `deps_position`, map `raw` to `deps_strategy="ignore"`, and drop the
  `type=` alias. For example, call
  `serialize(deps_strategy="document", deps_position="append")` on the
  result of `MyComp(...).render()`. There is no project-wide setting, so pass non-default values on each
  `serialize()` call.
- **DJC-023:** If you left `{% component_css_dependencies %}` out of a
  page to keep its CSS off, that no longer works. To keep an asset off a
  page, remove it from the component or filter it in `on_dependencies`.
- **DJC-074:** Templates, Vue Options (`this.message`), and
  `onServerRender` (`component.message`) can read `js_data()` values. After
  porting, check each component that pairs a plain script with
  `js_data()`: move the script into `$component` ([DJC-022](#djc-022)), or
  delete the unused `js_data()`. `css_data()` is not affected; its
  stylesheet ships whenever the component has CSS.
- **DJC-086:** Returning any value other than nothing or a cleanup
  function throws `TypeError`. An `async` callback is allowed and may
  resolve to a cleanup function; Citry does not wait for it, and logs a
  rejection instead of stopping the page. An error thrown by a
  synchronous callback stops the Vue app that contains the component, so
  catch errors that must not stop the page. Move server work to an Events
  handler and await `$sendEvent()`.

## Port built-ins, caching

These built-ins keep their purpose but change their tag, their Python
entry point, or where their data is cached.

| ID | django-components | Citry: what to do | Impact |
|---|---|---|---|
| <span id="djc-062">DJC-062</span> | `{% component name_var %}` is rejected | Use `<c-component c-is="name_var" />`. A tag name is always literal: `<c-{{ name }}>` does not interpolate. | 🔴 |
| <span id="djc-076">DJC-076</span> | `DynamicComponent`, the `dynamic` tag, `dynamic_component_name` | Write `<c-component c-is="x" />`. The tag name `c-component` is fixed, so delete `dynamic_component_name` and the import. Details below. | 🔴 |
| <span id="djc-079">DJC-079</span> | `{% component "error_fallback" %}`, a `content` slot, the `ErrorFallback` class | Write `<c-error-fallback>` with the guarded content as its body. Details below. | 🔴 |
| <span id="djc-075">DJC-075</span> | Processed JS/CSS cached in a Django cache under `__components:` keys at class definition | Each `Citry` instance caches in `Citry(cache=...)`, in memory by default, under `citry:` keys at the first render. Details below. | 🟡 |
| <span id="djc-091">DJC-091</span> | `Component.Cache.cache_name` picks a Django cache per component | A `Citry` instance has one cache backend. Pass it once as `Citry(cache=...)`. | 🟡 |
| <span id="djc-092">DJC-092</span> | `Cache.hash()`; `include_slots` | Replace both with `Cache.vary(self, kwargs, slots)`, returning only values that can change output; Citry hashes them. Details below. | 🔴 |
| <span id="djc-093">DJC-093</span> | `{% cache timeout key ... using=... %}` | Write `<c-cache key="..." c-ttl="..." c-vary="...">` in a component template, and remove `{% load cache %}` and `using=`. Details below. | 🔴 |
| <span id="djc-094">DJC-094</span> | Cached HTML keeps the original component IDs | Cached descendants get fresh IDs on each replay; only the cached component itself keeps its ID. Do not store or compare descendant IDs (`data-cid-*`); Citry updates its own dependency and Events records. | 🟡 |

Details:

- **DJC-076:** In Python, resolve the target yourself:
  `app.get(name)(**kwargs)` when you hold a name, or call the component
  class you already hold. [DJC-062](#djc-062) shows the tag.
- **DJC-079:** For a plain-text fallback, use the `fallback="..."`
  attribute. For markup, use a `fallback` fill that receives the error as
  slot data (`<c-fill name="fallback" data="d">`, then read `d.error`),
  and put the guarded content in the
  `default` fill, since fills cannot mix with other content. A leftover
  `<c-fill name="content">` fails at the component's first render with a
  parse error naming the fill. Giving both fallback forms raises
  `RuntimeError` ("give only one"); update `except` clauses and tests that
  matched `TemplateSyntaxError`. Delete `ErrorFallback` imports; in
  Python, call
  `app.get("error-fallback")(fallback="...", slots={"default": ...})`.
  See [Error boundaries](/concepts/error-boundaries/).
- **DJC-075:** If several workers shared processed assets through a
  Django cache, pass a shared store to `Citry(cache=...)`:
  `citry.contrib.django.DjangoCache` wraps a Django cache, and
  `citry.contrib.caches` has Redis and diskcache adapters. Update
  monitoring or warm-up jobs that looked for `__components:*` keys or
  expected the cache to fill when modules are imported.
- **DJC-091:** Split components across `Citry` instances only when they
  truly need separate instances; there is no per-component backend name.
- **DJC-092:** Every slot that produces content must appear in the
  `vary()` result, for example whether it is present or which caller
  option shapes it. Citry never guesses a slot's effect from closures or source text.
- **DJC-093:** Move standalone cached markup into a root component
  template, and turn the timeout and the vary-on values into `c-ttl` and
  `c-vary`. The cache uses the `Citry` instance's backend.

## Port extensions

Skip this section if your project has no custom extensions or custom
template tags.

A plain `str` that `on_component_rendered` or `on_slot_rendered` returns
shows as text, the same as one that `on_render` returns; wrap HTML in
`Markup`.

| ID | django-components | Citry: what to do | Impact |
|---|---|---|---|
| <span id="djc-058">DJC-058</span> | Nested `ComponentConfig` class (or the `ExtensionClass` alias) | Rename it to `Config` with the base `Extension.Config`. Update hook bodies for renamed context fields such as `ctx.component_class`. | 🔴 |
| <span id="djc-057">DJC-057</span> | Routes under `/components/ext/<name>/`; `<int:id>` converters | Routes live under `ext/<name>/` below your Citry mount prefix. Write `{id}` and convert it in the handler. Details below. | 🔴 |
| <span id="djc-084">DJC-084</span> | `ComponentCommand` subclasses whose `handle` receives Django's options | Base the commands on `citry.ExtensionCommand`. Details below. | 🔴 |
| <span id="djc-054">DJC-054</span> | Custom tags: `BaseNode` or `@template_tag` | There is no tag API. Rewrite each custom tag as a component. Details below. | 🔴 |
| <span id="djc-056">DJC-056</span> | `on_component_rendered` fires on the failing component | It fires on each enclosing component, with the original exception, not on the failing component itself. Move error handling to an ancestor's hook, or wrap the component in an error boundary. | 🟡 |
| <span id="djc-055">DJC-055</span> | `on_registry_created` / `on_registry_deleted` | No standalone registries, so no such hooks. Use `on_extension_created`, whose context carries the `Citry` instance. Details below. | 🟡 |
| <span id="djc-059">DJC-059</span> | `Component.template` / `.js` / `.css` return hook-processed content | The class attributes keep what you wrote. Read processed content with `get_template().source`, `get_js()`, and `get_css()`. | 🟡 |
| <span id="djc-090">DJC-090</span> | `on_component_class_deleted(ctx)` | Not available. Move cleanup to `on_component_unregistered`. Details below. | 🔴 |
| <span id="djc-061">DJC-061</span> | An unregistered class is freed with your last reference | Classes register when defined and the `Citry` instance keeps them. Call `app.unregister(cls)` before dropping the class. Details below. | 🟡 |

Details:

- **DJC-057:** The route table does not depend on Django; mount
  `app.urls` in your app with a `citry.contrib` adapter. Route parameters are
  always strings, so write `int(id)` in the handler. Return a
  `RouteResponse` instead of an `HttpResponse`.
- **DJC-084:** `ExtensionCommand` has the same shape: `name`, `help`,
  arguments built from `CommandArg` and `CommandArgGroup` (with the same
  argparse fields), nested subcommands, and `handle(**kwargs)`. `handle`
  receives only the options the command declares, so delete code that
  pops parser internals or reads Django's global options. Reach the
  `Citry` instance as `self.citry` instead of through Django settings.
  Users run the command as `citry ext run <extension> <command>`.
- **DJC-054:** A registered component is the one kind of user-defined
  tag: `<c-my-tag />` looks the name up, and an unknown name fails at
  render naming the tag. Move the tag's render function body into
  `template_data` or `on_render`, its parameters into `Kwargs` fields, and
  its body into the default slot. Turn flags into inputs as in
  [DJC-021](#djc-021).
- **DJC-055:** Registry-deletion cleanup has no replacement; the
  registry goes away with its `Citry` instance.
- **DJC-090:** For indexes that only
  live in memory and should drop an unregistered class, use a
  `weakref.WeakSet` or `WeakKeyDictionary`. `Citry.clear()` tears everything down at once and emits no
  per-component hooks.
- **DJC-061:** This matters for tooling that swaps classes at runtime,
  such as hot swapping or unloading plugins. Unregister the class, then
  drop your own references. Rendering does not keep a class alive, so
  Python then frees it.

## Update tests and CLI

These rows change how you test components and which commands your
scripts and CI call.

| ID | django-components | Citry: what to do | Impact |
|---|---|---|---|
| <span id="djc-066">DJC-066</span> | `@djc_test` resets global state | Remove it. In each test, create `c = Citry()` and set `citry = c` on the components under test. Details below. | 🟡 |
| <span id="djc-013">DJC-013</span> | Django's `template_rendered` signal and `assertTemplateUsed` | No template signal. Record renders with a test extension that implements `on_component_rendered`. | 🟡 |
| <span id="djc-052">DJC-052</span> | `data-djc-id-<id>` on each rendered root | `data-cid-<id>=""` appears only on output with no browser behavior, with a fresh ID each render. Details below. | 🟡 |
| <span id="djc-081">DJC-081</span> | `python manage.py components ...` | Use the standalone `citry` command. Details below. | 🔴 |
| <span id="djc-082">DJC-082</span> | `components create X` writes a directory of files | `citry create MyButton` writes one `my_button.py`. Details below. | 🟡 |
| <span id="djc-083">DJC-083</span> | `components list` with `--all`, `--columns`, `--simple` | `citry list` has fixed columns and none of these flags. Details below. | 🟡 |

Details:

- **DJC-066:** No test harness ships. Each `Citry` instance owns its
  registry and caches. The only process-wide state is the default
  instance, which a component uses when it does not set `citry=`, so give
  test components their own instance.
- **DJC-052:** Update CSS selectors, JavaScript lookups, and snapshots
  that match `data-djc-id-*`. On an interactive page no element carries
  the marker: select a component by a class or data attribute you write
  in its template, or use a template `ref` in its JavaScript.
- **DJC-081:** Installing Citry adds a `citry` command:
    - Commands: `citry list`, `citry inspect [component] --json`,
      `citry create <name>`, `citry check`, `citry format`,
      `citry watch`, `citry ext list`,
      `citry ext run <extension> <command>`, and `--version`.
    - Replace each `manage.py components ...` call in scripts, docs, and
      CI. If your project builds its own `Citry` instance, put
      `--app your.module:attribute` first (the convention ASGI and WSGI
      servers use).
    - Remove Django's global options (`--settings`, `--pythonpath`,
      `--traceback`, `--no-color`, `--skip-checks`, `-v`); they do not
      exist.
    - `upgrade` is gone, because Citry has no legacy Django template
      syntax to upgrade. Replace `startcomponent X` with
      `citry create X` ([DJC-082](#djc-082)).
    - `inspect --json` prints the component catalog of the loaded
      instance; a component name or alias (any case) narrows it to that
      component. It needs an instance that loads; there is no static
      analysis fallback.
- **DJC-082:** The file contains the component class with an inline
  multiline template, and no separate HTML, JS, or CSS files. The command
  takes only `--path`, always prints the created file's path, and never
  overwrites an existing file; delete the file first to redo it. Remove
  `--force`, `--dry-run`, `--js`, `--css`, `--template`, and `--verbose`
  from wrapper scripts, because they now fail with a usage error.
- **DJC-083:** `citry list` prints one row per component: all its
  registered names, the class name, and the file that defines it
  (relative to the working directory when inside it; empty when there is
  no source file). `citry ext list` prints extension names. Update
  anything that parses the output, and remove the old flags, which now
  fail with a usage error.

## Migrate `Component.View`

If the project defines `Component.View`, finish the template and
component port first, then follow
[Migrate from Component.View](/guides/migrate-from-component-view/). It
shows how to keep a verb-shaped route working before you split it into
named, typed Citry Events.

| ID | django-components | Citry: what to do | Impact |
|---|---|---|---|
| <span id="djc-088">DJC-088</span> | `Component.as_view()` dispatches `get` / `post` to a live component; `render_to_response(context=..., slots=...)` | Move handlers into `class Events(ViewEvents):`, a Citry Events class for GET/POST-style handlers, and return a component or an Events action (such as a redirect). Details below. | 🔴 |
| <span id="djc-089">DJC-089</span> | `get_component_url()`, `public=False`, `get_route_path()` with `args` / `kwargs` | Public methods in `Events` get fixed routes. Build URLs with `events.url(name, query=..., fragment=...)` or `get_event_url(...)`. Details below. | 🔴 |

Details:

- **DJC-088:** Handler inputs are typed `data` and a request object that
  does not depend on Django. `self` is the configuration for that one
  call, not a rendered component, so move values you read from the live
  component into explicit data, context, State, or application services.
  Replace manual request parsing with a data class.
- **DJC-089:** There is no `public` flag: expose a handler by putting it
  in `Events`, and hide it by leaving it out. There is no custom route
  per component. Keep query and fragment inputs, but move route
  parameters into typed event data. Use named handlers and the URL
  builders for call sites you want to keep stable. The method-only
  `ViewEvents` route has no URL builder of its own; treat it as a first
  step of the port, not as a routing API.

## Output-only changes { #update-exact-output-tests }

These differences do not change what the browser shows, but error
assertions and exact HTML snapshots may need updating.

| ID | django-components | Citry: what to do | Impact |
|---|---|---|---|
| <span id="djc-003">DJC-003</span> | Single quotes escaped as `&#x27;` | Escaped as `&#39;`, the same character. Update tests that assert the old bytes. | 🟢 |
| <span id="djc-005">DJC-005</span> | Inline JS/CSS containing its own end tag raises `RuntimeError` | Raises `ValueError`: `...contains a '</script>' end tag. This is not allowed.` | 🟢 |
| <span id="djc-006">DJC-006</span> | A runtime script on every document render | Added only when the output needs browser behavior: Vue syntax, component JS, `js_data()` values, or Events. Drop assertions that it is always present. | 🟢 |
| <span id="djc-038">DJC-038</span> | Parentheses opt a value into Python: `disabled=(not editable)` | The `c-` prefix makes it an expression; parentheses still work but are not needed: `c-disabled="not editable"`. | 🟢 |
| <span id="djc-041">DJC-041</span> | Helpers like `len` added to the context on each call | As before, builtins are not available: `len(...)` raises `KeyError` unless you supply it. Register helpers once: `Citry(template_globals={"len": len})`. | 🟢 |
| <span id="djc-044">DJC-044</span> | A plain base class with a `Media` class contributes its entries | Reusable bases and plain classes in `extend` contribute their `Dependencies`. Details below. | 🟢 |
| <span id="djc-048">DJC-048</span> | `js = ...` with `js_file = None` (or the reverse) raises | Allowed; only two values that are both set conflict. You can restore an explicit `= None`. | 🟢 |
| <span id="djc-049">DJC-049</span> | `://example.com/x.js` emitted as `%3A//example.com/...` | Emitted as written. Update tests that assert `%3A//`. | 🟢 |
| <span id="djc-053">DJC-053</span> | Error paths include a slot segment for content rendered through a slot | Content in a fill or fallback shows `Card(slot:body)`. A component placed by a fill shows only the components whose templates contain it (`Page > Failing`). Details below. | 🟢 |
| <span id="djc-063">DJC-063</span> | Text beside `{% fill %}` raises `TemplateSyntaxError` | The parent's first render raises `SyntaxError`: `Text cannot appear next to '<c-fill>'` (or `Expression cannot appear...` for a variable). | 🟢 |
| <span id="djc-078">DJC-078</span> | `NotRegistered`: "The component 'x' was not found" | Still `NotRegistered`, now "No component registered as 'x'." Details below. | 🟢 |

Details:

- **DJC-044:** Relative paths resolve from the module that declares them,
  and the files are registered to the component that uses them. Keep
  reusable assets on the class that owns them. To cut or choose branches,
  use `Dependencies = None`, `extend = False`, or an explicit `extend`
  list.
- **DJC-053:** django-components wrote `provider(slot:content)`. Update
  slot-segment assertions to the `Card(slot:body)` form, and drop the
  slot segment only from paths where a component placed by a fill fails.
- **DJC-078:** When `<c-component c-is="...">` cannot resolve a computed
  name, the message also suggests `<c-element>` for a plain HTML element.
  Code that only catches the exception type needs no change.

## Verify the migration

Before you remove django-components:

- Search again for its component, slot, fill, provide, dependency, and
  cache tags, its settings, and its registry imports.
- Run the original unit and snapshot tests. Change exact HTML assertions
  only where the checklist marks an output-only difference.
- In the browser, exercise the migrated pages' startup, Vue behavior,
  component assets, forms, CSRF protection, fragments, and event
  endpoints.
- Check that production serves Citry's generated asset routes, and that
  no old component source directory is exposed as a static directory.
- Run `citry list` and `citry inspect --json` against the same `Citry`
  instance the application serves.

## Use a coding agent { #give-this-migration-to-a-coding-agent }

Give the agent the Markdown version of this page, which has the
checklist without navigation or page markup. Ask for an audit first,
review its plan, and only then let it edit the project:

```text
Read this project's AGENTS.md, README, dependency files, and
test commands. Detect the installed Citry and django-components
versions. Read https://citry.dev/llms.txt and use its version
selector to find the Markdown version of the "Migrate from
django-components" guide that matches the installed Citry. If
there is none, report the mismatch instead of following another
version.

Audit the project for every DJC-### item in the guide. For each
item that applies, report the matching files, the rewrite, and
its risk. Mark every other item not applicable or blocked. List
the Python, browser, and snapshot commands that will verify the
work.

Do not edit files yet. Produce a staged plan that migrates one
connected group of components at a time and keeps the app
runnable between stages. Do not add django-components
compatibility shims.
```

After you approve the audit, tell the agent which stage to implement.
Ask it to report the `DJC-###` items it addressed and the verification
results before it starts the next stage.
