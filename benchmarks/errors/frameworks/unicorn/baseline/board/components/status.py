from django_unicorn.components import UnicornView

from .details import DetailsView


class StatusView(UnicornView):
    # Set from the {% unicorn "status" %} tag each time the details render.
    open: bool = False

    # The Close button runs this. Like the card, the status line reaches its
    # parent through self.parent and first checks that it is the details.
    def close(self):
        assert isinstance(self.parent, DetailsView)
        self.parent.close()
        # Render the details again too, so the details text hides.
        self.parent.force_render = True
