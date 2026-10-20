from django_unicorn.components import UnicornView


class DetailsView(UnicornView):
    # Whether the details show. The Details button's built-in `$toggle('open')`
    # action flips it on the server, and the status line receives it as input.
    open: bool = False

    # The status line inside the details calls this from its own close().
    def close(self):
        self.open = False
