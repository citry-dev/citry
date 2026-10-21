from collections.abc import Callable
from typing import Literal

from reactpy import component, create_context, html, use_context
from reactpy.types import VdomDict

# The board's name, which the page provides to every card inside it, so no
# card takes it as an argument.
BoardContext = create_context("")


@component
def Card(
    title: str,
    count: int,
    tone: Literal["plain", "accent"],
    # The card hands its title and count to `footer`, which builds the footer link.
    footer: Callable[[str, int], VdomDict],
    # The page's handler already knows which card it hides, so the card passes nothing.
    on_hide: Callable[[], None],
) -> VdomDict:
    board_name = use_context(BoardContext)
    return html.article(
        {"class_name": f"card card--{tone}"},
        html.p(f"{title}: {count} tasks"),
        html.p(f"Board: {board_name}"),
        html.footer(footer(title, count)),
        # The card only announces the click; the page decides what hiding means.
        html.button({"type": "button", "on_click": lambda event: on_hide()}, "Hide"),
    )
