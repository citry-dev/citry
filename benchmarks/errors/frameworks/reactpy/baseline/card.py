from collections.abc import Callable
from typing import Literal

from reactpy import component, html
from reactpy.types import VdomDict


@component
def Card(
    title: str,
    count: int,
    tone: Literal["plain", "accent"],
    # The card hands its title and count to `footer`, which builds the footer link.
    footer: Callable[[str, int], VdomDict],
    # The card tells the page which card to hide by its title.
    on_hide: Callable[[str], None],
) -> VdomDict:
    return html.article(
        {"class_name": f"card card--{tone}"},
        html.p(f"{title}: {count} tasks"),
        html.footer(footer(title, count)),
        # The card only announces the click; the page decides what hiding means.
        html.button({"type": "button", "on_click": lambda event: on_hide(title)}, "Hide"),
    )

