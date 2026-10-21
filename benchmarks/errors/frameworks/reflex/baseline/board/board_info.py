import reflex as rx


class BoardInfoState(rx.State):
    """The board's values, which any component reads straight from the state, not as arguments.

    A separate module, because the card cannot import the page's module, which imports the card.
    """

    # Every card shows the board's name.
    board_name: rx.Field[str] = rx.field("Projects")
