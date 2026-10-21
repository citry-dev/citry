import reflex as rx


class SharedState(rx.State):
    """Values any component reads straight from the state, without taking them as arguments.

    A separate module, because the card cannot import the page's module, which imports the card.
    """

    # Every card shows the board's name.
    board_name: rx.Field[str] = rx.field("Projects")
