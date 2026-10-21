from collections.abc import Callable
from typing import Literal

import reflex as rx
from reflex.event import EventType


def card(
    title: rx.Var[str],
    count: rx.Var[int],
    tone: rx.Var[Literal["plain", "accent"]],
    # The card hands its title and count to `footer`, which builds the footer link.
    footer: Callable[[rx.Var[str], rx.Var[int]], rx.Component],
    # The event the page passes already carries the card's title, so the card sends nothing.
    on_hide: EventType[()],
) -> rx.Component:
    return rx.card(
        rx.text(title, ": ", count, " tasks"),
        rx.box(footer(title, count)),
        # The card only announces the click; the page decides what hiding means.
        rx.button("Hide", type="button", on_click=on_hide),
        class_name=f"card card--{tone}",
        # The project's title keys the card, so React matches each card to its
        # project when an earlier one is hidden.
        key=title,
    )
