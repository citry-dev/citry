from collections.abc import Callable

from reactpy import component, html
from reactpy.types import VdomDict


# The status line only shows the details panel's state, so the panel owns
# `open` and the status line asks it to close through `on_close`.
@component
def Status(open: bool, on_close: Callable[[], None]) -> VdomDict:
    return html.p(
        f"Status: {'open' if open else 'closed'} ",
        html.button({"type": "button", "on_click": lambda event: on_close()}, "Close"),
    )
