# pygments-citry

A [Pygments](https://pygments.org/) lexer for [Citry](https://citry.dev)
components. It highlights a component the way an editor would: the Python class,
plus the HTML, JavaScript, and CSS embedded in its `template`, `js`, and `css`
string attributes, each in its own language.

Without it, a Citry component in a ` ```python ` block renders the template,
JS script, and CSS stylesheet as flat string literals. With it, a ` ```citry `
block colours the `<c-*>` tags, the `{{ ... }}` interpolation, the embedded
stylesheet, and the embedded script.

## Install

```bash
pip install pygments-citry
```

The package registers a `citry` lexer as a Pygments plugin, so any tool that
resolves lexers by name picks it up once it is installed.

## Use it

On the command line:

```bash
pygmentize -l citry my_component.py
```

In Python:

```python
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name

lexer = get_lexer_by_name("citry")
html = highlight(source, lexer, HtmlFormatter())
```

In a Markdown site (mkdocs with `pymdownx.highlight` / `pymdownx.superfences`,
or any python-markdown setup that resolves Pygments lexers by name), tag the
fence with `citry`:

````markdown
```citry
from citry import Component

class Welcome(Component):
    template = """
      <div class="card">
        <h1>{{ title }}</h1>
        <p c-if="count">You have {{ count }} new messages.</p>
      </div>
    """
```
````

No superfences `custom_fences` entry is needed: once the package is installed,
`citry` resolves like any other Pygments lexer.

## What it highlights

A `citry` block is highlighted as Python, and the following Citry constructs
inside the `template` / `js` / `css` attributes are highlighted in their own
language:

- The HTML in `template`, including the `<c-*>` component and control-flow tags
  (the built-ins `c-if`, `c-for`, `c-slot`, `<c-raw>`, and so on) and `c-*`
  dynamic attributes.
- `{{ ... }}` interpolation, whose body is a Python expression.
- `{# ... #}` template comments.
- The JavaScript in `js` and the CSS in `css`.

The `<c-raw>...</c-raw>` element is treated as verbatim text, matching the
engine: `{{ }}` and tags inside it are not interpreted.

## Template-only blocks: `citry-html`

For a fenced block that shows only a template, with no surrounding Python (just
`<c-*>` tags, `{{ ... }}`, and `{# ... #}`), tag it `citry-html`:

````markdown
```citry-html
<c-for each="item in items">
  <li c-if="item.visible">{{ item.label }}</li>
</c-for>
```
````

`citry` expects full component code (Python with embedded strings), so a bare
template belongs in a `citry-html` block instead.

## License

MIT. Part of the [Citry](https://github.com/citry-dev/citry) project.
