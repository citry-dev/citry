import reflex as rx
from reflex.event import EventType


# The status line only shows the details panel's state, so the panel owns
# `open` and the status line asks it to close through `on_close`.
def status(open: rx.Var[bool], on_close: EventType[()]) -> rx.Component:
    return rx.text(
        "Status: ",
        rx.cond(open, "open", "closed"),
        " ",
        rx.button("Close", type="button", on_click=on_close),
    )
