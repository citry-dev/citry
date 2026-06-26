# Jinja2 port of the django-components small benchmark scenario
# (test_benchmark_djc_small.py, vendored in this directory): the same Button
# component, theme data, and render entrypoints, expressed in Jinja2. The
# benchmark harness reads this file as a source string and slices it at the
# markers below, so the code outside the pytest section must stay
# self-contained. See docs/design/benchmarking.md (section 2.1 lists Jinja2 as
# the first engine beyond the Django family).
#
# Fairness notes (docs/design/benchmarking.md section 6.5): Jinja2 has no
# component model, so the Button is a plain template rendered with a context
# dict, exactly as the vendored Django port renders `button_template_str`. The
# derived values (the merged CSS class, the link/button branch) are computed in
# Python `button()`, mirroring Django's `button()` function. Jinja2 has no
# `{% html_attrs %}` tag, so the port supplies one as a registered global, which
# is the idiomatic Jinja2 extension point and the direct parallel to Django's
# tag (both are Python helpers the template calls). Autoescape is on, matching
# the Django and citry ports' escaping.

from typing import Literal, NamedTuple, TypeAlias

from jinja2 import Environment, Template
from markupsafe import Markup

# ----------- IMPORTS END ------------ #

# There is no Const variant of the small scenario: a single dynamic Button has
# no render-invariant literals to mark, so the Const optimization (a
# citry-specific axis) has nothing to fold here. See citry's small scenario for
# the same note; the large scenario is where Const is exercised.

#####################################
#
# IMPLEMENTATION START
#
#####################################

# Autoescape on, so the port escapes the same values the Django and citry ports
# do. Templates compiled by `env.from_string` are not cached by Jinja2, so the
# scenario caches them by hand below (the Django port does the same), which puts
# the one-time compile in the `first` render and reuses it for `subsequent`.
env = Environment(autoescape=True)


def html_attrs(attrs: "dict | None", *extra_classes: str) -> Markup:
    """
    Render an HTML attribute string, merging every `class` source.

    The element's own `class` (from `attrs`) and each extra class string merge
    into one source-ordered, de-duplicated list (Vue/django-components style,
    where multiple class sources combine rather than overwrite); the remaining
    attributes render as `key="value"` pairs, with `True` rendering as a bare
    boolean attribute and `False`/`None` dropping it.

    This is the Jinja2 port's stand-in for Django's `{% html_attrs %}` tag.
    """
    attrs = attrs or {}

    seen: set[str] = set()
    classes: list[str] = []
    for source in (attrs.get("class", ""), *extra_classes):
        for token in source.split():
            if token not in seen:
                seen.add(token)
                classes.append(token)

    # `Markup(literal).format(...)` escapes the substituted values, so the join
    # of these pieces is safe to mark as already-escaped HTML.
    parts: list[Markup] = []
    if classes:
        parts.append(Markup(' class="{}"').format(" ".join(classes)))
    for key, value in attrs.items():
        if key == "class":
            continue
        if value is True:
            parts.append(Markup(" {}").format(key))
        elif value is False or value is None:
            continue
        else:
            parts.append(Markup(' {}="{}"').format(key, value))
    return Markup("").join(parts)


env.globals["html_attrs"] = html_attrs

templates_cache: dict[int, Template] = {}


def lazy_load_template(template: str) -> Template:
    template_hash = hash(template)
    if template_hash in templates_cache:
        return templates_cache[template_hash]
    template_instance = env.from_string(template)
    templates_cache[template_hash] = template_instance
    return template_instance


#####################################
# RENDER ENTRYPOINT
#####################################


def gen_render_data():
    data = ButtonData(
        href="https://example.com",
        disabled=False,
        variant="primary",
        type="button",
        attrs={
            "class": "py-2 px-4",
        },
        slot_content="Click me!",
    )
    return data


def render(data: "ButtonData"):
    return button(data)


#####################################
# THEME
#####################################

ThemeColor: TypeAlias = Literal["default", "error", "success", "alert", "info"]
ThemeVariant: TypeAlias = Literal["primary", "secondary"]

VARIANTS = ["primary", "secondary"]


class ThemeStylingUnit(NamedTuple):
    """
    Smallest unit of info, this class defines a specific styling of a specific
    component in a specific state.

    E.g. styling of a disabled "Error" button.
    """

    color: str
    """CSS class(es) specifying color"""
    css: str = ""
    """Other CSS classes not specific to color"""


class ThemeStylingVariant(NamedTuple):
    """
    Collection of styling combinations that are meaningful as a group.

    E.g. all "error" variants - primary, disabled, secondary, ...
    """

    primary: ThemeStylingUnit
    primary_disabled: ThemeStylingUnit
    secondary: ThemeStylingUnit
    secondary_disabled: ThemeStylingUnit


class Theme(NamedTuple):
    """Class for defining a styling and color theme for the app."""

    default: ThemeStylingVariant
    error: ThemeStylingVariant
    alert: ThemeStylingVariant
    success: ThemeStylingVariant
    info: ThemeStylingVariant


_secondary_btn_styling = "ring-1 ring-inset"

theme = Theme(
    default=ThemeStylingVariant(
        primary=ThemeStylingUnit(
            color="bg-blue-600 text-white hover:bg-blue-500 focus-visible:outline-blue-600 transition",
        ),
        primary_disabled=ThemeStylingUnit(color="bg-blue-300 text-blue-50 focus-visible:outline-blue-600 transition"),
        secondary=ThemeStylingUnit(
            color="bg-white text-gray-800 ring-gray-300 hover:bg-gray-100 focus-visible:outline-gray-600 transition",
            css=_secondary_btn_styling,
        ),
        secondary_disabled=ThemeStylingUnit(
            color="bg-white text-gray-300 ring-gray-300 focus-visible:outline-gray-600 transition",
            css=_secondary_btn_styling,
        ),
    ),
    error=ThemeStylingVariant(
        primary=ThemeStylingUnit(color="bg-red-600 text-white hover:bg-red-500 focus-visible:outline-red-600"),
        primary_disabled=ThemeStylingUnit(color="bg-red-300 text-white focus-visible:outline-red-600"),
        secondary=ThemeStylingUnit(
            color="bg-white text-red-600 ring-red-300 hover:bg-red-100 focus-visible:outline-red-600",
            css=_secondary_btn_styling,
        ),
        secondary_disabled=ThemeStylingUnit(
            color="bg-white text-red-200 ring-red-100 focus-visible:outline-red-600",
            css=_secondary_btn_styling,
        ),
    ),
    alert=ThemeStylingVariant(
        primary=ThemeStylingUnit(color="bg-amber-500 text-white hover:bg-amber-400 focus-visible:outline-amber-500"),
        primary_disabled=ThemeStylingUnit(color="bg-amber-100 text-orange-300 focus-visible:outline-amber-500"),
        secondary=ThemeStylingUnit(
            color="bg-white text-amber-500 ring-amber-300 hover:bg-amber-100 focus-visible:outline-amber-500",
            css=_secondary_btn_styling,
        ),
        secondary_disabled=ThemeStylingUnit(
            color="bg-white text-orange-200 ring-amber-100 focus-visible:outline-amber-500",
            css=_secondary_btn_styling,
        ),
    ),
    success=ThemeStylingVariant(
        primary=ThemeStylingUnit(color="bg-green-600 text-white hover:bg-green-500 focus-visible:outline-green-600"),
        primary_disabled=ThemeStylingUnit(color="bg-green-300 text-white focus-visible:outline-green-600"),
        secondary=ThemeStylingUnit(
            color="bg-white text-green-600 ring-green-300 hover:bg-green-100 focus-visible:outline-green-600",
            css=_secondary_btn_styling,
        ),
        secondary_disabled=ThemeStylingUnit(
            color="bg-white text-green-200 ring-green-100 focus-visible:outline-green-600",
            css=_secondary_btn_styling,
        ),
    ),
    info=ThemeStylingVariant(
        primary=ThemeStylingUnit(color="bg-sky-600 text-white hover:bg-sky-500 focus-visible:outline-sky-600"),
        primary_disabled=ThemeStylingUnit(color="bg-sky-300 text-white focus-visible:outline-sky-600"),
        secondary=ThemeStylingUnit(
            color="bg-white text-sky-600 ring-sky-300 hover:bg-sky-100 focus-visible:outline-sky-600",
            css=_secondary_btn_styling,
        ),
        secondary_disabled=ThemeStylingUnit(
            color="bg-white text-sky-200 ring-sky-100 focus-visible:outline-sky-600",
            css=_secondary_btn_styling,
        ),
    ),
)


def get_styling_css(
    variant: "ThemeVariant | None" = None,
    color: "ThemeColor | None" = None,
    disabled: "bool | None" = None,
):
    """
    Dynamically access CSS styling classes for a specific variant and state.

    E.g. following two calls get styling classes for:
    1. Secondary error state
    1. Secondary alert disabled state
    2. Primary default disabled state
    ```py
    get_styling_css('secondary', 'error')
    get_styling_css('secondary', 'alert', disabled=True)
    get_styling_css(disabled=True)
    ```
    """
    variant = variant or "primary"
    color = color or "default"
    disabled = disabled if disabled is not None else False

    color_variants: ThemeStylingVariant = getattr(theme, color)

    if variant not in VARIANTS:
        raise ValueError(f'Unknown theme variant "{variant}", must be one of {VARIANTS}')

    variant_name = variant if not disabled else f"{variant}_disabled"
    styling: ThemeStylingUnit = getattr(color_variants, variant_name)

    return f"{styling.color} {styling.css}".strip()


#####################################
# BUTTON
#####################################

# A near line-for-line parallel of the vendored Django port's button template,
# in Jinja2 syntax. `{% html_attrs ... %}` becomes a call to the `html_attrs`
# global registered above; everything else (the if/else branch, `{{ var }}`,
# the `{# comment #}`) is shared Jinja2/Django syntax.
button_template_str = """
    {# Based on buttons from https://tailwindui.com/components/application-ui/overlays/modals #}

    {% if is_link %}
    <a
        href="{{ href }}"
        {{ html_attrs(attrs, btn_class, "no-underline") }}
    >
    {% else %}
    <button
        type="{{ type }}"
        {% if disabled %} disabled {% endif %}
        {{ html_attrs(attrs, btn_class) }}
    >
    {% endif %}

        {{ slot_content }}

    {% if is_link %}
    </a>
    {% else %}
    </button>
    {% endif %}
"""


class ButtonData(NamedTuple):
    href: str | None = None
    link: bool | None = None
    disabled: bool | None = False
    variant: "ThemeVariant | Literal['plain']" = "primary"
    color: "ThemeColor | str" = "default"
    type: str | None = "button"
    attrs: dict | None = None
    slot_content: str | None = ""


def button(data: ButtonData):
    common_css = (
        "inline-flex w-full text-sm font-semibold"
        " sm:mt-0 sm:w-auto focus-visible:outline-2 focus-visible:outline-offset-2"
    )
    if data.variant == "plain":
        all_css_class = common_css
    else:
        button_classes = get_styling_css(data.variant, data.color, data.disabled)  # type: ignore[arg-type]
        all_css_class = f"{button_classes} {common_css} px-3 py-2 justify-center rounded-md shadow-sm"

    is_link = not data.disabled and (data.href or data.link)

    all_attrs = {**(data.attrs or {})}
    if data.disabled:
        all_attrs["aria-disabled"] = "true"

    return lazy_load_template(button_template_str).render(
        href=data.href,
        disabled=data.disabled,
        type=data.type,
        btn_class=all_css_class,
        attrs=all_attrs,
        is_link=is_link,
        slot_content=data.slot_content,
    )


#####################################
#
# IMPLEMENTATION END
#
#####################################


# ----------- TESTS START ------------ #
# The code above is also used when benchmarking.
# The section below is NOT included.

# The expected output is observed, then locked (see /CLAUDE.md). The class
# string matches the Django port's (same merge-and-dedupe of the class sources);
# the surrounding whitespace is Jinja2's own, so the string is not byte-identical
# to the other engines' (docs/design/benchmarking.md section 6.5).

EXPECTED_HTML = (
    "\n    \n\n    \n    <a\n"
    '        href="https://example.com"\n'
    '         class="py-2 px-4 bg-blue-600 text-white hover:bg-blue-500'
    " focus-visible:outline-blue-600 transition inline-flex w-full text-sm font-semibold"
    " sm:mt-0 sm:w-auto focus-visible:outline-2 focus-visible:outline-offset-2"
    ' px-3 justify-center rounded-md shadow-sm no-underline"\n'
    "    >\n    \n\n        Click me!\n\n    \n    </a>\n    "
)


def test_render():
    data = gen_render_data()
    rendered = render(data)
    assert rendered == EXPECTED_HTML
