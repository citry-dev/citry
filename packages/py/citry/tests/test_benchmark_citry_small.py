# Citry port of the django-components small benchmark scenario
# (test_benchmark_djc_small.py, vendored in this directory): the same Button
# component, theme data, and render entrypoints, expressed in citry. The
# benchmark harness reads this file as a source string and slices it at the
# markers below, so the code outside the pytest section must stay
# self-contained. See docs/design/benchmarking.md.

from typing import Literal, NamedTuple, TypeAlias

from citry import Citry, Component

# ----------- IMPORTS END ------------ #

# There is no Const variant of the small scenario: a single dynamic Button has
# no render-invariant literals to mark, so the Const optimization has nothing
# to fold here (docs/design/benchmarking.md section 6.4). The large scenario's
# Const variant (test_benchmark_citry_const.py) is where Const is exercised.

app = Citry()

#####################################
#
# IMPLEMENTATION START
#
#####################################

#####################################
# RENDER ENTRYPOINT
#####################################


def gen_render_data():
    data = {
        "href": "https://example.com",
        "disabled": False,
        "variant": "primary",
        "type": "button",
        "attrs": {
            "class": "py-2 px-4",
        },
    }
    return data


def render(data: dict):
    return str(Button(**data, slots={"content": "Click me!"}))


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


class Button(Component):
    citry = app

    class Kwargs:
        href: "str | None" = None
        link: "bool | None" = None
        disabled: "bool | None" = False
        variant: "ThemeVariant | Literal['plain']" = "primary"
        color: "ThemeColor | str" = "default"
        type: "str | None" = "button"
        attrs: "dict | None" = None

    def template_data(self, kwargs, slots):
        common_css = (
            "inline-flex w-full text-sm font-semibold"
            " sm:mt-0 sm:w-auto focus-visible:outline-2 focus-visible:outline-offset-2"
        )
        if kwargs.variant == "plain":
            all_css_class = common_css
        else:
            button_classes = get_styling_css(kwargs.variant, kwargs.color, kwargs.disabled)
            all_css_class = f"{button_classes} {common_css} px-3 py-2 justify-center rounded-md shadow-sm"

        is_link = not kwargs.disabled and (kwargs.href or kwargs.link)

        all_attrs = {**(kwargs.attrs or {})}
        if kwargs.disabled:
            all_attrs["aria-disabled"] = "true"

        return {
            "href": kwargs.href,
            "disabled": kwargs.disabled,
            "type": kwargs.type,
            "btn_class": all_css_class,
            "attrs": all_attrs,
            "is_link": is_link,
        }

    # The DJC original wraps the same content in <a> or <button> with
    # unbalanced open/close tags across {% if %} branches; citry templates are
    # well-formed HTML, so each branch is a complete element. Class sources
    # merge in source order (c-bind's class, then btn_class, then the static
    # class), matching DJC's `{% html_attrs attrs class=btn_class ... %}`.
    template = """
        {# Based on buttons from https://tailwindui.com/components/application-ui/overlays/modals #}

        <a
            c-if="is_link"
            c-href="href"
            c-bind="attrs"
            c-class="btn_class"
            class="no-underline"
        ><c-slot name="content" /></a>
        <button
            c-else
            c-type="type"
            c-disabled="disabled"
            c-bind="attrs"
            c-class="btn_class"
        ><c-slot name="content" /></button>
    """


#####################################
#
# IMPLEMENTATION END
#
#####################################


# ----------- TESTS START ------------ #
# The code above is also used when benchmarking.
# The section below is NOT included.

# The expected output is observed, then locked (see /CLAUDE.md). The
# `data-cid-c1` marker is deterministic in tests via the conftest fixture.

EXPECTED_HTML = (
    "\n        \n\n        "
    '<a href="https://example.com" class="py-2 px-4 bg-blue-600 text-white hover:bg-blue-500'
    " focus-visible:outline-blue-600 transition inline-flex w-full text-sm font-semibold"
    " sm:mt-0 sm:w-auto focus-visible:outline-2 focus-visible:outline-offset-2"
    ' px-3 justify-center rounded-md shadow-sm no-underline" data-cid-c1="">'
    "Click me!</a>\n    "
)


def test_render():
    data = gen_render_data()
    rendered = render(data)
    assert rendered == EXPECTED_HTML
