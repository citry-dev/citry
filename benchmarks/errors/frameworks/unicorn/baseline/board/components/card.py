from typing import Literal

from django_unicorn.components import UnicornView

from .project_list import ProjectListView


class CardView(UnicornView):
    # Set from the {% unicorn "card" %} tag's keyword arguments. django-unicorn
    # sets each one as an attribute when it creates the card.
    title: str = ''
    count: int = 0
    tone: Literal['plain', 'accent'] = 'plain'

    # The Hide button runs this. The child-components docs reach the parent
    # through self.parent, which pyright types as any component, so the card
    # first checks that its parent is the card list.
    def hide(self):
        assert isinstance(self.parent, ProjectListView)
        self.parent.hide(self.title)
        # Render the card list again too, so the hidden card leaves the page.
        self.parent.force_render = True
